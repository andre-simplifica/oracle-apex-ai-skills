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
repo_pycache_dir="${repo_root}/.tmp/pycache"
mkdir -p "${repo_pycache_dir}"
PYTHONPYCACHEPREFIX="${repo_pycache_dir}" \
  python3 -m py_compile scripts/manage_project_installation.py tests/*.py
PYTHONPYCACHEPREFIX="${repo_pycache_dir}" \
  python3 -m unittest discover -s tests -v

python3 - <<'PY'
import json
from pathlib import Path

root = Path.cwd()
json.loads((root / "templates" / "compatibility.json").read_text(encoding="utf-8"))
for schema in sorted((root / "schemas").glob("*.schema.json")):
    json.loads(schema.read_text(encoding="utf-8"))

expected = {
    "oracle-apex-ai-skills",
    "oracle-apex-dev",
    "oracle-apex-export",
    "oracle-apex-object-lock",
}
actual = {
    path.name
    for path in (root / "skills").iterdir()
    if path.is_dir() and (path / "SKILL.md").is_file()
}
if actual != expected:
    raise SystemExit(f"Unexpected core skill set: {sorted(actual)}")
PY

if rg -n --glob '!validate_repo.sh' \
  '\[TODO|TODO:' skills templates docs scripts README.md README.pt-BR.md; then
  echo "Unresolved TODO marker found." >&2
  missing=1
fi

if rg -n --hidden \
  '(BEGIN (RSA |OPENSSH )?PRIVATE KEY|AKIA[0-9A-Z]{16}|password[[:space:]]*=[[:space:]]*[^<[:space:]]+)' \
  skills templates docs scripts README.md README.pt-BR.md; then
  echo "Potential secret found in public content." >&2
  missing=1
fi

if [[ "${missing}" -ne 0 ]]; then
  exit 1
fi

echo "Repository validation passed."
