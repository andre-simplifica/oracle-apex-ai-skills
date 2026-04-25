# Contributing

This project standardizes AI-assisted development for Oracle APEX 24.2.

## Main Rule

Do not put company-specific or application-specific rules in the generic skill core.

If a rule depends on a package, page, theme, menu, breadcrumb, naming convention, or flow that only exists in one application, it belongs in the consuming project's `project-profile.md`, not in `skills/oracle-apex-dev/SKILL.md`.

## Where to Contribute

- General APEX, SQLcl, validation, or guardrail improvements: `skills/oracle-apex-dev/`.
- General export/snapshot improvements: `skills/oracle-apex-export/`.
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
- Did you read `SECURITY.md` before posting examples, logs, or screenshots?
- Did you run `bash scripts/validate_repo.sh`?

## Language Policy

- The repository is international: documentation, skills, templates, metadata, and scripts should be in English.
- The only Portuguese public onboarding document is `README.pt-BR.md`.
- When changing the public README, update `README.pt-BR.md` when the onboarding message changes.
- Oracle/APEX technical terms may stay in English when that is the natural community usage.
