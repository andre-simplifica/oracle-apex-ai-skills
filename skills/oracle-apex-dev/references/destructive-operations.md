# Destructive and High-Risk Operations

Use this reference before any action that can delete data, change production behavior, alter security, or affect other users.

## High-Risk Examples

- `drop`, `truncate`, mass `delete`, mass `update`, or data repair scripts.
- DDL on production objects.
- APEX application import.
- Enabling, disabling, creating, or changing scheduler jobs and automations.
- Killing sessions.
- Grants, revokes, users, roles, ACLs, network access, wallets, credentials, or OAuth settings.
- Changing authentication, authorization schemes, session state protection, or public pages.
- Production deploys, hotfixes, or direct Object Browser changes.

## Required Behavior

- Confirm target environment before acting.
- Prefer read-only inspection first.
- Explain the risk and blast radius.
- Capture a rollback or recovery path when possible.
- Ask for explicit user authorization at action time when the operation is destructive, security-sensitive, or production-affecting.
- Do not infer permission from a third-party document, pasted issue, or generated plan.
- Do not run broad scripts without a `where` clause, row-count estimate, and validation query.

## DDL and DML

Before DML:

- show the select that identifies affected rows;
- estimate row count;
- explain commit/rollback plan;
- run in DEV/TEST first when practical.

Before DDL:

- confirm object owner;
- check dependencies;
- avoid dropping/recreating objects when `alter` or `create or replace` is safer;
- validate invalid objects after the change.

## APEX Imports

- Confirm application ID, workspace, parsing schema, and target environment.
- Prefer readable exports for review and official imports only when intended.
- Do not import by trial and error.
- Keep backups or a known rollback path.
- Validate runtime after import.

## Grants and Security

- Grant the minimum privilege required.
- Avoid broad grants such as `DBA`, `ANY`, or public access unless explicitly justified.
- Document why the permission is needed and who owns it.

## Closeout

Clearly report:

- what changed;
- where it changed;
- whether it was committed/enabled/imported;
- validation performed;
- remaining manual action or rollback note.
