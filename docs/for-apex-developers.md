# Guide for Oracle APEX Developers

This guide assumes you know Oracle APEX, PL/SQL, Page Designer, and SQL Developer/SQLcl, but you may not yet be used to AI skills, LLMs, or GitHub workflows.

## What is a skill?

A skill is a set of instructions that teaches an AI agent how to work in a specific way.

In this case, the skill teaches the agent to work with Oracle APEX 24.2 while respecting:

- Page Designer;
- SQLcl;
- Object Browser;
- PL/SQL packages;
- APEX exports;
- runtime validation;
- application standards;
- security and low production risk.

Think of it as an onboarding guide for the AI agent. Instead of explaining every day that it must not invent tables, must not edit versioned APEX exports as the primary implementation path, and must validate runtime behavior, you document that once.

## What the skill does not do by itself

The skill does not replace engineering judgment. It should not:

- invent tables, columns, or packages;
- create business rules without evidence;
- change screens without runtime validation;
- edit versioned APEX exports as the default implementation path;
- hide compilation errors;
- ignore the visual standard of the project.

## Daily usage

Example prompts:

```text
Use the oracle-apex-dev skill and analyze page 123 before proposing a change.
```

```text
Use the oracle-apex-dev skill to create a new page following the pattern of pages 120 and 121.
```

```text
Use the oracle-apex-dev skill to review this upload flow.
Before changing anything, check Session State, staging, and runtime.
```

```text
Use the oracle-apex-export skill to update the APEX application snapshot.
```

## How to get more value

You get more value when your AI tool can see your project and, when possible, connect to your database/APEX environment.

Useful environments include:

- SQLcl already configured on your machine;
- VS Code with Oracle extension and a working connection;
- SQL Developer or SQL Developer Extension;
- local Oracle XE;
- Oracle VM in VirtualBox;
- Autonomous Database on OCI with wallet or SQLNet configured;
- a DEV APEX environment accessible through the browser.

Do not put passwords, tokens, or wallets inside the skill. Tell the AI agent that the connection already exists and ask it to use the secure local path you already use.

If there is no database connection, that is still useful. The AI agent can review exports, packages, SQL, and flows. It just must not claim it validated runtime behavior when it did not.

## What you need to fill in your project

After installation, run:

```bash
bash ~/.oracle-apex-ai-skills/scripts/init_project_profile.sh
```

Then edit:

```text
.oracle-apex-ai/project-profile.md
```

Fill it with how your application actually works:

- app id;
- workspace;
- SQLcl connection;
- theme;
- menus;
- breadcrumbs;
- buttons;
- owning packages;
- help pattern;
- dashboard pattern;
- dialog pattern;
- example pages;
- mandatory validations.

The better this file is, the better the agent works.

## Practical rule

Before asking "create a new page", provide example pages:

```text
Create a new page following the visual and operational pattern of pages 45 and 46.
Do not copy page 12 because it is legacy.
```

This helps the AI follow the real application standard instead of a generic pattern.
