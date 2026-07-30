from __future__ import annotations

import json
from pathlib import Path
import re
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
        for relative in ("install.sql", "audit-installation.sql", "validate-installation.sql"):
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
            "proc_adquirir_lock",
            "proc_renovar_lock",
            "proc_liberar_lock",
            "proc_assert_lock_compilacao",
            "func_status_lock",
            "func_status_recente",
        ):
            self.assertIn(symbol, spec.lower())
            self.assertIn(symbol, body.lower())
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
        self.assertEqual(compatibility["apex"]["target"], "24.2")
        self.assertEqual(set(compatibility["core_skills"]), EXPECTED_SKILLS)
        self.assertEqual(
            compatibility["database"]["object_lock_runtime_required"], "1.0.0"
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
        ):
            self.assertIn(term, combined)

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
