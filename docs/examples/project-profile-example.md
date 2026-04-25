# Example Project Profile

This is a fictional example. Do not replace it with real private environment data in this public repository.

In a real project, this content should live at:

```text
.oracle-apex-ai/project-profile.md
```

## Identification

- Project name: Example CRM
- Main APEX application: Example CRM Backoffice
- App ID: 100
- Workspace: WORKSPACE_NAME
- Schema owner: APP_SCHEMA
- APEX version: 24.2
- Database/environment: OCI Autonomous Database DEV
- SQLcl command/saved connection: `sql -name DEV_EXAMPLE`
- Default branch: `main`
- API/OpenAPI documentation location: `openapi/example/openapi.yaml`
- Authentication pattern for internal/private APIs: OAuth2 Client Credentials, documented in private project docs

## Environments

| Environment | URL/Base | App ID | Workspace | Schema | Notes |
|---|---|---:|---|---|---|
| DEV | `https://apex.example.com/ords/` | 100 | WORKSPACE_NAME | APP_SCHEMA | Safe for agent-assisted changes after confirmation |
| TEST | `https://test.example.com/ords/` | 100 | WORKSPACE_NAME | APP_SCHEMA | Validate release candidates |
| PROD | `https://prod.example.com/ords/` | 100 | WORKSPACE_NAME | APP_SCHEMA | Read-only unless explicitly authorized |

## Implementation Rules

- When to use Page Designer: focused page structure changes, buttons, Dynamic Actions, items, and regions.
- When to use SQLcl: diagnostics, metadata inspection, PL/SQL compilation, `user_errors`, and read-only exports.
- When to use Object Browser: package compilation fallback when SQLcl is unavailable.
- When to use internal APEX APIs: repeatable multi-page changes only after testing in DEV.
- When to ask for authorization before changing the database: any DDL, mass DML, grants, jobs, imports, PROD action, or security setting.
- How to publish Git changes: commit only task-scoped files and open a pull request.

## Code Ownership

| Feature type | Where it should live | Notes |
|---|---|---|
| Contextual help | `PK_HELP` | Render through Dynamic Content |
| Dashboards | `PK_DASHBOARD` | APEX calls public package functions |
| Management reports | `PK_REPORTS` | Keep SQL readable and business-language labels |
| Transactional rules | domain packages | Do not place complex rules directly in page processes |
| HTTP/REST integrations | integration packages | Follow `rest-integrations.md` and project auth docs |

## Screen Patterns

- Theme: Universal Theme with compact business screens.
- Menu: side navigation.
- Breadcrumb: page title plus help action when the page has contextual help.
- Primary buttons: top/right for page-level actions, footer for modal save.
- Secondary buttons: near the primary action, visually lower priority.
- Row actions: menu or icon actions in report rows.
- Filters: visible only when they change the operational result.
- Cards: compact, with business labels.
- Classic Report: operational lists with simple row actions.
- Interactive Report: user-driven analysis.
- Interactive Grid: inline editing only when business validation is clear.
- Forms: short, grouped by business concept.
- Modals/dialogs/drawers: use for focused create/edit/review flows.
- Empty-state messages: explain what the user can do next.
- Success messages: short business confirmation.
- Error messages: business-safe text, technical detail in logs.

## Contextual Help

- Where content lives: package function in the project help package.
- How the screen renders it: Dynamic Content region.
- How the user opens/closes it: help icon near the page header or breadcrumb.
- When help is always visible: only for critical first-use context.
- When help is collapsed/hidden: default for long tutorials, examples, and operational rules.

## User-Facing Language

Preferred terms:

- customer
- opportunity
- follow-up
- payment

Forbidden terms for end users:

- table name
- column name
- internal ID
- raw provider error

## Example Pages

| Type | Good pages to follow | Legacy pages/do not copy | Notes |
|---|---|---|---|
| Dashboard | 10, 20 | 1 | Compact cards, top filters, package-backed Dynamic Content |
| Operational report | 40, 41 | 7 | Classic Report with row actions |
| Create/edit form | 31, 32 | 5 | Save/Cancel in footer |
| Modal/dialog | 50, 51 | 8 | Focused action with clear return path |
| Wizard/upload/import | 60, 61 | 9 | Validate, review, confirm, history |

## Project Runtime Checklist

- [ ] Correct page.
- [ ] Correct session/context.
- [ ] Main flow tested.
- [ ] Known failure case tested.
- [ ] Text uses user-facing language.
- [ ] Layout is coherent in the real viewport.
- [ ] No internal technical names exposed.
- [ ] No APEX error.
