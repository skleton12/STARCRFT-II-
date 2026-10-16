#!/usr/bin/env python3
"""0.2.21 -> 0.2.22: use actual Dehaka co-op trained units in repeated drops."""
import argparse
import copy
import json
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from patch_support_roster import append_catalog, strings, replace_once

MAP = "TRaynor02.SC2Map/"
SWAPS = {
    "PrimalZergling": "DehakaZerglingLevel2",
    "PrimalHydralisk": "DehakaHydraliskLevel2",
    "PrimalRoach": "DehakaRoachLevel2",
}


def patch_script(data):
    for old, new in SWAPS.items():
        data = replace_once(data, f'"{old}",0,9,Point(49.0,20.0),90.0)'.encode(),
                            f'"{new}",0,9,Point(49.0,20.0),90.0)'.encode())
    return data


def build(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError("Use a new output path")
    payload = json.loads((Path(__file__).parent / "data/dehaka_support.json").read_text())
    with zipfile.ZipFile(source) as z:
        if z.testzip() or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError("Input integrity failed")
        meta = z.read("metadata.txt")
        if meta.splitlines().count(b"version=0.2.21") != 1:
            raise ValueError("Expected version 0.2.21")
        replacements = {
            "metadata.txt": meta.replace(b"version=0.2.21", b"version=0.2.22", 1),
            MAP + "mapscript.galaxy": patch_script(z.read(MAP + "mapscript.galaxy")),
        }
        for fn, snippets in payload["catalogs"].items():
            name = MAP + "base.sc2data/gamedata/" + fn
            data = z.read(name) if name in z.namelist() else b'<Catalog></Catalog>'
            replacements[name] = append_catalog(data, snippets)
        for name in z.namelist():
            if name.startswith(MAP) and name.endswith("/localizeddata/gamestrings.txt"):
                replacements[name] = strings(z.read(name), payload["strings"], "/kokr.sc2data/" in name)
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, "x") as out:
                for info in z.infolist():
                    out.writestr(copy.copy(info), replacements.get(info.filename, z.read(info.filename)))
                for name, data in replacements.items():
                    if name not in z.namelist():
                        out.writestr(name, data, compress_type=zipfile.ZIP_DEFLATED)
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
