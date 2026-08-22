#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
user_state_root="${APEX_AI_CODEX_USER_STATE_ROOT:-${HOME}/.agents}"
target_root="${APEX_AI_CODEX_USER_SKILLS_ROOT:-${HOME}/.agents/skills}"
legacy_target_root="${CODEX_HOME:-${HOME}/.codex}/skills"
replace_existing="false"
backup_root=""

if [[ "${1:-}" == "--replace-existing" ]]; then
  replace_existing="true"
fi

skills=(
  "oracle-apex-ai-skills"
  "oracle-apex-dev"
  "oracle-apex-export"
  "oracle-apex-object-lock"
)

create_backup_root() {
  if [[ -z "${backup_root}" ]]; then
    backup_root="${user_state_root}/skill-backups/oracle-apex-ai-skills-$(date -u +%Y%m%dT%H%M%SZ)"
    mkdir -p "${backup_root}"
  fi
}

if [[ "${legacy_target_root}" != "${target_root}" ]]; then
  legacy_entries=()
  for skill in "${skills[@]}"; do
    legacy_dir="${legacy_target_root}/${skill}"
    if [[ -e "${legacy_dir}" || -L "${legacy_dir}" ]]; then
      legacy_entries+=("${legacy_dir}")
    fi
  done

  if (( ${#legacy_entries[@]} > 0 )) && [[ "${replace_existing}" != "true" ]]; then
    echo "Legacy Codex skill entries were found under ${legacy_target_root}:" >&2
    printf '  %s\n' "${legacy_entries[@]}" >&2
    echo "Review them, then rerun with --replace-existing to back them up and remove the duplicate discovery path." >&2
    exit 1
  fi

  if (( ${#legacy_entries[@]} > 0 )); then
    create_backup_root
    mkdir -p "${backup_root}/legacy-codex-skills"
    for legacy_dir in "${legacy_entries[@]}"; do
      skill="$(basename "${legacy_dir}")"
      mv "${legacy_dir}" "${backup_root}/legacy-codex-skills/${skill}"
      echo "Backed up legacy ${legacy_dir} -> ${backup_root}/legacy-codex-skills/${skill}"
    done
  fi
fi

mkdir -p "${target_root}"

for skill in "${skills[@]}"; do
  source_dir="${repo_root}/skills/${skill}"
  target_dir="${target_root}/${skill}"

  if [[ ! -f "${source_dir}/SKILL.md" ]]; then
    echo "Skill source not found: ${source_dir}" >&2
    exit 1
  fi

  if [[ ( -e "${target_dir}" || -L "${target_dir}" ) && ! -L "${target_dir}" ]]; then
    if [[ "${replace_existing}" != "true" ]]; then
      echo "Refusing to replace non-symlink path: ${target_dir}" >&2
      echo "Review it, then rerun with --replace-existing to move it into a timestamped backup." >&2
      exit 1
    fi

    create_backup_root
    mkdir -p "${backup_root}/user-skills"
    mv "${target_dir}" "${backup_root}/user-skills/${skill}"
    echo "Backed up ${target_dir} -> ${backup_root}/user-skills/${skill}"
  fi

  ln -sfn "${source_dir}" "${target_dir}"
  echo "Installed ${skill} -> ${source_dir}"
done

echo
echo "Codex skills installed in: ${target_root}"
if [[ -n "${backup_root}" ]]; then
  echo "Previous entries were preserved in: ${backup_root}"
fi
echo "This is a personal/global installation."
echo "For a team project, prefer scripts/manage_project_installation.py."
echo "Restart Codex only if the updated skill list does not appear automatically."
