# Update and Contribute

## Check the Installed Project

Run the manager already copied into the consuming repository:

```bash
python3 Util/scripts/manage_oracle_apex_ai_skills.py status --project-root .
python3 Util/scripts/manage_oracle_apex_ai_skills.py doctor --project-root .
python3 Util/scripts/manage_oracle_apex_ai_skills.py profile-review --project-root .
```

Statuses:

- `HEALTHY`: every managed file matches its manifest.
- `NOT_INSTALLED`: no installation manifest exists.
- `MODIFIED`: a managed or metadata file changed, or an unrecorded file exists inside a managed skill.
- `INCOMPLETE`: a recorded managed file is missing.

Do not update a `MODIFIED` or `INCOMPLETE` installation until the difference is understood.

## Update From GitHub

Ask Codex:

```text
Oracle APEX AI Skills was updated. Update this project from:
https://github.com/andre-simplifica/oracle-apex-ai-skills

Use the requested release tag or commit.
Run status, doctor, check, and update --dry-run first.
Explain the exact managed-file diff and stop on local managed-file changes.
Preserve project-profile.md, app-patterns.md, page-patterns, export-policy.json, and all migrations.
Initialize newly introduced project files only when they are missing.
Do not change Oracle, import APEX, commit, or push as part of the updater.
```

Manual flow:

```bash
git clone https://github.com/andre-simplifica/oracle-apex-ai-skills.git /tmp/oracle-apex-ai-skills-next
git -C /tmp/oracle-apex-ai-skills-next checkout <tag-or-commit>
bash /tmp/oracle-apex-ai-skills-next/scripts/validate_repo.sh
```

Compare:

```bash
python3 /tmp/oracle-apex-ai-skills-next/scripts/manage_project_installation.py \
  check \
  --project-root /path/to/project \
  --source-ref <tag-or-commit>
```

Preview:

```bash
python3 /tmp/oracle-apex-ai-skills-next/scripts/manage_project_installation.py \
  update \
  --project-root /path/to/project \
  --source-ref <tag-or-commit> \
  --initialize-missing-project-files \
  --dry-run
```

Apply the file update:

```bash
python3 /tmp/oracle-apex-ai-skills-next/scripts/manage_project_installation.py \
  update \
  --project-root /path/to/project \
  --source-ref <tag-or-commit> \
  --initialize-missing-project-files
```

Then inspect the consuming-project Git diff and run its validation. Commit/push only when the project's rules or the user authorize publication.

## Update Boundaries

The updater:

- copies the four core skills;
- updates its own project manager;
- updates managed validation, retention, identity-preflight and lock-test helpers;
- updates compatibility and source/checksum metadata;
- preserves project-owned standards and migrations;
- creates a newly introduced project template only with the explicit `--initialize-missing-project-files` flag and only when absent;
- removes an obsolete managed file only when its current checksum still matches the previous manifest.

The updater never:

- connects to Oracle;
- upgrades `PK_DEV_OBJECT_LOCK`;
- applies pending DDL or DML;
- prunes repository releases or database snapshots;
- compiles PL/SQL;
- imports APEX;
- commits or pushes.

When a new kit requires a newer object-lock runtime, the compatibility diff reports it. Audit and database installation remain separate authorized operations.

## Contribute Improvements

The GitHub Actions workflow runs `bash scripts/validate_repo.sh` for pull requests
and pushes to `main`, with Python 3.10 and 3.14 on Ubuntu 24.04. Local prerequisites
are Python 3.10+, Bash, Git and ripgrep (`rg`); no pip dependency or Oracle
credential is needed. The workflow has read-only repository permissions and pins
actions to commit SHAs. It checks local contracts, not Oracle runtime behavior or
full JSON Schema compliance. Live tests remain separate authorized operations.

See [backlog-decisions.md](backlog-decisions.md) for the scope and deferred work
from the 2026-11-17 review.

Contribute generic behavior here; keep application-specific rules in the consuming project.

1. Update the source clone.
2. Create a focused branch.
3. Change only the relevant skills, references, templates, scripts, or docs.
4. Update both public READMEs when onboarding behavior changes.
5. Run:

```bash
bash scripts/validate_repo.sh
```

6. Review the complete diff for private identifiers and secrets.
7. Commit, push the branch, and open a pull request according to repository rules.

Good core contributions include APEX 24.2+ version gates, SQLcl/standard-SQL export improvements, public API catalogs, full/partial five-file release logic, pending/retention validation, cooperative-lock improvements, deterministic installer behavior, and clearer project templates. APEXlang workflows belong in a separate repository.

Package names, page IDs, customer rules, private environment names, and application-specific UI conventions belong in the consuming project's `.oracle-apex-ai/` files.
