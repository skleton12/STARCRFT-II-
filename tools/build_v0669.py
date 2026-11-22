#!/usr/bin/env python3
"""0.6.68 -> 0.6.69 (user 2026-11-22 "광물은 2로 하고 가스만 3으로 해주고 파수병 공업 안먹히는것같은제 확인좀").

Maps 3-6:
- Inexhaustible Resources: minerals regrow +2 / +4 / +6 per field every 0.5 s by level, refinery gas keeps
  +3 / +6 / +9. Caps and the 100 floor unchanged. Tooltips updated.
- Legionnaire (ZealotPurifier) weapon upgrade: the allies are given ProtossGroundWeaponsLevel1-3, but the
  Legionnaire entries (Effect LegionnairePsiBlades Amount +2, Weapon RM_LegionnairePsiBlades Level +1) only sat in the
  map override of the parent ProtossGroundWeapons. Moved into each Level upgrade (with the level icon) and the parent
  override removed, so the bonus counts exactly once whether or not the parent is inherited.
- Map 3 armor levels also get Unit,ZealotPurifier,LifeArmorLevel and the actor armor icon (maps 4-6 already had them).
Game not run.

Usage: python3 tools/build_v0669.py <0.6.68 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO

OLD, NEW = b'version=0.6.68', b'version=0.6.69'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
UP = 'base.sc2data/gamedata/upgradedata.xml'
PARENT = ('<CUpgrade id="ProtossGroundWeapons"><EffectArray Reference="Effect,LegionnairePsiBlades,Amount" Value="2" />'
          '<EffectArray Reference="Weapon,RM_LegionnairePsiBlades,Level" Value="1" /></CUpgrade>')
SUBS = [('int gv_rmEternalStep = 1;\n',
         'int gv_rmEternalStep = 1;\n'
         '// 0.6.69 (user 2026-11-22): minerals regrow 2 per level per tick, refinery gas keeps 3 per level.\n'
         'int gv_rmEternalStepMin = 2;\n'),
        ('    else if (cur < top) { cur = MinI(top, cur + gv_rmEternalStep); }\n',
         '    else if (cur < top) {\n'
         '        if (top == gv_rmEternalCapGas) { cur = MinI(top, cur + gv_rmEternalStep); }\n'
         '        else { cur = MinI(top, cur + gv_rmEternalStepMin); }\n'
         '    }\n'),
        ('    gv_rmEternalTick = (gv_rmEternalTick + 1) % 4;\n',
         '    gv_rmEternalTick = (gv_rmEternalTick + 1) % 4;\n'
         '    gv_rmEternalStepMin = 2 * lv;\n')]
CAP = '(광물 최대 10000, 가스 최대 50000)'
CAP_EN = '(minerals up to 10000, vespene up to 50000)'
STR = {'Button/Tooltip/RM6_EternalRes': f'단계마다 사령부 근처 광물과 레이너 정제소 가스가 고갈되지 않고 다시 찹니다 {CAP}. 지대 하나당 0.5초마다 재생: 광물 1단계 2·2단계 4·3단계 6, 가스 1단계 3·2단계 6·3단계 9 (최대 3단계). /// Each level: minerals near your Command Centers and vespene in your Refineries no longer run out and regenerate {CAP_EN}. Regeneration per field every 0.5 s: minerals Level 1 2, Level 2 4, Level 3 6; vespene Level 1 3, Level 2 6, Level 3 9 (max 3 levels).'}
for n in (1, 2, 3):
    STR[f'Behavior/Tooltip/RM6_EternalShow{n}'] = (f'이 근처 광물·가스는 고갈되지 않고 0.5초마다 광물 {2*n}, 가스 {3*n}씩 다시 찹니다 {CAP}. '
                                                f'/// Resources here never run out and regrow every 0.5 s: minerals {2*n}, vespene {3*n} {CAP_EN}.')


def patch_upgrades(m, t):
    assert t.count(PARENT) == 1, m
    t = t.replace(PARENT, '')
    for n in (1, 2, 3):
        head = f'<CUpgrade id="ProtossGroundWeaponsLevel{n}">'
        assert t.count(head) == 1, (m, n)
        s = t.index(head); e = t.index('</CUpgrade>', s)
        add = (f'<EffectArray Reference="Effect,LegionnairePsiBlades,Amount" Value="2" />'
               f'<EffectArray Reference="Weapon,RM_LegionnairePsiBlades,Level" Value="1" />'
               f'<EffectArray Operation="Set" Reference="Weapon,RM_LegionnairePsiBlades,Icon" '
               f'Value="Assets\\Textures\\btn-upgrade-protoss-groundweaponslevel{n}.dds" />')
        assert 'LegionnairePsiBlades' not in t[s:e]
        t = t[:e] + add + t[e:]
        if m == 'TRaynor03':
            head = f'<CUpgrade id="ProtossGroundArmorsLevel{n}">'
            assert t.count(head) == 1
            s = t.index(head); e = t.index('</CUpgrade>', s)
            assert 'Unit,ZealotPurifier,LifeArmorLevel' not in t[s:e]
            add = (f'<EffectArray Reference="Unit,ZealotPurifier,LifeArmorLevel" Value="1" />'
                   f'<EffectArray Operation="Set" Reference="Actor,ZealotPurifier,LifeArmorIcon" '
                   f'Value="Assets\\Textures\\btn-upgrade-protoss-groundarmorlevel{n}.dds" />')
            t = t[:e] + add + t[e:]
    return t


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
            for a, b in SUBS:
                assert t.count(a) == 1, (m, a[:40]); t = t.replace(a, b)
            files[p] = t.replace('\n', nl).encode('utf-8'); changed.add(p)
            u = f'{m}.SC2Map/{UP}'
            files[u] = patch_upgrades(m, files[u].decode('utf-8')).encode('utf-8'); changed.add(u)
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
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
