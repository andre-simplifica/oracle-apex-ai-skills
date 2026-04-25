# Agent Compatibility

This project should not be locked to a single tool.

## Base format

The main content is Markdown:

```text
skills/oracle-apex-dev/SKILL.md
skills/oracle-apex-dev/references/*.md
```

Any agent that can read Markdown instructions and project files can use this material.

## Codex

Codex recognizes skills under:

```text
~/.codex/skills/
```

Use:

```bash
bash scripts/install_codex.sh
```

## Claude Code

Claude Code recognizes skills under:

```text
~/.claude/skills/
```

or:

```text
.claude/skills/
```

Use:

```bash
bash scripts/install_claude_code.sh
```

## Other agents

For other agents, the recommendation is:

1. point the agent to `skills/oracle-apex-dev/SKILL.md`;
2. make sure it can read `references/`;
3. make sure it reads `.oracle-apex-ai/project-profile.md` in the consuming project;
4. adapt only the installation mechanism, not the technical content.

## Portability rule

The core must not depend on commands exclusive to a single tool when a simple alternative exists. When a tool has its own feature, document it as an adapter, not as the main technical rule.
