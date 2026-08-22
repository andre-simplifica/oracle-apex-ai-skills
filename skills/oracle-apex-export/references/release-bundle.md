# Full and Partial Database Release Bundles

Use this contract when the consuming project exports database objects from a confirmed snapshot or equivalent immutable source boundary.

## Scope

- `full`: export every supported object in the confirmed current snapshot.
- `partial`: export only new or changed objects compared with one explicit base snapshot.

Both scopes use the same five files and deterministic installation order. A partial bundle is not a different deployment format.

```text
snapshot_<current>_<scope>_01_package_specs.sql
snapshot_<current>_<scope>_02_views.sql
snapshot_<current>_<scope>_03_package_bodies.sql
snapshot_<current>_<scope>_04_triggers.sql
snapshot_<current>_<scope>_05_compile_objects.sql
```

The default five-file validator supports `PACKAGE`, `VIEW`, `PACKAGE BODY`, and `TRIGGER` source plus the configured compile step. If a project versions standalone procedures/functions, types, materialized views, or synonyms in normal releases, its profile must define their dependency-safe group mapping and extend the canonical exporter/validator before claiming a complete bundle. Do not hide unsupported object source in pending DDL as a workaround.

Use `scope=partial` in filenames and headers so an operator cannot mistake a delta for a full source set. The partial header must also record `BASE_SNAPSHOT_ID`.

## Partial Comparison

Compare the current and base inventories by normalized identity:

```text
owner + object type + object name + object subname
```

Use a normalized DDL hash such as SHA-256. Include an object when it is new or its hash changed. Do not use only `LAST_DDL_TIME`, task memory, or current Git changes as proof.

An object present in the base and absent from the current snapshot is a removal candidate. Record it in the inventory, but never emit an automatic `DROP`. Removal requires an explicit reviewed migration and authorization.

## File Header

Every file must identify its source:

```sql
-- ORACLE_APEX_AI_RELEASE
-- SNAPSHOT_ID: 381
-- SCOPE: PARTIAL
-- BASE_SNAPSHOT_ID: 375
-- OBJECT_GROUP: PACKAGE
```

For a full bundle, omit `BASE_SNAPSHOT_ID` or use `NONE`. Use `PACKAGE`, `VIEW`, `PACKAGE BODY`, `TRIGGER`, and `COMPILE` as the five `OBJECT_GROUP` values.

If a partial group has no changes, keep the file and write `-- NO CHANGES`. If a full source has no object of one type, write `-- NO OBJECTS`. Do not omit a file and do not invent an object to make it non-empty.

The compile file calls only the project-approved routine from `.oracle-apex-ai/export-policy.json`. When no routine is configured, keep the fifth file with a clear comment; never assume `PROC_COMPILAR_OBJETOS` exists.

## Validation

Before promotion, run the installed validator or the source equivalent:

```bash
python3 Util/scripts/validate_oracle_apex_release_bundle.py \
  --directory db/releases/<release> \
  --snapshot-id <current> \
  --scope partial \
  --base-snapshot-id <base>
```

Also reconcile expected object counts from the snapshot, reject empty/truncated/error-prefixed DDL, scan for secrets, preserve UTF-8, and confirm deterministic object ordering. Generate every file in a private candidate and promote the five files together.

The complete APEX application export remains separate and complete for both database scopes.
