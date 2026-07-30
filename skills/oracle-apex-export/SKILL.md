---
name: oracle-apex-export
description: "Use for Oracle APEX 24.2 export and database source publication: temporary read-only inspection, the first full application/schema baseline, official application snapshots, release exports of changed database objects, and pending DDL migration packaging."
---

# Oracle APEX Export

Export Oracle APEX 24.2 applications and application-schema database source with an explicit publication intent.

## Before Exporting

1. Read repository instructions and `.oracle-apex-ai/project-profile.md`.
2. Confirm environment, app ID, workspace, schema owner, SQLcl command, and destination paths.
3. Inspect current Git status and existing versioned artifacts.
4. Determine the mode from [export-modes.md](references/export-modes.md).
5. Confirm whether official repository publication was explicitly requested.

Do not infer official export authorization from a development, diagnosis, compile, or test request.

## Modes

- `temporary-inspection`: disposable read-only APEX export outside official folders.
- `initial-baseline`: first complete APEX export plus full application-schema structural DDL.
- `application-snapshot`: complete official APEX application export only.
- `release`: complete official APEX application export plus changed database objects and pending DDL.
- `builder-fallback`: manual App Builder download when the project permits it and SQLcl export is unavailable.

Read [export-modes.md](references/export-modes.md) for entry and exit criteria.

## APEX Export Contract

For official APEX exports:

- use the app ID and export options from the project profile;
- export to a candidate directory first;
- prefer a split source tree containing `install.sql` and `application/`;
- include `readable/` when the project requires readable YAML;
- include a monolithic `f<APP_ID>.sql` when the project requires it;
- make the Supporting Objects decision explicit;
- validate candidate structure and content before replacing the official snapshot;
- compare the diff to the requested application and scope;
- keep secrets, credentials, and environment-specific substitutions out of public artifacts.

Use the project's canonical export script when one exists. Do not replace it with a generic command merely because SQLcl can export the application.

## Database Source Contract

Read:

- [database-baseline.md](references/database-baseline.md) for version 1;
- [database-release.md](references/database-release.md) for a normal release;
- [pending-migrations.md](references/pending-migrations.md) for table and structural DDL.

Never export data as part of the structural baseline or release source unless the project explicitly defines reviewed seed/reference data.

## Safety

- A temporary export never replaces an official snapshot.
- An official export never imports or applies itself.
- A release export never applies pending DDL to TEST or PROD.
- Do not generate an entire schema baseline for a focused fix.
- Do not publish unrelated changed objects merely because they exist in DEV.
- Do not treat a database connection failure as evidence that versioned objects are current.
- Preserve unrelated worktree changes.

## Validation

Before publication:

- candidate export exists and is non-empty;
- expected app ID appears in metadata;
- required split/readable/monolithic structures exist;
- database object list matches baseline or release mode;
- SQL scripts have deterministic ordering and valid SQLcl terminators;
- pending migrations remain pending and are included exactly once;
- diff is limited to expected files;
- sensitive-value scan is clean;
- repository-specific validation passes.

## Closeout

Report:

- mode and source environment;
- application exported and destination;
- database objects exported;
- pending migrations included;
- exclusions and unresolved gaps;
- candidate validation performed;
- official snapshot replaced or left unchanged;
- Git publication status;
- confirmation that nothing was imported or applied to a target environment.
