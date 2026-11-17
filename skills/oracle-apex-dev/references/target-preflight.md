# Read-only Target Identity Preflight

Use the managed `Util/scripts/target_preflight.py` helper when a repeatable SQLcl
workflow needs to reject an unexpected connection. It **generates SQL only**;
it never connects, imports, compiles, exports, or changes Oracle objects.

## Inputs and Execution

Create a private JSON file containing independently confirmed expectations. All
five database fields are required; comparison is exact and case-sensitive.
Do not infer expected values from the same unverified session being checked.

```json
{
  "schema_version": 1,
  "session_user": "APP_SCHEMA",
  "current_schema": "APP_SCHEMA",
  "service_name": "EXAMPLE_SERVICE",
  "db_unique_name": "EXAMPLE_DB",
  "con_name": "EXAMPLE_PDB",
  "apex": {
    "version": "24.2.0",
    "application_id": 100,
    "workspace": "WORKSPACE_NAME",
    "parsing_schema": "APP_SCHEMA",
    "source_format": "sql"
  }
}
```

Omit the entire `apex` object for database-only work. When present, use the exact
`APEX_RELEASE.VERSION_NO` string, not a guessed patch number. Generation rejects
versions below 24.2, incomplete input and unknown fields. It rejects `apexlang`
as a source format, including on 26.2; that workflow belongs to the separate
[APEXlang kit](https://github.com/andre-simplifica/oracle-apex-ai-skills-apexlang).

```bash
python3 Util/scripts/target_preflight.py \
  --expect /private/path/target.json --output /private/path/check-target.sql
sql -name <confirmed-saved-connection> @/private/path/check-target.sql
```

The generator creates a new file with owner-only permissions and refuses to
overwrite an existing path. Both JSON and generated SQL contain private target
identifiers: keep them outside public Git and shared logs. The SQL initializes
binds with escaped values, disables SQLcl substitution and prints only PASS or
the failed field/stage and SQL error code, not expected or observed identifiers.
Inspect any unexpected raw SQLcl connection/compiler output locally before sharing.

## Checks and Failure Behavior

- Database identity comes from the current session's `SYS_CONTEXT('USERENV', ...)`.
  No DBA catalog privilege is required for those values. The helper assumes an
  ordinary local database connection, not GDS identity virtualization or a
  database link; those need a project-specific identity contract.
- APEX checks require visibility of the one application through
  `APEX_APPLICATIONS`, its workspace through `APEX_WORKSPACES`, the version through
  `APEX_RELEASE`, and access to the public
  `APEX_APPLICATION_ADMIN.GET_PARSING_SCHEMA` function. Missing privileges,
  invisible rows, duplicate rows, nulls and mismatches fail the check. It does not
  switch workspace, schema or container or grant access to make a check pass.
- A standalone script exits with rollback on success and failure; run it in a
  dedicated session without pending work. Failure has a nonzero process status.

A successful standalone check does **not** establish identity in a later session.
For a project-owned batch, import `render_preflight(load_expectations(path))`
from `target_preflight`, prepend its fragment to the already authorized batch,
and give that batch an explicit transaction/exit contract. The fragment intentionally
has no success `EXIT`, retains fail-on-error behavior, and leaves SQLcl substitution
disabled. Repeat it after any reconnect or schema/container/context change.
Generation and identity matching do not authorize the following operation.

## Evidence and Limits

Local tests cover input validation, bind generation, escaping, SQL/APEXlang routing,
private output creation and refusal to overwrite. They do not execute PL/SQL.
Before operational adoption, run positive and negative checks in an authorized
DEV target, including wrong identity, inaccessible APEX metadata, wrong workspace
and schema, and record the actual database/APEX/SQLcl versions. No live Oracle
validation is claimed by the initial implementation.

Primary references:

- [Oracle Database 19c SYS_CONTEXT](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/SYS_CONTEXT.html)
- [APEX 24.2 public views and privileges](https://docs.oracle.com/en/database/oracle/apex/24.2/htmdb/about-granted-privileges.html)
- [APEX 24.2 application/workspace lookup example](https://docs.oracle.com/en/database/oracle/apex/24.2/aeapi/about-web-credentials-APEX_WEB_SERVICE.html)
- [APEX 24.2 GET_PARSING_SCHEMA](https://docs.oracle.com/en/database/oracle/apex/24.2/aeapi/APEX_APPLICATION_ADMIN.GET_PARSING_SCHEMA-Function.html)
