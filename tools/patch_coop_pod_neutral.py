#!/usr/bin/env python3
"""0.2.19 -> 0.2.20: co-op drop-pod model and civilian/support neutrality."""
import argparse
import copy
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

MAP = "TRaynor02.SC2Map/"
POD_PATH = r"Assets\Effects\Zerg\ZergDropPod_AC\ZergDropPod_AC.m3"


def patch_models(data):
    bom = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    text = data.decode("utf-8-sig")
    pattern = r'<CModel\b[^>]*\bid="ZergDropPod"[^>]*>.*?</CModel>'
    matches = list(re.finditer(pattern, text, re.S))
    if len(matches) != 1:
        raise ValueError("Expected exactly one ZergDropPod definition")
    old = ET.fromstring(matches[0][0])
    if old.find("Model").get("value") != r"Assets\Effects\Zerg\ZergDropPodEx1\ZergDropPodEx1.m3":
        raise ValueError("Unexpected original drop-pod model")
    # Match the starcoop ZergDropPod override, including removal of the two
    # campaign model sound events. Do not import unrelated damage effects.
    new = ET.Element("CModel", id="ZergDropPod")
    ET.SubElement(new, "Model", value=POD_PATH)
    ET.SubElement(new, "Events", index="0", removed="1")
    ET.SubElement(new, "Events", index="1", removed="1")
    match = matches[0]
    result = text[:match.start()] + ET.tostring(new, encoding="unicode") + text[match.end():]
    ET.fromstring(result)
    return bom + result.encode("utf-8")


def patch_script(data):
    anchor = b'    libNtve_gf_SetAlliance(4,9,libNtve_ge_AllianceSetting_Neutral);'
    if data.count(anchor) != 1:
        raise ValueError("Expected one support-alliance initialization anchor")
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    lines = [b"    // Civilians (3) and allied support (8/9) must be mutually neutral."]
    for a, b in ((3, 8), (8, 3), (3, 9), (9, 3)):
        line = f"    libNtve_gf_SetAlliance({a},{b},libNtve_ge_AllianceSetting_Neutral);".encode()
        if line in data:
            raise ValueError("Civilian/support neutrality already patched")
        lines.append(line)
    return data.replace(anchor, anchor + nl + nl.join(lines), 1)


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
        if meta.splitlines().count(b"version=0.2.19") != 1:
            raise ValueError("Expected version 0.2.19")
        replacements = {
            "metadata.txt": meta.replace(b"version=0.2.19", b"version=0.2.20", 1),
            MAP + "mapscript.galaxy": patch_script(z.read(MAP + "mapscript.galaxy")),
            MAP + "base.sc2data/gamedata/modeldata.xml": patch_models(z.read(MAP + "base.sc2data/gamedata/modeldata.xml")),
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
