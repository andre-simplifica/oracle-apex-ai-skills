<!-- oracle-apex-ai-project-profile-version: 3 -->
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
- Confirmed live APEX version command/query:
- APEX compatibility validator command:
- APEX 26.1 public APIs allowed only after version gate: yes
- APEXlang operations: disabled
- Database/environment:
- SQLcl command/saved connection:
- Expected SQLcl `USER`:
- Expected SQLcl `SERVICE_NAME` or required service token:
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
- Operations that require explicit export/publication authorization:

## Oracle APEX AI Skills Installation

- Installation mode: project-managed `.agents/skills`
- Generated source/ref/commit record: `.oracle-apex-ai/upstream-lock.json`
- Installation manifest: `.oracle-apex-ai/installation-manifest.json`
- Compatibility record: `.oracle-apex-ai/compatibility.json`
- Project-owned export policy: `.oracle-apex-ai/export-policy.json`
- Update policy:

The installer owns only its manifest, upstream lock, compatibility record, copied core skills, copied project manager, and copied validation/retention helpers. It must not overwrite this profile, application patterns, page patterns, export policy, or migrations.

## Cooperative Database Object Locks

- Shared DEV schema: yes/no
- Runtime required before supported object compilation: yes
- Audit command:
- Install/upgrade command:
- Required runtime version: `1.1.0`
- Lock owner naming pattern:
- Default TTL minutes: `240`
- Git base reference checked before lock:
- Administrative force-lock policy:
- Released/expired lock history retention days: `30`

For packages, one `PACKAGE` lock covers both specification and body. The runtime is cooperative; manual DDL outside the workflow can bypass it.

## Versioned Source and Release

- Official APEX snapshot path:
- APEX export script/command:
- Require split export (`install.sql` + `application/`): yes/no
- Require readable YAML before APEX 26.1: yes/no
- Omit readable YAML on APEX 26.1 or later: yes
- APEXlang generate/export/validate/import: disabled
- Require monolithic `f<APP_ID>.sql`: yes/no
- Supporting Objects policy:
- Treat required APEX formats as one atomic snapshot: yes/no
- Canonical combined APEX/database export command:
- Supported database release scopes: partial/full
- Database snapshot/source identifier and reuse policy:
- Database snapshot runtime audit command:
- Database snapshot runtime install/upgrade command:
- Database snapshot runtime uninstall command:
- Global SQLcl/session cap for export workers:
- Target lock behavior:
- Manifest and per-worker log location:
- Required timing evidence: wall clock/APEX/database lanes
- Database baseline path: `db/baseline`
- Canonical database object source path:
- Release path pattern: `db/releases/<release>`
- Release inventory file:
- Database release scope default: `partial`
- Full bundle naming: `snapshot_<id>_full_<order>_<group>.sql`
- Partial bundle naming: `snapshot_<id>_partial_<order>_<group>.sql`
- Partial comparison base selection rule:
- Project-approved compile routine, or none:

Release modes:

- Initial baseline: complete APEX application + complete application-schema structural DDL.
- Normal partial release: complete APEX application + five files containing changed database objects + pending DDL/DML.
- Full release: complete APEX application + five files containing all supported database objects + pending DDL/DML.
- Daily development: no official export unless explicitly requested.

## Pending DDL and DML

- Pending path: `db/migrations/pending`
- Pending DDL file: `pending_ddl.sql`
- Pending DML file: `pending_dml.sql`
- Applied/archive path: `db/migrations/applied`
- Environment whose confirmed application advances lifecycle:
- Person/process that confirms application:
- Release handling (copy/reference):
- Confirmed-content archive/reset rule:

Every table or structural DDL change goes to the DDL file. Reviewed data corrections/backfills go to the DML file. APEX pages/components and standalone package/view/trigger/routine/type/synonym source never go to pending. Generating a release or testing in DEV does not archive/reset pending content.

## Export Retention

- Retention policy file: `.oracle-apex-ai/export-policy.json`
- Review every N release directories: `5`
- Repository release mode: report/prune
- Keep latest repository releases: `10`
- Database snapshot retention enabled: yes/no
- Keep database snapshot months: `6`
- Keep stored database scripts: `30`
- Canonical authorized cleanup command/script:

Retention review is part of release closeout. Deletion or database purge remains a separate explicit operation.

## Optional Companion Skills

- `build-apex-brand-reports` available: yes/no
- Repository: `https://github.com/andre-simplifica/oracle-apex-brand-report-kit`
- Installed tag/commit:
- Use it for:
- `oracle-apex-echarts` available: yes/no
- Repository: `https://github.com/andre-simplifica/oracle-apex-echarts`
- Installed tag/commit:
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
| Dynamic Content and package-owned UI |  |  |

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
- Dynamic Content `RETURN CLOB` regions:
- Dashboard click/filter/group/export actions:

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

## Continuous Pattern Learning

- Where user-declared standards are recorded: `.oracle-apex-ai/app-patterns.md`
- Page evidence directory: `.oracle-apex-ai/page-patterns/`
- Rule for distinguishing a reusable standard from a one-page exception:
- Required review before applying a new standard across pages:

## Project Runtime Checklist

- [ ] Correct page.
- [ ] Correct session/context.
- [ ] Main flow tested.
- [ ] Known failure case tested.
- [ ] Text uses user-facing language.
- [ ] Layout is coherent in the real viewport.
- [ ] No internal technical names exposed.
- [ ] No APEX error.
