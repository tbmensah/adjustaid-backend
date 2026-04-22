"""Deterministic Express Estimate JSON → readable markdown (no AI)."""

from __future__ import annotations

import json
from typing import Any


_SECTION_TITLES: dict[str, str] = {
    "projectDetails": "Project details",
    "exterior": "Exterior",
    "foundation": "Foundation",
    "rooms": "Rooms",
}


def _indent(level: int) -> str:
    return "  " * level


def _render_value(val: Any, level: int) -> list[str]:
    ind = _indent(level)
    if val is None:
        return [f"{ind}- _(none)_"]
    if isinstance(val, bool):
        return [f"{ind}- `{str(val).lower()}`"]
    if isinstance(val, (int, float)):
        return [f"{ind}- `{val}`"]
    if isinstance(val, str):
        s = val if val else "_(empty)_"
        return [f"{ind}- {s}"]
    if isinstance(val, list):
        if not val:
            return [f"{ind}- _(empty list)_"]
        out: list[str] = []
        for i, item in enumerate(val):
            if isinstance(item, dict):
                label = item.get("name") or item.get("id")
                title = f"Entry {i + 1}" + (f" — {label}" if label is not None else "")
                out.append(f"{ind}- **{title}**")
                out.extend(_render_value(item, level + 1))
            else:
                out.extend(_render_value(item, level))
        return out
    if isinstance(val, dict):
        if not val:
            return [f"{ind}- _(empty)_"]
        out = []
        for k in sorted(val.keys(), key=str):
            v = val[k]
            key_label = str(k)
            if isinstance(v, (dict, list)):
                out.append(f"{ind}- **{key_label}**")
                out.extend(_render_value(v, level + 1))
            elif v is None:
                out.append(f"{ind}- **{key_label}**: _(none)_")
            elif isinstance(v, bool):
                out.append(f"{ind}- **{key_label}**: `{str(v).lower()}`")
            elif isinstance(v, (int, float)):
                out.append(f"{ind}- **{key_label}**: `{v}`")
            elif isinstance(v, str):
                out.append(f"{ind}- **{key_label}**: {v if v else '_(empty)_'}")
            else:
                out.append(f"{ind}- **{key_label}**: `{json.dumps(v, default=str)}`")
        return out
    return [f"{ind}- `{json.dumps(val, default=str)}`"]


def render_payload_markdown(payload: dict[str, Any]) -> str:
    """Build human-readable markdown from stored EE payload."""
    title = "Express Estimate"
    pd = payload.get("projectDetails")
    if isinstance(pd, dict):
        pn = pd.get("projectName")
        if isinstance(pn, str) and pn.strip():
            title = f"Express Estimate — {pn.strip()}"

    lines: list[str] = [f"# {title}", ""]
    known_order = ("projectDetails", "exterior", "foundation", "rooms")
    seen: set[str] = set()

    for key in known_order:
        if key not in payload:
            continue
        seen.add(key)
        section = _SECTION_TITLES.get(key, key)
        lines.append(f"## {section}")
        lines.append("")
        chunk = payload[key]
        if chunk is None:
            lines.append("_Not provided._")
        else:
            lines.extend(_render_value(chunk, 0))
        lines.append("")

    other_keys = sorted(k for k in payload if k not in seen)
    for key in other_keys:
        lines.append(f"## {key}")
        lines.append("")
        chunk = payload[key]
        if chunk is None:
            lines.append("_Not provided._")
        elif isinstance(chunk, (dict, list)):
            lines.extend(_render_value(chunk, 0))
        else:
            lines.append(json.dumps(chunk, indent=2, default=str))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
