# SQL and PL/SQL Standards for APEX

Use this reference when writing, reviewing, or debugging SQL and PL/SQL for Oracle APEX applications.

## Ownership

- Prefer packages for reusable business logic.
- Do not put complex business rules directly in APEX page processes when a domain package already exists.
- Keep page processes thin: validate inputs, call package APIs, handle user-facing messages.
- Follow the consuming project's package ownership map before creating new code paths.
- Do not create new packages or database objects unless the user or project profile clearly authorizes it.

## SQL

- Use bind variables for APEX item values and user input.
- Avoid concatenating SQL from user input.
- Avoid repeatedly calling PL/SQL functions in predicates on large result sets unless there is a clear performance reason and supporting indexes/statistics.
- Check cardinality, filters, joins, and sort order before blaming APEX rendering.
- Do not expose table names, column names, IDs, or technical flags in user-facing text.

## PL/SQL

- Make transaction boundaries explicit in scripts and jobs.
- Do not add `commit` inside reusable package routines unless the routine is explicitly an autonomous or transactional boundary by design.
- Avoid `when others then null`.
- If catching exceptions, log useful sanitized context and either re-raise or return a structured failure.
- Use `bulk collect` / `forall` for large batch work when appropriate.
- Use CLOB-safe logic for large JSON, HTML, or API payloads.
- Prefer `json_value`, `json_table`, `json_object`, `json_arrayagg`, or `apex_json` according to project standards.

## Compilation and Validation

After changing PL/SQL, validate:

```sql
select name, type, line, position, text
  from user_errors
 where name in ('PACKAGE_OR_OBJECT_NAME')
 order by name, type, sequence;
```

Also check object status:

```sql
select object_name, object_type, status
  from user_objects
 where object_name in ('PACKAGE_OR_OBJECT_NAME')
 order by object_type, object_name;
```

Do not call PL/SQL work complete if changed objects are invalid.

## User-Facing Messages

- Keep business messages separate from technical diagnostics.
- User-facing Portuguese must use correct spelling and accents when the application language is Portuguese.
- Do not show raw ORA errors, provider payloads, stack traces, or internal object names unless the screen is explicitly technical/admin-only.

## Before Closing

- Compile changed objects.
- Check `user_errors`.
- Test the main path.
- Test at least one expected failure path when practical.
- Report whether changes were applied to the database, kept repository-only, or blocked.
