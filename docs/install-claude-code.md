# Install in Claude Code

This repository can also be used with Claude Code because the skill is Markdown with a compatible structure.

The simplest path is asking Claude Code to install it:

```text
Install this Oracle APEX skill for me:
https://github.com/andre-simplifica/oracle-apex-ai-skills

Use Claude Code as the target, create the local links, and then help me create my APEX project profile.
Do not overwrite any existing profile under .oracle-apex-ai/.
```

## Install globally

```bash
git clone https://github.com/andre-simplifica/oracle-apex-ai-skills.git ~/.oracle-apex-ai-skills
bash ~/.oracle-apex-ai-skills/scripts/install_claude_code.sh
```

The script creates links under:

```text
~/.claude/skills/oracle-apex-dev
~/.claude/skills/oracle-apex-export
```

## Install in the project

If you prefer to keep the skills inside the project repository:

```bash
bash ~/.oracle-apex-ai-skills/scripts/install_claude_code.sh --project
```

This creates:

```text
.claude/skills/oracle-apex-dev
.claude/skills/oracle-apex-export
```

## Project profile

Even when using Claude Code, keep the profile in:

```text
.oracle-apex-ai/project-profile.md
```

This way the same profile can serve Codex, Claude Code, and other agents that can read project files.
