#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
target_root="${HOME}/.agents/skills"

skills=(
  "oracle-apex-ai-skills"
  "oracle-apex-dev"
  "oracle-apex-export"
  "oracle-apex-object-lock"
)

mkdir -p "${target_root}"

for skill in "${skills[@]}"; do
  source_dir="${repo_root}/skills/${skill}"
  target_dir="${target_root}/${skill}"

  if [[ ! -f "${source_dir}/SKILL.md" ]]; then
    echo "Skill source not found: ${source_dir}" >&2
    exit 1
  fi

  if [[ -e "${target_dir}" && ! -L "${target_dir}" ]]; then
    echo "Refusing to replace non-symlink path: ${target_dir}" >&2
    echo "Move it away or remove it manually, then rerun this script." >&2
    exit 1
  fi

  ln -sfn "${source_dir}" "${target_dir}"
  echo "Installed ${skill} -> ${source_dir}"
done

echo
echo "Codex skills installed in: ${target_root}"
echo "This is a personal/global installation."
echo "For a team project, prefer scripts/manage_project_installation.py."
echo "Restart Codex only if the updated skill list does not appear automatically."
