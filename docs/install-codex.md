# Install in Codex

The simplest path is asking Codex itself to install it using this repository.

```text
Install this Oracle APEX skill for me:
https://github.com/andre-simplifica/oracle-apex-ai-skills

Use Codex as the target, create the local links, and then help me create my APEX project profile.
Do not overwrite any existing profile under .oracle-apex-ai/.
```

If Codex has access to your local terminal, it can run the commands below and explain each step. If you prefer doing it manually, follow this guide.

## Step 1: clone the skill repository

```bash
git clone https://github.com/andre-simplifica/oracle-apex-ai-skills.git ~/.oracle-apex-ai-skills
```

If the folder already exists:

```bash
cd ~/.oracle-apex-ai-skills
git pull
```

## Step 2: install the skills in Codex

```bash
bash ~/.oracle-apex-ai-skills/scripts/install_codex.sh
```

The script creates symbolic links under:

```text
~/.codex/skills/oracle-apex-dev
~/.codex/skills/oracle-apex-export
```

## Step 3: check it

```bash
ls -l ~/.codex/skills/oracle-apex-dev
ls -l ~/.codex/skills/oracle-apex-export
```

The paths should point to:

```text
~/.oracle-apex-ai-skills/skills/oracle-apex-dev
~/.oracle-apex-ai-skills/skills/oracle-apex-export
```

## Step 4: create the project profile

At the root of your APEX project repository:

```bash
bash ~/.oracle-apex-ai-skills/scripts/init_project_profile.sh
```

Then edit:

```text
.oracle-apex-ai/project-profile.md
```

## Step 5: use it

In a new Codex conversation:

```text
Use the oracle-apex-dev skill to analyze page 10.
Before proposing a change, read the project profile under .oracle-apex-ai/ and check the example pages.
```

If the skill name or description changes, open a new conversation so Codex reloads the skill list.
