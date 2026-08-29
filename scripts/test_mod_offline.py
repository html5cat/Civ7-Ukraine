#!/usr/bin/env python3
"""Offline test suite for Ukraine Historical Continuity.

Civilization VII is not installed in this environment, so these tests cannot
load the real gameplay DB. They catch the class of failures that crash mods
before/at map load when patterns are wrong (VisualRemaps via UpdateDatabase,
reversed remap direction, missing files, dangling modifiers, LOC gaps,
RandomCityNameDepth mismatches, known FK typos).
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODINFO = ROOT / "ukraine-historical-continuity.modinfo"

# Confirmed base-game / DLC identifiers from public docs + working Workshop mods.
KNOWN_LEADERS = {
    "LEADER_XERXES",
    "LEADER_CHARLEMAGNE",
    "LEADER_LAFAYETTE",
    "LEADER_BENJAMIN_FRANKLIN",
    "LEADER_CATHERINE",
}
KNOWN_UNITS = {
    "UNIT_CHARIOT",
    "UNIT_HORSEMAN",
    "UNIT_COURSER",
    "UNIT_KNIGHT",
    "UNIT_LANCER",
    "UNIT_LINE_INFANTRY",
    "UNIT_RIFLEMAN",
    "UNIT_INFANTRY_COMPANY",
    "UNIT_CUIRASSIER",
}
KNOWN_RESOURCES = {
    "RESOURCE_HORSES",
    "RESOURCE_FURS",
    "RESOURCE_COAL",
    "RESOURCE_IRON",
    "RESOURCE_COTTON",
    "RESOURCE_WINE",
    "RESOURCE_GOLD",
}
KNOWN_YIELDS = {
    "YIELD_FOOD",
    "YIELD_PRODUCTION",
    "YIELD_GOLD",
    "YIELD_SCIENCE",
    "YIELD_CULTURE",
    "YIELD_HAPPINESS",
    "YIELD_DIPLOMACY",
}
KNOWN_EFFECTS = {
    "EFFECT_UNIT_ADJUST_MOVEMENT",
    "EFFECT_ADJUST_UNIT_STRENGTH_MODIFIER",
    "EFFECT_CITY_ADJUST_YIELD",
    "EFFECT_ADJUST_WAR_SUPPORT_BONUS",
}
KNOWN_COLLECTIONS = {
    "COLLECTION_PLAYER_UNITS",
    "COLLECTION_PLAYER_COMBAT",
    "COLLECTION_PLAYER_CITIES",
    "COLLECTION_PLAYER_CAPITAL_CITY",
    "COLLECTION_OWNER",
    "COLLECTION_UNIT_COMBAT",
}
KNOWN_TERRAINS = {"TERRAIN_FLAT", "TERRAIN_HILL", "TERRAIN_COAST", "TERRAIN_MOUNTAIN"}
KNOWN_BIOMES = {
    "BIOME_GRASSLAND",
    "BIOME_PLAINS",
    "BIOME_DESERT",
    "BIOME_TUNDRA",
    "BIOME_TROPICAL",
    "BIOME_MARINE",
}

ERRORS: list[str] = []
WARNINGS: list[str] = []
PASSES: list[str] = []


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse(path: Path) -> ET.Element | None:
    try:
        return ET.parse(path).getroot()
    except ET.ParseError as exc:
        ERRORS.append(f"XML parse error in {path.relative_to(ROOT)}: {exc}")
        return None


def ok(msg: str) -> None:
    PASSES.append(msg)


def test_modinfo() -> ET.Element | None:
    root = parse(MODINFO)
    if root is None:
        return None

    props = {local(el.tag): (el.text or "") for el in root if local(el.tag) == "Properties" for el in list(el) or []}
    # Properties are nested
    props = {}
    for el in root.iter():
        if local(el.tag) == "Properties":
            for child in el:
                props[local(child.tag)] = (child.text or "").strip()

    if props.get("Name", "").startswith("LOC_"):
        ERRORS.append("modinfo Name uses LOC key; user mods need plain text")
    else:
        ok(f"modinfo Name is plain text: {props.get('Name')!r}")

    mod_el = next((el for el in root.iter() if local(el.tag) == "Mod"), root)
    version = mod_el.attrib.get("version", "")
    if not version.isdigit() or int(version) < 1:
        ERRORS.append(f"modinfo version must be positive integer, got {version!r}")
    else:
        ok(f"modinfo version is positive integer: {version}")

    # Collect actions
    update_db_files: list[str] = []
    visual_remap_files: list[str] = []
    icon_scopes: set[str] = set()
    for group in root.iter():
        if local(group.tag) != "ActionGroup":
            continue
        scope = group.attrib.get("scope", "")
        criteria = group.attrib.get("criteria", "")
        for actions in group:
            if local(actions.tag) != "Actions":
                continue
            for action in actions:
                aname = local(action.tag)
                items = [
                    (item.text or "").strip()
                    for item in action
                    if local(item.tag) == "Item" and item.text
                ]
                if aname == "UpdateDatabase":
                    update_db_files.extend(items)
                    for item in items:
                        if "visual-remap" in item.lower():
                            ERRORS.append(
                                f"Visual remaps file '{item}' loaded via UpdateDatabase "
                                "(crashes: no such table VisualRemaps). Use UpdateVisualRemaps."
                            )
                if aname == "UpdateVisualRemaps":
                    visual_remap_files.extend(items)
                    if criteria != "always":
                        WARNINGS.append(
                            f"UpdateVisualRemaps in criteria={criteria!r}; prefer always"
                        )
                if aname == "UpdateIcons" and criteria == "always":
                    icon_scopes.add(scope)

    if "game" in icon_scopes and "shell" in icon_scopes:
        ok("UpdateIcons present in both game and shell always groups")
    else:
        ERRORS.append(f"UpdateIcons missing dual always scopes; have {icon_scopes}")

    if visual_remap_files:
        ok(f"UpdateVisualRemaps configured: {visual_remap_files}")
    else:
        ERRORS.append("No UpdateVisualRemaps action — unique unit models will be missing")

    # All referenced files exist
    items: list[str] = []
    for el in root.iter():
        if local(el.tag) in {"Item", "File"} and el.text:
            items.append(el.text.strip())
    missing = [i for i in items if not (ROOT / i).exists()]
    if missing:
        for m in missing:
            ERRORS.append(f"modinfo references missing file: {m}")
    else:
        ok(f"All {len(items)} modinfo file references exist")

    # Age references
    refs = [
        el.attrib.get("id")
        for el in root.iter()
        if local(el.tag) == "Mod" and el.attrib.get("id", "").startswith("age-")
    ]
    # Dependencies/References children
    ref_ids = []
    for el in root.iter():
        if local(el.tag) == "References":
            for child in el:
                if local(child.tag) == "Mod":
                    ref_ids.append(child.attrib.get("id"))
    for needed in ("age-antiquity", "age-exploration", "age-modern"):
        if needed not in ref_ids:
            ERRORS.append(f"Missing References Mod id={needed}")
    if all(n in ref_ids for n in ("age-antiquity", "age-exploration", "age-modern")):
        ok("Age module References present")

    return root


def test_visual_remaps() -> None:
    path = ROOT / "data/visual-remaps.xml"
    root = parse(path)
    if root is None:
        return
    rows = [el for el in root.iter() if local(el.tag) == "Row"]
    if not rows:
        ERRORS.append("visual-remaps.xml has no rows")
        return

    our_units = {
        "UNIT_SAKA_HORSE_ARCHER",
        "UNIT_SAKA_HORSE_ARCHER_2",
        "UNIT_DRUZHINA",
        "UNIT_DRUZHINA_2",
        "UNIT_DRUZHINA_3",
        "UNIT_SICH_RIFLEMEN",
        "UNIT_SICH_RIFLEMEN_2",
        "UNIT_SICH_RIFLEMEN_3",
    }

    for row in rows:
        fields = {local(c.tag): (c.text or "").strip() for c in row}
        # Also support attributes
        fields.update({k: v for k, v in row.attrib.items()})
        donor = fields.get("From", "")
        target = fields.get("To", "")
        if target not in our_units:
            ERRORS.append(
                f"VisualRemap To={target!r} should be our unit (From=donor, To=custom). "
                f"Got From={donor!r} To={target!r}"
            )
        if donor not in KNOWN_UNITS:
            ERRORS.append(f"VisualRemap donor From={donor!r} is not a known base unit")
        if donor in our_units:
            ERRORS.append(f"VisualRemap From={donor!r} is reversed (donor must be base unit)")

    # Ensure unit DB files do not embed VisualRemaps
    for p in (ROOT / "data").glob("units-*.xml"):
        if "gameeffects" in p.name:
            continue
        text = p.read_text()
        if "<VisualRemaps>" in text:
            ERRORS.append(f"{p.name} still contains VisualRemaps inside UpdateDatabase content")

    ok(f"VisualRemaps direction + donors OK ({len(rows)} rows)")


def test_gameeffects_and_traits() -> None:
    trait_mods: set[str] = set()
    effect_ids: set[str] = set()

    for path in (ROOT / "data").rglob("*.xml"):
        root = parse(path)
        if root is None:
            continue
        for el in root.iter():
            if local(el.tag) == "Row" and "ModifierId" in el.attrib and "TraitType" in el.attrib:
                trait_mods.add(el.attrib["ModifierId"])
            if local(el.tag) == "Row" and "ModifierId" in el.attrib and "UnitAbilityType" in el.attrib:
                trait_mods.add(el.attrib["ModifierId"])
            if local(el.tag) == "Modifier" and "id" in el.attrib:
                effect_ids.add(el.attrib["id"])
                effect = el.attrib.get("effect", "")
                collection = el.attrib.get("collection", "")
                if effect and effect not in KNOWN_EFFECTS:
                    WARNINGS.append(f"Unlisted effect {effect} in {path.name} (may still be valid)")
                if collection and collection not in KNOWN_COLLECTIONS:
                    WARNINGS.append(f"Unlisted collection {collection} in {path.name}")
                for arg in el.iter():
                    if local(arg.tag) == "Argument" and arg.attrib.get("name") == "YieldType":
                        y = (arg.text or "").strip()
                        if y and y not in KNOWN_YIELDS:
                            ERRORS.append(f"Unknown YieldType {y!r} in {path.name}")

    dangling = sorted(trait_mods - effect_ids)
    for mid in dangling:
        ERRORS.append(f"Modifier '{mid}' attached but not defined in GameEffects")
    unused = sorted(effect_ids - trait_mods)
    # Allow unused? No — every defined effect should be attached
    for mid in unused:
        ERRORS.append(f"GameEffects Modifier '{mid}' is never attached")

    if not dangling and not unused and trait_mods:
        ok(f"All {len(trait_mods)} attached modifiers have GameEffects definitions")


def test_shared_civ_integrity() -> None:
    root = parse(ROOT / "data/civilizations-shared.xml")
    if root is None:
        return

    city_counts: dict[str, int] = defaultdict(int)
    depths: dict[str, int] = {}
    for el in root.iter():
        if local(el.tag) != "Row":
            continue
        if "CityName" in el.attrib and "CivilizationType" in el.attrib:
            city_counts[el.attrib["CivilizationType"]] += 1
        if "CivilizationType" in el.attrib and "RandomCityNameDepth" in el.attrib:
            depths[el.attrib["CivilizationType"]] = int(el.attrib["RandomCityNameDepth"])
        if "ResourceType" in el.attrib:
            r = el.attrib["ResourceType"]
            if r not in KNOWN_RESOURCES:
                ERRORS.append(f"Unknown StartBias resource {r}")
        if "TerrainType" in el.attrib:
            t = el.attrib["TerrainType"]
            if t not in KNOWN_TERRAINS:
                ERRORS.append(f"Unknown StartBias terrain {t}")
        if "BiomeType" in el.attrib:
            b = el.attrib["BiomeType"]
            if b not in KNOWN_BIOMES:
                ERRORS.append(f"Unknown StartBias biome {b}")
        if "LeaderType" in el.attrib and el.attrib["LeaderType"].startswith("LEADER_"):
            if el.attrib["LeaderType"] not in KNOWN_LEADERS:
                WARNINGS.append(f"LeaderType {el.attrib['LeaderType']} not in hard-coded known set")
        if "Leader" in el.attrib and el.attrib["Leader"].startswith("LEADER_"):
            if el.attrib["Leader"] not in KNOWN_LEADERS:
                WARNINGS.append(f"Leader {el.attrib['Leader']} not in hard-coded known set")

    for civ, depth in depths.items():
        count = city_counts.get(civ, 0)
        if count < depth:
            ERRORS.append(
                f"{civ} RandomCityNameDepth={depth} but only {count} CityNames rows"
            )
        else:
            ok(f"{civ} city list covers depth ({count}>={depth})")

    # Attribute TOT rows
    text = (ROOT / "data/civilizations-shared.xml").read_text()
    for tot in (
        "TRAIT_ATTRIBUTE_MILITARISTIC_TOT_AQ",
        "TRAIT_ATTRIBUTE_ECONOMIC_TOT_AQ",
        "TRAIT_ATTRIBUTE_CULTURAL_TOT_AQ",
    ):
        if tot not in text:
            ERRORS.append(f"Missing attribute TOT trait usage: {tot}")
    ok("Attribute TOT traits present in shared civ data")


def test_unit_replaces() -> None:
    for path in (ROOT / "data").glob("units-*.xml"):
        if "gameeffects" in path.name:
            continue
        root = parse(path)
        if root is None:
            continue
        for el in root.iter():
            if local(el.tag) == "Row" and "ReplacesUnitType" in el.attrib:
                base = el.attrib["ReplacesUnitType"]
                if base not in KNOWN_UNITS:
                    ERRORS.append(f"{path.name}: ReplacesUnitType {base} not in known set")
        ok(f"{path.name}: UnitReplaces targets checked")


def test_loc_coverage() -> None:
    defined: set[str] = set()
    for path in (ROOT / "text").glob("*.xml"):
        root = parse(path)
        if root is None:
            continue
        for el in root.iter():
            if local(el.tag) == "Row" and "Tag" in el.attrib:
                defined.add(el.attrib["Tag"])

    refs: set[str] = set()
    for path in list((ROOT / "data").rglob("*.xml")) + [ROOT / "config/config.xml", MODINFO]:
        root = parse(path)
        if root is None:
            continue
        for el in root.iter():
            for val in list(el.attrib.values()) + ([el.text] if el.text else []):
                if not val:
                    continue
                for token in val.replace(",", " ").split():
                    if token.startswith("LOC_"):
                        refs.add(token)

    prefixes = (
        "LOC_CIVILIZATION_",
        "LOC_TRAIT_",
        "LOC_CITY_NAME_",
        "LOC_UNIT_",
        "LOC_ABILITY_",
        "LOC_LOADING_",
        "LOC_UNLOCK_PLAY_AS_",
        "LOC_MODULE_UKRAINE_",
    )
    missing = sorted(
        r for r in refs if r.startswith(prefixes) and r not in defined
    )
    for m in missing:
        ERRORS.append(f"Missing LOC text for {m}")
    if not missing:
        ok(f"All {len([r for r in refs if r.startswith(prefixes)])} mod LOC keys defined")


def test_png_asset() -> None:
    png = ROOT / "assets/civ_sym_ukraine_continuity.png"
    if not png.exists():
        ERRORS.append("Missing civ symbol PNG")
        return
    data = png.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        ERRORS.append("civ symbol is not a valid PNG")
    else:
        ok(f"Civ symbol PNG OK ({png.stat().st_size} bytes)")


def main() -> int:
    print("=" * 60)
    print("Ukraine Historical Continuity — offline test suite")
    print("=" * 60)
    print()
    print("NOTE: Civilization VII is not installed here.")
    print("      These tests catch structural/crash-class issues only.")
    print("      Full verification still requires loading the mod in-game.")
    print()

    test_modinfo()
    test_visual_remaps()
    test_gameeffects_and_traits()
    test_shared_civ_integrity()
    test_unit_replaces()
    test_loc_coverage()
    test_png_asset()

    print("--- PASS ---")
    for msg in PASSES:
        print(f"  ✓ {msg}")
    if WARNINGS:
        print("--- WARN ---")
        for msg in WARNINGS:
            print(f"  ! {msg}")
    if ERRORS:
        print("--- FAIL ---")
        for msg in ERRORS:
            print(f"  ✗ {msg}")
        print()
        print(f"FAILED: {len(ERRORS)} error(s), {len(WARNINGS)} warning(s), {len(PASSES)} checks passed")
        return 1

    print()
    print(f"OK: {len(PASSES)} checks passed, {len(WARNINGS)} warning(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
