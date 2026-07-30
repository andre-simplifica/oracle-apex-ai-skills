# APEX Project Profile

Copy this file to:

```text
.oracle-apex-ai/project-profile.md
```

Fill it with the real standards of your application.

> [!WARNING]
> A filled project profile can expose private environment details.
>
> If this file contains private URLs, real workspace names, schema names, customer names, SQLcl aliases, hostnames, internal application IDs, or operational details, keep it in a private repository.
>
> Do not copy a filled project profile into the public `oracle-apex-ai-skills` repository.

## Identification

- Project name:
- Main APEX application:
- App ID:
- Workspace:
- Schema owner:
- APEX version:
- Database/environment:
- SQLcl command/saved connection:
- Default branch:
- Repository remote used as release base:
- API/OpenAPI documentation location:
- Authentication pattern for internal/private APIs:

## Environments

| Environment | URL/Base | App ID | Workspace | Schema | Notes |
|---|---|---:|---|---|---|
| DEV |  |  |  |  |  |
| TEST |  |  |  |  |  |
| PROD |  |  |  |  |  |

## Implementation Rules

- When to use Page Designer:
- When to use SQLcl:
- When to use Object Browser:
- When to use internal APEX APIs:
- When to ask for authorization before changing the database:
- How to publish Git changes:

## Oracle APEX AI Skills Installation

- Installation mode: project-managed `.agents/skills`
- Generated source/ref/commit record: `.oracle-apex-ai/upstream-lock.json`
- Installation manifest: `.oracle-apex-ai/installation-manifest.json`
- Compatibility record: `.oracle-apex-ai/compatibility.json`
- Update policy:

The installer owns only its manifest, upstream lock, compatibility record, copied core skills, and copied project manager. It must not overwrite this profile, application patterns, page patterns, or migrations.

## Cooperative Database Object Locks

- Shared DEV schema: yes/no
- Runtime required before supported object compilation: yes
- Audit command:
- Install/upgrade command:
- Required runtime version: `1.0.0`
- Lock owner naming pattern:
- Default TTL minutes: `240`
- Git base reference checked before lock:
- Administrative force-lock policy:

For packages, one `PACKAGE` lock covers both specification and body. The runtime is cooperative; manual DDL outside the workflow can bypass it.

## Versioned Source and Release

- Official APEX snapshot path:
- APEX export script/command:
- Require split export (`install.sql` + `application/`): yes/no
- Require readable YAML: yes/no
- Require monolithic `f<APP_ID>.sql`: yes/no
- Supporting Objects policy:
- Database baseline path: `db/baseline`
- Canonical database object source path:
- Release path pattern: `db/releases/<release>`
- Release inventory file:

Release modes:

- Initial baseline: complete APEX application + complete application-schema structural DDL.
- Normal release: complete APEX application + changed database objects + pending migrations.
- Daily development: no official export unless explicitly requested.

## Pending DDL Migrations

- Pending path: `db/migrations/pending`
- Applied/archive path: `db/migrations/applied`
- Filename convention: `YYYYMMDDHHMM_<short_description>.sql`
- Environment whose confirmed application advances lifecycle:
- Person/process that confirms application:
- Release handling (copy/reference/move):

Every table or structural DDL change starts in the pending path. Generating a release or testing in DEV does not move a migration to applied.

## Optional Companion Skills

- `build-apex-brand-reports` available: yes/no
- Use it for:
- `oracle-apex-echarts` available: yes/no
- Use it for:

The Oracle APEX AI Skills core works without these companions. Use them only when installed and relevant.

## Code Ownership

| Feature type | Where it should live | Notes |
|---|---|---|
| Contextual help |  |  |
| Dashboards |  |  |
| Management reports |  |  |
| Transactional rules |  |  |
| HTTP/REST integrations |  |  |

## Screen Patterns

- Theme:
- Menu:
- Breadcrumb:
- Primary buttons:
- Secondary buttons:
- Row actions:
- Filters:
- Cards:
- Classic Report:
- Interactive Report:
- Interactive Grid:
- Forms:
- Modals/dialogs/drawers:
- Empty-state messages:
- Success messages:
- Error messages:

## Contextual Help

- Where content lives:
- How the screen renders it:
- How the user opens/closes it:
- When help is always visible:
- When help is collapsed/hidden:

## User-Facing Language

Preferred terms:

- 

Forbidden terms for end users:

- 

## Example Pages

| Type | Good pages to follow | Legacy pages/do not copy | Notes |
|---|---|---|---|
| Dashboard |  |  |  |
| Operational report |  |  |  |
| Create/edit form |  |  |  |
| Modal/dialog |  |  |  |
| Wizard/upload/import |  |  |  |

## Project Runtime Checklist

- [ ] Correct page.
- [ ] Correct session/context.
- [ ] Main flow tested.
- [ ] Known failure case tested.
- [ ] Text uses user-facing language.
- [ ] Layout is coherent in the real viewport.
- [ ] No internal technical names exposed.
- [ ] No APEX error.
