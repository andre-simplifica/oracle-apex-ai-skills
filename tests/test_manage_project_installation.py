from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Optional
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
MANAGER = REPO_ROOT / "scripts" / "manage_project_installation.py"


def run_manager(
    *arguments: str, expected_returncode: int = 0
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, str(MANAGER), *arguments],
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


class ProjectInstallationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.project = self.root / "consumer"
        self.project.mkdir()
        self.source = self.root / "source"
        shutil.copytree(
            REPO_ROOT,
            self.source,
            ignore=shutil.ignore_patterns(".git", ".tmp"),
        )

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def initialize_source_git(self) -> str:
        commands = (
            ("init",),
            ("config", "user.email", "test@example.com"),
            ("config", "user.name", "Test User"),
            ("add", "."),
            ("commit", "-m", "fixture"),
        )
        for command in commands:
            subprocess.run(
                ["git", "-C", str(self.source), *command],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        return subprocess.run(
            ["git", "-C", str(self.source), "rev-parse", "HEAD"],
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        ).stdout.strip()

    def source_arguments(self, source: Optional[Path] = None) -> list[str]:
        source = source or self.source
        arguments = [
            "--source-root",
            str(source),
            "--source-ref",
            "HEAD" if (source / ".git").exists() else "test-ref",
            "--source-repository",
            "https://github.com/example/oracle-apex-ai-skills.git",
        ]
        if not (source / ".git").exists():
            arguments.extend(["--source-commit", "a" * 40])
        return arguments

    def test_install_dry_run_changes_nothing(self) -> None:
        completed = run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            "--dry-run",
        )

        self.assertIn("RESULT DRY_RUN_NO_FILES_CHANGED", completed.stdout)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_install_strips_credentials_from_recorded_repository_url(self) -> None:
        arguments = self.source_arguments()
        repository_index = arguments.index("--source-repository") + 1
        arguments[repository_index] = (
            "https://private-user:private-token@example.com/team/skills.git?token=x"
        )
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *arguments,
        )
        manifest = json.loads(
            (
                self.project
                / ".oracle-apex-ai"
                / "installation-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            manifest["source"]["repository"],
            "https://example.com/team/skills.git",
        )

    def test_install_from_clean_git_source_records_checked_out_head(self) -> None:
        expected_commit = self.initialize_source_git()
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        manifest = json.loads(
            (
                self.project
                / ".oracle-apex-ai"
                / "installation-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["source"]["requested_ref"], "HEAD")
        self.assertEqual(manifest["source"]["resolved_commit"], expected_commit)

    def test_install_creates_managed_kit_and_project_scaffold(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )

        for skill in (
            "oracle-apex-ai-skills",
            "oracle-apex-dev",
            "oracle-apex-export",
            "oracle-apex-object-lock",
        ):
            self.assertTrue(
                (self.project / ".agents" / "skills" / skill / "SKILL.md").is_file()
            )

        profile = self.project / ".oracle-apex-ai" / "project-profile.md"
        self.assertTrue(profile.is_file())
        self.assertTrue(
            (self.project / ".oracle-apex-ai" / "export-policy.json").is_file()
        )
        self.assertTrue(
            (self.project / "db" / "migrations" / "pending" / "pending_ddl.sql").is_file()
        )
        self.assertTrue(
            (self.project / "db" / "migrations" / "pending" / "pending_dml.sql").is_file()
        )
        self.assertTrue(
            (
                self.project
                / "Util"
                / "scripts"
                / "manage_oracle_apex_ai_skills.py"
            ).is_file()
        )

        manifest = json.loads(
            (
                self.project
                / ".oracle-apex-ai"
                / "installation-manifest.json"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(manifest["source"]["resolved_commit"], "a" * 40)
        self.assertNotIn(
            ".oracle-apex-ai/project-profile.md", manifest["managed_files"]
        )
        self.assertEqual(manifest["compatibility"]["kit_version"], "1.2.0")
        self.assertEqual(
            manifest["compatibility"]["apex_minimum_supported"], "24.2"
        )
        self.assertEqual(
            manifest["compatibility"]["dynamic_content_from"], "22.2"
        )
        self.assertEqual(
            manifest["compatibility"]["apex_26_1_features_from"], "26.1"
        )
        self.assertEqual(manifest["compatibility"]["apexlang_policy"], "disabled")
        for tool in (
            "apex_version.py",
            "check_oracle_apex_pending.py",
            "manage_oracle_apex_export_retention.py",
            "validate_oracle_apex_compatibility.py",
            "validate_oracle_apex_export.py",
            "validate_oracle_apex_release_bundle.py",
        ):
            self.assertTrue((self.project / "Util" / "scripts" / tool).is_file())

        status = run_manager(
            "status",
            "--project-root",
            str(self.project),
        )
        self.assertIn("STATUS HEALTHY", status.stdout)

        installed_manager = (
            self.project / "Util" / "scripts" / "manage_oracle_apex_ai_skills.py"
        )
        installed_status = subprocess.run(
            [
                sys.executable,
                str(installed_manager),
                "status",
                "--project-root",
                str(self.project),
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        self.assertEqual(installed_status.returncode, 0)
        self.assertIn("STATUS HEALTHY", installed_status.stdout)

    def test_install_preserves_preexisting_project_owned_files(self) -> None:
        profile = self.project / ".oracle-apex-ai" / "project-profile.md"
        profile.parent.mkdir(parents=True)
        profile.write_text("existing project profile\n", encoding="utf-8")
        pending = self.project / "db" / "migrations" / "pending" / "existing.sql"
        pending.parent.mkdir(parents=True)
        pending.write_text("-- existing pending migration\n", encoding="utf-8")

        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )

        self.assertEqual(
            profile.read_text(encoding="utf-8"), "existing project profile\n"
        )
        self.assertEqual(
            pending.read_text(encoding="utf-8"),
            "-- existing pending migration\n",
        )
        self.assertFalse(
            (self.project / ".oracle-apex-ai" / "export-policy.json").exists()
        )
        self.assertFalse(
            (pending.parent / "pending_ddl.sql").exists()
        )
        self.assertFalse(
            (pending.parent / "pending_dml.sql").exists()
        )

    def test_install_refuses_existing_core_skill_directory(self) -> None:
        existing = self.project / ".agents" / "skills" / "oracle-apex-dev"
        existing.mkdir(parents=True)
        local_file = existing / "local.md"
        local_file.write_text("keep me\n", encoding="utf-8")

        completed = run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            expected_returncode=2,
        )
        self.assertIn("would overwrite existing managed paths", completed.stderr)
        self.assertEqual(local_file.read_text(encoding="utf-8"), "keep me\n")
        self.assertFalse(
            (self.project / ".oracle-apex-ai" / "installation-manifest.json").exists()
        )

    def test_install_refuses_dirty_git_source(self) -> None:
        self.initialize_source_git()
        profile = self.source / "templates" / "project-profile.md"
        profile.write_text(
            profile.read_text(encoding="utf-8") + "\nlocal change\n",
            encoding="utf-8",
        )

        completed = run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            expected_returncode=2,
        )
        self.assertIn("uncommitted or untracked files", completed.stderr)
        self.assertEqual(list(self.project.iterdir()), [])

    def test_update_preserves_project_owned_profile(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        profile = self.project / ".oracle-apex-ai" / "project-profile.md"
        profile.write_text("project-owned\n", encoding="utf-8")

        source_copy = self.root / "source-next"
        shutil.copytree(self.source, source_copy)
        changed_skill = source_copy / "skills" / "oracle-apex-dev" / "SKILL.md"
        changed_skill.write_text(
            changed_skill.read_text(encoding="utf-8") + "\n<!-- test update -->\n",
            encoding="utf-8",
        )

        check = run_manager(
            "check",
            "--project-root",
            str(self.project),
            *self.source_arguments(source_copy),
        )
        self.assertIn("UPDATE_AVAILABLE YES", check.stdout)

        run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(source_copy),
        )
        self.assertEqual(profile.read_text(encoding="utf-8"), "project-owned\n")
        self.assertIn(
            "<!-- test update -->",
            (
                self.project
                / ".agents"
                / "skills"
                / "oracle-apex-dev"
                / "SKILL.md"
            ).read_text(encoding="utf-8"),
        )

    def test_update_preserves_all_project_owned_customizations(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        custom_files = {
            ".oracle-apex-ai/project-profile.md": "custom profile\n",
            ".oracle-apex-ai/app-patterns.md": "custom patterns\n",
            ".oracle-apex-ai/export-policy.json": '{"custom": true}\n',
            ".oracle-apex-ai/page-patterns/p00100.md": "custom page\n",
            "db/migrations/pending/pending_ddl.sql": "-- custom ddl\n",
            "db/migrations/pending/pending_dml.sql": "-- custom dml\n",
            "db/migrations/applied/kept.sql": "-- applied history\n",
        }
        for relative, content in custom_files.items():
            path = self.project / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            "--initialize-missing-project-files",
        )
        for relative, content in custom_files.items():
            self.assertEqual(content, (self.project / relative).read_text(encoding="utf-8"))

    def test_update_refuses_modified_managed_file(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        managed = (
            self.project
            / ".agents"
            / "skills"
            / "oracle-apex-dev"
            / "SKILL.md"
        )
        managed.write_text("locally changed\n", encoding="utf-8")

        completed = run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            expected_returncode=2,
        )
        self.assertIn("STATUS MODIFIED", completed.stdout)
        self.assertIn("Refusing to update", completed.stderr)
        self.assertEqual(managed.read_text(encoding="utf-8"), "locally changed\n")

    def test_update_rejects_manifest_path_outside_managed_roots(self) -> None:
        readme = self.project / "README.md"
        readme.write_text("project readme\n", encoding="utf-8")
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        manifest_path = (
            self.project / ".oracle-apex-ai" / "installation-manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["managed_files"]["README.md"] = hashlib.sha256(
            readme.read_bytes()
        ).hexdigest()
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        completed = run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            expected_returncode=2,
        )
        self.assertIn("outside the kit-owned roots", completed.stderr)
        self.assertEqual(readme.read_text(encoding="utf-8"), "project readme\n")

    def test_update_removes_only_recorded_obsolete_file(self) -> None:
        source_v1 = self.root / "source-v1"
        shutil.copytree(self.source, source_v1)
        obsolete = source_v1 / "skills" / "oracle-apex-dev" / "obsolete.md"
        obsolete.write_text("managed old file\n", encoding="utf-8")

        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(source_v1),
        )
        installed_obsolete = (
            self.project
            / ".agents"
            / "skills"
            / "oracle-apex-dev"
            / "obsolete.md"
        )
        self.assertTrue(installed_obsolete.is_file())

        run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(self.source),
        )
        self.assertFalse(installed_obsolete.exists())

    def test_doctor_reports_current_project_contract(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )

        completed = run_manager(
            "doctor",
            "--project-root",
            str(self.project),
            "--apex-version",
            "26.1.3",
        )
        self.assertIn("PROJECT_PROFILE_VERSION 3 OK", completed.stdout)
        self.assertIn(
            "EXPORT_POLICY VALID schema=2 readable_yaml=before-26.1 apexlang=disabled",
            completed.stdout,
        )
        self.assertIn("APEX_26_1_PUBLIC_APIS AVAILABLE", completed.stdout)
        self.assertIn("APEXLANG_SKILL_POLICY DISABLED", completed.stdout)
        self.assertIn("DOCTOR READY count=0", completed.stdout)

    def test_doctor_blocks_unsupported_apex_release(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        completed = run_manager(
            "doctor",
            "--project-root",
            str(self.project),
            "--apex-version",
            "23.2",
            expected_returncode=1,
        )
        self.assertIn("BLOCKER apex_version_below_24_2", completed.stdout)
        self.assertIn("DOCTOR BLOCKED", completed.stdout)

    def test_doctor_blocks_legacy_readable_policy_on_26_1(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        policy_path = self.project / ".oracle-apex-ai" / "export-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["schema_version"] = 1
        policy["apex"].pop("readable_yaml_mode")
        policy["apex"].pop("apexlang_policy")
        policy["apex"]["require_readable_yaml"] = True
        policy_path.write_text(json.dumps(policy), encoding="utf-8")

        completed = run_manager(
            "doctor",
            "--project-root",
            str(self.project),
            "--apex-version",
            "26.1",
            expected_returncode=1,
        )
        self.assertIn("BLOCKER readable_yaml_would_generate_apexlang", completed.stdout)
        self.assertIn("ADVISORY export_policy_v2_migration_required", completed.stdout)

    def test_doctor_reports_invalid_project_owned_export_policy(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        policy_path = self.project / ".oracle-apex-ai" / "export-policy.json"
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        policy["pending"]["allow_apex_components"] = True
        policy_path.write_text(json.dumps(policy), encoding="utf-8")

        completed = run_manager(
            "doctor",
            "--project-root",
            str(self.project),
        )
        self.assertIn("ADVISORY export_policy_invalid", completed.stdout)
        self.assertIn("DOCTOR ADVISORY", completed.stdout)

    def test_update_can_initialize_only_missing_project_owned_files(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            "--no-project-scaffold",
        )
        self.assertFalse(
            (self.project / ".oracle-apex-ai" / "project-profile.md").exists()
        )

        dry_run = run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            "--initialize-missing-project-files",
            "--dry-run",
        )
        self.assertIn(
            "ACTION CREATE_PROJECT_FILE .oracle-apex-ai/export-policy.json",
            dry_run.stdout,
        )
        self.assertFalse(
            (self.project / ".oracle-apex-ai" / "export-policy.json").exists()
        )

        run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
            "--initialize-missing-project-files",
        )
        self.assertTrue(
            (self.project / ".oracle-apex-ai" / "export-policy.json").is_file()
        )
        self.assertTrue(
            (
                self.project
                / "db"
                / "migrations"
                / "pending"
                / "pending_ddl.sql"
            ).is_file()
        )

    def test_update_accepts_pre_1_1_manifest_and_adds_managed_helpers(self) -> None:
        run_manager(
            "install",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )

        manifest_path = (
            self.project / ".oracle-apex-ai" / "installation-manifest.json"
        )
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        new_helpers = {
            "Util/scripts/apex_version.py",
            "Util/scripts/check_oracle_apex_pending.py",
            "Util/scripts/manage_oracle_apex_export_retention.py",
            "Util/scripts/validate_oracle_apex_compatibility.py",
            "Util/scripts/validate_oracle_apex_export.py",
            "Util/scripts/validate_oracle_apex_release_bundle.py",
        }
        for relative in new_helpers:
            manifest["managed_files"].pop(relative)
            (self.project / relative).unlink()
        manifest["compatibility"].pop("kit_version", None)
        manifest_path.write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

        completed = run_manager(
            "update",
            "--project-root",
            str(self.project),
            *self.source_arguments(),
        )
        self.assertIn("RESULT INSTALLATION_UPDATED", completed.stdout)
        for relative in new_helpers:
            self.assertTrue((self.project / relative).is_file())


if __name__ == "__main__":
    unittest.main()
