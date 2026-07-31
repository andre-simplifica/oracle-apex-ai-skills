# Initial Database Baseline

Use this workflow when no complete database structure is versioned and the user requests the first repository version.

## Scope Boundary

The baseline covers the schema that owns or supports the APEX application, not the entire database, CDB, PDB, or unrelated schemas.

Include structural source for:

1. tables;
2. table and referential constraints;
3. indexes not already represented by constraint DDL;
4. sequences;
5. object and collection types, including type bodies;
6. views and materialized views;
7. package specifications and bodies;
8. standalone procedures and functions;
9. triggers;
10. synonyms;
11. explicit object grants required by the application.

Classify jobs, queues, REST modules, application contexts, and environment configuration separately. Include them only when the project profile explicitly versions them.

## Exclusions

Exclude:

- table data;
- users, roles, tablespaces, and system-owned objects;
- wallets, credentials, passwords, API keys, tokens, and private endpoints;
- database-link credentials;
- runtime logs, queues, and transient data;
- APEX workspace administration metadata unrelated to the application;
- grants obtained implicitly from broad environment roles.

Reviewed, deterministic seed data requires its own explicit project rule and script.

## Output

Use project-defined folders. A recommended structure is:

```text
db/
  baseline/
    manifest.json
    install.sql
    tables/
    constraints/
    indexes/
    sequences/
    types/
    views/
    packages/
    routines/
    triggers/
    synonyms/
    grants/
apex/
  f<APP_ID>/
```

Order installation deterministically and keep one logical object per source file when practical. Preserve package specification/body separation when the project uses it.

## Extraction

Prefer the project's canonical export scripts. Otherwise use SQLcl and supported Oracle metadata APIs with explicit transform settings. Inspect generated DDL for storage/environment noise before publication.

Do not use a consolidated CLOB-only spool as the sole artifact when size or timeout risk makes it unreliable. Retain the inventory and extract objects individually when necessary.

## Validation

- compare inventory counts to source metadata;
- verify every included object has a non-empty file;
- verify package/type specs precede bodies;
- verify table dependencies and constraints have a valid order;
- verify statements have correct `/` or `;` terminators;
- scan for secrets and environment identifiers;
- compile or parse only in an authorized disposable/DEV target;
- record anything that could not be extracted.

The baseline is version 1 source evidence. It is not permission to recreate the schema in another environment.
