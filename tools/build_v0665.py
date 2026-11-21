#!/usr/bin/env python3
"""0.6.64 -> 0.6.65 (user 2026-11-21 "아그리아 가스쪽 문제", "정제소 일반가스 가스 1개").

Mission 6 (THanson01, Agria): Raynor's base had one rich geyser and one pre-built normal Refinery (Id 107, player 4
colonists, handed to Raynor with the base). Make that refinery a RefineryRich (same position and reserve 5720), and add
"RefineryRich" to the original hand-over list so it still passes to Raynor. Nothing else changes. Game not run.

Usage: python3 tools/build_v0665.py <0.6.64 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.64', b'version=0.6.65'
OBJ = 'THanson01.SC2Map/objects'
SCR = 'THanson01.SC2Map/mapscript.galaxy'
HAND = b'(UnitGetType(autoEAEE2387_var) == "Refinery") || '
HAND_NEW = HAND + b'(UnitGetType(autoEAEE2387_var) == "RefineryRich") || '


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        o = files[OBJ]
        o, n = re.subn(rb'(<ObjectUnit Id="107" Position="26\.5,44\.5,0"[^>]*UnitType=")Refinery(")', rb'\1RefineryRich\2', o)
        assert n == 1; E.fromstring(o); files[OBJ] = o
        s = files[SCR]; assert s.count(HAND) == 1; files[SCR] = s.replace(HAND, HAND_NEW)
        changed = {'metadata.txt', OBJ, SCR}
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
