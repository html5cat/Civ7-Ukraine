#!/usr/bin/env python3
"""Structural validation for the Ukraine Historical Continuity Civ7 mod.

Checks XML well-formedness, modinfo file references, and LOC key coverage.
Does not require the Civilization VII game binary.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODINFO = ROOT / "ukraine-historical-continuity.modinfo"
ERRORS: list[str] = []
WARNINGS: list[str] = []


def parse(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        ERRORS.append(f"XML parse error in {path.relative_to(ROOT)}: {exc}")
        return None


def local(tag: str) -> str:
    if "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def collect_modinfo_items(root: ET.Element) -> list[str]:
    items: list[str] = []
    for el in root.iter():
        if local(el.tag) == "Item" and el.text:
            items.append(el.text.strip())
        if local(el.tag) == "File" and el.text:
            items.append(el.text.strip())
    return items


def collect_tags(root: ET.Element, attr: str = "Tag") -> set[str]:
    tags: set[str] = set()
    for el in root.iter():
        if local(el.tag) == "Row" and attr in el.attrib:
            tags.add(el.attrib[attr])
        # Also support child <Tag> elements
        if local(el.tag) == attr and el.text:
            tags.add(el.text.strip())
    return tags


def collect_loc_refs(root: ET.Element) -> set[str]:
    refs: set[str] = set()
    for el in root.iter():
        for val in list(el.attrib.values()) + ([el.text] if el.text else []):
            if not val:
                continue
            for token in val.replace(",", " ").split():
                token = token.strip()
                if token.startswith("LOC_"):
                    refs.add(token)
    return refs


def main() -> int:
    print(f"Validating mod at {ROOT}")

    modinfo_root = parse(MODINFO)
    if modinfo_root is None:
        print_report()
        return 1

    # Properties should use plain text for Workshop/user mods
    for prop in modinfo_root.iter():
        if local(prop.tag) in {"Name", "Description"} and prop.text and prop.text.startswith("LOC_"):
            WARNINGS.append(
                f"modinfo {local(prop.tag)} uses LOC key '{prop.text}' — "
                "user mods should prefer plain text so Additional Content shows a readable name."
            )

    items = collect_modinfo_items(modinfo_root)
    missing_files = [i for i in items if not (ROOT / i).exists()]
    for missing in missing_files:
        ERRORS.append(f"modinfo references missing file: {missing}")

    # Parse every XML under the mod
    xml_files = sorted(ROOT.rglob("*.xml")) + sorted(ROOT.rglob("*.modinfo"))
    defined_locs: set[str] = set()
    referenced_locs: set[str] = set()
    trait_modifiers: set[str] = set()
    gameeffect_ids: set[str] = set()

    for path in xml_files:
        root = parse(path)
        if root is None:
            continue
        rel = path.relative_to(ROOT)
        if "text" in path.parts:
            defined_locs |= collect_tags(root, "Tag")
        referenced_locs |= collect_loc_refs(root)

        if local(root.tag) == "GameEffects" or root.find(".//{GameEffects}Modifier") is not None or any(
            local(el.tag) == "Modifier" for el in root.iter()
        ):
            for el in root.iter():
                if local(el.tag) == "Modifier" and "id" in el.attrib:
                    gameeffect_ids.add(el.attrib["id"])

        for el in root.iter():
            if local(el.tag) == "Row" and "ModifierId" in el.attrib and "TraitType" in el.attrib:
                trait_modifiers.add(el.attrib["ModifierId"])

        # Empty age ability files are no longer allowed
        if path.name in {
            "civilizations-antiquity.xml",
            "civilizations-exploration.xml",
            "civilizations-modern.xml",
        }:
            has_modifier = any(
                local(el.tag) == "Row" and "ModifierId" in el.attrib for el in root.iter()
            )
            if not has_modifier:
                ERRORS.append(f"{rel} has no TraitModifiers rows")

    dangling_traits = sorted(trait_modifiers - gameeffect_ids)
    for mod_id in dangling_traits:
        ERRORS.append(f"TraitModifier '{mod_id}' has no matching GameEffects Modifier id")

    # Only check LOC refs that appear in data/config (not every file's self-refs)
    required_missing = sorted(
        loc
        for loc in referenced_locs
        if loc not in defined_locs and loc.startswith("LOC_") and not loc.startswith("LOC_MODULE_BASE")
        and not loc.startswith("LOC_MODULE_AGE")
        and not loc.startswith("LOC_CREATE_GAME")
        and not loc.startswith("LOC_LOCKED_")
        and loc
        not in {
            # Base-game LOC keys we intentionally reuse
            "LOC_CREATE_GAME_STRATEGIC_CHOICE",
            "LOC_CREATE_GAME_HISTORICAL_CHOICE",
            "LOC_LOCKED_INCLUDED_WITH_CONTENT",
        }
    )
    # Filter to keys this mod is expected to define (our prefixes)
    our_missing = [
        loc
        for loc in required_missing
        if any(
            loc.startswith(p)
            for p in (
                "LOC_CIVILIZATION_",
                "LOC_TRAIT_",
                "LOC_CITY_NAME_",
                "LOC_UNIT_",
                "LOC_ABILITY_",
                "LOC_LOADING_",
                "LOC_UNLOCK_PLAY_AS_",
                "LOC_MODULE_UKRAINE_",
            )
        )
    ]
    for loc in our_missing:
        ERRORS.append(f"Missing localization for {loc}")

    # Required gameplay files
    required = [
        "data/civilizations-shared.xml",
        "data/civilizations-antiquity-gameeffects.xml",
        "data/civilizations-exploration-gameeffects.xml",
        "data/civilizations-modern-gameeffects.xml",
        "data/units-antiquity.xml",
        "data/units-exploration.xml",
        "data/units-modern.xml",
        "config/config.xml",
        "assets/civ_sym_ukraine_continuity.png",
    ]
    for rel in required:
        if not (ROOT / rel).exists():
            ERRORS.append(f"Required file missing: {rel}")

    print_report()
    return 1 if ERRORS else 0


def print_report() -> None:
    for w in WARNINGS:
        print(f"WARNING: {w}")
    for e in ERRORS:
        print(f"ERROR: {e}")
    if not ERRORS:
        print("OK: mod structure looks valid.")
    else:
        print(f"FAILED with {len(ERRORS)} error(s).")


if __name__ == "__main__":
    sys.exit(main())
