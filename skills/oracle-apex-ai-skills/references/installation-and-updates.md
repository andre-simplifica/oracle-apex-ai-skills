# Project Installation and Updates

The recommended Codex installation is repository-scoped:

```text
<project>/.agents/skills/oracle-apex-ai-skills/
<project>/.agents/skills/oracle-apex-dev/
<project>/.agents/skills/oracle-apex-export/
<project>/.agents/skills/oracle-apex-object-lock/
```

Codex discovers `.agents/skills` from the current directory up to the repository root. Keep the files in Git so every developer and agent uses the same version.

## Managed and Project-Owned Files

The installer manages:

```text
.agents/skills/<four-core-skills>/
.oracle-apex-ai/compatibility.json
.oracle-apex-ai/installation-manifest.json
.oracle-apex-ai/upstream-lock.json
Util/scripts/manage_oracle_apex_ai_skills.py
Util/scripts/check_oracle_apex_pending.py
Util/scripts/manage_oracle_apex_export_retention.py
Util/scripts/validate_oracle_apex_export.py
Util/scripts/validate_oracle_apex_release_bundle.py
```

The project owns and the installer never overwrites:

```text
.oracle-apex-ai/project-profile.md
.oracle-apex-ai/app-patterns.md
.oracle-apex-ai/page-patterns/
.oracle-apex-ai/export-policy.json
db/migrations/pending/pending_ddl.sql
db/migrations/pending/pending_dml.sql
db/migrations/applied/
```

## Install From GitHub

Ask the agent to:

1. Inspect the current project and Git status.
2. Clone or fetch `https://github.com/andre-simplifica/oracle-apex-ai-skills`.
3. Prefer an immutable release tag or explicit commit. If using a branch, record its resolved commit.
4. Confirm the source checkout is clean and that the requested ref resolves to its `HEAD`.
5. Run repository validation on the source.
6. Run:

```bash
python3 <source>/scripts/manage_project_installation.py install \
  --project-root <project> \
  --source-ref <tag-or-commit> \
  --dry-run
```

7. Explain every create, update, preserve, and conflict action.
8. Run the same command without `--dry-run`.
9. Run `status` and `doctor`, then inspect the Git diff.
10. Audit the object-lock runtime separately. Do not connect automatically during file installation.

If the project already contains a profile or patterns, preserve them byte-for-byte.

## Check and Update

From a freshly fetched or cloned upstream source:

```bash
python3 <source>/scripts/manage_project_installation.py check \
  --project-root <project> \
  --source-ref <tag-or-commit>

python3 <source>/scripts/manage_project_installation.py update \
  --project-root <project> \
  --source-ref <tag-or-commit> \
  --dry-run
```

Review the proposed diff, then run `update` without `--dry-run`.

For a project installed before the current profile/export-policy contract, preview missing project-owned scaffolding explicitly:

```bash
python3 <source>/scripts/manage_project_installation.py update \
  --project-root <project> \
  --source-ref <tag-or-commit> \
  --initialize-missing-project-files \
  --dry-run
```

This creates only absent templates. It never edits an existing project profile, pattern catalog, export policy, or pending file. If the project already has a profile, custom pending SQL, or an export policy whose layout cannot be inferred safely, the installer leaves that contract untouched and `doctor` reports the manual alignment needed.

The updater must stop when:

- a managed file was modified after installation;
- a managed file is missing unexpectedly;
- an existing untracked path would be overwritten;
- the previous manifest is invalid;
- the source does not contain all required skills.

Resolve conflicts intentionally. Never delete local edits or use a force option merely to make an update pass.

## What Update Does Not Do

An update does not:

- connect to Oracle;
- install or upgrade `PK_DEV_OBJECT_LOCK`;
- apply pending DDL or DML;
- prune repository releases or database snapshot tables;
- compile database objects;
- import an APEX application;
- change project-owned profile or pattern files;
- commit, push, merge, or open a PR.

If the compatibility record requires a newer object-lock runtime, report the migration and request separate DEV authorization.

## Transparent Status

Use:

```bash
python3 Util/scripts/manage_oracle_apex_ai_skills.py status --project-root .
python3 Util/scripts/manage_oracle_apex_ai_skills.py doctor --project-root .
```

Expected outcomes:

- `NOT_INSTALLED`: no installation manifest exists.
- `HEALTHY`: every managed file matches its recorded checksum.
- `MODIFIED`: at least one managed file changed locally.
- `INCOMPLETE`: a recorded managed file is missing.

The manifest records source repository, requested ref, resolved Git commit, install time, compatibility, and SHA-256 for every managed file.
