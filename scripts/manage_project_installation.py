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

from apex_version import ApexVersionError, evaluate_apex_version


KIT_NAME = "oracle-apex-ai-skills"
MANIFEST_SCHEMA_VERSION = 1
PROJECT_PROFILE_VERSION = 3
CORE_SKILLS = (
    "oracle-apex-ai-skills",
    "oracle-apex-dev",
    "oracle-apex-export",
    "oracle-apex-object-lock",
)
MANIFEST_PATH = Path(".oracle-apex-ai/installation-manifest.json")
UPSTREAM_LOCK_PATH = Path(".oracle-apex-ai/upstream-lock.json")
COMPATIBILITY_PATH = Path(".oracle-apex-ai/compatibility.json")
EXPORT_POLICY_PATH = Path(".oracle-apex-ai/export-policy.json")
PROJECT_MANAGER_PATH = Path("Util/scripts/manage_oracle_apex_ai_skills.py")
PENDING_CHECKER_PATH = Path("Util/scripts/check_oracle_apex_pending.py")
RETENTION_MANAGER_PATH = Path("Util/scripts/manage_oracle_apex_export_retention.py")
APEX_EXPORT_VALIDATOR_PATH = Path("Util/scripts/validate_oracle_apex_export.py")
APEX_VERSION_MODULE_PATH = Path("Util/scripts/apex_version.py")
APEX_COMPATIBILITY_VALIDATOR_PATH = Path(
    "Util/scripts/validate_oracle_apex_compatibility.py"
)
RELEASE_VALIDATOR_PATH = Path("Util/scripts/validate_oracle_apex_release_bundle.py")
PROJECT_TOOL_PATHS = (
    PROJECT_MANAGER_PATH,
    PENDING_CHECKER_PATH,
    RETENTION_MANAGER_PATH,
    APEX_EXPORT_VALIDATOR_PATH,
    APEX_VERSION_MODULE_PATH,
    APEX_COMPATIBILITY_VALIDATOR_PATH,
    RELEASE_VALIDATOR_PATH,
)
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
        Path("VERSION"),
        Path("scripts/manage_project_installation.py"),
        Path("scripts/check_pending_migrations.py"),
        Path("scripts/manage_export_retention.py"),
        Path("scripts/apex_version.py"),
        Path("scripts/validate_apex_compatibility.py"),
        Path("scripts/validate_apex_export.py"),
        Path("scripts/validate_release_bundle.py"),
        Path("templates/compatibility.json"),
        Path("templates/export-policy.json"),
        Path("templates/pending-ddl.sql"),
        Path("templates/pending-dml.sql"),
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
    kit_version = (source_root / "VERSION").read_text(encoding="utf-8").strip()
    if compatibility.get("kit") != KIT_NAME:
        raise InstallationError("Source compatibility record has an unexpected kit name")
    if compatibility.get("schema_version") != 2:
        raise InstallationError("Unsupported source compatibility schema")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", kit_version):
        raise InstallationError("Source VERSION is not semantic version X.Y.Z")
    if compatibility.get("kit_version") != kit_version:
        raise InstallationError("Source VERSION and compatibility kit_version differ")


