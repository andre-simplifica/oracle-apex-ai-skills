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

If it does not exist, guide the user to create it with:

```bash
bash ~/.oracle-apex-ai-skills/scripts/init_project_profile.sh
```

## What the Profile Should Contain

- Main app id.
- Workspace.
- Schema owner.
- DEV/TEST/PROD environments.
- SQLcl command or saved connection.
- API/OpenAPI documentation location.
- Authentication pattern for internal/private APIs.
- Default branch and publication rule.
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

If the profile does not answer one of these questions and the repository does not prove the answer either, ask the user or record the decision as pending.
