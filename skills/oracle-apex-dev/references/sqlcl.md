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

## PL/SQL Compilation

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
- Make `commit` or `rollback` explicit in scripts that change data/metadata.
- Do not run APEX imports by trial and error.
