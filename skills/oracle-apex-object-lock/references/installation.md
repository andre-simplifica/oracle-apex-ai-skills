# Object-Lock Runtime Installation

## Shipped Database Objects

- `DEV_OBJECT_LOCK`
- `DEV_OBJECT_LOCK_UI1`
- `DEV_OBJECT_LOCK_I1`
- `VW_DEV_OBJECT_LOCK_ATIVO`
- `VW_DEV_OBJECT_LOCK_RECENTE`
- `PK_DEV_OBJECT_LOCK`

The package exposes runtime version `1.0.0`.

## Read-Only Audit

Run from the consuming project root with its approved SQLcl saved connection:

```bash
sql -name <dev-connection> @.agents/skills/oracle-apex-object-lock/assets/database/audit-installation.sql
```

The audit reads `USER_OBJECTS`, `USER_ERRORS`, and the package version dynamically. It does not create, replace, update, or delete anything.

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

The script does not remove lock history.

## Upgrade Handling

Audit before upgrading. Review the script diff and current runtime state. Because the package is replaced, active locks remain in the table but new package behavior takes effect immediately.

Coordinate an upgrade when other developers are actively compiling objects. Apply the runtime only to the intended shared DEV schema unless a separately approved environment policy says otherwise.

## Installed-State Contract

`INSTALLED` requires:

- the table, both indexes, both views, and package specification/body present;
- all 19 required table columns and three named constraints present and enabled;
- table, views, and package objects valid;
- no package compilation errors;
- package runtime version equal to the required version.

Anything less is `PARTIAL` or `INCOMPATIBLE`, not "working".
