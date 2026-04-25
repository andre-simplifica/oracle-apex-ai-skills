# Adapt the Skill to Your Project

The most important file in the consuming project is:

```text
.oracle-apex-ai/project-profile.md
```

It is the contract between your APEX application and the generic skill.

## Step 1: create the profile

At the root of your project:

```bash
bash ~/.oracle-apex-ai-skills/scripts/init_project_profile.sh
```

This creates:

```text
.oracle-apex-ai/project-profile.md
.oracle-apex-ai/app-patterns.md
.oracle-apex-ai/page-patterns/.gitkeep
```

## Step 2: fill in the basics

In `project-profile.md`, fill in:

- application name;
- app id;
- workspace;
- schema owner;
- DEV environment;
- SQLcl command;
- API/OpenAPI documentation location, if the project has REST services;
- authentication pattern for internal/private APIs, using placeholders when needed;
- default branch;
- how changes are published.

## Step 3: document screen patterns

Describe how your application works:

- side menu, top menu, or both;
- breadcrumb pattern;
- primary and secondary buttons;
- action placement;
- modal pages;
- Inline Dialog, drawer, or another pattern;
- reports, cards, IG, IR, Classic Report;
- filter pattern;
- empty-state messages;
- success and error messages.

## Step 4: document ownership

Example:

```text
Executive dashboards live in PK_DASHBOARD.
Contextual help lives in PK_AJUDA.
Transactional rules stay in domain packages.
APEX calls public facades; it does not use loose SQL when a package already exists.
```

Each project must have its own packages and rules.

## Step 5: list example pages

Create a table like this:

```markdown
| Page type | Good pages to copy | Do not copy | Notes |
|---|---:|---:|---|
| Executive dashboard | 10, 20 | 1 | Uses compact cards and top filters |
| Modal form | 31, 32 | 5 | Uses Cancel/Save buttons in the footer |
| Operational report | 40, 41 | 7 | Classic Report with row actions |
```

## Step 6: version it in the project Git repository

The profile should live in the consuming project's Git repository. This way all developers and agents use the same standard.

```bash
git add .oracle-apex-ai/
git commit -m "Add APEX AI project profile"
git push
```

## Important

Do not put this in a public profile:

- passwords;
- tokens;
- wallets;
- sensitive customer data;
- private URLs that cannot be shared with the team;
- real schema names, workspace names, hostnames, customer names, or environment details that identify a private system;
- screenshots with confidential information.

If your project profile needs those details for your team to work well, keep the consuming project repository private.
