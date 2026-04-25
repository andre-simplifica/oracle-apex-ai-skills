#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"

cd "${repo_root}"

missing=0

for skill in skills/*; do
  [[ -d "${skill}" ]] || continue
  if [[ ! -f "${skill}/SKILL.md" ]]; then
    echo "Missing SKILL.md in ${skill}" >&2
    missing=1
  fi
done

if [[ ! -f README.pt-BR.md ]]; then
  echo "Missing README.pt-BR.md" >&2
  missing=1
fi

if [[ ! -f SECURITY.md ]]; then
  echo "Missing SECURITY.md" >&2
  missing=1
fi

if [[ ! -f .github/PULL_REQUEST_TEMPLATE.md ]]; then
  echo "Missing .github/PULL_REQUEST_TEMPLATE.md" >&2
  missing=1
fi

if [[ -d docs/en ]]; then
  echo "Unexpected docs/en directory. Keep docs in English at docs/ root." >&2
  missing=1
fi

bash -n scripts/*.sh

if [[ "${missing}" -ne 0 ]]; then
  exit 1
fi

echo "Repository validation passed."
