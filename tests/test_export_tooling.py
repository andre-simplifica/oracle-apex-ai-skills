from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Optional
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_script(
    relative: str, *arguments: str, expected_returncode: int = 0
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(REPO_ROOT / relative), *arguments],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != expected_returncode:
        raise AssertionError(
            f"Unexpected return code {completed.returncode}\n"
            f"STDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    return completed


class ExportToolingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name) / "project"
        self.project.mkdir()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def initialize_policy(self) -> dict:
        policy = json.loads(
            (REPO_ROOT / "templates/export-policy.json").read_text(
                encoding="utf-8"
            )
        )
        policy_path = self.project / ".oracle-apex-ai/export-policy.json"
        policy_path.parent.mkdir(parents=True)
        policy_path.write_text(
            json.dumps(policy, indent=2) + "\n", encoding="utf-8"
        )
        return policy

    def initialize_pending(self) -> Path:
        self.initialize_policy()
        pending = self.project / "db/migrations/pending"
        pending.mkdir(parents=True)
        shutil.copy2(
            REPO_ROOT / "templates/pending-ddl.sql",
            pending / "pending_ddl.sql",
        )
        shutil.copy2(
            REPO_ROOT / "templates/pending-dml.sql",
            pending / "pending_dml.sql",
        )
        return pending

    def write_apex_export(
        self,
        *,
        app_id: int = 100,
        include_readable: bool,
        quoted_scn: bool = False,
    ) -> Path:
        root = self.project / f"apex/app_{app_id}"
        (root / "application/pages").mkdir(parents=True)
        if include_readable:
            (root / "readable/application/pages").mkdir(parents=True)
        scn = "'1'" if quoted_scn else "1"
        (root / "install.sql").write_text(
            "@application/create_application.sql\n", encoding="utf-8"
        )
        (root / "application/create_application.sql").write_text(
            "begin\nwwv_flow_imp.create_flow("
            f"p_default_application_id=>{app_id},p_version_scn=>{scn});\n"
            "end;\n/\n",
            encoding="utf-8",
        )
        (root / "application/pages/page_00001.sql").write_text(
            "begin null; end;\n/\n", encoding="utf-8"
        )
        if include_readable:
            (root / "readable/application/pages/p00001.yaml").write_text(
                "id: 1\n", encoding="utf-8"
            )
        (root / f"f{app_id}.sql").write_text(
            "begin\nwwv_flow_imp.create_flow("
            f"p_default_application_id=>{app_id},"
            "p_flow_status=>'AVAILABLE_W_EDIT_LINK',"
            f"p_version_scn=>{scn});\nend;\n/\n",
            encoding="utf-8",
        )
        return root

    def test_pending_contract_accepts_two_clean_files(self) -> None:
        self.initialize_pending()
        completed = run_script(
            "scripts/check_pending_migrations.py",
            "--project-root",
            str(self.project),
        )
        self.assertIn("PENDING_CONTRACT OK files=2", completed.stdout)

    def test_pending_contract_rejects_apex_and_standalone_objects(self) -> None:
        pending = self.initialize_pending()
        (pending / "pending_ddl.sql").write_text(
            "begin\n  wwv_flow_imp_page.create_page(p_id=>1);\nend;\n/\n"
            "create or replace package pk_wrong as end;\n/\n",
            encoding="utf-8",
        )
        completed = run_script(
            "scripts/check_pending_migrations.py",
            "--project-root",
            str(self.project),
            expected_returncode=1,
        )
        self.assertIn("APEX application/page/component source", completed.stdout)
        self.assertIn("canonical object export", completed.stdout)

    def write_release_bundle(
        self, snapshot_id: int, scope: str, base_snapshot_id: Optional[int] = None
    ) -> Path:
        directory = self.project / "db/releases/2026-08-22"
        directory.mkdir(parents=True)
        groups = (
            ("01", "package_specs", "PACKAGE", "create or replace package PK_A as end PK_A;\n/"),
            ("02", "views", "VIEW", "create or replace view VW_A as select 1 n from dual;"),
            ("03", "package_bodies", "PACKAGE BODY", "create or replace package body PK_A as end PK_A;\n/"),
            (
                "04",
                "triggers",
                "TRIGGER",
                "-- NO CHANGES" if scope == "partial" else "-- NO OBJECTS",
            ),
            ("05", "compile_objects", "COMPILE", "-- No project-approved compile routine configured."),
        )
        for order, group, object_type, body in groups:
            lines = [
                "-- ORACLE_APEX_AI_RELEASE",
                f"-- SNAPSHOT_ID: {snapshot_id}",
                f"-- SCOPE: {scope.upper()}",
            ]
            if base_snapshot_id is not None:
                lines.append(f"-- BASE_SNAPSHOT_ID: {base_snapshot_id}")
            lines.extend((f"-- OBJECT_GROUP: {object_type}", body, ""))
            (directory / f"snapshot_{snapshot_id}_{scope}_{order}_{group}.sql").write_text(
                "\n".join(lines), encoding="utf-8"
            )
        return directory

    def test_release_validator_accepts_full_and_partial_five_file_layout(self) -> None:
        full = self.write_release_bundle(10, "full")
        completed = run_script(
            "scripts/validate_release_bundle.py",
            "--directory",
            str(full),
            "--snapshot-id",
            "10",
            "--scope",
            "full",
        )
        self.assertIn("RELEASE_BUNDLE OK scope=FULL snapshot=10 files=5", completed.stdout)

        shutil.rmtree(full)
        partial = self.write_release_bundle(11, "partial", 10)
        completed = run_script(
            "scripts/validate_release_bundle.py",
            "--directory",
            str(partial),
            "--snapshot-id",
            "11",
            "--scope",
            "partial",
            "--base-snapshot-id",
            "10",
        )
        self.assertIn("RELEASE_BUNDLE OK scope=PARTIAL snapshot=11 files=5", completed.stdout)

    def test_retention_is_report_only_by_default_and_guarded_when_applied(self) -> None:
        policy = self.initialize_policy()
        releases = self.project / policy["database_release"]["output_directory"]
        for day in range(1, 16):
            (releases / f"2026-08-{day:02d}").mkdir(parents=True)

        completed = run_script(
            "scripts/manage_export_retention.py",
            "status",
            "--project-root",
            str(self.project),
        )
        self.assertIn("RETENTION_DUE YES", completed.stdout)
        self.assertEqual(completed.stdout.count("CANDIDATE "), 5)

        policy["retention"]["repository_releases"]["mode"] = "prune"
        (self.project / ".oracle-apex-ai/export-policy.json").write_text(
            json.dumps(policy, indent=2) + "\n", encoding="utf-8"
        )
        run_script(
            "scripts/manage_export_retention.py",
            "prune",
            "--project-root",
            str(self.project),
            "--apply",
            "--confirm",
            "PRUNE_OLD_RELEASES",
        )
        self.assertEqual(len(list(releases.iterdir())), 10)

    def test_database_retention_emits_preflight_only_without_confirmation(self) -> None:
        self.initialize_policy()
        completed = run_script(
            "scripts/manage_export_retention.py",
            "database-sql",
            "--project-root",
            str(self.project),
            "--include-disabled",
            "--owner",
            "APP_SCHEMA",
        )
        self.assertIn("select count(*) snapshot_count", completed.stdout)
        self.assertNotIn("begin\n    PK_DDL_SNAPSHOT", completed.stdout)
        self.assertIn("EMIT_DB_SNAPSHOT_PURGE", completed.stdout)

    def test_apex_validator_checks_pre_26_1_atomic_formats(self) -> None:
        root = self.write_apex_export(include_readable=True)
        completed = run_script(
            "scripts/validate_apex_export.py",
            "--root",
            str(root),
            "--app-id",
            "100",
            "--apex-version",
            "24.2",
        )
        self.assertIn(
            "APEX_EXPORT OK atomic_formats=split-sql,readable-yaml,monolithic-sql",
            completed.stdout,
        )

    def test_apex_validator_checks_26_1_sql_formats_and_quoted_scn(self) -> None:
        root = self.write_apex_export(
            include_readable=False,
            quoted_scn=True,
        )
        completed = run_script(
            "scripts/validate_apex_export.py",
            "--root",
            str(root),
            "--app-id",
            "100",
            "--apex-version",
            "26.1.3",
        )
        self.assertIn(
            "APEX_COMPATIBILITY OK version=26.1.3 status=SUPPORTED_26_1_PLUS",
            completed.stdout,
        )
        self.assertIn("APEX_PAGES OK split=1 readable=NOT_REQUIRED", completed.stdout)
        self.assertIn(
            "APEX_EXPORT OK atomic_formats=split-sql,monolithic-sql",
            completed.stdout,
        )

    def test_apex_validator_rejects_readable_yaml_on_26_1(self) -> None:
        root = self.write_apex_export(include_readable=True)
        completed = run_script(
            "scripts/validate_apex_export.py",
            "--root",
            str(root),
            "--app-id",
            "100",
            "--apex-version",
            "26.1",
            expected_returncode=2,
        )
        self.assertIn("readable/ is forbidden on APEX 26.1+", completed.stderr)

    def test_apex_validator_rejects_apexlang_artifacts_on_every_version(self) -> None:
        root = self.write_apex_export(include_readable=False)
        (root / "application.apx").write_text("not accepted\n", encoding="utf-8")
        completed = run_script(
            "scripts/validate_apex_export.py",
            "--root",
            str(root),
            "--app-id",
            "100",
            "--apex-version",
            "26.1",
            expected_returncode=2,
        )
        self.assertIn("APEXlang artifacts are disabled", completed.stderr)

    def test_apex_validator_rejects_versions_below_24_2(self) -> None:
        root = self.write_apex_export(include_readable=True)
        completed = run_script(
            "scripts/validate_apex_export.py",
            "--root",
            str(root),
            "--app-id",
            "100",
            "--apex-version",
            "23.2",
            expected_returncode=2,
        )
        self.assertIn("below the supported minimum 24.2", completed.stderr)

    def test_compatibility_validator_enforces_feature_boundaries(self) -> None:
        unsupported = run_script(
            "scripts/validate_apex_compatibility.py",
            "--apex-version",
            "23.2",
            "--json",
            expected_returncode=2,
        )
        self.assertIn("below 24.2", unsupported.stderr)
        unsupported_report = json.loads(unsupported.stdout)
        self.assertFalse(unsupported_report["supported"])
        self.assertTrue(
            unsupported_report["capabilities"]["dynamic_content_return_clob"]
        )

        legacy = run_script(
            "scripts/validate_apex_compatibility.py",
            "--apex-version",
            "24.2",
            "--require",
            "readable-yaml-export",
        )
        self.assertIn("REQUIREMENT readable-yaml-export AVAILABLE", legacy.stdout)

        gated = run_script(
            "scripts/validate_apex_compatibility.py",
            "--apex-version",
            "24.2",
            "--require",
            "apex-26.1-public-apis",
            expected_returncode=2,
        )
        self.assertIn("REQUIREMENT apex-26.1-public-apis BLOCKED", gated.stdout)

        current = run_script(
            "scripts/validate_apex_compatibility.py",
            "--apex-version",
            "26.1.3",
            "--require",
            "apex-26.1-public-apis",
        )
        self.assertIn("REQUIREMENT apex-26.1-public-apis AVAILABLE", current.stdout)
        self.assertIn("OFFICIAL_EXPORT_FORMATS split-sql,monolithic-sql", current.stdout)

        apexlang = run_script(
            "scripts/validate_apex_compatibility.py",
            "--apex-version",
            "26.1.3",
            "--require",
            "apexlang",
            expected_returncode=2,
        )
        self.assertIn("REQUIREMENT apexlang BLOCKED", apexlang.stdout)
        self.assertIn("APEXlang operations are disabled", apexlang.stderr)


if __name__ == "__main__":
    unittest.main()
