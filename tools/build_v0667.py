#!/usr/bin/env python3
"""0.6.66 -> 0.6.67 (user 2026-11-22 "미네랄 가스 차는거 가스는 최대 5만 광물은 1만으로").

Maps 3-6, Inexhaustible Resources (RM6_EternalRes): fields now regrow up to a fixed cap instead of their starting
amount - mineral fields 10000, Raynor's refineries 50000 (constants gv_rmEternalCapMin/Gas). Per-second regen by level
(2/3/4), the 100 floor and everything else unchanged. Tooltips updated. Game not run.

Usage: python3 tools/build_v0667.py <0.6.66 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO

OLD, NEW = b'version=0.6.66', b'version=0.6.67'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
CAP_MIN, CAP_GAS = 10000, 50000
FN_OLD = '''void gf_rmEternalField (unit u) {
    int cur = UnitGetPropertyInt(u, c_unitPropResources, c_unitPropCurrent);
    int top = FixedToInt(UnitGetCustomValue(u, 7));
    if (cur <= 0 && top <= 0) { return; }
    if (cur > top) { top = cur; UnitSetCustomValue(u, 7, IntToFixed(top)); }
    if (cur < 100) { cur = 100; }
    else if (cur < top) { cur = MinI(top, cur + gv_rmEternalStep); }
    UnitSetPropertyInt(u, c_unitPropResources, cur);
}
'''
FN_NEW = f'''// 0.6.67 (user 2026-11-22): regrow up to a fixed cap - minerals 10000, refinery gas 50000.
const int gv_rmEternalCapMin = {CAP_MIN};
const int gv_rmEternalCapGas = {CAP_GAS};
void gf_rmEternalField (unit u) {{
    int cur = UnitGetPropertyInt(u, c_unitPropResources, c_unitPropCurrent);
    int top = gv_rmEternalCapMin;
    if (StringFind(UnitGetType(u), "Refinery", c_stringNoCase) != c_stringNotFound) {{ top = gv_rmEternalCapGas; }}
    if (cur < 100) {{ cur = 100; }}
    else if (cur < top) {{ cur = MinI(top, cur + gv_rmEternalStep); }}
    else {{ return; }}
    UnitSetPropertyInt(u, c_unitPropResources, cur);
}}
'''
STR = {'Button/Tooltip/RM6_EternalRes': '단계마다 사령부 근처 광물과 레이너 정제소 가스가 고갈되지 않고 다시 찹니다 (광물 최대 10000, 가스 최대 50000). 지대 하나당 초당 재생: 1단계 2, 2단계 3, 3단계 4 (최대 3단계). /// Each level: minerals near your Command Centers and vespene in your Refineries no longer run out and regenerate (minerals up to 10000, vespene up to 50000). Regeneration per field per second: Level 1 2, Level 2 3, Level 3 4 (max 3 levels).'}
for n, r in ((1, 2), (2, 3), (3, 4)):
    STR[f'Behavior/Tooltip/RM6_EternalShow{n}'] = (f'이 근처 광물·가스는 고갈되지 않고 초당 {r}씩 다시 찹니다 (광물 최대 10000, 가스 최대 50000). '
                                                f'/// Resources here never run out and regrow {r} per second (minerals up to 10000, vespene up to 50000).')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'; t = raw.replace('\r\n', '\n')
            assert t.count(FN_OLD) == 1, m
            files[p] = t.replace(FN_OLD, FN_NEW).replace('\n', nl).encode('utf-8'); changed.add(p)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], STR); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
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
