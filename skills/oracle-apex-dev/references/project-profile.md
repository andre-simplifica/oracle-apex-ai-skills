# Project Profile

The project profile is the file that turns the generic skill into behavior that matches a real application.

Look in the consuming project for:

```text
.oracle-apex-ai/project-profile.md
```

## Security Boundary

A filled project profile may contain private environment details.

If it includes private URLs, real workspace names, schema names, SQLcl aliases, hostnames, customer references, API authentication patterns, or operational rules that should not be public, it must stay in the consuming project's private repository.

Never copy a filled project profile into the public skill repository.

If it does not exist, initialize it through the project-managed installation. From a clean, reviewed source:

```bash
python3 /path/to/oracle-apex-ai-skills/scripts/manage_project_installation.py \
  install \
  --project-root /path/to/project \
  --source-ref <tag-or-commit>
```

If the four skills are already installed but the project intentionally skipped the scaffold, copy `templates/project-profile.md` manually only after confirming the target does not exist.

## What the Profile Should Contain

- Main app id.
- Workspace.
- Schema owner.
- DEV/TEST/PROD environments.
- SQLcl command or saved connection.
- API/OpenAPI documentation location.
- Authentication pattern for internal/private APIs.
- Default branch and publication rule.
- Installed skill source/ref/commit and update policy.
- Cooperative object-lock audit, runtime, actor, TTL, and Git-base rules.
- Official APEX snapshot and database baseline/object-source paths.
- Initial-baseline and normal-release rules.
- Pending and applied migration paths and lifecycle authority.
- Optional Brand Report Kit and ECharts usage.
- Page Designer vs SQLcl vs Object Browser standard.
- Owning packages by functionality type.
- Navigation, menu, and breadcrumb patterns.
- Button and action patterns.
- Contextual help pattern.
- Dialog, drawer, and modal patterns.
- Dashboard, report, card, IG/IR/Classic Report patterns.
- User-facing language and forbidden terms.
- Example pages that should be copied.
- Legacy pages that should not be copied.
- Runtime validation checklist.

## How to Use It

Before creating or editing a page, read the profile and answer:

- Which existing page is the best model?
- Which package should be called?
- How should help appear?
- Where do primary and secondary buttons go?
- How should success and known failure cases be validated?
- Which terms must not appear to end users?
- Which database objects require locks, and is the runtime currently compatible?
- Is this daily development, a first baseline, or an explicitly requested release?
- Which structural DDL must be created under the pending path?

If the profile does not answer one of these questions and the repository does not prove the answer either, ask the user or record the decision as pending.
