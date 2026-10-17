#!/usr/bin/env python3
"""0.2.18 -> 0.2.19: rich deposits and +20% contents for mission 2 player base.

Uses explicit audited placed-object IDs, not global resource type replacement.
Preserves per-difficulty deposit contents. Fractional contents round down.
"""
import argparse
import copy
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

MAP = "TRaynor02.SC2Map/"
MINERALS = {"2", "6", "20", "23", "24", "26", "27", "35", "308", "309"}
GAS = {"28"}
TARGETS = MINERALS | GAS


def patch_objects(data):
    bom = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    text = data.decode("utf-8-sig")
    seen = set()

    def replace(match):
        block = match[0]
        el = ET.fromstring(block)
        oid = el.get("Id")
        if oid not in TARGETS:
            return block
        if oid in seen:
            raise ValueError(f"Duplicate placed-object ID: {oid}")
        seen.add(oid)
        expected = "MineralField" if oid in MINERALS else "VespeneGeyser"
        if el.get("UnitType") != expected or el.get("Player", "0") != "0":
            raise ValueError(f"Unexpected original resource: {oid}")
        x, y, _ = map(float, el.get("Position").split(","))
        if not (74 <= x <= 87 and 22 <= y <= 33):
            raise ValueError(f"Resource outside audited player base: {oid}")
        if not el.get("Resources"):
            raise ValueError(f"Missing original contents: {oid}")
        block = block.replace(f'UnitType="{expected}"', f'UnitType="Rich{expected}"', 1)
        block = re.sub(r'\bResources="(\d+)"',
                       lambda m: f'Resources="{int(m[1]) * 6 // 5}"', block)
        # Difficulty-specific Resources overrides use Value, not Resources.
        block = re.sub(r'(<Resources\b[^>]*\bValue=")(\d+)(")',
                       lambda m: m[1] + str(int(m[2]) * 6 // 5) + m[3], block)
        return block

    result = re.sub(r'<ObjectUnit\b[^>]*?(?:/>|>.*?</ObjectUnit>)', replace, text, flags=re.S)
    if seen != TARGETS:
        raise ValueError(f"Missing expected resources: {TARGETS - seen}")
    ET.fromstring(result)
    return bom + result.encode("utf-8")


def patch_script(data):
    # The rich refinery is a distinct base-game unit. Let the existing tutorial
    # recognize it as a completed refinery too; leave economy code unchanged.
    original = b'UnitGroupCount(UnitGroup("Refinery", gv_pLAYER_01_USER, RegionEntireMap(), UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0), c_unitCountAlive)'
    if data.count(original) != 1:
        raise ValueError("Unexpected refinery tutorial condition")
    rich = original.replace(b'"Refinery"', b'"RefineryRich"')
    data = data.replace(original, b"(" + original + b" + " + rich + b")", 1)
    # Retain the starting-resource tutorial's field selection after type change.
    selection = b'UnitGroup("MineralField", 0, RegionFromId(30),'
    if data.count(selection) != 1:
        raise ValueError("Unexpected starting-mineral tutorial selection")
    return data.replace(selection, selection.replace(b'"MineralField"', b'"RichMineralField"'), 1)


def build(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError("Use a new output path")
    with zipfile.ZipFile(source) as z:
        if z.testzip():
            raise ValueError("Input CRC failed")
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP entries")
        meta = z.read("metadata.txt")
        if meta.splitlines().count(b"version=0.2.18") != 1:
            raise ValueError("Expected version 0.2.18")
        replacements = {
            "metadata.txt": meta.replace(b"version=0.2.18", b"version=0.2.19", 1),
            MAP + "objects": patch_objects(z.read(MAP + "objects")),
            MAP + "mapscript.galaxy": patch_script(z.read(MAP + "mapscript.galaxy")),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, "x") as out:
                for info in z.infolist():
                    out.writestr(copy.copy(info), replacements.get(info.filename, z.read(info.filename)))
            with zipfile.ZipFile(output) as out:
                if out.testzip() or names != out.namelist():
                    raise ValueError("Output integrity failed")
                if {n for n in names if z.read(n) != out.read(n)} != set(replacements):
                    raise ValueError("Unexpected changed entries")
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    print(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
