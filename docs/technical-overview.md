# Technical Overview

## Compatibility

The verified target is **Oracle APEX 24.2** with modern SQLcl and Oracle Database/Autonomous Database.

| Version | Status |
| --- | --- |
| APEX 24.2 | Verified design target |
| Other APEX versions | Validate API signatures, export options, metadata, and runtime behavior before use |

The consuming project receives `.oracle-apex-ai/compatibility.json`, which also records the required cooperative object-lock runtime.

## Responsibilities

- `oracle-apex-ai-skills`: router and installation/update contract.
- `oracle-apex-dev`: APEX and database development workflow.
- `oracle-apex-object-lock`: shared-DEV object coordination and runtime assets.
- `oracle-apex-export`: temporary inspection, version-1 baseline, official snapshots, and releases.
- `templates/`: project-owned profile/pattern scaffolding and managed compatibility.
- `scripts/manage_project_installation.py`: deterministic repository-scoped installer/updater.

## Installation Model

The team model copies a pinned source into the consuming repository:

```text
<project>/.agents/skills/<skill-name>
```

The manifest records:

- source repository;
- requested ref;
- resolved commit;
- installation time;
- APEX target;
- required lock runtime;
- SHA-256 of every managed file;
- project-owned paths that must be preserved.

`status` verifies local integrity. `check` compares a new source. `install` and `update` support `--dry-run`. Update stops on managed-file drift and uses temporary backups plus atomic file replacement for rollback on failure.

The script does not fetch the network itself. The agent or developer obtains and validates a Git source first, which keeps authentication and ref selection visible.

For a Git source, the manager requires a clean checkout and verifies that `--source-ref` resolves to the checked-out `HEAD`. It strips URL credentials and query strings before writing the repository identifier to project metadata.

## Project Profile

The profile is the project contract, not an installer configuration file. It documents:

- application/workspace/schema identity;
- approved DEV connection commands without secrets;
- APEX screen and language patterns;
- code ownership;
- object-lock policy;
- official APEX export structure;
- database baseline/object source paths;
- pending/applied migration lifecycle;
- release paths and publication rules;
- optional Brand Report Kit or ECharts usage.

The installer never overwrites it.

## Object-Lock Model

Runtime version `1.0.0` provides:

- one active lock per schema owner, object type, and object name;
- TTL expiration;
- actor, branch, task, context, Git base/head/start/end SHA evidence;
- active and recent views;
- acquire, renew, release, assert, and status APIs.

Package specification and body share one `PACKAGE` lock. The runtime uses autonomous transactions so lock state is not coupled to the caller's business transaction.

It remains cooperative: it does not install a schema DDL trigger. Any future hard-blocking mode must be an explicit, separately reviewed design.

## Export Model

An initial baseline is full structural source; a normal release is a delta plus a complete APEX app snapshot.

Baseline structural source includes tables, constraints, non-constraint indexes, sequences, types, views/materialized views, packages, standalone routines, triggers, synonyms, and explicit grants required by the app.

Release scope is reconciled from Git changes, task scope, locks, pending migrations, and authorized DEV source. Modification timestamps alone are insufficient.

Every table or structural DDL change starts in the configured pending directory. Release generation never applies or archives it.

## Optional Integrations

The kit has no dependency on:

- `build-apex-brand-reports`;
- `oracle-apex-echarts`.

When installed and relevant, the router hands those specialized tasks to them. Their files and versions are not managed by this repository.

## Security and Operations

- No passwords, tokens, wallets, connection strings, or private environment values belong in the public core.
- File installation does not authorize database access.
- Runtime audit is read-only; runtime installation is a DEV mutation.
- APEX export does not authorize import.
- Release generation does not authorize TEST/PROD execution.
- Git publication remains separate from implementation unless explicitly requested or required by the consuming repository.
