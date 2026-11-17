from pathlib import Path
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
from profile_lint import review_profile


class ProfileLintTests(unittest.TestCase):
    def setUp(self):
        self.template = (REPO_ROOT / "templates/project-profile.md").read_text()

    def test_new_template_needs_real_identity_values(self):
        notes = review_profile(self.template)
        self.assertEqual(4, len(notes))
        self.assertTrue(all(note.startswith("field_unfilled:") for note in notes))

    def test_custom_content_is_not_echoed_or_rejected(self):
        content = self.template
        for field in ("APEX version", "SQLcl command/saved connection", "Expected SQLcl `USER`",
                      "Expected SQLcl `SERVICE_NAME` or required service token"):
            content = content.replace(f"- {field}:\n", f"- {field}: private-example\n")
        content += "\n## My custom rules\nDo not expose private-example.\n"
        self.assertEqual([], review_profile(content))
        self.assertEqual(review_profile(content), review_profile(content))

    def test_version_cases_and_fenced_examples(self):
        for marker, prefix in (("", "version_missing"),
                               ("<!-- oracle-apex-ai-project-profile-version: 2 -->", "version_old"),
                               ("<!-- oracle-apex-ai-project-profile-version: 99 -->", "version_newer"),
                               ("<!-- oracle-apex-ai-project-profile-version: x -->", "version_ambiguous")):
            with self.subTest(marker=marker):
                notes = review_profile(marker + "\n```markdown\n" + self.template + "\n```\n")
                self.assertTrue(notes[0].startswith(prefix))
                self.assertTrue(any("field_unrecognized" in note for note in notes))
        duplicate = self.template + "\n<!-- oracle-apex-ai-project-profile-version: 3 -->\n"
        self.assertTrue(review_profile(duplicate)[0].startswith("version_ambiguous"))

    def test_source_route_does_not_enable_apexlang_by_version(self):
        content = self.template.replace("- APEX version:\n", "- APEX version: 26.2.0\n")
        self.assertFalse(any(note.startswith("source_route") for note in review_profile(content)))
        content = content.replace("- APEXlang operations: disabled", "- APEXlang operations: enabled")
        self.assertTrue(any(note.startswith("source_route_review") for note in review_profile(content)))
