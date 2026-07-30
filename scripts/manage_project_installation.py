#!/usr/bin/env python3
"""Install and update Oracle APEX AI Skills inside a consuming repository."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import Optional, Union
from urllib.parse import urlsplit, urlunsplit
import uuid


KIT_NAME = "oracle-apex-ai-skills"
MANIFEST_SCHEMA_VERSION = 1
CORE_SKILLS = (
    "oracle-apex-ai-skills",
    "oracle-apex-dev",
    "oracle-apex-export",
    "oracle-apex-object-lock",
)
MANIFEST_PATH = Path(".oracle-apex-ai/installation-manifest.json")
UPSTREAM_LOCK_PATH = Path(".oracle-apex-ai/upstream-lock.json")
COMPATIBILITY_PATH = Path(".oracle-apex-ai/compatibility.json")
PROJECT_MANAGER_PATH = Path("Util/scripts/manage_oracle_apex_ai_skills.py")
IGNORED_NAMES = {".DS_Store", "__pycache__"}


class InstallationError(RuntimeError):
    """Expected installation or validation failure."""


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise InstallationError(f"Required file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise InstallationError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(value, dict):
        raise InstallationError(f"Expected a JSON object in {path}")
    return value


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def relative_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            raise InstallationError(f"Source contains a symbolic link: {path}")
        if not path.is_file():
            continue
        if any(part in IGNORED_NAMES for part in path.parts):
            continue
        files.append(path.relative_to(root))
    return sorted(files, key=lambda item: item.as_posix())


def validate_source(source_root: Path) -> None:
    missing: list[str] = []
    for skill in CORE_SKILLS:
        skill_root = source_root / "skills" / skill
        for required in ("SKILL.md", "agents/openai.yaml"):
            if not (skill_root / required).is_file():
                missing.append(f"skills/{skill}/{required}")

    for required_path in (
        Path("scripts/manage_project_installation.py"),
        Path("templates/compatibility.json"),
        Path("templates/project-profile.md"),
        Path("templates/app-patterns.md"),
    ):
        absolute = source_root / required_path
        if absolute.is_symlink():
            raise InstallationError(f"Source contains a symbolic link: {absolute}")
        if not absolute.is_file():
            missing.append(required_path.as_posix())

    if missing:
        raise InstallationError(
            "Source is not a complete Oracle APEX AI Skills kit: "
            + ", ".join(missing)
        )

    compatibility = read_json(source_root / "templates/compatibility.json")
    if compatibility.get("kit") != KIT_NAME:
        raise InstallationError("Source compatibility record has an unexpected kit name")
    if compatibility.get("schema_version") != 1:
        raise InstallationError("Unsupported source compatibility schema")


def source_file_map(source_root: Path) -> dict[str, Path]:
    validate_source(source_root)
    mapping: dict[str, Path] = {}

    for skill in CORE_SKILLS:
        skill_root = source_root / "skills" / skill
        for relative in relative_files(skill_root):
            target = Path(".agents/skills") / skill / relative
            mapping[target.as_posix()] = skill_root / relative

    mapping[PROJECT_MANAGER_PATH.as_posix()] = (
        source_root / "scripts/manage_project_installation.py"
    )
    mapping[COMPATIBILITY_PATH.as_posix()] = (
        source_root / "templates/compatibility.json"
    )
    return dict(sorted(mapping.items()))


def run_git(source_root: Path, *args: str) -> Optional[str]:
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_root), *args],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    value = completed.stdout.strip()
    return value or None


def clean_repository_identifier(value: str) -> str:
    if "://" not in value:
        return value
    try:
        parts = urlsplit(value)
        hostname = parts.hostname or ""
        if ":" in hostname and not hostname.startswith("["):
            hostname = f"[{hostname}]"
        netloc = hostname
        if parts.port:
            netloc = f"{netloc}:{parts.port}"
    except ValueError as exc:
        raise InstallationError("Invalid source repository URL") from exc
    return urlunsplit((parts.scheme, netloc, parts.path, "", ""))


def resolve_source_metadata(args: argparse.Namespace, source_root: Path) -> dict:
    git_top_level = run_git(source_root, "rev-parse", "--show-toplevel")
    is_git_root = (
        git_top_level is not None
        and Path(git_top_level).resolve() == source_root.resolve()
    )
    git_commit = run_git(source_root, "rev-parse", "HEAD") if is_git_root else None
    if is_git_root:
        try:
            status = subprocess.run(
                [
                    "git",
                    "-C",
                    str(source_root),
                    "status",
                    "--porcelain",
                    "--untracked-files=all",
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except (FileNotFoundError, subprocess.CalledProcessError) as exc:
            raise InstallationError(
                "Cannot verify that the source Git checkout is clean"
            ) from exc
        dirty = status.stdout.strip()
        if dirty:
            raise InstallationError(
                "Source Git checkout has uncommitted or untracked files; "
                "use a clean reviewed tag/commit."
            )
    commit = args.source_commit or git_commit
    if not commit:
        raise InstallationError(
            "Cannot resolve the source commit. Use a Git clone or pass --source-commit."
        )
    if not re.fullmatch(r"[0-9a-fA-F]{7,64}", commit):
        raise InstallationError(f"Invalid resolved source commit: {commit}")

    if git_commit and args.source_commit and args.source_commit.lower() != git_commit.lower():
        raise InstallationError(
            "--source-commit does not match the checked-out Git source"
        )

    if git_commit and args.source_ref != "HEAD":
        ref_commit = run_git(
            source_root, "rev-parse", f"{args.source_ref}^{{commit}}"
        )
        if not ref_commit:
            raise InstallationError(
                f"Requested source ref is not available in the clone: {args.source_ref}"
            )
        if ref_commit.lower() != git_commit.lower():
            raise InstallationError(
                "The checked-out source does not match --source-ref: "
                f"HEAD={git_commit}, {args.source_ref}={ref_commit}"
            )

    repository = (
        args.source_repository
        or (
            run_git(source_root, "config", "--get", "remote.origin.url")
            if is_git_root
            else None
        )
        or "local-source"
    )
    repository = clean_repository_identifier(repository)
    return {
        "repository": repository,
        "requested_ref": args.source_ref,
        "resolved_commit": commit,
    }


def load_manifest(project_root: Path) -> Optional[dict]:
    path = project_root / MANIFEST_PATH
    if not path.exists():
        return None
    manifest = read_json(path)
    if manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION:
        raise InstallationError(
            f"Unsupported installation manifest schema in {MANIFEST_PATH}"
        )
    if manifest.get("kit") != KIT_NAME:
        raise InstallationError(f"Unexpected kit name in {MANIFEST_PATH}")
    managed_files = manifest.get("managed_files")
    if not isinstance(managed_files, dict):
        raise InstallationError(f"Invalid managed_files in {MANIFEST_PATH}")
    for relative, digest in managed_files.items():
        if not isinstance(relative, str):
            raise InstallationError(f"Invalid managed path in {MANIFEST_PATH}")
        if not is_allowed_managed_file(relative):
            raise InstallationError(
                f"Managed path is outside the kit-owned roots: {relative}"
            )
        safe_project_path(project_root, relative)
        if not isinstance(digest, str) or len(digest) != 64:
            raise InstallationError(
                f"Invalid checksum for managed path in {MANIFEST_PATH}: {relative}"
            )
    required_managed = {
        PROJECT_MANAGER_PATH.as_posix(),
        COMPATIBILITY_PATH.as_posix(),
    }
    for skill in CORE_SKILLS:
        required_managed.add(f".agents/skills/{skill}/SKILL.md")
        required_managed.add(f".agents/skills/{skill}/agents/openai.yaml")
    missing_required = sorted(required_managed - set(managed_files))
    if missing_required:
        raise InstallationError(
            "Installation manifest omits required managed files: "
            + ", ".join(missing_required)
        )

    metadata_files = manifest.get("metadata_files", {})
    if not isinstance(metadata_files, dict):
        raise InstallationError(f"Invalid metadata_files in {MANIFEST_PATH}")
    if set(metadata_files) != {UPSTREAM_LOCK_PATH.as_posix()}:
        raise InstallationError(
            f"{MANIFEST_PATH} must record exactly {UPSTREAM_LOCK_PATH}"
        )
    for relative, digest in metadata_files.items():
        if not isinstance(relative, str):
            raise InstallationError(f"Invalid metadata path in {MANIFEST_PATH}")
        if relative != UPSTREAM_LOCK_PATH.as_posix():
            raise InstallationError(
                f"Unexpected metadata path in {MANIFEST_PATH}: {relative}"
            )
        safe_project_path(project_root, relative)
        if not isinstance(digest, str) or len(digest) != 64:
            raise InstallationError(
                f"Invalid metadata checksum in {MANIFEST_PATH}: {relative}"
            )
    return manifest


def is_allowed_managed_file(relative: str) -> bool:
    path = Path(relative)
    if path in (PROJECT_MANAGER_PATH, COMPATIBILITY_PATH):
        return True
    parts = path.parts
    return (
        len(parts) >= 4
        and parts[0:2] == (".agents", "skills")
        and parts[2] in CORE_SKILLS
    )


def safe_project_path(project_root: Path, relative: Union[str, Path]) -> Path:
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise InstallationError(f"Unsafe project-relative path: {relative}")
    target = project_root / relative_path
    current = project_root
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            raise InstallationError(
                f"Refusing symbolic links in managed project path: {relative}"
            )
    try:
        resolved = target.resolve(strict=False)
    except OSError as exc:
        raise InstallationError(f"Cannot resolve project path: {relative}") from exc
    if not resolved.is_relative_to(project_root):
        raise InstallationError(
            f"Project path escapes through a symbolic link: {relative}"
        )
    return target


def validate_project_root(project_root: Path) -> None:
    if not project_root.is_dir():
        raise InstallationError(f"Project root is not a directory: {project_root}")
    if project_root == Path(project_root.anchor):
        raise InstallationError("Refusing to use the filesystem root as a project")
    if project_root == Path.home().resolve():
        raise InstallationError("Refusing to use the user home directory as a project")


def managed_roots() -> tuple[Path, ...]:
    return tuple(
        [Path(".agents/skills") / skill for skill in CORE_SKILLS]
        + [PROJECT_MANAGER_PATH, COMPATIBILITY_PATH]
    )


def find_unrecorded_managed_files(
    project_root: Path, recorded: set[str]
) -> list[str]:
    extras: list[str] = []
    for root in managed_roots():
        absolute = project_root / root
        if absolute.is_symlink():
            extras.append(root.as_posix())
            continue
        if absolute.is_file():
            candidates = [absolute]
        elif absolute.is_dir():
            candidates = [
                path
                for path in absolute.rglob("*")
                if path.is_file()
                and not any(part in IGNORED_NAMES for part in path.parts)
            ]
        else:
            candidates = []

        for path in candidates:
            relative = path.relative_to(project_root).as_posix()
            if relative not in recorded:
                extras.append(relative)
    return sorted(set(extras))


def inspect_installation(project_root: Path, manifest: Optional[dict]) -> dict:
    if manifest is None:
        return {
            "status": "NOT_INSTALLED",
            "missing": [],
            "modified": [],
            "unrecorded": [],
            "metadata_issues": [],
        }

    recorded = manifest["managed_files"]
    missing: list[str] = []
    modified: list[str] = []

    for relative, expected_hash in sorted(recorded.items()):
        path = safe_project_path(project_root, relative)
        if not path.is_file():
            missing.append(relative)
        elif sha256_file(path) != expected_hash:
            modified.append(relative)

    unrecorded = find_unrecorded_managed_files(project_root, set(recorded))
    metadata_issues: list[str] = []
    metadata_files = manifest.get("metadata_files", {})
    if not isinstance(metadata_files, dict):
        metadata_issues.append("manifest metadata_files is invalid")
    else:
        for relative, expected_hash in sorted(metadata_files.items()):
            if not isinstance(relative, str):
                metadata_issues.append("invalid metadata path")
                continue
            path = safe_project_path(project_root, relative)
            if not path.is_file():
                metadata_issues.append(f"missing {relative}")
            elif sha256_file(path) != expected_hash:
                metadata_issues.append(f"modified {relative}")

    if missing:
        status = "INCOMPLETE"
    elif modified or unrecorded or metadata_issues:
        status = "MODIFIED"
    else:
        status = "HEALTHY"

    return {
        "status": status,
        "missing": missing,
        "modified": modified,
        "unrecorded": unrecorded,
        "metadata_issues": metadata_issues,
    }


def print_inspection(inspection: dict) -> None:
    print(f"STATUS {inspection['status']}")
    for category in ("missing", "modified", "unrecorded", "metadata_issues"):
        for value in inspection[category]:
            print(f"{category.upper()} {value}")


def source_hashes(mapping: dict[str, Path]) -> dict[str, str]:
    return {relative: sha256_file(path) for relative, path in mapping.items()}


def build_plan(
    command: str,
    project_root: Path,
    manifest: Optional[dict],
    mapping: dict[str, Path],
) -> list[tuple[str, str]]:
    new_hashes = source_hashes(mapping)
    plan: list[tuple[str, str]] = []

    if command == "install":
        if manifest is not None:
            raise InstallationError(
                "The kit is already installed. Use check or update."
            )
        conflicts = [
            relative
            for relative in new_hashes
            if safe_project_path(project_root, relative).exists()
        ]
        conflicts.extend(
            root.as_posix()
            for root in managed_roots()
            if safe_project_path(project_root, root).exists()
        )
        conflicts.extend(
            path.as_posix()
            for path in (UPSTREAM_LOCK_PATH, MANIFEST_PATH)
            if safe_project_path(project_root, path).exists()
        )
        conflicts = sorted(set(conflicts))
        if conflicts:
            raise InstallationError(
                "Install would overwrite existing managed paths: "
                + ", ".join(conflicts)
            )
        plan.extend(("CREATE", relative) for relative in sorted(new_hashes))
        return plan

    if manifest is None:
        raise InstallationError("The kit is not installed. Use install first.")

    inspection = inspect_installation(project_root, manifest)
    if inspection["status"] != "HEALTHY":
        print_inspection(inspection)
        raise InstallationError(
            "Refusing to update a modified or incomplete managed installation."
        )

    old_hashes = manifest["managed_files"]
    for relative in sorted(set(old_hashes) | set(new_hashes)):
        if relative not in old_hashes:
            plan.append(("CREATE", relative))
        elif relative not in new_hashes:
            plan.append(("DELETE", relative))
        elif old_hashes[relative] != new_hashes[relative]:
            plan.append(("UPDATE", relative))
        else:
            plan.append(("PRESERVE", relative))
    return plan


def scaffold_plan(
    project_root: Path, source_root: Path
) -> list[tuple[str, Path, Optional[Path]]]:
    candidates = (
        (
            "CREATE_PROJECT_FILE",
            Path(".oracle-apex-ai/project-profile.md"),
            source_root / "templates/project-profile.md",
        ),
        (
            "CREATE_PROJECT_FILE",
            Path(".oracle-apex-ai/app-patterns.md"),
            source_root / "templates/app-patterns.md",
        ),
        (
            "CREATE_PROJECT_FILE",
            Path(".oracle-apex-ai/page-patterns/.gitkeep"),
            None,
        ),
        (
            "CREATE_PROJECT_FILE",
            Path("db/migrations/pending/.gitkeep"),
            None,
        ),
        (
            "CREATE_PROJECT_FILE",
            Path("db/migrations/applied/.gitkeep"),
            None,
        ),
    )
    missing = []
    for candidate in candidates:
        direct_target = project_root / candidate[1]
        if direct_target.exists() or direct_target.is_symlink():
            continue
        safe_project_path(project_root, candidate[1])
        missing.append(candidate)
    return missing


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(f".{path.name}.tmp-{uuid.uuid4().hex}")
    try:
        temp.write_bytes(content)
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


def remove_empty_parents(path: Path, stop: Path) -> None:
    current = path.parent
    while current != stop and current.is_relative_to(stop):
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def apply_plan(
    project_root: Path,
    source_root: Path,
    mapping: dict[str, Path],
    plan: list[tuple[str, str]],
    scaffold: list[tuple[str, Path, Optional[Path]]],
    source_metadata: dict,
    previous_manifest: Optional[dict],
) -> None:
    timestamp = utc_now()
    new_hashes = source_hashes(mapping)
    backup_parent = safe_project_path(project_root, ".oracle-apex-ai")
    backup_parent_existed = backup_parent.exists()
    backup_parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix=".installation-backup-", dir=backup_parent
    ) as backup_name:
        backup_root = Path(backup_name)
        touched: list[tuple[Path, Optional[Path]]] = []
        created_scaffold: list[Path] = []

        def backup(path: Path) -> Optional[Path]:
            if not path.exists():
                touched.append((path, None))
                return None
            destination = backup_root / path.relative_to(project_root)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, destination)
            touched.append((path, destination))
            return destination

        try:
            for action, relative in plan:
                target = safe_project_path(project_root, relative)
                if action in {"CREATE", "UPDATE"}:
                    backup(target)
                    atomic_write(target, mapping[relative].read_bytes())
                    if relative == PROJECT_MANAGER_PATH.as_posix():
                        target.chmod(0o755)
                elif action == "DELETE":
                    backup(target)
                    target.unlink()
                    remove_empty_parents(target, project_root)

            for _, relative, source in scaffold:
                target = safe_project_path(project_root, relative)
                if target.exists():
                    continue
                content = source.read_bytes() if source else b""
                atomic_write(target, content)
                created_scaffold.append(target)

            upstream_lock = {
                "schema_version": 1,
                "kit": KIT_NAME,
                "installed_at": timestamp,
                **source_metadata,
            }
            upstream_bytes = json_bytes(upstream_lock)
            upstream_target = safe_project_path(project_root, UPSTREAM_LOCK_PATH)
            backup(upstream_target)
            atomic_write(upstream_target, upstream_bytes)

            compatibility = read_json(source_root / "templates/compatibility.json")
            manifest = {
                "schema_version": MANIFEST_SCHEMA_VERSION,
                "kit": KIT_NAME,
                "installed_at": timestamp,
                "source": source_metadata,
                "compatibility": {
                    "apex_target": compatibility["apex"]["target"],
                    "object_lock_runtime_required": compatibility["database"][
                        "object_lock_runtime_required"
                    ],
                },
                "managed_files": new_hashes,
                "metadata_files": {
                    UPSTREAM_LOCK_PATH.as_posix(): sha256_bytes(upstream_bytes)
                },
                "project_owned_paths": [
                    ".oracle-apex-ai/project-profile.md",
                    ".oracle-apex-ai/app-patterns.md",
                    ".oracle-apex-ai/page-patterns/",
                    "db/migrations/pending/",
                    "db/migrations/applied/",
                ],
                "previous_source": (
                    previous_manifest.get("source")
                    if previous_manifest is not None
                    else None
                ),
            }
            manifest_target = safe_project_path(project_root, MANIFEST_PATH)
            backup(manifest_target)
            atomic_write(manifest_target, json_bytes(manifest))

            inspection = inspect_installation(project_root, manifest)
            if inspection["status"] != "HEALTHY":
                raise InstallationError(
                    "Post-write installation integrity check failed: "
                    + inspection["status"]
                )
        except Exception:
            for path in reversed(created_scaffold):
                if path.exists():
                    path.unlink()
                    remove_empty_parents(path, project_root)
            for path, backup_path in reversed(touched):
                if backup_path is None:
                    if path.exists():
                        path.unlink()
                        remove_empty_parents(path, project_root)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(backup_path, path)
            if not backup_parent_existed:
                try:
                    backup_parent.rmdir()
                except OSError:
                    pass
            raise


def command_status(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)
    manifest = load_manifest(project_root)
    inspection = inspect_installation(project_root, manifest)
    print_inspection(inspection)
    if manifest:
        source = manifest.get("source", {})
        print(f"SOURCE_REPOSITORY {source.get('repository', 'UNKNOWN')}")
        print(f"SOURCE_REF {source.get('requested_ref', 'UNKNOWN')}")
        print(f"SOURCE_COMMIT {source.get('resolved_commit', 'UNKNOWN')}")
    return 0 if inspection["status"] == "HEALTHY" else 1


def load_source(args: argparse.Namespace) -> tuple[Path, dict[str, Path], dict]:
    source_root = args.source_root.resolve()
    mapping = source_file_map(source_root)
    metadata = resolve_source_metadata(args, source_root)
    return source_root, mapping, metadata


def command_check(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)
    manifest = load_manifest(project_root)
    if manifest is None:
        print("STATUS NOT_INSTALLED")
        return 1

    inspection = inspect_installation(project_root, manifest)
    print_inspection(inspection)
    if inspection["status"] != "HEALTHY":
        return 1

    _, mapping, metadata = load_source(args)
    plan = build_plan("update", project_root, manifest, mapping)
    changes = [item for item in plan if item[0] != "PRESERVE"]
    if changes:
        print("UPDATE_AVAILABLE YES")
        for action, relative in changes:
            print(f"ACTION {action} {relative}")
    else:
        print("UPDATE_AVAILABLE NO")
    print(f"CANDIDATE_REF {metadata['requested_ref']}")
    print(f"CANDIDATE_COMMIT {metadata['resolved_commit']}")
    return 0


def command_install_or_update(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)

    source_root, mapping, metadata = load_source(args)
    manifest = load_manifest(project_root)
    plan = build_plan(args.command, project_root, manifest, mapping)
    scaffold = (
        []
        if args.command == "update" or args.no_project_scaffold
        else scaffold_plan(project_root, source_root)
    )

    for action, relative in plan:
        print(f"ACTION {action} {relative}")
    for action, relative, _ in scaffold:
        print(f"ACTION {action} {relative.as_posix()}")
    print(f"ACTION WRITE_METADATA {UPSTREAM_LOCK_PATH.as_posix()}")
    print(f"ACTION WRITE_METADATA {MANIFEST_PATH.as_posix()}")

    if args.dry_run:
        print("RESULT DRY_RUN_NO_FILES_CHANGED")
        return 0

    apply_plan(
        project_root,
        source_root,
        mapping,
        plan,
        scaffold,
        metadata,
        manifest,
    )
    inspection = inspect_installation(project_root, load_manifest(project_root))
    print_inspection(inspection)
    if inspection["status"] != "HEALTHY":
        raise InstallationError("Post-installation verification did not pass")
    print("RESULT INSTALLATION_UPDATED" if args.command == "update" else "RESULT INSTALLATION_CREATED")
    return 0


def add_source_arguments(parser: argparse.ArgumentParser) -> None:
    default_source = Path(__file__).resolve().parent.parent
    parser.add_argument(
        "--source-root",
        type=Path,
        default=default_source,
        help="Local clone or extracted source of oracle-apex-ai-skills.",
    )
    parser.add_argument(
        "--source-ref",
        default="HEAD",
        help="Requested immutable tag, commit, or branch recorded in the manifest.",
    )
    parser.add_argument(
        "--source-commit",
        help="Resolved commit for an archive without Git metadata.",
    )
    parser.add_argument(
        "--source-repository",
        help="Source repository URL when it cannot be read from Git metadata.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Install, inspect, and update repository-managed Oracle APEX AI Skills "
            "without connecting to Oracle or changing Git state."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    status = subparsers.add_parser("status", help="Verify the installed checksums.")
    status.add_argument("--project-root", type=Path, default=Path.cwd())
    status.set_defaults(handler=command_status)

    check = subparsers.add_parser(
        "check", help="Compare an installed project with a local upstream source."
    )
    check.add_argument("--project-root", type=Path, default=Path.cwd())
    add_source_arguments(check)
    check.set_defaults(handler=command_check)

    for command in ("install", "update"):
        operation = subparsers.add_parser(
            command,
            help=f"{command.capitalize()} managed files in a consuming project.",
        )
        operation.add_argument("--project-root", type=Path, default=Path.cwd())
        add_source_arguments(operation)
        operation.add_argument(
            "--dry-run",
            action="store_true",
            help="Print the exact plan without changing files.",
        )
        operation.add_argument(
            "--no-project-scaffold",
            action="store_true",
            help="Do not initialize missing project-owned profile or migration paths.",
        )
        operation.set_defaults(handler=command_install_or_update)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.handler(args)
    except InstallationError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    except OSError as exc:
        print(f"ERROR Filesystem operation failed: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
