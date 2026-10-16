#!/usr/bin/env python3
"""0.2.20 -> 0.2.21: repeat the combined support rosters every wave."""
import argparse
import copy
from pathlib import Path
import zipfile

ENTRY = "TRaynor02.SC2Map/mapscript.galaxy"


def patch_script(data):
    nl = b"\r\n" if b"\r\n" in data else b"\n"

    def replace(old, new):
        nonlocal data
        old = old.replace("\n", nl.decode()).encode()
        new = new.replace("\n", nl.decode()).encode()
        if data.count(old) != 1:
            raise ValueError(f"Unexpected source marker: {old!r}")
        data = data.replace(old, new, 1)

    replace("bool gv_os_firstWarp;\n", "")
    replace("    gv_os_firstWarp=true;\n", "")
    replace("    gv_os_firstWarp=false;\n", "")
    replace("    // First arrival: 4 zealots, 3 zealots, 1 stalker. Later: 2 zealots, 1 stalker.\n"
            "    if (gv_os_firstWarp) { rounds=2; } else { rounds=1; }",
            "    // Every arrival: 4 zealots, 3 zealots, 1 stalker.\n"
            "    rounds=2;")
    replace("        else if (gv_os_firstWarp && i==0) { wanted=4; }\n"
            "        else if (gv_os_firstWarp) { wanted=3; }\n"
            "        else { wanted=2; }",
            "        else if (i==0) { wanted=4; }\n"
            "        else { wanted=3; }")
    replace("    actor pod;\n    bool first;", "    actor pod;")
    replace("    first=!gv_os_primal;\n", "")
    replace('''        if (first) {
            UnitCreate(6,"PrimalZergling",0,9,Point(49.0,20.0),90.0);
            UnitCreate(2,"DehakaRavasaur",0,9,Point(49.0,20.0),90.0);
        } else {
            UnitCreate(2,"PrimalHydralisk",0,9,Point(49.0,20.0),90.0);
            UnitCreate(2,"PrimalRoach",0,9,Point(49.0,20.0),90.0);
        }''', '''        // Every drop carries the combined initial and repeat support roster.
        UnitCreate(6,"PrimalZergling",0,9,Point(49.0,20.0),90.0);
        UnitCreate(2,"DehakaRavasaur",0,9,Point(49.0,20.0),90.0);
        UnitCreate(2,"PrimalHydralisk",0,9,Point(49.0,20.0),90.0);
        UnitCreate(2,"PrimalRoach",0,9,Point(49.0,20.0),90.0);''')
    return data


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
        if meta.splitlines().count(b"version=0.2.20") != 1:
            raise ValueError("Expected version 0.2.20")
        replacements = {
            "metadata.txt": meta.replace(b"version=0.2.20", b"version=0.2.21", 1),
            ENTRY: patch_script(z.read(ENTRY)),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, "x") as out:
                for info in z.infolist():
                    out.writestr(copy.copy(info), replacements.get(info.filename, z.read(info.filename)))
            with zipfile.ZipFile(output) as out:
                if out.testzip() or out.namelist() != names:
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
