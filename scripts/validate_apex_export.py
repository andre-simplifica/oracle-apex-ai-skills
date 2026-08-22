#!/usr/bin/env python3
"""Validate an atomic Oracle APEX 24.2 split/readable/monolithic export."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys


VERSION_SCN_RE = re.compile(r"\bp_version_scn\s*=>\s*(\d+)", re.IGNORECASE)
APP_ID_RE_TEMPLATE = r"\bp_default_application_id\s*=>\s*{app_id}\b"
PAGE_FILE_RE = re.compile(r"page_(\d+)\.sql$", re.IGNORECASE)
YAML_PAGE_RE = re.compile(r"(?:page_|p)(\d+)\.ya?ml$", re.IGNORECASE)
HIGH_CONFIDENCE_SECRET_RE = re.compile(
    r"(?i)(?:-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY-----"
    r"|authorization\s*[:=]\s*bearer\s+[A-Za-z0-9._-]{20,})"
)
QUOTED_SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)(password|client_secret|api_key)\s*(?:=>|:|=)\s*"
    r"(?P<quote>['\"])(?P<value>[^'\"\r\n]{8,})(?P=quote)"
)
PLACEHOLDER_RE = re.compile(
    r"(?i)(?:placeholder|changeme|change_me|replace_me|example|dummy|password|secret|your[_ -])"
)


class ApexExportError(RuntimeError):
    pass


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def contains_potential_secret(content: str) -> bool:
    if HIGH_CONFIDENCE_SECRET_RE.search(content):
        return True
    for match in QUOTED_SECRET_ASSIGNMENT_RE.finditer(content):
        value = match.group("value").strip()
        if value.startswith(("<", "&", "#", "${", "{{")) or PLACEHOLDER_RE.search(value):
            continue
        categories = sum(
            bool(re.search(pattern, value))
            for pattern in (r"[a-z]", r"[A-Z]", r"[0-9]", r"[^A-Za-z0-9]")
        )
        if (len(value) >= 12 and categories >= 3) or (
            len(value) >= 20 and categories >= 2
        ):
            return True
    return False


def find_pages(root: Path, pattern: re.Pattern[str]) -> set[int]:
    pages: set[int] = set()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        match = pattern.search(path.name)
        if match:
            pages.add(int(match.group(1)))
    return pages


def scn_multiset(paths: list[Path]) -> Counter[str]:
    values: Counter[str] = Counter()
    for path in paths:
        values.update(VERSION_SCN_RE.findall(read_text(path)))
    return values


def run(args: argparse.Namespace) -> int:
    root = args.root.resolve()
    if not root.is_dir():
        raise ApexExportError(f"APEX export root is missing: {root}")

    install = root / "install.sql"
    application = root / "application"
    readable = root / "readable"
    monolithic = root / f"f{args.app_id}.sql"
    required = (install, application, readable, monolithic)
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise ApexExportError("Required APEX artifacts are missing: " + ", ".join(missing))
    if not application.is_dir() or not readable.is_dir():
        raise ApexExportError("application/ and readable/ must be directories")
    if not re.search(
        r"(?mi)^\s*@@?application/create_application\.sql\s*$",
        read_text(install),
    ):
        raise ApexExportError("install.sql does not include application/create_application.sql")

    split_app = application / "create_application.sql"
    if not split_app.is_file():
        raise ApexExportError(f"Split create_application.sql is missing: {split_app}")
    app_pattern = re.compile(APP_ID_RE_TEMPLATE.format(app_id=args.app_id), re.IGNORECASE)
    monolithic_text = read_text(monolithic)
    split_app_text = read_text(split_app)
    if not app_pattern.search(monolithic_text) or not app_pattern.search(split_app_text):
        raise ApexExportError(f"Application identity {args.app_id} is not consistent")
    if args.require_editable_status:
        status_pattern = re.compile(
            r"p_flow_status\s*=>\s*'AVAILABLE_W_EDIT_LINK'", re.IGNORECASE
        )
        if not status_pattern.search(monolithic_text):
            raise ApexExportError("Monolithic export is not AVAILABLE_W_EDIT_LINK")

    split_pages = find_pages(application / "pages", PAGE_FILE_RE)
    readable_pages_root = readable / "application" / "pages"
    readable_pages = find_pages(readable_pages_root, YAML_PAGE_RE)
    if not split_pages:
        raise ApexExportError("No split APEX pages found")
    if split_pages != readable_pages:
        raise ApexExportError(
            "Split/readable page inventory differs: "
            f"split_only={sorted(split_pages - readable_pages)} "
            f"readable_only={sorted(readable_pages - split_pages)}"
        )

    split_sql = [
        path
        for path in root.rglob("*.sql")
        if path != monolithic and path != install and path.is_file()
    ]
    split_scns = scn_multiset(split_sql)
    monolithic_scns = Counter(VERSION_SCN_RE.findall(monolithic_text))
    if not args.allow_scn_drift and split_scns != monolithic_scns:
        raise ApexExportError(
            "Split and monolithic p_version_scn inventories differ: "
            f"split={sum(split_scns.values())} monolithic={sum(monolithic_scns.values())}"
        )

    readable_text = [
        path
        for path in readable.rglob("*")
        if path.is_file() and path.suffix.lower() in {".yaml", ".yml", ".json", ".xml", ".sql"}
    ]
    scanned = [monolithic, *split_sql, *readable_text]
    secret_hits = [
        str(path) for path in scanned if contains_potential_secret(read_text(path))
    ]
    if secret_hits:
        raise ApexExportError("Potential secret material found in: " + ", ".join(secret_hits))

    supporting = root / "application" / "shared_components" / "logic" / "supporting_objects"
    supporting_state = "PRESENT" if supporting.exists() else "ABSENT"
    if args.supporting_objects == "include" and supporting_state != "PRESENT":
        raise ApexExportError("Supporting Objects were required but not found in split source")
    if args.supporting_objects == "exclude" and supporting_state == "PRESENT":
        raise ApexExportError("Supporting Objects were excluded but found in split source")

    print(f"APEX_APPLICATION OK app_id={args.app_id}")
    print(f"APEX_PAGES OK split={len(split_pages)} readable={len(readable_pages)}")
    print(
        f"APEX_SCN_INVENTORY OK split={sum(split_scns.values())} monolithic={sum(monolithic_scns.values())}"
    )
    print(f"APEX_SUPPORTING_OBJECTS {supporting_state}")
    print("APEX_EXPORT OK atomic_formats=split,readable,monolithic")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--app-id", type=int, required=True)
    parser.add_argument(
        "--supporting-objects",
        choices=("include", "exclude", "project-defined"),
        default="project-defined",
    )
    parser.add_argument("--allow-scn-drift", action="store_true")
    parser.add_argument(
        "--require-editable-status",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run(args)
    except (ApexExportError, OSError, UnicodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
