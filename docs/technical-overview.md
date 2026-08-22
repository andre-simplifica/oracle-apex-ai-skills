# Technical Overview

## Compatibility

The verified target is **Oracle APEX 24.2** with modern SQLcl and Oracle Database/Autonomous Database.

| Version | Status |
| --- | --- |
| APEX 24.2 | Verified design target |
| Other APEX versions | Validate API signatures, export options, metadata, and runtime behavior before use |

The consuming project receives `.oracle-apex-ai/compatibility.json`, which records kit version `1.1.0`, the required cooperative object-lock runtime, and optional external companion repositories.

## Responsibilities

- `oracle-apex-ai-skills`: router and installation/update contract.
- `oracle-apex-dev`: APEX and database development workflow.
- `oracle-apex-object-lock`: shared-DEV object coordination and runtime assets.
- `oracle-apex-export`: temporary inspection, version-1 baseline, official snapshots, and releases.
- `templates/`: project-owned profile/pattern/export-policy/pending scaffolding and managed compatibility.
- `scripts/manage_project_installation.py`: deterministic repository-scoped installer/updater.
- managed validators: APEX export, five-file database bundle, pending contract, and export retention.

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
- kit version;
- required lock runtime;
- SHA-256 of every managed file;
- project-owned paths that must be preserved.

`status` verifies local integrity. `doctor` also reports project-owned profile/pattern/export readiness. `check` compares a new source. `install` and `update` support `--dry-run`. Update stops on managed-file drift and uses temporary backups plus atomic file replacement for rollback on failure. `--initialize-missing-project-files` creates only newly introduced missing templates and never replaces custom project files.

The script does not fetch the network itself. The agent or developer obtains and validates a Git source first, which keeps authentication and ref selection visible.

For a Git source, the manager requires a clean checkout and verifies that `--source-ref` resolves to the checked-out `HEAD`. It strips URL credentials and query strings before writing the repository identifier to project metadata.

## Project Profile

The profile is the project contract, not an installer configuration file. It documents:

- application/workspace/schema identity;
- expected `USER` and `SERVICE_NAME` for each saved connection;
- approved DEV connection commands without secrets;
- APEX screen and language patterns;
- code ownership;
- object-lock policy;
- official APEX export structure;
- database baseline/object source paths;
- pending/applied migration lifecycle;
- full/partial five-file release and retention policy;
- release paths and publication rules;
- optional Brand Report Kit or ECharts usage.

The installer never overwrites it.

## Object-Lock Model

Runtime version `1.1.0` provides:

- one active lock per schema owner, object type, and object name;
- TTL expiration;
- actor, branch, task, context, Git base/head/start/end SHA evidence;
- active and recent views;
- acquire, renew, release, assert, and status APIs.
- bounded character semantics, byte-safe audit text, explicit history purge, guarded uninstall, and stricter installed-object validation.

Package specification and body share one `PACKAGE` lock. The runtime uses autonomous transactions so lock state is not coupled to the caller's business transaction.

It remains cooperative: it does not install a schema DDL trigger. Legacy force parameters are rejected because a shared-schema package cannot infer trusted administrator identity. Any future hard-blocking or administrative recovery mode must be an explicit, separately reviewed design.

## Export Model

An initial baseline is full structural source. An explicit release always contains a complete, atomic APEX split SQL/readable YAML/monolithic snapshot plus either a `full` or `partial` database bundle.

Baseline structural source includes tables, constraints, non-constraint indexes, sequences, types, views/materialized views, packages, standalone routines, triggers, synonyms, and explicit grants required by the app.

Both database scopes use the same five files: package specs, views, package bodies, triggers, and compile step. Partial scope compares normalized object identity and DDL hashes with one explicit base snapshot; timestamps alone are insufficient. Removals become reviewed migration candidates, never automatic drops.

Pending has exactly one DDL and one DML file. Table/constraint/index/sequence structure belongs in DDL; reviewed corrections, backfills, and seed/reference data belong in DML. APEX and standalone object source are rejected. Release generation never applies or archives pending content.

The project-owned retention policy reviews repository releases every configured number of versions and reports candidates by default. Guarded pruning requires policy opt-in plus an explicit confirmation token. Snapshot-table retention emits SQL only and requires a separately authorized compatible project runtime.

## Optional Integrations

The kit has no dependency on:

- [Oracle APEX Brand Report Kit](https://github.com/andre-simplifica/oracle-apex-brand-report-kit), including its browser-rendered PDF workflow;
- [Oracle APEX ECharts](https://github.com/andre-simplifica/oracle-apex-echarts).

When installed and relevant, the router hands those specialized tasks to them. Their files and versions are not managed by this repository.

## Security and Operations

- No passwords, tokens, wallets, connection strings, or private environment values belong in the public core.
- File installation does not authorize database access.
- Runtime audit is read-only; runtime installation is a DEV mutation.
- APEX export does not authorize import.
- Release generation does not authorize TEST/PROD execution.
- Git publication remains separate from implementation unless explicitly requested or required by the consuming repository.
