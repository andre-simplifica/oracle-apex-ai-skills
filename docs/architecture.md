# Repository Architecture

This repository has two separate responsibilities.

## 1. Shared core

Located at:

```text
skills/oracle-apex-dev/
skills/oracle-apex-export/
```

This core should work in any Oracle APEX 24.2 project. It defines:

- when to use Page Designer;
- when to use SQLcl;
- when to use Object Browser;
- how to validate runtime behavior;
- how to use temporary read-only exports;
- when to consider internal APEX APIs;
- how to separate analysis, implementation, and publication;
- which guardrails to use so the agent does not invent objects, rules, or structure.

## 2. Local project profile

Located inside each consuming project repository:

```text
.oracle-apex-ai/project-profile.md
.oracle-apex-ai/app-patterns.md
.oracle-apex-ai/page-patterns/
```

This profile defines details that change from one project to another:

- main app id;
- workspace and environment;
- theme;
- menu pattern;
- breadcrumb pattern;
- button pattern;
- help pattern;
- owning packages;
- example pages;
- old pages that should not be copied;
- user-facing language;
- visual validation checklist.

## Why not copy everything into the skill?

Because the skill must be reusable. If "help opens from the breadcrumb icon in an Inline Dialog" is true for one project, but another project uses a side drawer, that rule cannot live in the core.

The core should say:

> Read the project profile before creating or changing screens.

The project profile should say:

> In this project, help opens from the breadcrumb icon in an Inline Dialog.

## How refresh works

The developer installs the shared core as symbolic links pointing to the clone of this repository.

When there is an improvement:

```bash
cd ~/.oracle-apex-ai-skills
bash scripts/update_core.sh
```

The links continue to point to the updated files. The project profile is not overwritten because it lives in the application repository.
