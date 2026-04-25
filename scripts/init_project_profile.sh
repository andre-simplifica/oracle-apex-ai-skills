#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
project_root="$(pwd)"
target_dir="${project_root}/.oracle-apex-ai"

mkdir -p "${target_dir}/page-patterns"

copy_if_missing() {
  local source_file="$1"
  local target_file="$2"

  if [[ -e "${target_file}" ]]; then
    echo "Keeping existing ${target_file}"
  else
    cp "${source_file}" "${target_file}"
    echo "Created ${target_file}"
  fi
}

copy_if_missing "${repo_root}/templates/project-profile.md" "${target_dir}/project-profile.md"
copy_if_missing "${repo_root}/templates/app-patterns.md" "${target_dir}/app-patterns.md"

if [[ ! -e "${target_dir}/page-patterns/.gitkeep" ]]; then
  : > "${target_dir}/page-patterns/.gitkeep"
  echo "Created ${target_dir}/page-patterns/.gitkeep"
fi

echo
echo "Project profile initialized in: ${target_dir}"
echo "Next step: edit .oracle-apex-ai/project-profile.md with your application's real standards."
