# SQLcl

Use SQLcl as the reproducible technical route for Oracle Database and APEX.

## Common Uses

- Diagnostic queries.
- APEX metadata in `apex_application_*` views.
- Temporary read-only exports.
- PL/SQL compilation.
- `user_errors`, `user_objects`, logs, staging, and history.
- Idempotent scripts.

## SQL vs SQLcl

Classify before running:

- SQL/PLSQL: `select`, `insert`, `update`, `create or replace package`, `begin...end;` blocks.
- SQLcl: `show errors`, `apex export`, `apex export -list`, `info`, `ddl`, `desc`, `oerr`, `codescan`.

`show errors` is a SQLcl command, not plain SQL.

## Execution Pattern

Generic example:

```bash
printf 'select user from dual;\nexit\n' | sql -S -L -name DEV
```

Use the connection and alias defined in the project profile.

Before every query, compile, import, or export operation, validate both values in the same saved connection:

```sql
select user,
       sys_context('USERENV', 'SERVICE_NAME') as service_name
  from dual;
```

Compare them with the project profile. A successful login, familiar schema name, or reachable database is not enough when the service identity is wrong.

## PL/SQL Compilation

When DEV is shared, audit the required object-lock runtime, acquire the supported object lock, and run `proc_assert_lock_compilacao` immediately before the compilation. One `PACKAGE` lock covers specification and body.

After compiling, validate:

```sql
select name, type, line, position, text
  from user_errors
 order by name, type, sequence;
```

Do not close as done if a changed object is invalid.

## Guardrails

- Do not pass passwords on the command line.
- Prefer saved connections.
- Confirm environment before DDL/DML.
- Version table/structural DDL and reviewed DML in the two configured pending files before applying them.
- Keep APEX components and standalone package/view/trigger/routine/type/synonym source out of pending.
- Do not bypass an active cooperative lock with a direct SQLcl compilation.
- Make `commit` or `rollback` explicit in scripts that change data/metadata.
- Do not run APEX imports by trial and error.
