#!/usr/bin/env python3
"""Make a 0.2.17 test CCM from a supplied 0.2.16 CCM, without source/.

Uses the built-in Fenix purifier skin model paths, resolved from
SC2Mapster/SC2GameData's starcoop ModelData/SkinData and core Building tokens.
The M3/textures are client assets, not bundled or runtime-verified here.
Keep the normal Pylon actor: do not create a second unit or actor.
"""
import argparse
import copy
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile

MODEL_PATHS = {
    "Pylon": r"Assets\Buildings\Protoss\Pylon_Purifier_COOP\Pylon_Purifier_COOP.m3",
    "PylonBirth": r"Assets\Buildings\Protoss\Pylon_Purifier_WarpIn\Pylon_Purifier_WarpIn.m3",
    "PylonDeath": r"Assets\Buildings\Protoss\Pylon_Purifier_Coop_Death\Pylon_Purifier_Coop_Death.m3",
}
# The inherited Pylon actor can select these for Collector's Edition accounts.
MODEL_PATHS["PylonXPR"] = MODEL_PATHS["Pylon"]
MODEL_PATHS["PylonXPRDeath"] = MODEL_PATHS["PylonDeath"]
MODEL_ENTRY = "TRaynor02.SC2Map/base.sc2data/gamedata/modeldata.xml"
SCRIPT_ENTRY = "TRaynor02.SC2Map/mapscript.galaxy"


def patch_models(data):
    root = ET.fromstring(data)
    if root.tag != "Catalog":
        raise ValueError("Expected a ModelData Catalog")
    if any(el.get("id") in MODEL_PATHS for el in root):
        raise ValueError("Pylon model overrides already present; refusing to duplicate them")
    # Append text rather than serializing existing data: retain processing
    # instructions, token definitions, whitespace and all original elements.
    text = data.decode("utf-8")
    if text.count("</Catalog>") != 1:
        raise ValueError("Expected one Catalog closing tag")
    nl = "\r\n" if "\r\n" in text else "\n"
    entries = []
    for model_id, path in MODEL_PATHS.items():
        el = ET.Element("CModel", id=model_id)
        ET.SubElement(el, "Model", value=path)
        entries.append("    " + ET.tostring(el, encoding="unicode"))
    result = text.replace("</Catalog>", nl.join(entries) + nl + "</Catalog>")
    ET.fromstring(result)
    return result.encode("utf-8")


def build(source, output):
    if source.resolve() == output.resolve():
        raise ValueError("Input and output must differ")
    if output.exists():
        raise FileExistsError(output)
    with zipfile.ZipFile(source) as z:
        bad = z.testzip()
        if bad:
            raise ValueError(f"Input CRC failed: {bad}")
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive entries")
        meta = z.read("metadata.txt")
        if meta.splitlines().count(b"version=0.2.16") != 1:
            raise ValueError("Expected version 0.2.16")
        g = z.read(SCRIPT_ENTRY)
        if g.count(b'UnitCreate(1,"Pylon",c_unitCreateConstruct,8,Point(85.0,73.0),270.0);') != 1:
            raise ValueError("Unexpected support pylon creation code")
        objects = ET.fromstring(z.read("TRaynor02.SC2Map/objects"))
        if any(el.get("UnitType", "").startswith("Pylon") for el in objects.iter()):
            raise ValueError("Preplaced Pylon found: review the scope of model overrides")
        model_data = patch_models(z.read(MODEL_ENTRY))
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as out:
                for info in z.infolist():
                    data = z.read(info.filename)
                    if info.filename == "metadata.txt":
                        data = meta.replace(b"version=0.2.16", b"version=0.2.17", 1)
                    elif info.filename == MODEL_ENTRY:
                        data = model_data
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                if out.testzip():
                    raise ValueError("Output CRC failed")
                changed = [n for n in names if z.read(n) != out.read(n)]
                if set(changed) != {"metadata.txt", MODEL_ENTRY}:
                    raise ValueError(f"Unexpected changes: {changed}")
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    print(f"Created test build: {output}")
    print("Changed only metadata version and mission 2 Pylon model overrides.")
    print("Requires game verification: built-in M3/texture resolution and animations.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
