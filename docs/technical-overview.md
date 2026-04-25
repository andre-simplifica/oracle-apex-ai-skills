# Technical Overview

This page is the more structured version of the README for people who want to understand the repository layout, installation model, and project-profile strategy before using the skill.

## Supported APEX version

Current target: **Oracle APEX 24.2**.

The instructions were written for APEX 24.2, modern SQLcl, and Oracle Database/Autonomous Database. In other versions, validate API signatures, export behavior, and runtime behavior before standardizing the workflow.

| Version | Status |
| --- | --- |
| APEX 24.2 | Main target |
| APEX 24.1 | Likely compatible, validate export behavior and API signatures |
| APEX 23.2 | Use with caution and validate runtime behavior |
| APEX older than 23 | Not recommended without adaptation |

## Repository responsibilities

This repository provides:

- generic APEX development skill: `oracle-apex-dev`;
- generic APEX export/snapshot skill: `oracle-apex-export`;
- templates to document each application's standards;
- install/update scripts for Codex and Claude Code;
- human documentation for APEX developers who are new to AI agents, skills, or GitHub.

## Core idea

Always separate:

**Reusable core**

The shared APEX workflow: SQLcl, Page Designer, Object Browser, internal APEX APIs, runtime validation, read-only exports, and guardrails.

**Project profile**

The way your application works: theme, navigation, breadcrumbs, menus, dialogs, dashboards, owning packages, user-facing language, and example pages.

The reusable core lives here. The project profile lives inside each consuming project.

## Installation model

The install scripts create symbolic links from the AI tool skill folder to this repository's `skills/` folders.

For Codex:

```text
~/.codex/skills/oracle-apex-dev
~/.codex/skills/oracle-apex-export
```

For Claude Code:

```text
~/.claude/skills/oracle-apex-dev
~/.claude/skills/oracle-apex-export
```

Because they are links, updating the repository updates the skill source without copying files around.

## Manual install

For Codex:

```bash
git clone https://github.com/andre-simplifica/oracle-apex-ai-skills.git ~/.oracle-apex-ai-skills
bash ~/.oracle-apex-ai-skills/scripts/install_codex.sh
```

For Claude Code:

```bash
git clone https://github.com/andre-simplifica/oracle-apex-ai-skills.git ~/.oracle-apex-ai-skills
bash ~/.oracle-apex-ai-skills/scripts/install_claude_code.sh
```

Inside the consuming APEX project:

```bash
bash ~/.oracle-apex-ai-skills/scripts/init_project_profile.sh
```

Then edit:

```text
.oracle-apex-ai/project-profile.md
```

## Update model

When this repository gets an improvement:

```bash
cd ~/.oracle-apex-ai-skills
bash scripts/update_core.sh
```

The script pulls the shared core and reinstalls links. It does not overwrite project profiles under `.oracle-apex-ai/`.

## Using the database

The skill can work from files only, but it is stronger when the agent can safely use your development environment.

Good setups include:

- SQLcl with an existing connection;
- VS Code with Oracle/SQL Developer extension;
- SQL Developer connection already working;
- Oracle XE local;
- Oracle VM;
- OCI Autonomous Database with wallet or SQLNet;
- browser access to DEV APEX.

Never store secrets in this repository or in the project profile. Tell the AI agent how to use the secure local connection you already use.

## What belongs in the core

Good core rules:

- generic APEX guardrails;
- SQLcl and export practices;
- runtime validation checklists;
- Page Designer and Object Browser workflow;
- REST integration, SQL/PLSQL, debugging, background job, security, and high-risk operation guidance that applies broadly;
- guidance that works across multiple APEX projects.

Do not put project-specific rules in the core:

- package names that only exist in one product;
- one application's breadcrumb convention;
- one company's menu names;
- customer-specific business rules;
- private URLs, credentials, or screenshots.

Those belong in the consuming project's `.oracle-apex-ai/` profile.

## Documentation Language

The repository is international, so documentation, skills, templates, metadata, and scripts should be in English.

The only Portuguese public onboarding document is:

```text
README.pt-BR.md
```

When changing the public README message, update `README.pt-BR.md` as well so Brazilian APEX developers have an easier onboarding path.
