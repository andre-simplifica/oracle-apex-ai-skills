from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SKILLS = {
    "oracle-apex-ai-skills",
    "oracle-apex-dev",
    "oracle-apex-export",
    "oracle-apex-object-lock",
}


class RepositoryContractTests(unittest.TestCase):
    def test_every_core_skill_has_required_metadata(self) -> None:
        for name in EXPECTED_SKILLS:
            root = REPO_ROOT / "skills" / name
            skill = (root / "SKILL.md").read_text(encoding="utf-8")
            metadata = (root / "agents" / "openai.yaml").read_text(
                encoding="utf-8"
            )
            self.assertRegex(skill, rf"(?m)^name: {re.escape(name)}$")
            self.assertRegex(skill, r"(?m)^description: .+")
            self.assertIn("default_prompt:", metadata)
            self.assertNotIn("[TODO", skill)
            frontmatter = skill.split("---", 2)[1]
            description_line = next(
                line for line in frontmatter.splitlines()
                if line.startswith("description:")
            )
            description_value = description_line.split(":", 1)[1].strip()
            if not description_value.startswith(("'", '"')):
                self.assertNotIn(
                    ": ",
                    description_value,
                    "A plain YAML description containing ': ' must be quoted.",
                )

    def test_object_lock_assets_are_complete(self) -> None:
        root = (
            REPO_ROOT
            / "skills"
            / "oracle-apex-object-lock"
            / "assets"
            / "database"
        )
        required = {
            "install.sql",
            "audit-installation.sql",
            "validate-installation.sql",
            "purge-history.sql",
            "uninstall.sql",
            "packages/pk_dev_object_lock.pks",
            "packages/pk_dev_object_lock.pkb",
        }
        self.assertEqual(
            required,
            {
                path.relative_to(root).as_posix()
                for path in root.rglob("*")
                if path.is_file()
            },
        )
        for relative in (
            "install.sql",
            "audit-installation.sql",
            "validate-installation.sql",
            "purge-history.sql",
            "uninstall.sql",
        ):
            script = (root / relative).read_text(encoding="utf-8").lower()
            self.assertIn("whenever sqlerror exit", script)
            self.assertRegex(script, r"(?m)^exit success$")

        spec = (root / "packages" / "pk_dev_object_lock.pks").read_text(
            encoding="utf-8"
        )
        body = (root / "packages" / "pk_dev_object_lock.pkb").read_text(
            encoding="utf-8"
        )
        self.assertIn("c_runtime_version", spec)
        for symbol in (
            "func_runtime_version",
            "proc_expirar_locks",
            "proc_purgar_historico",
            "proc_adquirir_lock",
            "proc_renovar_lock",
            "proc_liberar_lock",
            "proc_assert_lock_compilacao",
            "func_status_lock",
            "func_status_recente",
        ):
            self.assertIn(symbol, spec.lower())
            self.assertIn(symbol, body.lower())
        self.assertIn("l_flag in ('s', 'y', 'sim', 'yes', 'true', '1')", body.lower())
        self.assertIn("dev_object_lock.object_name%type", body.lower())
        self.assertIn("dev_object_lock.locked_by%type", body.lower())
        install = (root / "install.sql").read_text(encoding="utf-8")
        for included in re.findall(r"(?m)^@@(.+)$", install):
            self.assertTrue(
                (root / included.strip()).is_file(),
                f"Missing SQL include from install.sql: {included}",
            )

    def test_compatibility_record_matches_skills(self) -> None:
        compatibility = json.loads(
            (REPO_ROOT / "templates" / "compatibility.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(compatibility["schema_version"], 2)
        self.assertEqual(compatibility["apex"]["minimum_supported"], "24.2")
        self.assertEqual(
            compatibility["apex"]["feature_gates"][
                "dynamic_content_return_clob"
            ],
            "22.2",
        )
        self.assertEqual(
            compatibility["apex"]["feature_gates"]["apex_26_1_public_apis"],
            "26.1",
        )
        self.assertEqual(compatibility["apex"]["apexlang_policy"], "disabled")
        self.assertEqual(
            compatibility["apex"]["official_export_before_26_1"],
            ["split-sql", "readable-yaml", "monolithic-sql"],
        )
        self.assertEqual(
            compatibility["apex"]["official_export_from_26_1"],
            ["split-sql", "monolithic-sql"],
        )
        self.assertEqual(set(compatibility["core_skills"]), EXPECTED_SKILLS)
        self.assertEqual(
            compatibility["database"]["object_lock_runtime_required"], "1.1.0"
        )
        self.assertEqual(compatibility["kit_version"], "1.2.2")
        self.assertEqual(
            (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip(),
            compatibility["kit_version"],
        )

    def test_export_skill_defines_baseline_release_and_pending(self) -> None:
        export_root = REPO_ROOT / "skills" / "oracle-apex-export"
        combined = "\n".join(
            path.read_text(encoding="utf-8")
            for path in sorted(export_root.rglob("*.md"))
        ).lower()
        for term in (
            "initial-baseline",
            "release",
            "pending",
            "complete application",
            "structural ddl",
            "monolithic",
            "parallel-export.md",
            "same confirmed snapshot",
            "release-bundle.md",
            "partial",
            "pending ddl/dml",
            "export-retention.md",
        ):
            self.assertIn(term, combined)

    def test_project_export_policy_has_five_file_and_pending_contract(self) -> None:
        policy = json.loads(
            (REPO_ROOT / "templates" / "export-policy.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            policy["database_release"]["five_file_groups"],
            [
                "package_specs",
                "views",
                "package_bodies",
                "triggers",
                "compile_objects",
            ],
        )
        self.assertEqual(policy["pending"]["ddl_file"], "pending_ddl.sql")
        self.assertEqual(policy["pending"]["dml_file"], "pending_dml.sql")
        self.assertFalse(policy["pending"]["allow_apex_components"])
        self.assertFalse(policy["pending"]["allow_standalone_object_source"])
        self.assertEqual(policy["schema_version"], 2)
        self.assertEqual(policy["apex"]["readable_yaml_mode"], "before-26.1")
        self.assertEqual(policy["apex"]["apexlang_policy"], "disabled")

    def test_managed_export_tools_are_present(self) -> None:
        for relative in (
            "scripts/check_pending_migrations.py",
            "scripts/manage_export_retention.py",
            "scripts/apex_version.py",
            "scripts/validate_apex_compatibility.py",
            "scripts/validate_apex_export.py",
            "scripts/validate_release_bundle.py",
        ):
            self.assertTrue((REPO_ROOT / relative).is_file())

    def test_personal_codex_installer_uses_current_user_location(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env.pop("CODEX_HOME", None)
            result = subprocess.run(
                ["bash", str(REPO_ROOT / "scripts" / "install_codex.sh")],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            for skill in EXPECTED_SKILLS:
                installed = home / ".agents" / "skills" / skill
                self.assertTrue(installed.is_symlink())
                self.assertEqual(
                    (REPO_ROOT / "skills" / skill).resolve(),
                    installed.resolve(),
                )
            self.assertFalse((home / ".codex" / "skills").exists())

    def test_personal_codex_installer_migrates_legacy_copy_only_with_flag(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            legacy = home / ".codex" / "skills" / "oracle-apex-dev"
            legacy.mkdir(parents=True)
            (legacy / "marker.txt").write_text("legacy", encoding="utf-8")
            env = os.environ.copy()
            env["HOME"] = str(home)
            env.pop("CODEX_HOME", None)
            command = ["bash", str(REPO_ROOT / "scripts" / "install_codex.sh")]

            refused = subprocess.run(
                command,
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(0, refused.returncode)
            self.assertTrue((legacy / "marker.txt").is_file())

            migrated = subprocess.run(
                [*command, "--replace-existing"],
                cwd=REPO_ROOT,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(0, migrated.returncode, migrated.stderr)
            self.assertFalse(legacy.exists())
            backups = list(
                (home / ".agents" / "skill-backups").glob(
                    "oracle-apex-ai-skills-*/legacy-codex-skills/oracle-apex-dev/marker.txt"
                )
            )
            self.assertEqual(1, len(backups))

    def test_local_markdown_links_resolve(self) -> None:
        markdown_files = [
            path
            for path in REPO_ROOT.rglob("*.md")
            if ".git" not in path.parts and ".tmp" not in path.parts
        ]
        failures = []
        for markdown in markdown_files:
            content = markdown.read_text(encoding="utf-8")
            for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", content):
                target = target.strip()
                if (
                    not target
                    or target.startswith(("http://", "https://", "mailto:", "#"))
                ):
                    continue
                path_text = target.split("#", 1)[0]
                if path_text.startswith("<") and path_text.endswith(">"):
                    path_text = path_text[1:-1]
                resolved = (markdown.parent / path_text).resolve()
                if not resolved.exists():
                    failures.append(
                        f"{markdown.relative_to(REPO_ROOT)} -> {target}"
                    )
        self.assertEqual([], failures)


if __name__ == "__main__":
    unittest.main()
