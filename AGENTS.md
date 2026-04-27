# AGENTS.md

This repository is the reusable Oracle APEX AI Skills project.

## Context

- Repository: `andre-simplifica/oracle-apex-ai-skills`
- Audience: Oracle APEX developers, PL/SQL developers, Oracle OCI users, and AI-assisted development practitioners
- Main target: Oracle APEX 24.2
- Core purpose: provide reusable skills, templates, scripts, and documentation that help AI agents work safely with Oracle APEX projects.

## Working Rules

- Work directly on `main` for this repository.
- When a change is finished, commit and push to `origin main` unless the user explicitly asks not to publish.
- Keep this repository generic and reusable. Do not add company-specific, customer-specific, or application-specific rules to the core.
- Do not include private schema names, workspace names, hostnames, internal URLs, credentials, production payloads, or customer data.
- Do not invent APEX, SQLcl, PL/SQL, OCI, Codex, Claude Code, or GitHub behavior. Verify current files before changing instructions.
- Prefer small, explicit, production-friendly guidance over broad abstractions.
- Keep documentation and skill content in English, except `README.pt-BR.md`, which is the Portuguese onboarding document.

## Source Boundaries

- General APEX development guidance belongs in `skills/oracle-apex-dev/`.
- General export and snapshot guidance belongs in `skills/oracle-apex-export/`.
- Human-facing guides belong in `docs/`.
- Reusable project-profile scaffolding belongs in `templates/`.
- Installer and validation logic belongs in `scripts/`.
- Application-specific project standards belong in the consuming project's `.oracle-apex-ai/` profile, not in this reusable core.

## Validation

Before committing, run:

```bash
bash scripts/validate_repo.sh
```

If the validation cannot run locally, state the blocker clearly in the final response.

## Publication Flow

For Codex work:

1. Inspect `git status --short --branch`.
2. Keep edits scoped to the requested improvement.
3. Run `bash scripts/validate_repo.sh`.
4. Commit the scoped change.
5. Push to `origin main`.