def source_file_map(source_root: Path) -> dict[str, Path]:
    validate_source(source_root)
    mapping: dict[str, Path] = {}

    for skill in CORE_SKILLS:
        skill_root = source_root / "skills" / skill
        for relative in relative_files(skill_root):
            target = Path(".agents/skills") / skill / relative
            mapping[target.as_posix()] = skill_root / relative

    project_tools = {
        PROJECT_MANAGER_PATH: Path("scripts/manage_project_installation.py"),
        PENDING_CHECKER_PATH: Path("scripts/check_pending_migrations.py"),
        RETENTION_MANAGER_PATH: Path("scripts/manage_export_retention.py"),
        APEX_VERSION_MODULE_PATH: Path("scripts/apex_version.py"),
        APEX_COMPATIBILITY_VALIDATOR_PATH: Path(
            "scripts/validate_apex_compatibility.py"
        ),
        APEX_EXPORT_VALIDATOR_PATH: Path("scripts/validate_apex_export.py"),
        RELEASE_VALIDATOR_PATH: Path("scripts/validate_release_bundle.py"),
    }
    for target, source in project_tools.items():
        mapping[target.as_posix()] = source_root / source
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
    # Keep schema-v1 installations updatable. Version 1.0 manifests predate the
    # four export helpers, so requiring the current complete tool set here would
    # block the update that needs to add those files.
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
    if path in (*PROJECT_TOOL_PATHS, COMPATIBILITY_PATH):
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
        + [*PROJECT_TOOL_PATHS, COMPATIBILITY_PATH]
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
    pending_root = project_root / "db/migrations/pending"
    existing_pending_sql = (
        sorted(path for path in pending_root.rglob("*.sql") if path.is_file())
        if pending_root.is_dir()
        else []
    )
    existing_export_policy = (project_root / EXPORT_POLICY_PATH).exists()
    existing_project_profile = (
        project_root / ".oracle-apex-ai/project-profile.md"
    ).exists()
    preserve_existing_pending_contract = bool(
        existing_pending_sql or existing_export_policy or existing_project_profile
    )
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
            EXPORT_POLICY_PATH,
            source_root / "templates/export-policy.json",
        ),
        (
            "CREATE_PROJECT_FILE",
            Path(".oracle-apex-ai/page-patterns/.gitkeep"),
            None,
        ),
        (
            "CREATE_PROJECT_FILE",
            Path("db/migrations/pending/pending_ddl.sql"),
            source_root / "templates/pending-ddl.sql",
        ),
        (
            "CREATE_PROJECT_FILE",
            Path("db/migrations/pending/pending_dml.sql"),
            source_root / "templates/pending-dml.sql",
        ),
        (
            "CREATE_PROJECT_FILE",
            Path("db/migrations/applied/.gitkeep"),
            None,
        ),
    )
    missing = []
    for candidate in candidates:
        if preserve_existing_pending_contract and candidate[1] in {
            EXPORT_POLICY_PATH,
            Path("db/migrations/pending/pending_ddl.sql"),
            Path("db/migrations/pending/pending_dml.sql"),
        }:
            continue
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
                    if relative in {path.as_posix() for path in PROJECT_TOOL_PATHS}:
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

            compatibility = read_json(source_root / "templates/compatibility.json")
            upstream_lock = {
                "schema_version": 1,
                "kit": KIT_NAME,
                "kit_version": compatibility["kit_version"],
                "installed_at": timestamp,
                **source_metadata,
            }
            upstream_bytes = json_bytes(upstream_lock)
            upstream_target = safe_project_path(project_root, UPSTREAM_LOCK_PATH)
            backup(upstream_target)
            atomic_write(upstream_target, upstream_bytes)

            manifest = {
                "schema_version": MANIFEST_SCHEMA_VERSION,
                "kit": KIT_NAME,
                "installed_at": timestamp,
                "source": source_metadata,
                "compatibility": {
                    "kit_version": compatibility["kit_version"],
                    "apex_target": compatibility["apex"]["minimum_supported"],
                    "apex_minimum_supported": compatibility["apex"][
                        "minimum_supported"
                    ],
                    "dynamic_content_from": compatibility["apex"][
                        "feature_gates"
                    ]["dynamic_content_return_clob"],
                    "apex_26_1_features_from": compatibility["apex"][
                        "feature_gates"
                    ]["apex_26_1_public_apis"],
                    "apexlang_policy": compatibility["apex"]["apexlang_policy"],
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
                    ".oracle-apex-ai/export-policy.json",
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
        compatibility = manifest.get("compatibility", {})
        print(f"KIT_VERSION {compatibility.get('kit_version', 'UNKNOWN')}")
        print(
            "APEX_MINIMUM_SUPPORTED "
            + str(
                compatibility.get(
                    "apex_minimum_supported",
                    compatibility.get("apex_target", "UNKNOWN"),
                )
            )
        )
        print(
            "DYNAMIC_CONTENT_FROM "
            + str(compatibility.get("dynamic_content_from", "22.2"))
        )
        print(
            "APEX_26_1_FEATURES_FROM "
            + str(compatibility.get("apex_26_1_features_from", "26.1"))
        )
        print(
            "APEXLANG_POLICY "
            + str(compatibility.get("apexlang_policy", "UNKNOWN")).upper()
        )
        print(f"SOURCE_REPOSITORY {source.get('repository', 'UNKNOWN')}")
        print(f"SOURCE_REF {source.get('requested_ref', 'UNKNOWN')}")
        print(f"SOURCE_COMMIT {source.get('resolved_commit', 'UNKNOWN')}")
    return 0 if inspection["status"] == "HEALTHY" else 1


def doctor_export_policy(
    project_root: Path, policy: dict
) -> tuple[Path, Path, dict]:
    schema_version = policy.get("schema_version")
    if schema_version not in {1, 2}:
        raise InstallationError("Unsupported export policy schema")
    apex = policy.get("apex")
    release = policy.get("database_release")
    pending = policy.get("pending")
    retention = policy.get("retention")
    if not all(isinstance(value, dict) for value in (apex, release, pending, retention)):
        raise InstallationError("Export policy sections are incomplete")
    if apex.get("official_export_scope") != "complete-application":
        raise InstallationError("Official APEX export scope must be complete-application")
    if apex.get("require_split_sql") is not True:
        raise InstallationError("Official APEX exports must require split SQL")
    if apex.get("require_monolithic_sql") is not True:
        raise InstallationError("Official APEX exports must require monolithic SQL")
    if not isinstance(apex.get("require_editable_build_status"), bool):
        raise InstallationError("Editable APEX build-status policy is invalid")
    if apex.get("supporting_objects") not in {
        "include",
        "exclude",
        "project-defined",
    }:
        raise InstallationError("Supporting Objects policy is invalid")

    if schema_version == 1:
        if not isinstance(apex.get("require_readable_yaml"), bool):
            raise InstallationError("Readable YAML policy is invalid")
        apex_contract = {
            "schema_version": 1,
            "readable_yaml_mode": (
                "always" if apex["require_readable_yaml"] else "disabled"
            ),
            "apexlang_policy": "unspecified",
        }
    else:
        if apex.get("readable_yaml_mode") != "before-26.1":
            raise InstallationError(
                "Readable YAML must be limited to supported releases before 26.1"
            )
        if apex.get("apexlang_policy") != "disabled":
            raise InstallationError("APEXlang must be disabled by project policy")
        apex_contract = {
            "schema_version": 2,
            "readable_yaml_mode": "before-26.1",
            "apexlang_policy": "disabled",
        }
    if release.get("default_scope") not in {"full", "partial"}:
        raise InstallationError("Database release default scope is invalid")
    if release.get("five_file_groups") != [
        "package_specs",
        "views",
        "package_bodies",
        "triggers",
        "compile_objects",
    ]:
        raise InstallationError("Database release five-file groups are invalid")
    output_directory = release.get("output_directory")
    if not isinstance(output_directory, str) or not output_directory.strip():
        raise InstallationError("Database release output directory is invalid")
    safe_project_path(project_root, output_directory)
    compile_routine = release.get("compile_routine")
    if compile_routine is not None and not (
        isinstance(compile_routine, str)
        and re.fullmatch(
            r"[A-Za-z][A-Za-z0-9_$#]*(?:\.[A-Za-z][A-Za-z0-9_$#]*)?",
            compile_routine,
        )
    ):
        raise InstallationError("Database compile routine is invalid")
    if pending.get("allow_apex_components") is not False or pending.get(
        "allow_standalone_object_source"
    ) is not False:
        raise InstallationError("Pending policy must reject APEX and standalone object source")
    directory = pending.get("directory")
    ddl_file = pending.get("ddl_file")
    dml_file = pending.get("dml_file")
    if not isinstance(directory, str) or not directory.strip():
        raise InstallationError("Pending directory is invalid")
    for filename in (ddl_file, dml_file):
        if not (
            isinstance(filename, str)
            and Path(filename).name == filename
            and filename.endswith(".sql")
        ):
            raise InstallationError("Pending filename is invalid")
    if ddl_file == dml_file:
        raise InstallationError("Pending DDL and DML filenames must differ")
    repository_retention = retention.get("repository_releases")
    database_retention = retention.get("database_snapshots")
    if not isinstance(repository_retention, dict) or not isinstance(database_retention, dict):
        raise InstallationError("Retention policy is incomplete")
    if repository_retention.get("mode") not in {"report", "prune"}:
        raise InstallationError("Repository retention mode is invalid")
    if not isinstance(database_retention.get("enabled"), bool):
        raise InstallationError("Database retention enabled flag is invalid")
    package = database_retention.get("package")
    if not isinstance(package, str) or not re.fullmatch(
        r"[A-Za-z][A-Za-z0-9_$#]*", package
    ):
        raise InstallationError("Database retention package is invalid")
    for value in (
        retention.get("review_every_releases"),
        repository_retention.get("keep_latest"),
        database_retention.get("keep_months"),
        database_retention.get("keep_scripts"),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise InstallationError("Retention counts must be positive integers")
    return (
        safe_project_path(project_root, Path(directory) / ddl_file),
        safe_project_path(project_root, Path(directory) / dml_file),
        apex_contract,
    )


def command_doctor(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)
    manifest = load_manifest(project_root)
    inspection = inspect_installation(project_root, manifest)
    print_inspection(inspection)
    if manifest is None or inspection["status"] != "HEALTHY":
        print("DOCTOR BLOCKED managed_installation_not_healthy")
        return 1

    compatibility = manifest.get("compatibility", {})
    print(f"KIT_VERSION {compatibility.get('kit_version', 'UNKNOWN')}")
    advisories: list[str] = []
    blockers: list[str] = []
    policy_contract: Optional[dict] = None

    profile = safe_project_path(project_root, ".oracle-apex-ai/project-profile.md")
    if not profile.is_file():
        advisories.append("project_profile_missing")
    else:
        content = profile.read_text(encoding="utf-8", errors="strict")
        match = re.search(
            r"oracle-apex-ai-project-profile-version:\s*(\d+)", content
        )
        installed_version = int(match.group(1)) if match else None
        if installed_version == PROJECT_PROFILE_VERSION:
            print(f"PROJECT_PROFILE_VERSION {installed_version} OK")
        else:
            print(
                "PROJECT_PROFILE_VERSION "
                f"{installed_version if installed_version is not None else 'UNKNOWN'} "
                f"EXPECTED {PROJECT_PROFILE_VERSION}"
            )
            advisories.append("project_profile_merge_required")

    patterns = safe_project_path(project_root, ".oracle-apex-ai/app-patterns.md")
    if patterns.is_file():
        print("APP_PATTERNS PRESENT")
    else:
        advisories.append("app_patterns_missing")

    policy_path = safe_project_path(project_root, EXPORT_POLICY_PATH)
    if not policy_path.is_file():
        advisories.append("export_policy_missing")
    else:
        try:
            policy = read_json(policy_path)
            ddl, dml, policy_contract = doctor_export_policy(project_root, policy)
            if not ddl.is_file() or not dml.is_file():
                advisories.append("configured_pending_files_missing")
            else:
                print(f"PENDING_DDL {ddl.relative_to(project_root)}")
                print(f"PENDING_DML {dml.relative_to(project_root)}")
            print(
                "EXPORT_POLICY VALID "
                f"schema={policy_contract['schema_version']} "
                f"readable_yaml={policy_contract['readable_yaml_mode']} "
                f"apexlang={policy_contract['apexlang_policy']}"
            )
            if policy_contract["schema_version"] == 1:
                advisories.append("export_policy_v2_migration_required")
        except (KeyError, TypeError, InstallationError, OSError, UnicodeError):
            advisories.append("export_policy_invalid")

    if args.apex_version:
        try:
            apex_report = evaluate_apex_version(args.apex_version)
            print(f"APEX_VERSION {apex_report['apex_version']}")
            print(f"APEX_SUPPORT {apex_report['support_status']}")
            print(
                "APEX_26_1_PUBLIC_APIS "
                + (
                    "AVAILABLE"
                    if apex_report["capabilities"]["apex_26_1_public_apis"]
                    else "UNAVAILABLE"
                )
            )
            print(
                "APEXLANG_PRODUCT "
                + (
                    "AVAILABLE"
                    if apex_report["capabilities"]["apexlang_product"]
                    else "UNAVAILABLE"
                )
            )
            print("APEXLANG_SKILL_POLICY DISABLED")
            if not apex_report["supported"]:
                blockers.append("apex_version_below_24_2")
            elif (
                policy_contract is not None
                and apex_report["capabilities"]["apex_26_1_public_apis"]
                and policy_contract["readable_yaml_mode"] == "always"
            ):
                blockers.append("readable_yaml_would_generate_apexlang")
        except ApexVersionError:
            blockers.append("apex_version_invalid")
    else:
        print("APEX_VERSION NOT_PROVIDED")

    print("COMPANIONS EXTERNAL build-apex-brand-reports oracle-apex-echarts")
    for blocker in blockers:
        print(f"BLOCKER {blocker}")
    for advisory in advisories:
        print(f"ADVISORY {advisory}")
    if blockers:
        print(f"DOCTOR BLOCKED count={len(blockers)} advisories={len(advisories)}")
        return 1
    print(f"DOCTOR {'READY' if not advisories else 'ADVISORY'} count={len(advisories)}")
    return 0


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

    source_root, mapping, metadata = load_source(args)
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
    print(
        "INSTALLED_KIT_VERSION "
        + str(manifest.get("compatibility", {}).get("kit_version", "UNKNOWN"))
    )
    print(
        "CANDIDATE_KIT_VERSION "
        + str(read_json(source_root / "templates/compatibility.json")["kit_version"])
    )
    return 0


def command_install_or_update(args: argparse.Namespace) -> int:
    project_root = args.project_root.resolve()
    validate_project_root(project_root)

    source_root, mapping, metadata = load_source(args)
    manifest = load_manifest(project_root)
    plan = build_plan(args.command, project_root, manifest, mapping)
    initialize_scaffold = (
        args.command == "install" or args.initialize_missing_project_files
    )
    scaffold = (
        []
        if args.no_project_scaffold or not initialize_scaffold
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

    doctor = subparsers.add_parser(
        "doctor", help="Inspect managed integrity and project-owned contract readiness."
    )
    doctor.add_argument("--project-root", type=Path, default=Path.cwd())
    doctor.add_argument(
        "--apex-version",
        help=(
            "Confirmed live APEX version used to enforce the 24.2 minimum, "
            "26.1 API gate, and version-specific export policy."
        ),
    )
    doctor.set_defaults(handler=command_doctor)

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
        operation.add_argument(
            "--initialize-missing-project-files",
            action="store_true",
            help=(
                "During update, create only missing project-owned templates. "
                "Never overwrite existing profile, patterns, policy, or pending files."
            ),
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
    except (OSError, UnicodeError) as exc:
        print(f"ERROR Filesystem operation failed: {exc}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
