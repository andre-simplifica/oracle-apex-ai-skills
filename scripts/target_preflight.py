#!/usr/bin/env python3
"""Generate a read-only SQLcl identity check; never connect to a database."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from apex_version import evaluate_apex_version


DB_FIELDS = ("session_user", "current_schema", "service_name", "db_unique_name", "con_name")
APEX_FIELDS = ("version", "application_id", "workspace", "parsing_schema", "source_format")
SQLCL_SETTINGS = """set echo off
set verify off
set define off
set feedback off
set serveroutput on
whenever oserror exit failure rollback
whenever sqlerror exit failure rollback
"""


def validate_expectations(value: object) -> dict:
    if not isinstance(value, dict) or set(value) - {"schema_version", *DB_FIELDS, "apex"}:
        raise ValueError("Expected a target object containing only documented fields")
    if type(value.get("schema_version")) is not int or value["schema_version"] != 1:
        raise ValueError("Unsupported target schema_version")
    for field in DB_FIELDS:
        validate_text(value.get(field), field)
    if "apex" in value:
        apex = value["apex"]
        if not isinstance(apex, dict) or set(apex) != set(APEX_FIELDS):
            raise ValueError("APEX identity requires all documented fields")
        if apex["source_format"] != "sql":
            raise ValueError("This kit only checks SQL workflows; use the separate kit for APEXlang")
        for field in ("version", "workspace", "parsing_schema"):
            validate_text(apex[field], "apex." + field)
        if not evaluate_apex_version(apex["version"])["supported"]:
            raise ValueError("APEX versions below 24.2 are outside this kit")
        if type(apex["application_id"]) is not int or not 1 <= apex["application_id"] <= 999999999999:
            raise ValueError("APEX application_id must be a positive integer of at most 12 digits")
    return value


def validate_text(value: object, field: str) -> None:
    if (not isinstance(value, str) or not value.strip() or value != value.strip()
            or len(value.encode("utf-8")) > 256 or not value.isprintable()):
        raise ValueError(f"Invalid or missing target field: {field}")


def load_expectations(path: Path) -> dict:
    # Do not include JSON decode errors: they can contain private input values.
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_fields)
    except (OSError, ValueError, UnicodeError) as exc:
        raise ValueError("Cannot read target expectations as UTF-8 JSON") from exc
    return validate_expectations(value)


def unique_fields(pairs: list) -> dict:
    value: dict = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate target field")
        value[key] = item
    return value


def sql_literal(value: str) -> str:
    """Only for bind initialization, with SQLcl substitution disabled."""
    return "'" + value.replace("'", "''") + "'"


def render_preflight(expectations: dict) -> str:
    """SQLcl fragment for the SAME session; the batch owner supplies EXIT."""
    validate_expectations(expectations)
    bindings = {key: expectations[key] for key in DB_FIELDS}
    if "apex" in expectations:
        bindings.update({"apex_" + key: value for key, value in expectations["apex"].items()
                         if key != "source_format"})
    lines = [SQLCL_SETTINGS.rstrip()]
    for key, value in bindings.items():
        lines.append(f"variable pf_{key} {'number' if type(value) is int else 'varchar2(256)'}")
    lines.append("begin")
    for key, value in bindings.items():
        literal = str(value) if type(value) is int else sql_literal(value)
        lines.append(f"  :pf_{key} := {literal};")
    lines.extend(["end;", "/", "declare", "  l_actual varchar2(4000);",
                  "  l_workspace_id number;", "  l_stage varchar2(40);",
                  "  procedure check_value(p_field varchar2, p_actual varchar2, p_expected varchar2) is",
                  "  begin",
                  "    if p_actual is null or p_expected is null or",
                  "       utl_raw.cast_to_raw(p_actual) != utl_raw.cast_to_raw(p_expected) then",
                  "      raise_application_error(-20070, 'TARGET_PREFLIGHT mismatch: ' || p_field);",
                  "    end if;", "  end;", "begin"])
    for key in DB_FIELDS:
        lines.append(f"  check_value('{key}', sys_context('USERENV', '{key.upper()}'), :pf_{key});")
    if "apex" in expectations:
        lines.extend([
            "  l_stage := 'apex_version';",
            "  execute immediate 'select version_no from apex_release' into l_actual;",
            "  check_value(l_stage, l_actual, :pf_apex_version);",
            "  l_stage := 'application_workspace';",
            "  execute immediate 'select workspace_id from apex_applications where application_id = :app'",
            "    into l_workspace_id using :pf_apex_application_id;",
            "  execute immediate 'select workspace from apex_workspaces where workspace_id = :workspace'",
            "    into l_actual using l_workspace_id;",
            "  check_value(l_stage, l_actual, :pf_apex_workspace);",
            "  l_stage := 'parsing_schema';",
            "  execute immediate 'begin :result := apex_application_admin.get_parsing_schema(p_application_id => :app); end;'",
            "    using out l_actual, in :pf_apex_application_id;",
            "  check_value(l_stage, l_actual, :pf_apex_parsing_schema);",
        ])
    lines.extend([
        "  dbms_output.put_line('TARGET_PREFLIGHT PASS');",
        "exception", "  when others then",
        "    if sqlcode = -20070 then raise; end if;",
        "    raise_application_error(-20071, 'TARGET_PREFLIGHT unavailable: ' ||",
        "      nvl(l_stage, 'database_identity') || '; SQLCODE=' || to_char(sqlcode));",
        "end;", "/", "",
    ])
    return "\n".join(lines)


def write_private_file(path: Path, text: str) -> None:
    # Exclusive creation also refuses existing symlinks and prevents accidental overwrite.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect", type=Path, required=True, help="Private target JSON; no credentials")
    parser.add_argument("--output", type=Path, required=True, help="New private SQL file; never overwritten")
    args = parser.parse_args()
    try:
        sql = render_preflight(load_expectations(args.expect)) + "exit success rollback\n"
        write_private_file(args.output, sql)
    except (ValueError, OSError) as exc:
        # File paths can themselves disclose private identifiers.
        print("TARGET_PREFLIGHT ERROR: " + (str(exc) if isinstance(exc, ValueError)
                                          else "Cannot create output file"), file=sys.stderr)
        return 1
    print("TARGET_PREFLIGHT GENERATED; database not contacted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
