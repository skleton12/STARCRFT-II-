#!/usr/bin/env python3
"""Patch a 0.2.17 CCM into 0.2.18 with simultaneous 4/3/1 first-wave batches."""
import argparse
import copy
from pathlib import Path
import zipfile

ENTRY = "TRaynor02.SC2Map/mapscript.galaxy"
START = "bool gt_os_Warp_Func (bool testConds,bool runActions) {"
END = "    // Keep new arrivals near the pylon until this wave has assembled."
PREFIX = '''bool gt_os_Warp_Func (bool testConds,bool runActions) {
    int rounds;
    int i;
    int k;
    int wanted;
    int available;
    actor[4] fx;
    point[4] at;
    unit u;
    int j;
    bool gathered;
    int waited;
    if (!runActions) { return true; }
    // First arrival: 4 zealots, 3 zealots, 1 stalker. Later: 2 zealots, 1 stalker.
    if (gv_os_firstWarp) { rounds=2; } else { rounds=1; }
    for (i=0;i<=rounds;i+=1) {
        if (gv_gameOver || !UnitIsAlive(gv_os_pylon)) { break; }
        if (i==rounds) { wanted=1; }
        else if (gv_os_firstWarp && i==0) { wanted=4; }
        else if (gv_os_firstWarp) { wanted=3; }
        else { wanted=2; }
        available=20-UnitGroupCount(gf_os_Army(8),c_unitCountAlive);
        if (available<=0) { break; }
        if (wanted>available) { wanted=available; }
        // Place the whole batch's warp effects before the single shared delay.
        for (k=0;k<wanted;k+=1) {
            at[k]=Point(85.0+(k-(wanted-1)*0.5)*2.0,68.5+1.0*i);
            fx[k]=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at[k]);
            ActorSend(fx[k],"AnimPlay Warp Birth NonLooping");
        }
        Wait(1.0,c_timeGame);
        // No waits in this loop: all units in this batch spawn in the same tick.
        for (k=0;k<wanted;k+=1) {
            // Recheck after the delay in case the army size or pylon changed.
            if (!gv_gameOver && UnitIsAlive(gv_os_pylon) && UnitGroupCount(gf_os_Army(8),c_unitCountAlive)<20) {
                if (i==rounds) { UnitCreate(1,"StalkerPurifier",0,8,at[k],270.0); }
                else { UnitCreate(1,"ZealotPurifier",0,8,at[k],270.0); }
                u=UnitLastCreated();
                UnitGroupAdd(gv_os_pending,u);
                UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("move",0),Point(85.0,71.0)),c_orderQueueReplace);
            }
            ActorSend(fx[k],"Destroy");
        }
        Wait(1.0,c_timeGame);
    }
'''


def patch_script(data):
    bom = b"\xef\xbb\xbf" if data.startswith(b"\xef\xbb\xbf") else b""
    text = data.decode("utf-8-sig")
    nl = "\r\n" if "\r\n" in text else "\n"
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("Unexpected warp function markers")
    start = text.index(START)
    end = text.index(END, start)
    old = text[start:end].replace("\r\n", "\n")
    if 'if (gv_os_firstWarp) { rounds=3; } else { rounds=1; }' not in old:
        raise ValueError("Expected original 0.2.17 sequential warp")
    if old.count('UnitCreate(1,"StalkerPurifier"') != 1 or old.count('UnitCreate(1,"ZealotPurifier"') != 1:
        raise ValueError("Unexpected source unit creation")
    return bom + (text[:start] + PREFIX.replace("\n", nl) + text[end:]).encode("utf-8")


def build(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError("Use a new output path; never overwrite the input")
    with zipfile.ZipFile(source) as z:
        if z.testzip():
            raise ValueError("Input CRC failed")
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive members")
        meta = z.read("metadata.txt")
        if meta.splitlines().count(b"version=0.2.17") != 1:
            raise ValueError("Expected 0.2.17 input")
        script = patch_script(z.read(ENTRY))
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, "x") as out:
                for info in z.infolist():
                    data = z.read(info.filename)
                    if info.filename == "metadata.txt":
                        data = meta.replace(b"version=0.2.17", b"version=0.2.18", 1)
                    elif info.filename == ENTRY:
                        data = script
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                if out.testzip() or out.namelist() != names:
                    raise ValueError("Output integrity failed")
                changed = {n for n in names if z.read(n) != out.read(n)}
                if changed != {"metadata.txt", ENTRY}:
                    raise ValueError(f"Unexpected changes: {changed}")
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
