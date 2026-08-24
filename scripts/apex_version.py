#!/usr/bin/env python3
"""Shared Oracle APEX version and feature-gate helpers."""

from __future__ import annotations

from dataclasses import dataclass
import re


MINIMUM_SUPPORTED = (24, 2)
DYNAMIC_CONTENT_RETURN_CLOB = (22, 2)
APEX_26_1 = (26, 1)
VERSION_RE = re.compile(
    r"^\s*(?P<major>\d+)\.(?P<minor>\d+)"
    r"(?:\.(?P<patch>\d+))?(?:\.(?P<revision>\d+))?\s*$"
)


class ApexVersionError(ValueError):
    """Raised when an APEX version cannot be evaluated safely."""


@dataclass(frozen=True, order=True)
class ApexVersion:
    major: int
    minor: int
    patch: int = 0
    revision: int = 0

    @property
    def feature_release(self) -> tuple[int, int]:
        return (self.major, self.minor)

    @property
    def normalized(self) -> str:
        values = [self.major, self.minor, self.patch, self.revision]
        while len(values) > 2 and values[-1] == 0:
            values.pop()
        return ".".join(str(value) for value in values)


def parse_apex_version(value: str) -> ApexVersion:
    match = VERSION_RE.fullmatch(value)
    if not match:
        raise ApexVersionError(
            "APEX version must use numeric release notation such as 24.2 or 26.1.3"
        )
    return ApexVersion(
        int(match.group("major")),
        int(match.group("minor")),
        int(match.group("patch") or 0),
        int(match.group("revision") or 0),
    )


def evaluate_apex_version(value: str) -> dict:
    version = parse_apex_version(value)
    supported = version.feature_release >= MINIMUM_SUPPORTED
    has_dynamic_content = version.feature_release >= DYNAMIC_CONTENT_RETURN_CLOB
    has_26_1_features = supported and version.feature_release >= APEX_26_1

    if not supported:
        status = "UNSUPPORTED"
        formats: list[str] = []
    elif has_26_1_features:
        status = "SUPPORTED_26_1_PLUS"
        formats = ["split-sql", "monolithic-sql"]
    else:
        status = "SUPPORTED_LEGACY_EXPORT"
        formats = ["split-sql", "readable-yaml", "monolithic-sql"]

    return {
        "schema_version": 1,
        "apex_version": version.normalized,
        "feature_release": f"{version.major}.{version.minor}",
        "minimum_supported": "24.2",
        "support_status": status,
        "supported": supported,
        "capabilities": {
            "core_skill_workflows": supported,
            "dynamic_content_return_clob": has_dynamic_content,
            "sql_application_export": supported,
            "readable_yaml_export": supported and not has_26_1_features,
            "apex_26_1_public_apis": has_26_1_features,
            "apexlang_product": has_26_1_features,
        },
        "policy": {
            "apexlang_operations": "disabled",
            "apexlang_export": False,
            "apexlang_import": False,
            "apexlang_generate": False,
            "apexlang_validate": False,
        },
        "official_export_formats": formats,
    }
