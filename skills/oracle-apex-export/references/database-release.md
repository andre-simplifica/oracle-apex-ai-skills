# Database Release Export

Use this workflow after implementation is complete and the user requests a release export.

## Determine Changed Objects

Build the release inventory from evidence:

- files changed in the task branch;
- object locks acquired during the task;
- packages, views, triggers, types, procedures, functions, or synonyms compiled in DEV;
- pending DDL migration files;
- explicit task notes.

Reconcile the sources. A lock is coordination evidence, not proof that the object changed. DEV modification timestamps alone are not reliable release scope.

## Export Rules

- Export current source for every changed versioned database object.
- For a package change, inspect and export both specification and body when either could affect the public contract; do not publish a stale spec/body pair.
- Preserve one canonical source location per object.
- Include table and structural DDL from `migrations/pending/`; do not replace it with a fresh `DBMS_METADATA` table dump.
- Include newly created object source and any dependency ordering required by the release.
- Exclude unrelated DEV drift and objects changed by another open task.

## Recommended Release Layout

Use the project's existing layout. When none exists:

```text
db/releases/<YYYY-MM-DD-or-version>/
  README.md
  install.sql
  objects/
  migrations/
```

`README.md` or equivalent inventory should state:

- release identifier;
- APEX app ID and snapshot path;
- changed database objects;
- included pending migrations;
- required order;
- validation environment;
- items intentionally excluded or blocked.

## Pending Migration Lifecycle

Copy or reference pending migrations exactly once in the release installer. Do not move them to `applied/` merely because the release package was generated.

Move a migration out of pending only after the project-defined target application is confirmed. Record the target and confirmation according to repository rules.

## Validation

- compare exported source with the authorized DEV object;
- compile changed PL/SQL in DEV when authorized;
- ensure dependencies precede dependents;
- confirm no duplicate DDL;
- verify SQLcl exit behavior and terminators;
- check APEX export and DB inventory belong to the same task/release;
- scan the complete release diff for secrets and unrelated files.

Generating a release is publication work. Applying it is a separate operation.
