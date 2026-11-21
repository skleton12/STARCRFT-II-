#!/usr/bin/env python3
"""0.6.52 -> 0.6.53 (user 2026-11-21 "멀티샷 한번만 업글 가능하게", "왜 아주어려움 거 공방이 2/2").

1. Multishot (RM6_Multishot, maps 3-6) could be researched again and again: the research button had no requirement
   and the upgrade no MaxLevel. Now MaxLevel 1 + button requirement RM6_MultishotLearn (hidden once queued/done),
   same pattern as RMC_EnduranceLearn.
2. Very Hard enemy upgrades showed 2/2: the mod's Very Hard +1 over the original levels (0.6.13, gf_rmVHAdd /
   gv_rmVeryHardExtraLevels) stacked on the original Very Hard level-1 grants. Removed in all mission maps
   (constant 0, gf_rmVHAdd returns at once). Original mission upgrades (start grants, timed upgrades) stay.

Usage: python3 tools/build_v0653.py <0.6.52 zip> <new output zip>
"""
import argparse, copy, re, zipfile, xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.52', b'version=0.6.53'
ALL = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
MS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
G = '.SC2Map/base.sc2data/gamedata/'
REQ = b'<CRequirement id="RM6_MultishotLearn"><NodeArray index="Show" Link="RM6_MultishotShow" /></CRequirement>'
NODES = (b'<CRequirementCountUpgrade id="RM6_MultishotQueued"><Count Link="RM6_Multishot" State="QueuedOrBetter" />'
         b'</CRequirementCountUpgrade><CRequirementNot id="RM6_MultishotNotQueued"><OperandArray index="0" '
         b'value="RM6_MultishotQueued" /></CRequirementNot><CRequirementAnd id="RM6_MultishotShow"><OperandArray '
         b'value="RM6_MultishotNotQueued" /></CRequirementAnd>')


def once(data, a, b, what):
    assert data.count(a) == 1, (what, data.count(a))
    return data.replace(a, b)


def end_insert(data, add, what):
    i = data.rindex(b'</Catalog>')
    assert data[i:].strip() == b'</Catalog>', what
    return data[:i] + add + data[i:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in ALL:
            k = m + '.SC2Map/mapscript.galaxy'; s = files[k]
            s = once(s, b'const int gv_rmVeryHardExtraLevels = 1;',
                     b'const int gv_rmVeryHardExtraLevels = 0; // 0.6.53: Very Hard +1 removed (user "\xec\x95\x84\xec\xa3\xbc\xec\x96\xb4\xeb\xa0\xa4\xec\x9b\x80 \xea\xb3\xb5\xeb\xb0\xa9 2/2")', m)
            s = once(s, b'if (libNtve_gf_DifficultyValueInt(0,0,0,1)==0 || gv_rmVHLines[p]>=8) { return; }',
                     b'if (gv_rmVeryHardExtraLevels<=0 || libNtve_gf_DifficultyValueInt(0,0,0,1)==0 || gv_rmVHLines[p]>=8) { return; }', m)
            files[k] = s; changed.add(k)
        for m in MS:
            k = m + G + 'upgradedata.xml'; s = files[k]
            s = once(s, b'<CUpgrade id="RM6_Multishot"><Race value="Terr" />',
                     b'<CUpgrade id="RM6_Multishot"><Race value="Terr" /><MaxLevel value="1" />', m) \
                if b'<CUpgrade id="RM6_Multishot"><Race value="Terr" />' in s else \
                re.sub(rb'(<CUpgrade id="RM6_Multishot">\s*<Race value="Terr" />)', rb'\1<MaxLevel value="1" />', s, count=1)
            assert s.count(b'<MaxLevel value="1" />') >= 1 and b'RM6_Multishot"><Race value="Terr" /><MaxLevel' in s or re.search(rb'RM6_Multishot">\s*<Race value="Terr" /><MaxLevel value="1" />', s), m
            files[k] = s; changed.add(k)
            k = m + G + 'abildata.xml'
            files[k] = once(files[k], b'<Button DefaultButtonFace="RM6_Multishot" State="Available" />',
                            b'<Button DefaultButtonFace="RM6_Multishot" State="Available" Requirements="RM6_MultishotLearn" />', m)
            changed.add(k)
            k = m + G + 'requirementdata.xml'; files[k] = end_insert(files[k], REQ, m); changed.add(k)
            k = m + G + 'requirementnodedata.xml'; files[k] = end_insert(files[k], NODES, m); changed.add(k)
        for k in changed:
            if k.endswith('.xml'): E.fromstring(files[k])
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
