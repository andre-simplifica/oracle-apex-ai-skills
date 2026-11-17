"""Advisory review of project-owned Markdown; never rewrite or print its values."""

from __future__ import annotations

import re


PROJECT_PROFILE_VERSION = 3
SECTIONS = (
    "Identification", "Implementation Rules", "Cooperative Database Object Locks",
    "Versioned Source and Release", "Pending DDL and DML",
)
IDENTITY_FIELDS = (
    "APEX version", "SQLcl command/saved connection", "Expected SQLcl `USER`",
    "Expected SQLcl `SERVICE_NAME` or required service token",
)


def prose_lines(content: str) -> list[str]:
    """Ignore fenced examples, which must not establish the profile contract."""
    lines: list[str] = []
    fence = None
    for line in content.splitlines():
        match = re.match(r"^\s{0,3}(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence is None:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence):
                fence = None
            continue
        if fence is None:
            lines.append(line)
    return lines


def review_profile(content: str) -> list[str]:
    """Stable suggestions, not evidence that a customized profile is invalid."""
    lines = prose_lines(content)
    text = "\n".join(lines)
    notes: list[str] = []
    markers = re.findall(r"<!--\s*oracle-apex-ai-project-profile-version:\s*(.*?)\s*-->", text)
    if not markers:
        notes.append("version_missing: compare with the current template before adding a marker")
    elif len(markers) != 1 or not markers[0].isascii() or not markers[0].isdigit():
        notes.append("version_ambiguous: reconcile duplicate or malformed version markers")
    elif int(markers[0]) < PROJECT_PROFILE_VERSION:
        notes.append("version_old: merge relevant guidance manually; preserve local decisions")
    elif int(markers[0]) > PROJECT_PROFILE_VERSION:
        notes.append("version_newer: use the matching kit; do not downgrade this profile")

    headings = {match.group(1).strip().casefold() for line in lines
                if (match := re.match(r"^##\s+(.+?)\s*#*\s*$", line))}
    for section in SECTIONS:
        if section.casefold() not in headings:
            notes.append(f"section_unrecognized: {section}; locate equivalent local guidance or add it if applicable")

    for field in IDENTITY_FIELDS:
        matches = re.findall(r"^[ \t]*[-*][ \t]+" + re.escape(field) + r":[ \t]*(.*?)[ \t]*$", text, re.M)
        if not matches:
            notes.append(f"field_unrecognized: {field}; confirm its location in the local profile")
        elif len(matches) > 1:
            notes.append(f"field_repeated: {field}; confirm the intended environment for each value")
        elif not matches[0] or re.fullmatch(r"<[^>]*>", matches[0]):
            notes.append(f"field_unfilled: {field}; record confirmed evidence in the private profile")

    policy = re.findall(r"^[ \t]*[-*][ \t]+APEXlang operations:[ \t]*(.*?)[ \t]*$", text, re.M | re.I)
    if not policy:
        notes.append("source_route_unrecognized: confirm SQL-only use here; APEXlang 26.2 belongs in the separate kit")
    elif len(policy) != 1 or policy[0].strip('`').casefold() != "disabled":
        notes.append("source_route_review: confirm the intended kit before using this SQL-only workflow")
    return notes
