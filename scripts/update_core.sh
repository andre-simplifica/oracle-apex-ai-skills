#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

cd "${repo_root}"

if [[ ! -d .git ]]; then
  echo "This script must run inside a git clone of oracle-apex-ai-skills." >&2
  exit 1
fi

git pull --ff-only

if [[ -d "${CODEX_HOME:-${HOME}/.codex}" ]]; then
  bash scripts/install_codex.sh
fi

if [[ -d "${HOME}/.claude" ]]; then
  bash scripts/install_claude_code.sh
fi

echo
echo "Core skills updated. Project profiles under .oracle-apex-ai/ were not modified."
