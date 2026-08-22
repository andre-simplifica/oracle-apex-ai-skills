#!/usr/bin/env python3
"""Plan or apply configured repository export retention without connecting to Oracle."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
from typing import Optional


DEFAULT_CONFIG = Path(".oracle-apex-ai/export-policy.json")
CONFIRMATION = "PRUNE_OLD_RELEASES"
DATABASE_SQL_CONFIRMATION = "EMIT_DB_SNAPSHOT_PURGE"


class RetentionError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RetentionError(f"Export policy is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise RetentionError(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RetentionError(f"Expected a JSON object in {path}")
    return value


def safe_path(project_root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise RetentionError(f"Unsafe project-relative path: {relative}")
    target = (project_root / path).resolve(strict=False)
    if not target.is_relative_to(project_root):
        raise RetentionError(f"Path escapes project root: {relative}")
    return target


def load_policy(project_root: Path, config: Path) -> dict:
    path = config if config.is_absolute() else safe_path(project_root, str(config))
    policy = read_json(path)
    if policy.get("schema_version") != 1:
        raise RetentionError("Unsupported export-policy schema_version")
    release = policy.get("database_release")
    retention = policy.get("retention")
    if not isinstance(release, dict) or not isinstance(retention, dict):
        raise RetentionError("Export policy is missing database_release or retention")
    repository = retention.get("repository_releases")
    database = retention.get("database_snapshots")
    if not isinstance(repository, dict) or not isinstance(database, dict):
        raise RetentionError("Export retention policy is incomplete")
    if repository.get("mode") not in {"report", "prune"}:
        raise RetentionError("Repository retention mode must be 'report' or 'prune'")
    if not isinstance(repository.get("keep_latest"), int) or repository["keep_latest"] < 1:
        raise RetentionError("retention.repository_releases.keep_latest must be positive")
    for key in ("keep_months", "keep_scripts"):
        if not isinstance(database.get(key), int) or database[key] < 1:
            raise RetentionError(f"retention.database_snapshots.{key} must be positive")
    if not isinstance(database.get("enabled"), bool):
        raise RetentionError("retention.database_snapshots.enabled must be boolean")
    sql_name(database.get("package", ""))
    return policy


def release_plan(project_root: Path, policy: dict, force_review: bool) -> dict:
    release = policy["database_release"]
    retention = policy["retention"]
    repository = retention["repository_releases"]
    release_root = safe_path(project_root, release["output_directory"])
    try:
        directory_pattern = re.compile(repository["directory_name_pattern"])
    except re.error as exc:
        raise RetentionError(f"Invalid release directory pattern: {exc}") from exc
    keep_latest = repository["keep_latest"]
    review_every = retention["review_every_releases"]
    if not isinstance(keep_latest, int) or keep_latest < 1:
        raise RetentionError("retention.repository_releases.keep_latest must be positive")
    if not isinstance(review_every, int) or review_every < 1:
        raise RetentionError("retention.review_every_releases must be positive")

    releases = []
    if release_root.is_dir():
        releases = sorted(
            path
            for path in release_root.iterdir()
            if path.is_dir() and directory_pattern.fullmatch(path.name)
        )
    candidates = releases[:-keep_latest] if len(releases) > keep_latest else []
    due = bool(candidates) and (
        force_review or len(candidates) >= review_every
    )
    return {
        "root": release_root,
        "releases": releases,
        "candidates": candidates if due else [],
        "deferred_candidates": [] if due else candidates,
        "keep_latest": keep_latest,
        "review_every": review_every,
        "mode": repository["mode"],
        "due": due,
    }


def git_changes(project_root: Path, paths: list[Path]) -> list[str]:
    if not paths or not (project_root / ".git").exists():
        return []
    relative = [str(path.relative_to(project_root)) for path in paths]
    completed = subprocess.run(
        ["git", "-C", str(project_root), "status", "--porcelain", "--", *relative],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise RetentionError("Cannot verify Git status for retention candidates")
    return [line for line in completed.stdout.splitlines() if line.strip()]


def print_release_plan(plan: dict) -> None:
    print(f"RELEASE_ROOT {plan['root']}")
    print(f"RELEASE_COUNT {len(plan['releases'])}")
    print(f"KEEP_LATEST {plan['keep_latest']}")
    print(f"REVIEW_EVERY_RELEASES {plan['review_every']}")
    print(f"RETENTION_MODE {plan['mode'].upper()}")
    print(f"RETENTION_DUE {'YES' if plan['due'] else 'NO'}")
    for path in plan["candidates"]:
        print(f"CANDIDATE {path}")
    for path in plan["deferred_candidates"]:
        print(f"DEFERRED {path}")


def command_status(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)
    policy = load_policy(project_root, args.config)
    print_release_plan(release_plan(project_root, policy, args.force_review))
    database = policy["retention"]["database_snapshots"]
    print(f"DATABASE_RETENTION {'ENABLED' if database['enabled'] else 'DISABLED'}")
    print(f"DATABASE_KEEP_MONTHS {database['keep_months']}")
    print(f"DATABASE_KEEP_SCRIPTS {database['keep_scripts']}")
    return 0


def command_prune(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)
    policy = load_policy(project_root, args.config)
    plan = release_plan(project_root, policy, args.force_review)
    print_release_plan(plan)
    if not args.apply:
        print("RESULT DRY_RUN_NO_FILES_CHANGED")
        return 0
    if plan["mode"] != "prune":
        raise RetentionError("Repository retention mode must be 'prune' before applying deletion")
    if args.confirm != CONFIRMATION:
        raise RetentionError(f"Applying retention requires --confirm {CONFIRMATION}")
    if not plan["due"]:
        print("RESULT NO_RETENTION_DUE")
        return 0
    changes = git_changes(project_root, plan["candidates"])
    if changes:
        raise RetentionError(
            "Retention candidates contain uncommitted Git changes: " + " | ".join(changes)
        )
    for path in plan["candidates"]:
        if path.parent != plan["root"] or not path.is_dir() or path.is_symlink():
            raise RetentionError(f"Refusing unexpected retention target: {path}")
    for path in plan["candidates"]:
        shutil.rmtree(path)
        print(f"PRUNED {path}")
    print(f"RESULT PRUNED_RELEASES count={len(plan['candidates'])}")
    return 0


def sql_name(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_$#]*", value):
        raise RetentionError(f"Unsafe Oracle identifier: {value}")
    return value.upper()


def command_database_sql(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)
    policy = load_policy(project_root, args.config)
    database = policy["retention"]["database_snapshots"]
    if not database["enabled"] and not args.include_disabled:
        raise RetentionError(
            "Database snapshot retention is disabled; enable it in export-policy or use --include-disabled for review"
        )
    package = sql_name(database["package"])
    owner = sql_name(args.owner) if args.owner else None
    owner_expression = f"'{owner}'" if owner else "user"
    print("whenever sqlerror exit sql.sqlcode rollback")
    print("whenever oserror exit failure rollback")
    print("set serveroutput on")
    print("select user, sys_context('USERENV','SERVICE_NAME') service_name from dual;")
    print("select count(*) snapshot_count from ddl_snapshot where ds_owner = upper(" + owner_expression + ");")
    print("select count(*) script_count from ddl_snapshot_script where ds_owner = upper(" + owner_expression + ");")
    print("-- The mutation block is omitted by default.")
    if args.emit_apply_block:
        if args.confirm != DATABASE_SQL_CONFIRMATION:
            raise RetentionError(
                "Executable database purge SQL requires "
                f"--confirm {DATABASE_SQL_CONFIRMATION}"
            )
        print("-- Execute only after reviewing current preflight results in the confirmed target.")
        print("begin")
        print(
            f"    {package}.purge_old_scripts(p_owner => {owner_expression}, p_keep => {database['keep_scripts']});"
        )
        print(
            f"    {package}.purge_old_snapshots(p_owner => {owner_expression}, p_keep_months => {database['keep_months']});"
        )
        print("end;")
        print("/")
    else:
        print(
            "-- Re-run with --emit-apply-block --confirm "
            + DATABASE_SQL_CONFIRMATION
            + " only after separate authorization."
        )
    print("exit success")
    return 0


def validate_project_root(project_root: Path) -> None:
    if not project_root.is_dir() or project_root == Path(project_root.anchor):
        raise RetentionError(f"Unsafe or missing project root: {project_root}")
    try:
        user_home = Path.home().resolve()
    except RuntimeError:
        user_home = None
    if user_home is not None and project_root == user_home:
        raise RetentionError("Refusing to use the user home directory as a project")


def common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--project-root", type=Path, default=Path.cwd())
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    status = subparsers.add_parser("status", help="Show whether retention review is due.")
    common_arguments(status)
    status.add_argument("--force-review", action="store_true")
    status.set_defaults(handler=command_status)

    prune = subparsers.add_parser("prune", help="Preview or apply repository release retention.")
    common_arguments(prune)
    prune.add_argument("--force-review", action="store_true")
    prune.add_argument("--apply", action="store_true")
    prune.add_argument("--confirm")
    prune.set_defaults(handler=command_prune)

    database = subparsers.add_parser(
        "database-sql", help="Emit reviewed SQL for PK_DDL_SNAPSHOT retention; never connects."
    )
    common_arguments(database)
    database.add_argument("--owner")
    database.add_argument("--include-disabled", action="store_true")
    database.add_argument("--emit-apply-block", action="store_true")
    database.add_argument("--confirm")
    database.set_defaults(handler=command_database_sql)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return args.handler(args)
    except (RetentionError, OSError, UnicodeError) as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
