# Update and Contribute

## Keep your local skills up to date

This repository changes over time. Refresh your local installation whenever new guardrails, references, examples, or scripts are published.

The easiest path is to ask your AI agent:

```text
Refresh my local Oracle APEX skill installation using:
https://github.com/andre-simplifica/oracle-apex-ai-skills

Keep my project-specific files under .oracle-apex-ai/ unchanged.
Explain what changed after the update.
```

If you prefer doing it manually:

```bash
cd ~/.oracle-apex-ai-skills
bash scripts/update_core.sh
```

## What the refresh updates

The refresh updates:

- `oracle-apex-dev`;
- `oracle-apex-export`;
- generic references;
- installation scripts;
- templates.

It does not automatically delete or overwrite:

- `.oracle-apex-ai/project-profile.md` in your project;
- `.oracle-apex-ai/app-patterns.md` in your project;
- examples and standards specific to your application.

## Contribute improvements

Suggested flow:

1. Update your clone:

```bash
cd ~/.oracle-apex-ai-skills
git pull
```

2. Create a branch:

```bash
git checkout -b my-improvement
```

3. Edit the files.

4. If you update the public README onboarding message, update `README.pt-BR.md` too.

5. Validate scripts:

```bash
bash scripts/validate_repo.sh
```

6. Commit:

```bash
git add .
git commit -m "Improve Dynamic Actions validation"
```

7. Push:

```bash
git push -u origin my-improvement
```

8. Open a Pull Request on GitHub.

## What belongs in a PR to the core

Good candidate:

- generic APEX guardrail;
- SQLcl improvement;
- validation checklist that applies to any app;
- clearer profile template;
- installation script;
- documentation fix.

Not a good candidate for the core:

- "In my project the package is named PK_CLIENTE_X";
- "Our help always uses page 999";
- "Our menu is named MENU_ADMIN";
- business rules for a specific customer.

Those details belong in the consuming project's profile.
