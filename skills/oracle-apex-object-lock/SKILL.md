---
name: oracle-apex-object-lock
description: Use for installing, upgrading, auditing, retaining, uninstalling, and enforcing the cooperative PK_DEV_OBJECT_LOCK runtime before editing, compiling, replacing, or testing versioned PL/SQL and other supported objects in a shared Oracle DEV schema.
---

# Oracle APEX Object Lock

Coordinate changes to live, versioned database objects in a shared DEV schema. This skill ships the table, indexes, views, package, audit, installation, validation, retention, and guarded uninstall scripts required by the runtime.

## Determine Runtime State

Read [installation.md](references/installation.md), then run the read-only `assets/database/audit-installation.sql` through the project's approved SQLcl connection.

Classify the result:

- `INSTALLED`: all required objects are valid and the runtime version is compatible.
- `ABSENT`: none of the required objects exists.
- `PARTIAL`: only part of the runtime exists or an object is invalid.
- `INCOMPATIBLE`: the package exists but does not expose the required runtime version.

Do not assume that copying this skill installed database objects. The file installation and the DEV runtime installation are separate operations.

## Install or Upgrade

Database installation is a mutation. Obtain explicit authorization and confirm the DEV connection before running:

```text
@.agents/skills/oracle-apex-object-lock/assets/database/install.sql
```

The installer is idempotent: rerunning it preserves compatible existing data, creates missing pieces, applies known metadata upgrades, replaces the package specification/body, and validates the runtime. Do not run it in TEST or PROD merely because the skill is present there.

After installation, run `audit-installation.sql` again. Record the status in the task closeout; never store a password or connection string in the project profile.

## Lock Workflow

Follow [workflow.md](references/workflow.md) for every supported object that will be changed in shared DEV:

1. Refresh and validate the Git base.
2. Inspect active and recent locks.
3. Acquire the lock before editing or compiling.
4. Assert ownership immediately before every compilation or `create or replace`.
5. Renew long-running locks.
6. Release the lock with the final repository SHA or an abandonment reason.

One `PACKAGE` lock covers both package specification and body. Normalize `PACKAGE BODY`, `PACKAGE SPEC`, `PKB`, and `PKS` to `PACKAGE`. One `TYPE` lock likewise covers its specification and body.

## Supported Object Types

- `PACKAGE`
- `VIEW`
- `TRIGGER`
- `PROCEDURE`
- `FUNCTION`
- `TYPE`
- `SYNONYM`

For unsupported object types or structural table DDL, use the pending migration workflow and the project's coordination rules. Do not invent a lock type.

## Boundaries

- This is a cooperative application-level lock, not an Oracle DDL trigger.
- It is coordination, not an authorization boundary: `p_lock_owner` is caller-supplied and must follow the project's stable actor convention.
- Manual SQL executed outside this workflow can bypass it.
- Object names are canonicalized to uppercase without double quotes. Do not use this runtime to distinguish quoted mixed-case identifiers that differ only by case.
- Never force another owner's lock as a normal recovery path.
- Runtime `1.1.0` keeps the legacy `p_forcar` parameter for call compatibility but rejects forced acquire, renew, and release operations. Coordinate owner release or use a separately reviewed administrative recovery.
- An expired or released recent lock is still a signal to refresh Git before working on the object.
- A database connection failure does not prove that the runtime is absent.

## Retention and Uninstall

- Run `purge-history.sql <keep-days>` only after confirming the DEV connection, reviewing candidate counts, and authorizing the delete. It never deletes active locks.
- Run `uninstall.sql` only when the user explicitly requests runtime removal. It refuses active locks, then permanently removes the package, views, table, indexes, constraints, and lock history.
- Skill-file update, runtime upgrade, history purge, and runtime uninstall are four separate operations.

## Closeout

List:

- runtime state and version;
- objects locked, renewed, and released;
- objects not compiled because another owner held the lock;
- remaining active locks;
- whether the database was changed.
