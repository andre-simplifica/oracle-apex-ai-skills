# Pending DDL Migrations

Every structural change must start as a versioned pending migration before it is applied to a shared environment.

This includes:

- `create table`;
- `alter table`;
- table/column/constraint changes;
- structural indexes;
- sequences tied to a new structure;
- materialized-view structure;
- grants or synonyms required by the structural change;
- reversible data backfill when it is inseparable from the structure and explicitly reviewed.

Package, procedure, function, view, trigger, and type source normally remains in its canonical object folder. Include a migration wrapper only when the project release process requires one.

## Default Layout

Use the project profile. If the project has no convention, initialize:

```text
db/migrations/
  pending/
  applied/
```

Recommended filename:

```text
YYYYMMDDHHMM_<short_description>.sql
```

Use a deterministic sequence suffix when more than one migration shares a timestamp.

## Migration Contract

Each migration should:

- state purpose and dependency in a comment;
- use explicit object names;
- be safe for the project's supported deployment model;
- stop on SQL or operating-system error;
- end explicitly when it is a standalone non-interactive SQLcl batch;
- avoid secrets and environment-specific connection commands;
- include preconditions or current-state checks when rerun behavior matters;
- avoid swallowing `WHEN OTHERS`;
- include rollback guidance when practical and safe.

Do not claim idempotency unless repeated execution was designed and tested.

When a migration is a fragment included by a release `install.sql`, the outer installer owns `whenever ... exit` and the final `exit`; the included fragment must not terminate the SQLcl session before later release steps run.

## Lifecycle

```text
pending -> included in release -> applied to defined target -> archived as applied
```

Release generation does not move a file to `applied/`. A DEV test also does not prove TEST or PROD application.

The project profile must define:

- pending path;
- applied/archive path;
- who confirms application;
- which environment advances lifecycle;
- whether release installers copy, reference, or move migrations.

## Release Checks

- every relevant pending migration is in the release inventory;
- no migration is included twice;
- ordering is explicit;
- object source and structural DDL agree;
- applied migrations are not silently reintroduced;
- unrelated pending work from another task is excluded or clearly blocked.
