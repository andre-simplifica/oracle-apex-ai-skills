# Database Release Export

Use this workflow after implementation is complete and the user requests a release export.

## Determine Changed Objects

Build the release inventory from evidence:

- files changed in the task branch;
- object locks acquired during the task;
- packages, views, triggers, types, procedures, functions, or synonyms compiled in DEV;
- pending DDL and DML files;
- explicit task notes.

Reconcile the sources. A lock is coordination evidence, not proof that the object changed. DEV modification timestamps alone are not reliable release scope.

## Export Rules

- Export current source for every changed versioned database object.
- For a package change, inspect and export both specification and body when either could affect the public contract; do not publish a stale spec/body pair.
- Preserve one canonical source location per object.
- Include table and structural DDL plus reviewed data changes from the two configured pending files; do not replace structural migrations with a fresh `DBMS_METADATA` table dump.
- Include newly created object source and any dependency ordering required by the release.
- Exclude unrelated DEV drift and objects changed by another open task.

## Full and Partial Snapshot Releases

The consuming project chooses `full` or `partial` in its profile/export policy.
Both use the canonical five-file contract in [release-bundle.md](release-bundle.md).

- `full` publishes every supported object in the confirmed current snapshot.
- `partial` publishes objects whose normalized DDL hash is new or changed from
  one explicit base snapshot.

- Create or select one confirmed source snapshot for the entire release.
- Generate every object group from that same snapshot identifier.
- Reconcile inventory counts by type and reject missing, empty, truncated, or
  error-prefixed source.
- Generate independent object groups concurrently when the canonical exporter
  supports it and the global database-session budget permits it.
- Keep deterministic installation order separate from worker completion order.
- Preserve prior versioned snapshot sets and complementary release files unless
  the project explicitly authorizes their removal.
- On a downstream failure, reuse the already confirmed snapshot after fixing the
  cause instead of creating a duplicate.

See [parallel-export.md](parallel-export.md) for bundle coordination, atomic
promotion, failure handling, and timing evidence.

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
- included pending DDL and DML;
- required order;
- validation environment;
- items intentionally excluded or blocked.

## Pending Migration Lifecycle

Copy or reference the configured pending DDL and DML exactly once in the release installer. Do not move or reset them merely because the release package was generated.

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
