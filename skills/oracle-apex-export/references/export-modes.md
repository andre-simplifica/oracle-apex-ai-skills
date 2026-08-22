# Export Modes

## Decision Table

| User intent | Mode | APEX scope | Database scope | Versioned output |
| --- | --- | --- | --- | --- |
| Inspect a page/component | `temporary-inspection` | Full or component export needed for inspection | None by default | No |
| Create version 1 / first export | `initial-baseline` | Complete application | Complete application-schema structure | Yes |
| Refresh official app source only | `application-snapshot` | Complete application | None | Yes |
| Changes complete / prepare partial release | `release` | Complete application | Objects changed from one explicit base snapshot + pending DDL/DML | Yes |
| Create a full database-object release | `release` | Complete application | All supported objects in one confirmed snapshot + pending DDL/DML | Yes |
| SQLcl export unavailable | `builder-fallback` | As permitted by profile | Separate database process | Depends on original intent |

## Temporary Inspection

Use for read-only analysis. Export to a disposable directory outside the official snapshot. Do not stage, import, or replace versioned files.

Exit when the required metadata has been inspected. Report that official source was not refreshed.

## Initial Baseline

Use only when versioned APEX/database source does not yet exist or when the user explicitly requests a new version-1 baseline.

Produce:

- complete official APEX application export;
- complete application-schema structural DDL as defined in [database-baseline.md](database-baseline.md);
- baseline metadata listing source environment, extraction time, object inventory, exclusions, and validation.

Do not use this mode for routine releases.

## Application Snapshot

Use when the user explicitly asks to refresh the official APEX snapshot without a database release.

Export the complete application, validate the candidate, then replace the official snapshot atomically or with the project's canonical script.

## Release

Use when the user says the changes are complete and requests the export/release package.

Produce:

- complete official export of the application being changed;
- versioned source for database objects changed by the release;
- the canonical five-file database bundle in full or partial scope;
- every applicable pending DDL and DML fragment;
- release inventory explaining what changed and what was excluded.

Use Git history, task scope, owned locks, pending migrations, and DEV object comparison as evidence. Do not export unrelated DEV drift.

If the project profile explicitly defines a full database snapshot release,
follow that existing contract instead of silently narrowing it to changed
objects. Capture the database source boundary once and generate every full
release artifact from the same confirmed snapshot ID. Use
[parallel-export.md](parallel-export.md) when the canonical workflow supports
coordinated APEX and database workers.

For a partial release, compare normalized object identity and DDL hash against
one explicit base snapshot. Use the same five-file layout as full scope, add
`partial` to filenames and headers, and record the base snapshot. Never infer a
drop from an object missing in the current snapshot.

## Builder Fallback

Use when SQLcl is unavailable and the project profile permits manual App Builder export.

Validate the downloaded artifact, normalize it with the project script when one exists, and preserve the same candidate-before-replace and scope checks as a SQLcl export.
