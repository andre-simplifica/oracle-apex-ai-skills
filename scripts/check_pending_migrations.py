#!/usr/bin/env python3
"""Validate the two-file pending DDL/DML contract for a consuming project."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Union


DEFAULT_CONFIG = Path(".oracle-apex-ai/export-policy.json")
APEX_MARKERS = re.compile(
    r"\b(?:wwv_flow_imp|apex_application_install|apex_application_import)\b"
    r"|\b(?:create|remove|update)_page\s*\(",
    re.IGNORECASE,
)
STANDALONE_OBJECT_DDL = re.compile(
    r"\bcreate\s+(?:or\s+replace\s+)?(?:editionable\s+|noneditionable\s+)?"
    r"(?:package(?:\s+body)?|procedure|function|view|trigger|type(?:\s+body)?|synonym)\b",
    re.IGNORECASE,
)
DDL_STATEMENT = re.compile(
    r"\b(?:create|alter|drop|truncate|comment\s+on|grant|revoke)\b",
    re.IGNORECASE,
)
DML_STATEMENT = re.compile(r"\b(?:insert\s+into|update|delete\s+from|merge\s+into)\b", re.IGNORECASE)


class ContractError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ContractError(f"Export policy is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"Expected a JSON object in {path}")
    return value


def safe_path(project_root: Path, relative: Union[str, Path]) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ContractError(f"Unsafe project-relative path: {relative}")
    target = (project_root / path).resolve(strict=False)
    if not target.is_relative_to(project_root):
        raise ContractError(f"Path escapes project root: {relative}")
    return target


def strip_comments_and_literals(sql: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    without_line_comments = re.sub(r"--[^\r\n]*", " ", without_block_comments)
    return re.sub(r"'(?:''|[^'])*'", "''", without_line_comments)


def validate_policy(policy: dict) -> dict:
    if policy.get("schema_version") != 1:
        raise ContractError("Unsupported export-policy schema_version")
    pending = policy.get("pending")
    if not isinstance(pending, dict):
        raise ContractError("export-policy pending section is missing")
    required = {
        "directory",
        "ddl_file",
        "dml_file",
        "allow_apex_components",
        "allow_standalone_object_source",
    }
    missing = sorted(required - set(pending))
    if missing:
        raise ContractError("Missing pending policy keys: " + ", ".join(missing))
    if pending["allow_apex_components"] is not False:
        raise ContractError("APEX components are never allowed in pending migrations")
    if pending["allow_standalone_object_source"] is not False:
        raise ContractError("Standalone object source is never allowed in pending migrations")
    for name in ("ddl_file", "dml_file"):
        value = pending[name]
        if not isinstance(value, str) or Path(value).name != value or not value.endswith(".sql"):
            raise ContractError(f"pending.{name} must be one SQL filename")
    if pending["ddl_file"] == pending["dml_file"]:
        raise ContractError("pending DDL and DML files must be different")
    return pending


def validate_file(path: Path, role: str) -> list[str]:
    problems: list[str] = []
    sql = path.read_text(encoding="utf-8", errors="strict")
    searchable = strip_comments_and_literals(sql)
    if APEX_MARKERS.search(searchable):
        problems.append(f"{path}: APEX application/page/component source is forbidden in pending")
    if STANDALONE_OBJECT_DDL.search(searchable):
        problems.append(
            f"{path}: package/view/trigger/routine/type/synonym source belongs in canonical object export"
        )
    if role == "DDL" and DML_STATEMENT.search(searchable):
        problems.append(f"{path}: DML belongs in the configured pending DML file")
    if role == "DML" and DDL_STATEMENT.search(searchable):
        problems.append(f"{path}: DDL belongs in the configured pending DDL file")
    return problems


def run(project_root: Path, config_path: Path) -> int:
    project_root = project_root.resolve()
    if not project_root.is_dir() or project_root == Path(project_root.anchor):
        raise ContractError(f"Unsafe or missing project root: {project_root}")
    config = config_path if config_path.is_absolute() else safe_path(project_root, config_path)
    pending = validate_policy(read_json(config))
    pending_dir = safe_path(project_root, pending["directory"])
    if not pending_dir.is_dir():
        raise ContractError(f"Pending directory is missing: {pending_dir}")

    expected = {
        pending["ddl_file"]: "DDL",
        pending["dml_file"]: "DML",
    }
    problems: list[str] = []
    for filename, role in expected.items():
        path = pending_dir / filename
        if not path.is_file():
            problems.append(f"{path}: configured pending {role} file is missing")
        else:
            problems.extend(validate_file(path, role))

    actual_sql = sorted(
        path.relative_to(pending_dir).as_posix()
        for path in pending_dir.rglob("*.sql")
        if path.is_file()
    )
    unexpected = sorted(set(actual_sql) - set(expected))
    for filename in unexpected:
        problems.append(
            f"{pending_dir / filename}: undeclared pending SQL; use only the configured DDL and DML files"
        )

    if problems:
        for problem in problems:
            print(f"ERROR {problem}")
        print(f"PENDING_CONTRACT FAIL errors={len(problems)}")
        return 1

    print(f"PENDING_DDL OK {pending_dir / pending['ddl_file']}")
    print(f"PENDING_DML OK {pending_dir / pending['dml_file']}")
    print("PENDING_CONTRACT OK files=2")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run(args.project_root, args.config)
    except (ContractError, OSError, UnicodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
