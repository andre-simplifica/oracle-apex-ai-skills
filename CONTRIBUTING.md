# Contributing

This project standardizes AI-assisted development for Oracle APEX 24.2.

## Main Rule

Do not put company-specific or application-specific rules in the generic skill core.

If a rule depends on a package, page, theme, menu, breadcrumb, naming convention, or flow that only exists in one application, it belongs in the consuming project's `project-profile.md`, not in `skills/oracle-apex-dev/SKILL.md`.

## Where to Contribute

- General APEX, SQLcl, validation, or guardrail improvements: `skills/oracle-apex-dev/`.
- Main routing and installation contract: `skills/oracle-apex-ai-skills/`.
- Cooperative object-lock behavior and runtime: `skills/oracle-apex-object-lock/`.
- General baseline/export/snapshot/release improvements: `skills/oracle-apex-export/`.
- Human-facing guides: `docs/`.
- Reusable templates: `templates/`.
- Installation automation: `scripts/`.
- Brazilian onboarding copy only: `README.pt-BR.md`.

## Pull Request Checklist

- Is the change generic enough for other APEX projects?
- Does the text avoid credentials, private URLs, customer names, and private screenshots?
- Did you remove real schema names, workspace names, hostnames, internal URLs, production payloads, and customer data?
- Does the rule mention APEX 24.2 or SQLcl when version behavior matters?
- Does the workflow state when runtime validation is required?
- Does the local project profile remain separate from the core?
- Does a project update preserve profiles, patterns, and migrations?
- Are database runtime installation and file installation still separate?
- Do shared-DEV compilation rules enforce cooperative object locks?
- Does the project keep one pending root with exactly one DDL file and one DML file?
- Are APEX components and standalone package/view/trigger/routine/type/synonym source excluded from pending?
- Do full and partial database exports keep the five-file release contract and explicit snapshot lineage?
- Are retention and database cleanup report-only unless separately configured and authorized?
- Are new project-owned standards recorded in the consuming project's patterns instead of the generic core?
- Did you read `SECURITY.md` before posting examples, logs, or screenshots?
- Did you run `bash scripts/validate_repo.sh`?

## Language Policy

- The repository is international: documentation, skills, templates, metadata, and scripts should be in English.
- The only Portuguese public onboarding document is `README.pt-BR.md`.
- When changing the public README, update `README.pt-BR.md` when the onboarding message changes.
- Oracle/APEX technical terms may stay in English when that is the natural community usage.
