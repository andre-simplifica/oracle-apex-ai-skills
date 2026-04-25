---
name: oracle-apex-dev
description: Use for Oracle APEX 24.2 development requests involving Page Designer, SQLcl, Object Browser, SQL/PLSQL, REST integrations, background jobs, regions, reports, Dynamic Actions, contextual help, runtime validation, temporary read-only exports, security guardrails, destructive-operation review, and local standards defined by the project profile.
---

# Oracle APEX DEV

Generic skill for working with Oracle APEX 24.2 in a pragmatic, traceable, and low-risk way.

## Layers

Always separate:

- **APEX core**: workflow, SQLcl, Page Designer, Object Browser, PL/SQL, runtime validation, read-only exports, guardrails, and risk criteria.
- **Project profile**: standards for the current application. This should live in the consuming project at `.oracle-apex-ai/project-profile.md`.
- **Learned application patterns**: catalog of example pages, regions, templates, buttons, menus, breadcrumbs, dialogs, and packages. This should live in the consuming project at `.oracle-apex-ai/app-patterns.md` and `.oracle-apex-ai/page-patterns/`.

Do not put conventions from one specific application into this skill core.

## Before Implementing

1. Read current repository instructions (`AGENTS.md`, `CLAUDE.md`, `README`, or equivalent), if present.
2. Read `.oracle-apex-ai/project-profile.md`, if present.
3. When the request involves a new screen, visual flow, or UI pattern, read `.oracle-apex-ai/app-patterns.md` and the referenced example pages.
4. Confirm environment, app id, workspace, schema, and SQLcl connection before any technical execution.
5. If essential context is missing, state the limitation and ask or perform read-only inspection.

## Essential Rules

- Do not invent tables, columns, packages, procedures, APIs, pages, or business rules.
- Use Page Designer for focused visual and functional APEX page changes.
- Use SQLcl for queries, validation, PL/SQL compilation, metadata inspection, and read-only exports.
- Use Object Browser as a fallback when SQLcl is unavailable or when the project requires the Builder UI.
- Do not edit versioned APEX exports as the default implementation path; use them as functional reference.
- When changing versioned PL/SQL for implementation, bug fix, or test work, compile in DEV and validate errors unless the user or environment blocks it.
- When the user asks only for a plan, review, explanation, or direction, do not change the database without explicit authorization.
- Runtime validation is required for any visual or functional screen change.
- User-visible text must use business language and must not expose internal technical names.
- Never store credentials, tokens, wallets, passwords, or secrets in versioned files.
- Treat vibe coding as context-driven engineering: inspect first, follow standards, make small changes, validate runtime, and report risk clearly.
- For destructive, security-sensitive, or production-affecting work, stop and follow the high-risk reference before acting.

## Routing

- **Project profile**: read `.oracle-apex-ai/project-profile.md`; if it does not exist, use [project-profile.md](references/project-profile.md) to guide creation.
- **Learned patterns**: read [apex-pattern-learning.md](references/apex-pattern-learning.md) and `.oracle-apex-ai/app-patterns.md`.
- **Page Designer**: follow [page-designer.md](references/page-designer.md).
- **SQLcl**: follow [sqlcl.md](references/sqlcl.md).
- **SQL/PLSQL standards**: follow [sql-plsql-standards.md](references/sql-plsql-standards.md) before writing or reviewing database code.
- **REST integrations**: follow [rest-integrations.md](references/rest-integrations.md) before creating, changing, or debugging outbound APIs, OAuth, webhooks, or OpenAPI-backed flows.
- **APEX debugging**: follow [apex-debugging.md](references/apex-debugging.md) for runtime errors, Session State, Dynamic Actions, AJAX, upload/import flows, and generic APEX errors.
- **Background jobs**: follow [background-jobs.md](references/background-jobs.md) for APEX Automations, DBMS_SCHEDULER, queues, retries, and long-running processes.
- **Destructive operations**: follow [destructive-operations.md](references/destructive-operations.md) before any DDL, mass DML, APEX import, drop, truncate, scheduler enablement, session kill, grants, or production change.
- **Security and permissions**: follow [security-and-permissions.md](references/security-and-permissions.md) for authentication, authorization, credentials, public pages, ORDS/REST privileges, grants, ACLs, and sensitive data.
- **Object Browser**: follow [object-browser.md](references/object-browser.md).
- **Internal APEX APIs**: follow [apex-internal-apis.md](references/apex-internal-apis.md) when the change is repeatable, multi-page, or safer through a controlled script.
- **Runtime**: follow [runtime-validation.md](references/runtime-validation.md).
- **Help and user text**: follow [help-and-ux.md](references/help-and-ux.md), then apply the local project profile.

## Standard Flow

1. Understand the request and locate the page/module/object.
2. Read the local project profile and relevant learned patterns.
3. Classify the task: read-only, small adjustment, repeatable change, new/complex screen, PL/SQL backend, REST/API, background job, debugging, security-sensitive, or destructive/high-risk.
4. Inspect the repository and/or APEX metadata before changing anything.
5. Choose the route: Page Designer, SQLcl, Object Browser, or controlled script.
6. Apply changes in small, validatable units.
7. Save the page and/or compile objects.
8. Validate runtime behavior in the application.
9. Update documentation/profile/patterns when the change reveals a reusable rule.
10. If the project uses Git and local rules allow it, commit/push only the current task scope.

## Required Closeout

For PL/SQL/database-object tasks, clearly report:

- `Objects compiled in DEV: ...`
- `Objects not applied to the database; repository only: ...`
- `No database objects changed.`

For screen tasks, report whether runtime validation was completed or why it was not possible.
