# Pending DDL and DML

Use one pending directory with exactly two configured SQL fragments: one for structural DDL and one for reviewed DML. Every applicable change must be versioned there before it is applied to a shared environment.

The DDL file includes:

- `create table`;
- `alter table`;
- table/column/constraint changes;
- structural indexes;
- sequences tied to a new structure;
- materialized-view structure;
- grants required by the structural change.

The DML file includes reviewed data corrections, backfills, and approved deterministic seed/reference data. It must contain restrictive preflight, expected-row-count, rollback, and post-check logic appropriate to the risk.

APEX pages, regions, components, and imports never belong in pending. Publish APEX through the complete official application export.

Package, package body, procedure, function, view, trigger, type, and synonym source also never belongs in pending. Export new and changed standalone objects through the canonical database-object exporter and five-file release bundle.

## Default Layout

Use the project profile. If the project has no convention, initialize:

```text
db/migrations/
    pending/
      pending_ddl.sql
      pending_dml.sql
  applied/
```

Projects may rename the two files in `.oracle-apex-ai/export-policy.json`, but must not create parallel pending roots or undeclared SQL files.

## Migration Contract

Each pending fragment should:

- state purpose and dependency in a comment;
- use explicit object names;
- be safe for the project's supported deployment model;
- stop on SQL or operating-system error;
- end explicitly when it is a standalone non-interactive SQLcl batch;
- avoid secrets and environment-specific connection commands;
- include preconditions or current-state checks when rerun behavior matters;
- avoid swallowing `WHEN OTHERS`;
- include rollback guidance when practical and safe.

Do not claim idempotency (safe repeat execution without changing an already-correct result) unless it was designed and tested.

When a migration is a fragment included by a release `install.sql`, the outer installer owns `whenever ... exit` and the final `exit`; the included fragment must not terminate the SQLcl session before later release steps run.

## Lifecycle

```text
pending DDL/DML -> included in release -> applied to defined target -> archived/reset after confirmation
```

Release generation does not move a file to `applied/`. A DEV test also does not prove TEST or PROD application.

The project profile must define:

- pending path and the two configured filenames;
- applied/archive path;
- who confirms application;
- which environment advances lifecycle;
- whether release installers copy or reference the two fragments;
- how confirmed content is archived and how the two pending files are reset.

## Release Checks

- the installed `check_oracle_apex_pending.py` validator passes;
- both configured fragments are in the release inventory exactly once;
- ordering is explicit;
- object source and structural DDL agree;
- applied content is not silently reintroduced;
- no APEX component or standalone object source appears in pending;
- unrelated pending work from another task is excluded or clearly blocked.
