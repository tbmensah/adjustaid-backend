"""Deterministic Express Estimate JSON → readable markdown / Excel (no AI)."""

from __future__ import annotations

import io
import json
import re
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font


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
        for key in ("projectName", "insuredName", "claimNumber"):
            val = pd.get(key)
            if isinstance(val, str) and val.strip():
                title = f"Express Estimate — {val.strip()}"
                break

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


_JOIN = " » "


def _humanize_key(key: str) -> str:
    """camelCase / snake_case-ish → Title Words for spreadsheet Field column."""
    s = str(key).strip()
    if not s:
        return s
    if s.lower() == "id":
        return "ID"
    s = re.sub(r"[_-]+", " ", s)
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", s)
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", s)
    parts = [p for p in s.split() if p]
    if not parts:
        return str(key)
    out: list[str] = []
    for i, p in enumerate(parts):
        if p.isupper() and len(p) <= 4:
            out.append(p)
        elif i == 0:
            out.append(p[0].upper() + p[1:].lower() if len(p) > 1 else p.upper())
        else:
            out.append(p.lower() if p.islower() or p.isupper() else p[0].upper() + p[1:])
    return " ".join(out)


def _cell_value(val: Any) -> str:
    if val is None:
        return "—"
    if isinstance(val, bool):
        return "Yes" if val else "No"
    if isinstance(val, float):
        if val.is_integer():
            return str(int(val))
        return str(val)
    if isinstance(val, (int, str)):
        return str(val)
    return json.dumps(val, default=str)


def _section_title(key: str) -> str:
    return _SECTION_TITLES.get(key, _humanize_key(key))


def _walk_section(section: str, val: Any, label_parts: list[str], rows: list[tuple[str, str, str]]) -> None:
    if val is None:
        rows.append((section, _JOIN.join(label_parts) if label_parts else "(empty)", "—"))
        return
    if isinstance(val, (bool, int, float, str)):
        rows.append((section, _JOIN.join(label_parts) if label_parts else "(value)", _cell_value(val)))
        return
    if isinstance(val, dict):
        if not val:
            rows.append((section, _JOIN.join(label_parts) if label_parts else "(empty)", "—"))
            return
        for k in sorted(val.keys(), key=str):
            _walk_section(section, val[k], label_parts + [_humanize_key(k)], rows)
        return
    if isinstance(val, list):
        if not val:
            rows.append((section, _JOIN.join(label_parts) if label_parts else "(list)", "—"))
            return
        for i, item in enumerate(val):
            if isinstance(item, dict):
                nm = item.get("name")
                rid = item.get("id")
                extra = ""
                if isinstance(nm, str) and nm.strip():
                    extra = f" — {nm.strip()}"
                elif rid is not None:
                    extra = f" — {rid}"
                if section == "Rooms":
                    head = f"Room {i + 1}{extra}"
                elif label_parts:
                    head = f"{label_parts[-1]} {i + 1}{extra}"
                else:
                    head = f"Entry {i + 1}{extra}"
                base = label_parts[:-1] + [head] if label_parts else [head]
                _walk_section(section, item, base, rows)
            else:
                ip = (label_parts + [f"Item {i + 1}"]) if label_parts else [f"Item {i + 1}"]
                _walk_section(section, item, ip, rows)
        return
    rows.append((section, _JOIN.join(label_parts) if label_parts else "(value)", _cell_value(val)))


def _user_friendly_rows(payload: dict[str, Any]) -> list[tuple[str, str, str]]:
    """Section, Field (humanized), Value — one block per top-level key like markdown."""
    rows: list[tuple[str, str, str]] = []
    known_order = ("projectDetails", "exterior", "foundation", "rooms")
    seen: set[str] = set()
    for key in known_order:
        if key not in payload:
            continue
        seen.add(key)
        sec = _section_title(key)
        chunk = payload[key]
        if chunk is None:
            rows.append((sec, "—", "Not provided"))
        else:
            _walk_section(sec, chunk, [], rows)
    for key in sorted(k for k in payload if k not in seen):
        sec = _section_title(key)
        chunk = payload[key]
        if chunk is None:
            rows.append((sec, "—", "Not provided"))
        elif isinstance(chunk, (dict, list)):
            _walk_section(sec, chunk, [], rows)
        else:
            rows.append((sec, _humanize_key(key), _cell_value(chunk)))
    return rows


def render_payload_xlsx_bytes(payload: dict[str, Any]) -> bytes:
    """Workbook: title row + Section | Field | Value (humanized, grouped)."""
    title = "Express Estimate"
    pd = payload.get("projectDetails")
    if isinstance(pd, dict):
        for key in ("projectName", "insuredName", "claimNumber"):
            val = pd.get(key)
            if isinstance(val, str) and val.strip():
                title = f"Express Estimate — {val.strip()}"
                break

    data_rows = _user_friendly_rows(payload)

    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.merge_cells("A1:C1")
    top = ws["A1"]
    top.value = title
    top.font = Font(bold=True, size=14)
    top.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[1].height = 28
    ws.append([])
    ws.append(["Section", "Field", "Value"])
    for c in range(1, 4):
        cell = ws.cell(row=3, column=c)
        cell.font = Font(bold=True)
        cell.alignment = Alignment(vertical="top", wrap_text=True)
    for section, field, value in data_rows:
        ws.append([section, field, value])
    for row in ws.iter_rows(min_row=4, max_row=ws.max_row, min_col=1, max_col=3):
        for cell in row:
            cell.alignment = Alignment(vertical="top", wrap_text=True)

    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 48
    ws.column_dimensions["C"].width = 40
    ws.freeze_panes = "A4"

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
