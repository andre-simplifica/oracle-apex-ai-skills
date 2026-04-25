---
name: oracle-apex-export
description: Use to guide or execute Oracle APEX 24.2 export/snapshot work with SQLcl, distinguishing official snapshots, temporary read-only exports, App Builder fallback, and Git publication according to the project profile.
---

# Oracle APEX Export

Generic skill for exporting Oracle APEX 24.2 applications.

## Before Running

1. Read `.oracle-apex-ai/project-profile.md`.
2. Confirm app id, workspace, SQLcl connection, and official snapshot folder.
3. Confirm whether the intent is an official snapshot or temporary inspection.
4. Check `git status` if there is a repository.

## Modes

- **Official snapshot**: updates the project's versioned folder, validates the diff, and may generate commit/push.
- **Temporary inspection**: exports to `/tmp` for read-only analysis. Do not stage, import, or replace the snapshot.
- **Builder fallback**: used when SQLcl/wallet/network fails and the profile allows manual export through App Builder.

## Rules

- Official snapshots must use the export options defined in the project profile.
- Prefer split/readable exports for source control when supported.
- Supporting Objects must follow the project's decision; do not assume.
- Do not mix an APEX snapshot with unrelated changes.
- Do not treat a temporary export as the official artifact.

## Validation

- `install.sql` is present for split exports.
- `application/` is present.
- `readable/` is present when the project requires readable YAML.
- Snapshot README/metadata is updated when the project requires it.
- Diff is limited to the expected scope.
- No duplicate files or accidental downloads.
