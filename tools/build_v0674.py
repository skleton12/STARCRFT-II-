#!/usr/bin/env python3
"""0.6.73 -> 0.6.74 (user 2026-11-22 "가스 1개가 풍부하지 않는군", "방패 2단계 업그레이드 무기고 업글시 사라짐").

Combat Shield Level 2 (RM6_ShieldSplash, maps 3-7): its button needed RM6_ShieldDone = mod research RM3_Shield
complete. A Hyperion armory Combat Shield purchase (CombatShield, gives War Pigs +10 life in the Liberty layer)
blocks the mod research, so level 2 never showed. RM6_ShieldDone is now RM3_Shield OR CombatShield complete, and
the level-1 button (RM3_ShieldLearn) is hidden once the armory shield is owned (it was disallowed anyway).
Also TTosh02 base resources: 0.6.70 scaled only the default reserve; the Hard/Brutal reserves (Index 3/4) now get
the same +20% (minerals) / x2 (gas) too.

Mission 7 (TTosh02, Bel'Shir): Raynor's base had one rich geyser and one pre-built normal Refinery (Id 97, player 1,
reserve doubled to 6200 by 0.6.70). Make that refinery a RefineryRich (same position and reserve), like 0.6.65 Agria.
The original script never names "Refinery" (only the mod eternal-resources code, which also covers RefineryRich). Game not run.

Usage: python3 tools/build_v0674.py <0.6.73 zip> <new output zip>
"""
import argparse, copy, math, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.73', b'version=0.6.74'
OBJ = 'TTosh02.SC2Map/objects'
MAPS = ('TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02')
DONE_OLD = b'<CRequirementCountUpgrade id="RM6_ShieldDone"><Count Link="RM3_Shield" State="CompleteOnly" /></CRequirementCountUpgrade>'
DONE_NEW = (b'<CRequirementCountUpgrade id="RM6_ShieldDoneMod"><Count Link="RM3_Shield" State="CompleteOnly" /></CRequirementCountUpgrade>'
            b'<CRequirementCountUpgrade id="RM6_ShieldDoneArm"><Count Link="CombatShield" State="CompleteOnly" /></CRequirementCountUpgrade>'
            b'<CRequirementOr id="RM6_ShieldDone"><OperandArray value="RM6_ShieldDoneMod" /><OperandArray value="RM6_ShieldDoneArm" /></CRequirementOr>'
            b'<CRequirementNot id="RM3_ShieldNoArmory"><OperandArray index="0" value="RM6_ShieldDoneArm" /></CRequirementNot>'
            b'<CRequirementAnd id="RM3_ShieldShow"><OperandArray value="RM3_ShieldNotQueued" /><OperandArray value="RM3_ShieldNoArmory" /></CRequirementAnd>')
LEARN_OLD = b'<NodeArray index="Show" Link="RM3_ShieldNotQueued" />\n    </CRequirement>'
LEARN_NEW = b'<NodeArray index="Show" Link="RM3_ShieldShow" />\n    </CRequirement>'


def base_difficulty_reserves(o):
    """0.6.70 scaled only the default reserve; scale the Hard/Brutal ones (Index 3/4) the same way."""
    cnt = [0, 0]
    def fix(m):
        b = m.group(0).decode()
        x, y = map(float, re.search(r'Position="([\d.]+),([\d.]+)', b).groups())
        ut = re.search(r'UnitType="(\w+)"', b).group(1)
        if math.hypot(x - 79.5, y - 25.5) > 16 or not re.search('Mineral|Geyser|Refinery', ut): return m.group(0)
        gas = 'Mineral' not in ut; cnt[gas] += 1
        return re.sub(r'(<Resources Index="[34]" Value=")(\d+)', lambda r: r.group(1) + str(int(r.group(2)) * 2 if gas else int(r.group(2)) * 120 // 100), b).encode()
    o = re.sub(rb'<ObjectUnit [^>]*?(?:/>|>.*?</ObjectUnit>)', fix, o, flags=re.S)
    return o, tuple(cnt)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        o, n = re.subn(rb'(<ObjectUnit Id="97" Position="77\.5,18\.5,0"[^>]*UnitType=")Refinery(" Player="1")',
                       rb'\1RefineryRich\2', files[OBJ])
        assert n == 1
        o, cnt = base_difficulty_reserves(o); assert cnt == (8, 2), cnt
        E.fromstring(o); files[OBJ] = o
        changed = {'metadata.txt', OBJ}
        for m in MAPS:
            nd, rq = f'{m}.SC2Map/base.sc2data/gamedata/requirementnodedata.xml', f'{m}.SC2Map/base.sc2data/gamedata/requirementdata.xml'
            t = files[nd]; assert t.count(DONE_OLD) == 1 and b'RM6_ShieldDoneArm' not in t
            t = t.replace(DONE_OLD, DONE_NEW); E.fromstring(t); files[nd] = t
            t = files[rq]; assert t.count(LEARN_OLD) == 1
            t = t.replace(LEARN_OLD, LEARN_NEW); E.fromstring(t); files[rq] = t
            changed |= {nd, rq}
        assert b'UnitGroup("RefineryRich", 1' in files['TTosh02.SC2Map/mapscript.galaxy']  # eternal resources covers it
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
