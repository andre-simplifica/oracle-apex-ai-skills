# Install in Codex

The recommended setup is a repository-scoped installation. Codex scans `.agents/skills` from the current directory up to the repository root, so checked-in skills are available to everyone working in that project.

## Ask Codex to Install It

Open the consuming project and send:

```text
Install Oracle APEX AI Skills in this project from:
https://github.com/andre-simplifica/oracle-apex-ai-skills

Use the repository-managed .agents/skills installation.
Inspect and validate the source, run the installation dry-run first, and explain the exact file diff.
Preserve existing project-owned profiles, patterns, and migrations.
Do not connect to Oracle, compile objects, import APEX, commit, or push during file installation.
Afterward, audit the object-lock runtime separately without changing the database.
```

Pasting the GitHub URL tells Codex where to fetch the source. It is not a special `@github-url` syntax. After installation, use `@Oracle APEX AI Skills` in ChatGPT/Codex desktop or `$oracle-apex-ai-skills` in Codex CLI and IDE surfaces.

## What Codex Should Do

1. Inspect the consuming repository and current Git status.
2. Clone or fetch this repository.
3. Prefer a release tag or explicit commit; record the resolved commit when a branch is requested.
4. Run `bash scripts/validate_repo.sh` in the source.
5. Run the install manager with `--dry-run`.
6. Explain every `CREATE`, `UPDATE`, `PRESERVE`, and conflict.
7. Run the installation without `--dry-run`.
8. Run `status` and inspect the consuming-project diff.
9. Audit the object-lock runtime separately.

## Manual Project Install

Clone a reviewed source:

```bash
git clone https://github.com/andre-simplifica/oracle-apex-ai-skills.git /tmp/oracle-apex-ai-skills
git -C /tmp/oracle-apex-ai-skills checkout <tag-or-commit>
bash /tmp/oracle-apex-ai-skills/scripts/validate_repo.sh
```

Preview:

```bash
python3 /tmp/oracle-apex-ai-skills/scripts/manage_project_installation.py install \
  --project-root /path/to/your/project \
  --source-ref <tag-or-commit> \
  --dry-run
```

Install:

```bash
python3 /tmp/oracle-apex-ai-skills/scripts/manage_project_installation.py install \
  --project-root /path/to/your/project \
  --source-ref <tag-or-commit>
```

Verify:

```bash
python3 /path/to/your/project/Util/scripts/manage_oracle_apex_ai_skills.py \
  status \
  --project-root /path/to/your/project
```

Expected result: `STATUS HEALTHY`.

## Installed Layout

Managed:

```text
.agents/skills/oracle-apex-ai-skills/
.agents/skills/oracle-apex-dev/
.agents/skills/oracle-apex-export/
.agents/skills/oracle-apex-object-lock/
.oracle-apex-ai/compatibility.json
.oracle-apex-ai/installation-manifest.json
.oracle-apex-ai/upstream-lock.json
Util/scripts/manage_oracle_apex_ai_skills.py
```

Initialized when missing and then owned by the consuming project:

```text
.oracle-apex-ai/project-profile.md
.oracle-apex-ai/app-patterns.md
.oracle-apex-ai/page-patterns/
db/migrations/pending/
db/migrations/applied/
```

Use `--no-project-scaffold` only when the repository already has an intentional alternative layout and its profile documents it.

## Audit Object Locks

File installation does not change Oracle. With a confirmed read-only DEV connection, run:

```bash
sql -name <dev-connection> \
  @.agents/skills/oracle-apex-object-lock/assets/database/audit-installation.sql
```

The result is `INSTALLED`, `ABSENT`, `PARTIAL`, or `INCOMPATIBLE`. Installing or upgrading the runtime requires separate authorization:

```bash
sql -name <dev-connection> \
  @.agents/skills/oracle-apex-object-lock/assets/database/install.sql
```

Do not run the installer simply because the skill files exist.

## Personal Installation

For local experimentation across projects:

```bash
git clone https://github.com/andre-simplifica/oracle-apex-ai-skills.git ~/.oracle-apex-ai-skills
bash ~/.oracle-apex-ai-skills/scripts/install_codex.sh
```

This personal symlink mode is secondary. A project-managed installation is easier for a team to review, reproduce, and update.

## Discovery

Codex normally detects skill changes automatically. If a new or updated skill does not appear, restart Codex. Current Codex skill discovery behavior is documented in the [official OpenAI skill guide](https://learn.chatgpt.com/codex/build-skills#where-codex-loads-local-skills).
