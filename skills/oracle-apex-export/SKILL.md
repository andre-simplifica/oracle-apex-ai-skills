---
name: oracle-apex-export
description: "Use for version-gated Oracle APEX 24.2+ standard SQL export and database source publication: temporary inspection, complete application snapshots, five-file database releases, coordinated exports, retention, and pending DDL/DML packaging. APEXlang workflows are excluded."
---

# Oracle APEX Export

Export supported Oracle APEX applications from 24.2 onward and application-schema database source with an explicit publication intent.

## Before Exporting

1. Read repository instructions and `.oracle-apex-ai/project-profile.md`.
2. Read `.oracle-apex-ai/export-policy.json` when present.
3. Confirm the configured SQLcl connection by checking the expected `USER` and `SERVICE_NAME`, then confirm app ID, workspace, schema owner, and destination paths.
4. Confirm the live APEX version and run `validate_oracle_apex_compatibility.py`; stop below 24.2.
5. Inspect current Git status and existing versioned artifacts.
6. Determine the mode from [export-modes.md](references/export-modes.md).
7. Confirm whether official repository publication was explicitly requested.

Do not infer official export authorization from a development, diagnosis, compile, or test request.

## Modes

- `temporary-inspection`: disposable read-only APEX export outside official folders.
- `initial-baseline`: first complete APEX export plus full application-schema structural DDL.
- `application-snapshot`: complete official APEX application export only.
- `release`: complete official APEX application export plus a full or partial five-file database bundle and pending DDL/DML.
- `builder-fallback`: manual App Builder download when the project permits it and SQLcl export is unavailable.

Read [export-modes.md](references/export-modes.md) for entry and exit criteria.

## APEX Export Contract

For official APEX exports:

- use the app ID and export options from the project profile;
- export to a candidate directory first;
- prefer a split source tree containing `install.sql` and `application/`;
- include `readable/` only on supported APEX releases before 26.1;
- on APEX 26.1 or later, do not request `READABLE_YAML`, because Oracle produces APEXlang instead;
- include a monolithic `f<APP_ID>.sql` when the project requires it;
- do not assume a split export also creates the monolithic file; run the
  project-approved non-split application export when both forms are required;
- treat split SQL, the version-allowed readable YAML, and the monolithic file as one atomic application snapshot;
- reject `.apx`, APEXlang directories, and APEXlang generate/export/validate/import commands in every version;
- make the Supporting Objects decision explicit;
- validate candidate structure and content before replacing the official snapshot;
- compare the diff to the requested application and scope;
- keep secrets, credentials, and environment-specific substitutions out of public artifacts.

Use the project's canonical export script when one exists. Do not replace it with a generic command merely because SQLcl can export the application.

Validate a generated candidate with `validate_oracle_apex_export.py --apex-version <confirmed-version>` when the managed helper is installed. Reconcile application identity, version-allowed page inventories, monolithic source, editable build status, component version evidence, Supporting Objects policy, absence of APEXlang, and the secret scan.

## Coordinated and Parallel Exports

When an official request includes multiple independent application or database
artifacts, read [parallel-export.md](references/parallel-export.md). Parallelize
only within the project's connection budget and canonical workflow. Workers
write to private candidates; one coordinator validates and promotes the complete
bundle. Never publish a partial success.

## Database Source Contract

Read:

- [database-baseline.md](references/database-baseline.md) for version 1;
- [database-release.md](references/database-release.md) for a normal release;
- [release-bundle.md](references/release-bundle.md) for the common full/partial five-file layout;
- [snapshot-runtime-contract.md](references/snapshot-runtime-contract.md) for adapting a project-owned immutable snapshot exporter;
- [pending-migrations.md](references/pending-migrations.md) for the two-file pending DDL/DML contract;
- [export-retention.md](references/export-retention.md) for repository and snapshot-table retention.

Never export data as part of the structural baseline or release source unless the project explicitly defines reviewed seed/reference data.

## Safety

- A temporary export never replaces an official snapshot.
- An official export never imports or applies itself.
- A release export never applies pending DDL or DML to TEST or PROD.
- Do not generate an entire schema baseline for a focused fix.
- Do not publish unrelated changed objects merely because they exist in DEV.
- Do not export or refresh any official source merely because a connection is available.
- Do not treat a database connection failure as evidence that versioned objects are current.
- Preserve unrelated worktree changes.

## Validation

Before publication:

- candidate export exists and is non-empty;
- expected app ID appears in metadata;
- required version-gated SQL/readable structures exist and no APEXlang artifact exists;
- database object list matches baseline or release mode;
- full and partial database bundles use the same five scoped files, with an explicit base snapshot for partial mode;
- every database artifact in a coordinated snapshot uses the same confirmed
  snapshot or source boundary;
- SQL scripts have deterministic ordering and valid SQLcl terminators;
- pending migrations remain pending and are included exactly once;
- the pending validator confirms one configured DDL file and one configured DML file, with no APEX or standalone object source;
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
- overall wall-clock time and per-lane durations when the export was timed;
- manifest/log location when a coordinator produced execution evidence;
- official snapshot replaced or left unchanged;
- Git publication status;
- confirmation that nothing was imported or applied to a target environment.
