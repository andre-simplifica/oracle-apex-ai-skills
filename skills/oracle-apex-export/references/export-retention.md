# Export and Snapshot Retention

Repository release retention and database snapshot-table retention are different operations. Configure both in the consuming project's project-owned `.oracle-apex-ai/export-policy.json`.

## Default Behavior

- Review retention every five new release directories.
- Keep the latest ten repository releases.
- Report candidates by default; do not delete them.
- Keep database retention disabled until the project confirms that it uses the compatible `PK_DDL_SNAPSHOT` API.

The defaults are starting points, not permission to remove history. Read [snapshot-runtime-contract.md](snapshot-runtime-contract.md) before declaring a project runtime compatible.

## Repository Releases

Run:

```bash
python3 Util/scripts/manage_oracle_apex_export_retention.py status --project-root .
python3 Util/scripts/manage_oracle_apex_export_retention.py prune --project-root .
```

`prune` is a dry-run unless the policy mode is `prune` and the caller passes both `--apply` and `--confirm PRUNE_OLD_RELEASES`. It considers only direct release directories matching the configured pattern and refuses candidates with uncommitted Git changes. Git history remains the recovery source after a reviewed deletion is committed.

## Database Snapshot Tables

When `PK_DDL_SNAPSHOT` exposes `purge_old_scripts` and `purge_old_snapshots`, generate the reviewed SQL without connecting:

```bash
python3 Util/scripts/manage_oracle_apex_export_retention.py database-sql \
  --project-root . \
  --owner <APP_SCHEMA>
```

That command emits preflight SQL only. After a separate cleanup authorization, request the executable block explicitly with `--emit-apply-block --confirm EMIT_DB_SNAPSHOT_PURGE`, inspect the generated file, and run it through the confirmed saved connection. Emitting SQL still does not execute it.

Before execution, confirm the saved DEV connection, `USER`, `SERVICE_NAME`, owner, snapshot/script counts, keep values, and rollback/recovery implications. Purge is a separate authorized database mutation; an official export request does not authorize it.

Run retention only after the new snapshot and release candidate are validated. Never delete the only confirmed snapshot needed by an in-progress full/partial comparison or retry.
