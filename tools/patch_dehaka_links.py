#!/usr/bin/env python3
"""0.2.22 -> 0.2.23: repair confirmed missing Dehaka presentation references.

This repairs catalog defects, not a verified diagnosis of the reported load crash.
"""
import argparse
import copy
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from patch_support_roster import append_catalog, update_entry

GD = "TRaynor02.SC2Map/base.sc2data/gamedata/"
IMPACT = r'''<CModel id="DehakaRoachMissileImpact" parent="ImpactFX"><Model value="Assets\Effects\Zerg\RoachMissileImpactEx1\RoachMissileImpactEx1.m3"/><EditorCategories value="Race:Zerg"/></CModel>'''


def fix_roach(el):
    for node in el.iter():
        if node.get("VoiceLink") == "RoachPrimal_Death":
            # The normal explosion sound remains; the unavailable extra voice
            # record is not part of the map's declared dependency catalogs.
            del node.attrib["VoiceLink"]


def fix_hydralisk(el):
    for parent in el.iter():
        for node in list(parent):
            if node.tag == "AbilSoundArray" and node.get("AbilCmd", "").startswith("PrimalHydraliskToMutalisk,"):
                parent.remove(node)


def build(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError("Use a new output path")
    with zipfile.ZipFile(source) as z:
        if z.testzip():
            raise ValueError("Input CRC failed")
        meta = z.read("metadata.txt")
        if meta.splitlines().count(b"version=0.2.22") != 1:
            raise ValueError("Expected version 0.2.22")
        actors = update_entry(z.read(GD + "actordata.xml"), "DehakaRoachLevel2", fix_roach)
        actors = update_entry(actors, "DehakaHydraliskLevel2", fix_hydralisk)
        replacements = {
            "metadata.txt": meta.replace(b"version=0.2.22", b"version=0.2.23", 1),
            GD + "actordata.xml": actors,
            GD + "modeldata.xml": append_catalog(z.read(GD + "modeldata.xml"), [IMPACT]),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, "x") as out:
                for info in z.infolist():
                    out.writestr(copy.copy(info), replacements.get(info.filename, z.read(info.filename)))
            with zipfile.ZipFile(output) as out:
                if out.testzip():
                    raise ValueError("Output CRC failed")
                for name in out.namelist():
                    if name.endswith(".xml"):
                        ET.fromstring(out.read(name))
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
