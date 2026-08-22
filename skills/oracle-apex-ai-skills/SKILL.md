---
name: oracle-apex-ai-skills
description: Use as the main entry point for installing, updating, or applying the repository-managed Oracle APEX 24.2 skill kit in a project. Route APEX development, project learning, cooperative database object locks, complete application exports, full/partial database releases, retention, and pending DDL/DML while preserving project-owned standards.
---

# Oracle APEX AI Skills

Use this skill as the project-level router for the Oracle APEX AI Skills kit. The kit targets Oracle APEX 24.2 and works by itself. Optional reporting, document, and chart skills may improve a task but are never required.

## Start Every Task

1. Read repository instructions such as `AGENTS.md`.
2. Read `.oracle-apex-ai/project-profile.md`, `.oracle-apex-ai/app-patterns.md`, and `.oracle-apex-ai/export-policy.json` when present.
3. Inspect `.oracle-apex-ai/installation-manifest.json`, `.oracle-apex-ai/upstream-lock.json`, and `.oracle-apex-ai/compatibility.json` to identify the installed kit version, APEX target, and required lock runtime.
4. Classify the request with [routing.md](references/routing.md).
5. Separate read-only inspection, database mutation, APEX import, and Git publication. Do not infer authorization for one from another.

## Route the Request

- Use `oracle-apex-dev` for Page Designer, SQLcl, Object Browser, SQL/PLSQL, REST, jobs, security, runtime validation, and day-to-day implementation.
- Use `oracle-apex-object-lock` whenever a shared DEV database object may be edited, compiled, replaced, or tested.
- Use `oracle-apex-export` for temporary inspection exports, the first full versioned baseline, official APEX snapshots, and release-ready database deltas.
- Read [installation-and-updates.md](references/installation-and-updates.md) when installing from GitHub, checking status, or updating a consuming project.

Load only the routed skill and references needed for the current task.

## Interpret Common Requests

### "Install Oracle APEX AI Skills in this project"

Install the four core skills and managed helpers under the repository, then initialize only missing project-owned files without overwriting existing standards. Run the installer in dry-run mode first. Installation never connects to Oracle, imports APEX, compiles PL/SQL, applies DDL, commits, or pushes.

After file installation, use `oracle-apex-object-lock` to audit the DEV runtime. If it is absent or incompatible, show the exact database script and request the authorization required to run it.

### "Use Oracle APEX AI Skills to implement this"

Read local standards, identify affected database objects, enforce cooperative locks before any shared DEV compilation, implement the smallest valid change, and validate runtime behavior. Do not generate an official snapshot merely because development is complete.

### "Initialize version 1" or "Create the first versioned export"

Use `oracle-apex-export` in `initial-baseline` mode. Export the complete APEX application and the complete structural DDL for the application schema. Exclude data, secrets, wallets, users, and system-owned objects.

### "The changes are finished; generate the release export"

Use `oracle-apex-export` in `release` mode. Always generate the complete official APEX application snapshot. Generate the configured five-file database bundle as `partial` (only new/changed objects from one explicit base snapshot) or `full` (all supported objects), then include the configured pending DDL and DML exactly once.

### "The GitHub skill was updated; update this project"

Inspect local modifications and the installed upstream commit, fetch or clone the requested release tag/commit, run `status`, `doctor`, `check`, and `update --dry-run`, explain the exact diff, and only then update managed files. Preserve project-owned profiles, patterns, export policy, and migrations. Use `--initialize-missing-project-files` only after reviewing its dry-run.

## Mandatory Boundaries

- Call this a **skill kit** or **skills**, not a plugin.
- Treat APEX 24.2 as the verified target. For another APEX version, identify and validate compatibility differences before implementation.
- Never invent application objects, paths, IDs, schemas, connections, or business rules.
- Never overwrite project-owned files under `.oracle-apex-ai/`, except the generated manifest, upstream lock, and compatibility record managed by the installer.
- Keep table/structural DDL and reviewed DML in the two configured pending files. Never put APEX components or standalone object source there.
- Do not compile a supported object in shared DEV without an owned active lock and a successful lock assertion.
- The lock is cooperative. It coordinates compliant developers and agents but does not intercept arbitrary manual DDL.
- Do not modify the database merely to install or update the file-based skills.

## Optional Companion Skills

If available and relevant:

- use `build-apex-brand-reports` for project identity, branded reports, help canvases, PDF, and spreadsheet-oriented output;
- use `oracle-apex-echarts` for Apache ECharts regions in APEX.

These companions are independent repositories and are not copied, updated, or versioned by this kit:

- `https://github.com/andre-simplifica/oracle-apex-brand-report-kit`
- `https://github.com/andre-simplifica/oracle-apex-echarts`

State when an optional skill would improve the result. If the user wants it, install the selected companion separately from a reviewed tag/commit by following that repository's own instructions, then record its version in the project profile. Continue with this kit alone if it is unavailable or unnecessary.

## Continuous Project Learning

When the user declares a button, page layout, naming rule, Dynamic Content pattern, filter/action, dashboard interaction, or package convention to be a standard, inspect the real example and record the reusable rule in project-owned profile/pattern files. Do not keep a confirmed project standard only in conversation memory. Managed updates must preserve those files byte-for-byte.

## Closeout

Report separately:

- managed skill files installed or updated;
- project-owned files created or preserved;
- object-lock runtime status;
- database objects compiled or not changed;
- APEX application exported or not exported;
- pending DDL/DML updated and validator status;
- retention review status;
- validation performed;
- Git commit, push, or PR status.
