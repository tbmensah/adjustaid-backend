"""Tests for Express Estimate readable export field ordering."""

from __future__ import annotations

import re

from app.services.ee_readable_render import (
    _ordered_keys,
    _user_friendly_rows,
    render_payload_markdown,
)


def _top_level_bold_keys(md: str, section: str) -> list[str]:
    """Extract first-level `**key**` labels under a ## section (markdown export)."""
    m = re.search(rf"## {re.escape(section)}\n\n(.*?)(?=\n## |\Z)", md, re.S)
    assert m, f"section {section!r} not found"
    body = m.group(1)
    keys: list[str] = []
    for line in body.splitlines():
        if not line.startswith("- **"):
            continue
        # Skip list entry headers like "- **Entry 1**" / "- **Entry 1 — x**"
        if re.match(r"- \*\*Entry \d+", line):
            continue
        km = re.match(r"- \*\*([^*]+)\*\*(?::|\s*$)", line)
        if km:
            keys.append(km.group(1))
    return keys


def test_ordered_keys_respects_form_order_then_unknowns() -> None:
    obj = {"dumpster": 1, "pressureWash": 2, "extra": 3, "hvac": 4}
    order = ("pressureWash", "dumpster", "hvac", "electrical", "finishes")
    assert _ordered_keys(obj, order) == ["pressureWash", "dumpster", "hvac", "extra"]


def test_exterior_keys_site_order_not_alphabetical() -> None:
    payload = {
        "projectDetails": {"insuredName": "A", "claimNumber": "1"},
        "exterior": {
            "finishes": {"exteriorPaint": {"enabled": True}},
            "electrical": {"exteriorOutlets": "2"},
            "dumpster": {"enabled": True, "count": "1", "size": "20"},
            "hvac": {"condenserUnits": []},
            "pressureWash": {"enabled": True, "perimeterFeet": "100"},
        },
    }
    md = render_payload_markdown(payload)
    keys = _top_level_bold_keys(md, "Exterior")
    assert keys[:5] == [
        "pressureWash",
        "dumpster",
        "hvac",
        "electrical",
        "finishes",
    ]
    # Alphabetical would start with dumpster
    assert keys[0] != "dumpster"


def test_foundation_site_order_insulation_before_enclosure() -> None:
    payload = {
        "projectDetails": {"insuredName": "A", "claimNumber": "1"},
        "foundation": {
            "elevator": False,
            "electrical": {"outlets110": "1"},
            "enclosureRemoval": {"confinedSpace": True},
            "subgradeAreaCoverage": {"drywall": {"enabled": True}},
            "waterSoftener": {"enabled": True, "type": "manual-timer"},
            "waterHeater": {"enabled": True, "type": "gas"},
            "sumpPump": {"enabled": True, "hp": "1/3-hp"},
            "hvac": {"furnace": {"enabled": True}},
            "insulation": {"bellyPaper": True},
            "crawlspace": {"heavyCleanArea": True},
            "stairs": {"landingReplacement": True},
            "basement": {"enabled": False},
        },
    }
    md = render_payload_markdown(payload)
    keys = _top_level_bold_keys(md, "Foundation")
    assert keys.index("insulation") < keys.index("enclosureRemoval")
    assert keys.index("sumpPump") < keys.index("waterHeater") < keys.index("waterSoftener")
    assert keys.index("waterSoftener") < keys.index("subgradeAreaCoverage")
    assert keys.index("crawlspace") == 0


def test_room_windows_before_electrical_doors_before_notes() -> None:
    payload = {
        "projectDetails": {"insuredName": "A", "claimNumber": "1"},
        "rooms": [
            {
                "id": 1,
                "name": "Living",
                "type": "room",
                "notes": "bottom note",
                "doorsEnabled": True,
                "doors": [{"id": 2, "category": "interior", "type": "6-panel"}],
                "electrical": {"enabled": True, "outlets110": 2},
                "windowsEnabled": True,
                "windows": [{"id": 3, "type": "single-hung", "material": "vinyl"}],
                "nfipCleaning": {"enabled": True},
                "flooring": {"enabled": True},
            }
        ],
    }
    md = render_payload_markdown(payload)
    # Under Rooms section, after Entry header, keys are indented with two spaces
    m = re.search(r"## Rooms\n\n(.*)\Z", md, re.S)
    assert m
    body = m.group(1)
    # Room field keys at indent level 1 (two spaces)
    room_keys = []
    for line in body.splitlines():
        km = re.match(r"  - \*\*([^*]+)\*\*(?::|\s*$)", line)
        if km:
            room_keys.append(km.group(1))
    assert room_keys.index("windowsEnabled") < room_keys.index("electrical")
    assert room_keys.index("windows") < room_keys.index("electrical")
    assert room_keys.index("doors") < room_keys.index("notes")
    assert room_keys.index("doorsEnabled") < room_keys.index("notes")


