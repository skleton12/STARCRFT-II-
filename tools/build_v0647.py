#!/usr/bin/env python3
"""0.6.46 -> 0.6.47 (user 2026-11-21 "병영에 붙어 있는 기술실·반응로를 기술 반응로로 바꿔 주고, 병영 1개·군수 공장 1개 추가해서
좀 더 많이 나오게").

Missions 1·2, enemy Terran, Hard and up (same range as 0.6.41~0.6.45).
- An enemy Barracks/Factory/Starport whose add-on is a plain Tech Lab or Reactor has that add-on removed and gets a
  Tech Reactor instead (instant for the enemy since 0.6.45), so the original add-ons become Tech Reactors at mission start.
- Mission 2 extra production by the Dominion main (0.6.40/0.6.44): 1 Barracks + 1 Factory (was 2 Barracks + 1 Factory);
  Very Hard places the set twice. They get Tech Reactors too. Bunkers unchanged.

Usage: python3 tools/build_v0647.py <0.6.46 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.46', b'version=0.6.47'
MAPS = ('TRaynor01', 'TRaynor02')
DECL_OLD = '''bool gt_rmAddon_Func (bool testConds, bool runActions) {
    int p;
    int i;
    unit u;
'''
DECL_NEW = DECL_OLD + '    unit c;\n'
LOOP_OLD = '''                k = UnitGetType(u);
                if ((k == "Barracks" || k == "Factory" || k == "Starport") && !UnitTestState(u, c_unitStateUnderConstruction)
                    && UnitAddOnChild(u, 0) == null && !UnitGroupHasUnit(gv_rmAddonTried, u)) {
'''
LOOP_NEW = '''                k = UnitGetType(u);
                c = UnitAddOnChild(u, 0);
                // 0.6.47: a plain Tech Lab / Reactor is replaced by a Tech Reactor (user 2026-11-21).
                if ((k == "Barracks" || k == "Factory" || k == "Starport") && c != null
                    && !StringContains(UnitGetType(c), "TechReactor", c_stringAnywhere, c_stringCase)) {
                    UnitRemove(c);
                    c = null;
                    UnitGroupRemove(gv_rmAddonTried, u);
                }
                if ((k == "Barracks" || k == "Factory" || k == "Starport") && !UnitTestState(u, c_unitStateUnderConstruction)
                    && c == null && !UnitGroupHasUnit(gv_rmAddonTried, u)) {
'''
SET_OLD = '        if (gf_rmVHBaseBuild(p,"Barracks",c)) { n += 1; }\n        if (gf_rmVHBaseBuild(p,"Barracks",c)) { n += 1; }\n'
SET_NEW = '        // 0.6.47: 1 Barracks + 1 Factory (user 2026-11-21).\n        if (gf_rmVHBaseBuild(p,"Barracks",c)) { n += 1; }\n'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            eds = [(DECL_OLD, DECL_NEW), (LOOP_OLD, LOOP_NEW)] + ([(SET_OLD, SET_NEW)] if m == 'TRaynor02' else [])
            for a, b in eds:
                assert t.count(a) == 1, (m, a[:60]); t = t.replace(a, b)
            files[p] = t.replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                changed = {'metadata.txt'} | {f'{m}.SC2Map/mapscript.galaxy' for m in MAPS}
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
