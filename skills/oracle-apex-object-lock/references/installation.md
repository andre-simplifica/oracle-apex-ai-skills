# Object-Lock Runtime Installation

## Shipped Database Objects

- `DEV_OBJECT_LOCK`
- `DEV_OBJECT_LOCK_UI1`
- `DEV_OBJECT_LOCK_I1`
- `VW_DEV_OBJECT_LOCK_ATIVO`
- `VW_DEV_OBJECT_LOCK_RECENTE`
- `PK_DEV_OBJECT_LOCK`

The package exposes runtime version `1.1.0`.

## Read-Only Audit

Run from the consuming project root with its approved SQLcl saved connection:

```bash
sql -name <dev-connection> @.agents/skills/oracle-apex-object-lock/assets/database/audit-installation.sql
```

The audit reads Oracle dictionary metadata, package errors, and the runtime version dynamically. It checks the exact column/index/constraint/API contract and both view column inventories. It does not create, replace, update, or delete anything.

Do not classify a connection error as `ABSENT`.

## Installation

After explicit authorization for the confirmed DEV schema:

```bash
sql -name <dev-connection> @.agents/skills/oracle-apex-object-lock/assets/database/install.sql
```

The script:

1. creates the table when absent;
2. adds version-compatible repository reference columns when absent;
3. creates the active-lock unique index and expiry lookup index;
4. creates or replaces the active and recent views;
5. creates or replaces the package specification and body;
6. expires stale locks;
7. runs strict validation;
8. exits with a non-zero SQLcl status on failure.

The script does not remove lock history. Character-bounded metadata columns use `CHAR` semantics and long free-text values are truncated by bytes safely.

## Upgrade Handling

Audit before upgrading. Review the script diff and current runtime state. Because the package is replaced, active locks remain in the table but new package behavior takes effect immediately.

Coordinate an upgrade when other developers are actively compiling objects. Apply the runtime only to the intended shared DEV schema unless a separately approved environment policy says otherwise.

`Idempotent` means the installer is designed to be safely rerun: it preserves compatible table data, creates missing pieces, applies known upgrades, and converges on the required runtime contract. It does not mean database failures are ignored.

## History Retention

After a read-only count and explicit DEV authorization:

```bash
sql -name <dev-connection> \
  @.agents/skills/oracle-apex-object-lock/assets/database/purge-history.sql 30
```

The package accepts 7 through 3650 days and deletes only released/expired history older than the cutoff. Active locks are never retention candidates.

## Uninstall

After exporting any audit evidence that must be retained and obtaining explicit authorization:

```bash
sql -name <dev-connection> \
  @.agents/skills/oracle-apex-object-lock/assets/database/uninstall.sql
```

The script refuses to continue while a non-expired active lock exists. Oracle DDL auto-commits, so uninstall is not transactionally reversible; reinstall recreates the runtime but not deleted history.

## Installed-State Contract

`INSTALLED` requires:

- the table, both indexes, both views, and package specification/body present;
- all 19 required table columns with exact type/length/nullability semantics and three named validated constraints with their required keys/values;
- both index contracts, the expiry-index columns, three active-lock function expressions, both exact view column inventories, and nine package APIs present;
- table, views, and package objects valid;
- no package compilation errors;
- package runtime version equal to the required version.

Anything less is `PARTIAL` or `INCOMPATIBLE`, not "working".

For a new runtime or major upgrade, also perform a controlled two-session DEV test: session A acquires one synthetic supported-object lock; session B must fail to acquire/assert it; session A releases it; session B can then acquire and release it. Do not run that mutating test during a read-only audit.
