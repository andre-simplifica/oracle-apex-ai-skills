from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from target_preflight import load_expectations, render_preflight, validate_expectations


def database_target() -> dict:
    return dict(schema_version=1, session_user="APP_SCHEMA", current_schema="APP_SCHEMA",
                service_name="EXAMPLE_SERVICE", db_unique_name="EXAMPLE_DB", con_name="EXAMPLE_PDB")


class PreflightTests(unittest.TestCase):
    def test_duplicate_json_keys_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "target.json"
            value = json.dumps(database_target())
            target.write_text(value[:-1] + ', "service_name": "private-example"}')
            with self.assertRaises(ValueError) as error:
                load_expectations(target)
            self.assertNotIn("private-example", str(error.exception))

    def test_missing_or_unknown_fields_fail_without_disclosing_values(self):
        for field in database_target():
            value = database_target()
            value.pop(field)
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_expectations(value)
        for bad in (None, [], {**database_target(), "token": "private-example"},
                    {**database_target(), "service_name": "\nexit success"},
                    {**database_target(), "session_user": " "}):
            with self.assertRaises(ValueError) as error:
                validate_expectations(bad)
            self.assertNotIn("private-example", str(error.exception))

    def test_database_only_check_has_no_apex_dependency(self):
        sql = render_preflight(database_target()).lower()
        self.assertNotIn("apex_release", sql)
        self.assertNotIn("apex_applications", sql)
        self.assertIn("whenever sqlerror exit failure rollback", sql)
        self.assertIn("p_actual is null or p_expected is null", sql)
        for field in ("session_user", "current_schema", "service_name", "db_unique_name", "con_name"):
            self.assertIn(f"sys_context('userenv', '{field}'), :pf_{field}", sql)

    def test_values_are_escaped_and_sqlcl_substitution_is_disabled(self):
        target = database_target()
        target["service_name"] = "example';&define"
        sql = render_preflight(target)
        self.assertIn(":pf_service_name := 'example'';&define';", sql)
        self.assertLess(sql.index("set define off"), sql.index(":pf_service_name :="))
        self.assertNotIn("connect ", sql)

    def test_sql_versions_and_apexlang_route_are_independent(self):
        for version in ("24.2.0", "26.1.3", "26.2.0"):
            target = database_target()
            target["apex"] = dict(version=version, application_id=100, workspace="WORKSPACE_NAME",
                                  parsing_schema="APP_SCHEMA", source_format="sql")
            sql = render_preflight(target)
            self.assertIn("where application_id = :app", sql)
            self.assertIn("using :pf_apex_application_id", sql)
            self.assertIn("get_parsing_schema(p_application_id => :app)", sql)
            target["apex"]["source_format"] = "apexlang"
            with self.assertRaises(ValueError):
                render_preflight(target)
        target["apex"].update(source_format="sql", version="23.2")
        with self.assertRaises(ValueError):
            render_preflight(target)
        target["apex"].update(version="24.2", application_id=True)
        with self.assertRaises(ValueError):
            render_preflight(target)

    def test_cli_generates_private_file_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            target = path / "target.json"
            target.write_text(json.dumps(database_target()))
            output = path / "check.sql"
            command = [sys.executable, str(REPO_ROOT / "scripts/target_preflight.py"),
                       "--expect", str(target), "--output", str(output)]
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertNotIn("EXAMPLE_SERVICE", result.stdout)
            self.assertTrue(output.read_text().endswith("exit success rollback\n"))
            if os.name == "posix":
                self.assertEqual(0o600, output.stat().st_mode & 0o777)
            before = output.read_bytes()
            self.assertNotEqual(0, subprocess.run(command, capture_output=True).returncode)
            self.assertEqual(before, output.read_bytes())
