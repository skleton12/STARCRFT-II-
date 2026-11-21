#!/usr/bin/env python3
"""0.6.37 -> 0.6.38: mission 1 (TRaynor01) late enemies (user 2026-11-21).

"1번 미션에 불곰과 화염 방사병 중후반에 나오게, 1~3단계 업그레이드가 아닌 해병·불곰·화염방사병 업그레이드 조금 된 걸로".
- The final-objective defenders by the Dominion HQ (gf_rm_SpawnLateDefenders, already marines 9 + firebats 4) get
  marauders 2/3/3/4 by difficulty (trial values). Same stuck-spawn cleanup (gf_rmDropStuck).
- Dominion (player 2 only) gets unit upgrades, not weapon/armor levels: combat shield (marine life +10),
  marauder life +25, firebat armor +2 (Liberty campaign upgrades CombatShield, MarauderLifeBoost,
  FirebatJuggernautPlating). Only the missing level is added (no stacking). Raynor and allies are untouched.

Usage: python3 tools/build_v0638.py <0.6.37 zip> <new output zip>
"""
import argparse, copy, tempfile, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.37', b'version=0.6.38'
MAP = 'TRaynor01.SC2Map/mapscript.galaxy'
MARAUDERS = (2, 3, 3, 4)
UPGRADES = ('CombatShield', 'MarauderLifeBoost', 'FirebatJuggernautPlating')

A_OLD = '''    UnitCreate(2, "Firebat", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, 3.0, -6.0), 90.0);
    gf_rmDropStuck(UnitLastCreatedGroup());
}
'''
A_NEW = A_OLD[:-2] + '''    // 0.6.38 (user 2026-11-21): marauders join the final defenders (trial values by difficulty).
    UnitCreate(libNtve_gf_DifficultyValueInt(%d,%d,%d,%d), "Marauder", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, 0.0, -5.0), 90.0);
    gf_rmDropStuck(UnitLastCreatedGroup());
}
''' % MARAUDERS

B_OLD = '''        TechTreeUpgradeAddLevel(gv_p2_DOMINION_RED, "TerranInfantryArmorsLevel1", 1 - TechTreeUpgradeCount(gv_p2_DOMINION_RED, "TerranInfantryArmorsLevel1", c_techCountCompleteOnly));
    }
}
'''
B_NEW = B_OLD[:-2] + '    // 0.6.38: unit upgrades instead of levels (combat shield, marauder life, firebat armor).\n' + ''.join(
    f'    if (TechTreeUpgradeCount(gv_p2_DOMINION_RED, "{u}", c_techCountCompleteOnly) < 1) {{ TechTreeUpgradeAddLevel(gv_p2_DOMINION_RED, "{u}", 1); }}\n'
    for u in UPGRADES) + '}\n'


def once(t, old, new):
    assert t.count(old) == 1, old[:60]
    return t.replace(old, new)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        root = Path(tmp)
        prev.extractall(tmp)
        p = root / MAP
        raw = p.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in raw else '\n'
        t = once(raw.replace('\r\n', '\n'), A_OLD, A_NEW)
        t = once(t, B_OLD, B_NEW)
        p.write_bytes(t.replace('\n', nl).encode('utf-8'))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        changed = {'metadata.txt', MAP}
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in infos:
                    z.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == names
                for n in names:
                    if n not in changed: assert z.read(n) == prev.read(n), n
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
