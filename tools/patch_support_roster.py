#!/usr/bin/env python3
"""Build 0.2.21 from 0.2.20: continuous combined support, energizer, reconstruction."""
import argparse
import copy
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile
from patch_continuous_support import patch_script as continuous

MAP = "TRaynor02.SC2Map/"


def replace_once(data, old, new):
    if data.count(old) != 1:
        raise ValueError(f"Unexpected source marker: {old[:90]!r}")
    return data.replace(old, new, 1)


def patch_script(data):
    data = continuous(data)
    data = replace_once(data, b"// Every arrival: 4 zealots, 3 zealots, 1 stalker.",
                        b"// Every arrival: 4+4 sentinels, 2 instigators, 1 energizer.")
    data = replace_once(data, b"    rounds=2;", b"    rounds=3;")
    data = replace_once(data, b"else if (i==0) { wanted=4; }", b"else if (i<2) { wanted=4; }")
    data = replace_once(data, b"else { wanted=3; }", b"else { wanted=2; }")
    data = replace_once(data, b"68.5+1.0*i", b"67.5+1.0*i")
    data = replace_once(data,
        b'if (i==rounds) { UnitCreate(1,"StalkerPurifier",0,8,at[k],270.0); }',
        b'if (i==rounds) { UnitCreate(1,"RM21_Energizer",0,8,at[k],270.0); } '
        b'else if (i==rounds-1) { UnitCreate(1,"StalkerPurifier",0,8,at[k],270.0); }')
    anchor = b'    TechTreeUpgradeAddLevel(8,"Charge",1);'
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    data = replace_once(data, anchor, anchor + nl + b'    TechTreeUpgradeAddLevel(8,"ZealotResearchReconstruction",1);')
    return data


def update_entry(data, ident, change):
    text = data.decode("utf-8")
    pattern = rf'<([A-Za-z0-9_]+)\b[^>]*\bid="{re.escape(ident)}"[^>]*>.*?</\1>'
    matches = list(re.finditer(pattern, text, re.S))
    if len(matches) != 1:
        raise ValueError(f"Expected one definition: {ident}")
    m = matches[0]
    el = ET.fromstring(m[0])
    change(el)
    return (text[:m.start()] + ET.tostring(el, encoding="unicode") + text[m.end():]).encode("utf-8")


def revive_unit(el):
    found = False
    for b in el.findall("BehaviorArray"):
        if b.get("index") == "0" and b.get("Link") == "":
            b.set("Link", "ZealotPurifierRevive")
            found = True
    if not found:
        raise ValueError("Expected cleared sentinel reconstruction behavior")
    for layout in el.findall("CardLayouts"):
        for b in list(layout):
            if b.get("Face") == "ReconstructionLocked" or b.get("Requirements") == "ZealotPurifierReviveKaraxHide":
                layout.remove(b)


def revive_cooldown(el):
    for ch in list(el):
        if ch.tag in ("InitialEffect", "ExpireEffect"):
            el.remove(ch)
    ET.SubElement(el, "InitialEffect", value="ZealotPurifierReviveRemoveBehavior")
    ET.SubElement(el, "ExpireEffect", value="ZealotPurifierReviveApplyBehavior")


def revive_order(el):
    for ch in list(el):
        if ch.tag == "PreloadValidatorArray" and ch.get("value") == "KaraxCommanderActive":
            el.remove(ch)


def append_catalog(data, snippets):
    text = data.decode("utf-8")
    root = ET.fromstring(text)
    known = {el.get("id") for el in root}
    for s in snippets:
        el = ET.fromstring(s)
        if el.get("id") in known:
            raise ValueError(f"Catalog collision: {el.get('id')}")
        known.add(el.get("id"))
    if text.count("</Catalog>") != 1:
        raise ValueError("Expected a single catalog")
    nl = "\r\n" if "\r\n" in text else "\n"
    return text.replace("</Catalog>", nl.join(snippets) + nl + "</Catalog>").encode("utf-8")


def strings(data, entries, korean):
    text = data.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    for key, value in entries.items():
        v = value["en"]
        if korean and value["ko"] != v:
            v = value["ko"] + " /// " + v
        line = key + "=" + v
        pattern = re.compile(r"^" + re.escape(key) + r"=[^\r\n]*", re.M)
        if pattern.search(text):
            text = pattern.sub(lambda _: line, text)
        else:
            if not text.endswith(("\n", "\r")):
                text += nl
            text += line + nl
    return text.encode("utf-8")


def build(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError("Use a new output path")
    payload = json.loads((Path(__file__).parent / "data/support_energizer.json").read_text())
    with zipfile.ZipFile(source) as z:
        if z.testzip() or len(z.namelist()) != len(set(z.namelist())):
            raise ValueError("Input integrity failed")
        meta = z.read("metadata.txt")
        if meta.splitlines().count(b"version=0.2.20") != 1:
            raise ValueError("Expected version 0.2.20")
        replacements = {
            "metadata.txt": meta.replace(b"version=0.2.20", b"version=0.2.21", 1),
            MAP + "mapscript.galaxy": patch_script(z.read(MAP + "mapscript.galaxy")),
        }
        gd = MAP + "base.sc2data/gamedata/"
        replacements[gd + "unitdata.xml"] = update_entry(z.read(gd + "unitdata.xml"), "ZealotPurifier", revive_unit)
        replacements[gd + "behaviordata.xml"] = update_entry(z.read(gd + "behaviordata.xml"), "ZealotPurifierReviveSupressed", revive_cooldown)
        replacements[gd + "effectdata.xml"] = update_entry(z.read(gd + "effectdata.xml"), "ZealotPurifierReviveDeadIssueOrder", revive_order)
        for fn, snippets in payload["catalogs"].items():
            name = gd + fn
            data = replacements.get(name)
            if data is None:
                data = z.read(name) if name in z.namelist() else b'<?xml version="1.0" encoding="utf-8"?><Catalog></Catalog>'
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