def test_enabled_false_section_omitted_enabled_present() -> None:
    payload = {
        "projectDetails": {"insuredName": "A", "claimNumber": "1"},
        "exterior": {
            "pressureWash": {"enabled": False, "perimeterFeet": "50"},
            "dumpster": {"enabled": True, "count": "2", "size": "20"},
        },
    }
    md = render_payload_markdown(payload)
    assert "pressureWash" not in md
    assert "dumpster" in md
    assert "**count**: 2" in md

    rows = _user_friendly_rows(payload)
    fields = [f for _s, f, _v in rows if _s == "Exterior"]
    joined = " | ".join(fields)
    assert "Pressure Wash" not in joined
    assert "Dumpster" in joined


def test_false_toggles_inside_enabled_section_kept() -> None:
    payload = {
        "projectDetails": {"insuredName": "A", "claimNumber": "1"},
        "exterior": {
            "hvac": {
                "condenserUnits": [
                    {
                        "id": 1,
                        "tonnage": "3",
                        "replace": True,
                        "serviceCall": False,
                        "f9Note": "ABC",
                    }
                ]
            }
        },
    }
    md = render_payload_markdown(payload)
    assert "serviceCall" in md
    assert "`false`" in md


def test_xlsx_nested_room_lists_not_labeled_as_room() -> None:
    """Windows/doors under Rooms must not get a nested 'Room N' Field head."""
    payload = {
        "projectDetails": {"insuredName": "A", "claimNumber": "1"},
        "rooms": [
            {
                "id": 1,
                "name": "Living",
                "type": "room",
                "doors": [{"id": 2, "category": "interior", "type": "6-panel"}],
                "windows": [{"id": 3, "type": "single-hung", "material": "vinyl"}],
            }
        ],
    }
    rows = _user_friendly_rows(payload)
    room_fields = [f for s, f, _v in rows if s == "Rooms"]
    assert any(f.startswith("Room 1 — Living »") for f in room_fields)

    window_type = next(
        (f, v) for s, f, v in rows if s == "Rooms" and f.endswith("» Type") and v == "single-hung"
    )
    door_type = next(
        (f, v) for s, f, v in rows if s == "Rooms" and f.endswith("» Type") and v == "6-panel"
    )
    assert "Windows" in window_type[0]
    assert "Doors" in door_type[0]
    # Nested list items must not be re-labeled as Room N (regression for Room-only head).
    assert "» Room " not in window_type[0]
    assert "» Room " not in door_type[0]
    # List-row ids must not appear in Field paths or as ID value rows.
    assert window_type[0] == "Room 1 — Living » Windows 1 » Type"
    assert door_type[0] == "Room 1 — Living » Doors 1 » Type"
    assert not any(f.endswith("» ID") or f == "ID" for f in room_fields)


def test_xlsx_id_only_list_entries_use_entry_label_as_value() -> None:
    """Id-only stubs show Layer 1 / Condenser Unit 1 — never the client id number."""
    payload = {
        "projectDetails": {"insuredName": "A", "claimNumber": "1"},
        "exterior": {
            "hvac": {
                "condenserUnits": [{"id": 1785356713351}],
                "miniSplits": [{"id": 1785356737941}],
            }
        },
        "foundation": {
            "hvac": {
                "airHandlers": [
                    {
                        "id": 1785356747106,
                        "aCoil": {"enabled": True, "detachAndReset": True},
                    }
                ]
            }
        },
        "rooms": [
            {
                "id": 1785358035626,
                "name": "Kitchen 1",
                "type": "kitchen",
                "flooring": {"layers": [{"id": 1785357088747}]},
                "doors": [{"id": 1785451498257, "category": "interior", "nonCased": True}],
            }
        ],
    }
    rows = _user_friendly_rows(payload)
    fields = [f for _s, f, _v in rows]
    values = [v for _s, _f, v in rows]
    joined = " | ".join(f"{f}={v}" for f, v in zip(fields, values))

    assert not any(f.endswith("» ID") or f == "ID" for f in fields)
    for n in (
        "1785356713351",
        "1785356737941",
        "1785356747106",
        "1785358035626",
        "1785357088747",
        "1785451498257",
    ):
        assert n not in joined

    assert ("Exterior", "Hvac » Condenser Units 1", "Condenser Unit 1") in rows
    assert ("Exterior", "Hvac » Mini Splits 1", "Mini Split 1") in rows
    assert ("Rooms", "Room 1 — Kitchen 1 » Flooring » Layers 1", "Layer 1") in rows
    assert ("Rooms", "Room 1 — Kitchen 1 » Doors 1 » Category", "interior") in rows
    # Air handler has real nested fields — path has no id suffix.
    assert any(
        f == "Hvac » Air Handlers 1 » A Coil » Detach And Reset" and v == "Yes"
        for s, f, v in rows
        if s == "Foundation"
    )
    assert not any("1785356747106" in f for f in fields)
