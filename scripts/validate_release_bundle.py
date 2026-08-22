#!/usr/bin/env python3
"""Validate the canonical five-file Oracle database release bundle."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path
import re
import sys
from typing import Optional


GROUPS = (
    ("01", "package_specs", "PACKAGE"),
    ("02", "views", "VIEW"),
    ("03", "package_bodies", "PACKAGE BODY"),
    ("04", "triggers", "TRIGGER"),
    ("05", "compile_objects", "COMPILE"),
)
CREATE_PATTERNS = {
    "PACKAGE": re.compile(
        r"\bcreate\s+or\s+replace(?:\s+(?:editionable|noneditionable))?\s+package\s+(?!body\b)(?:\"([^\"]+)\"|([A-Za-z0-9_$#]+))",
        re.IGNORECASE,
    ),
    "VIEW": re.compile(
        r"\bcreate\s+or\s+replace(?:\s+force)?(?:\s+(?:editionable|noneditionable))?\s+view\s+(?:\"([^\"]+)\"|([A-Za-z0-9_$#]+))",
        re.IGNORECASE,
    ),
    "PACKAGE BODY": re.compile(
        r"\bcreate\s+or\s+replace(?:\s+(?:editionable|noneditionable))?\s+package\s+body\s+(?:\"([^\"]+)\"|([A-Za-z0-9_$#]+))",
        re.IGNORECASE,
    ),
    "TRIGGER": re.compile(
        r"\bcreate\s+or\s+replace(?:\s+(?:editionable|noneditionable))?\s+trigger\s+(?:\"([^\"]+)\"|([A-Za-z0-9_$#]+))",
        re.IGNORECASE,
    ),
}
ANY_OBJECT_CREATE = re.compile(
    r"\bcreate\s+or\s+replace(?:\s+force)?(?:\s+(?:editionable|noneditionable))?\s+"
    r"(package\s+body|type\s+body|materialized\s+view|package|procedure|function|view|trigger|type|synonym)\b",
    re.IGNORECASE,
)
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


class BundleError(RuntimeError):
    pass


def expected_names(snapshot_id: int, scope: str) -> list[str]:
    return [
        f"snapshot_{snapshot_id}_{scope}_{order}_{group}.sql"
        for order, group, _object_type in GROUPS
    ]


def header_value(content: str, key: str) -> Optional[str]:
    match = re.search(
        rf"(?mi)^\s*(?:--|/\*)?\s*{re.escape(key)}\s*:\s*([^\r\n*]+)",
        content,
    )
    return match.group(1).strip() if match else None


def object_names(content: str, object_type: str) -> list[str]:
    pattern = CREATE_PATTERNS[object_type]
    return [(quoted or plain).upper() for quoted, plain in pattern.findall(content)]


def strip_comments_and_literals(sql: str) -> str:
    without_block_comments = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    without_line_comments = re.sub(r"--[^\r\n]*", " ", without_block_comments)
    return re.sub(r"'(?:''|[^'])*'", "''", without_line_comments)


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


def validate_file(
    path: Path,
    snapshot_id: int,
    scope: str,
    base_snapshot_id: Optional[int],
    object_type: str,
    expected_count: Optional[int],
    compile_routine: Optional[str],
) -> int:
    content = path.read_text(encoding="utf-8", errors="strict")
    searchable = strip_comments_and_literals(content)
    if not content.strip() or "\x00" in content:
        raise BundleError(f"Empty or invalid release file: {path.name}")
    if re.search(r"(?mi)^\s*--\s*(?:ERROR|ERRO)\b", content):
        raise BundleError(f"Extraction error marker found in {path.name}")
    if contains_potential_secret(content):
        raise BundleError(f"Potential secret material found in {path.name}")
    if header_value(content, "SNAPSHOT_ID") != str(snapshot_id):
        raise BundleError(f"SNAPSHOT_ID header mismatch in {path.name}")
    if (header_value(content, "SCOPE") or "").lower() != scope:
        raise BundleError(f"SCOPE header mismatch in {path.name}")
    if scope == "partial":
        if header_value(content, "BASE_SNAPSHOT_ID") != str(base_snapshot_id):
            raise BundleError(f"BASE_SNAPSHOT_ID header mismatch in {path.name}")
    elif header_value(content, "BASE_SNAPSHOT_ID") not in (None, "NONE", "NULL", "-"):
        raise BundleError(f"Full release must not claim a base snapshot in {path.name}")

    claimed_group = (header_value(content, "OBJECT_GROUP") or "").upper()
    if claimed_group != object_type:
        raise BundleError(f"OBJECT_GROUP header mismatch in {path.name}: {claimed_group!r}")

    if object_type == "COMPILE":
        if ANY_OBJECT_CREATE.search(searchable):
            raise BundleError(f"Compile file contains exported object source: {path.name}")
        if compile_routine and not re.search(
            rf"\b{re.escape(compile_routine)}\s*;", content, re.IGNORECASE
        ):
            raise BundleError(f"Compile routine {compile_routine} not found in {path.name}")
        count = 1 if compile_routine else 0
        if expected_count is not None and count != expected_count:
            raise BundleError(
                f"Object count mismatch in {path.name}: expected={expected_count} actual={count}"
            )
        return count

    names = object_names(searchable, object_type)
    foreign_creates = []
    for match in ANY_OBJECT_CREATE.finditer(searchable):
        detected = re.sub(r"\s+", " ", match.group(1).upper())
        if detected != object_type:
            foreign_creates.append(detected)
    if foreign_creates:
        raise BundleError(
            f"Wrong object type in {path.name}: {', '.join(sorted(set(foreign_creates)))}"
        )
    if names != sorted(names):
        raise BundleError(f"Objects are not deterministically ordered in {path.name}")
    duplicates = [name for name, count in Counter(names).items() if count > 1]
    if duplicates:
        raise BundleError(f"Duplicate objects in {path.name}: {', '.join(sorted(duplicates))}")
    empty_marker = "NO CHANGES" if scope == "partial" else "NO OBJECTS"
    if not names and not re.search(
        rf"(?mi)^\s*--\s*{empty_marker}\s*$", content
    ):
        raise BundleError(
            f"No objects or required '{empty_marker}' marker in {path.name}"
        )
    if expected_count is not None and len(names) != expected_count:
        raise BundleError(
            f"Object count mismatch in {path.name}: expected={expected_count} actual={len(names)}"
        )
    return len(names)


def parse_expected_counts(values: list[str]) -> dict[str, int]:
    result: dict[str, int] = {}
    allowed = {object_type for _order, _group, object_type in GROUPS}
    for value in values:
        key, separator, raw_count = value.partition("=")
        key = key.strip().upper().replace("_", " ")
        if not separator or key not in allowed:
            raise BundleError(f"Invalid --expected-count value: {value}")
        try:
            count = int(raw_count)
        except ValueError as exc:
            raise BundleError(f"Invalid --expected-count value: {value}") from exc
        if count < 0:
            raise BundleError(f"Expected count cannot be negative: {value}")
        result[key] = count
    return result


def run(args: argparse.Namespace) -> int:
    directory = args.directory.resolve()
    if not directory.is_dir():
        raise BundleError(f"Release directory is missing: {directory}")
    if args.scope == "partial" and args.base_snapshot_id is None:
        raise BundleError("Partial release validation requires --base-snapshot-id")
    if args.scope == "full" and args.base_snapshot_id is not None:
        raise BundleError("Full release validation does not accept --base-snapshot-id")
    if args.compile_routine and not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_$#]*(?:\.[A-Za-z][A-Za-z0-9_$#]*)?",
        args.compile_routine,
    ):
        raise BundleError("--compile-routine must be one unquoted routine or package.routine name")

    expected = expected_names(args.snapshot_id, args.scope)
    actual = sorted(path.name for path in directory.iterdir() if path.is_file())
    if actual != sorted(expected):
        missing = sorted(set(expected) - set(actual))
        extra = sorted(set(actual) - set(expected))
        raise BundleError(
            f"Release must contain exactly five scoped SQL files; missing={missing} extra={extra}"
        )

    expected_counts = parse_expected_counts(args.expected_count)
    counts: dict[str, int] = {}
    for (order, group, object_type), filename in zip(GROUPS, expected):
        counts[object_type] = validate_file(
            directory / filename,
            args.snapshot_id,
            args.scope,
            args.base_snapshot_id,
            object_type,
            expected_counts.get(object_type),
            args.compile_routine,
        )
        print(f"FILE OK {filename} objects={counts[object_type]}")
    print(
        f"RELEASE_BUNDLE OK scope={args.scope.upper()} snapshot={args.snapshot_id} files=5"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--snapshot-id", type=int, required=True)
    parser.add_argument("--scope", choices=("full", "partial"), required=True)
    parser.add_argument("--base-snapshot-id", type=int)
    parser.add_argument(
        "--expected-count",
        action="append",
        default=[],
        metavar="GROUP=COUNT",
    )
    parser.add_argument("--compile-routine")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return run(args)
    except (BundleError, OSError, UnicodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
