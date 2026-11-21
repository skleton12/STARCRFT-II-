#!/usr/bin/env python3
"""0.6.62 -> 0.6.63 (user 2026-11-21 "마린 소총 변경 업그레이드 하면 그냥 가우스 소총으로 나오고 공격력·중장갑 공격력 추가만 나옴").

B-2 High-Cal LMG becomes a real weapon swap on the War Pig (maps 3-6), the way Blizzard enables the Purifier Colossus
lances: an upgrade flips weapon Options[Disabled]/[Hidden].
- New weapon RM6_B2Weapon "B-2 고구경 경기관총 /// B-2 High-Cal LMG": same timing, filters and effect chain as the War Pig's
  Gauss rifle (KelmorianMinerGaussRifle, effect RM6_MultiSetWP, so infantry weapon upgrades, multishot and the B-2
  damage +4 / +2 Armored still apply). Disabled and hidden until researched.
- War Pig gets it as WeaponArray[1].
- RM6_B2LMG (player 1 only): Gauss rifle Disabled+Hidden, B-2 Enabled+Shown. Enemy Kelmorian miners keep their rifle.
- Same per-weapon upgrades as the Gauss rifle: laser targeting range/scan +1 (RM3_Laser), multishot attack count 2,
  infantry weapons 1-3 level number and icon.
No script changes (0.6.58 rule: weapon names/icons are not changed by script). Game not run.

Usage: python3 tools/build_v0663.py <0.6.62 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD

OLD, NEW = b'version=0.6.62', b'version=0.6.63'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
W = 'RM6_B2Weapon'
WEAPON = f'''    <CWeaponLegacy id="{W}">
        <Name value="Weapon/Name/{W}" />
        <EditorCategories value="Race:Terran" />
        <Icon value="Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel0.dds" />
        <DisplayEffect value="KelmorianMinerDamage" />
        <TargetFilters value="Visible;Missile,Stasis,Dead,Hidden,Invulnerable" />
        <Period value="0.8608" />
        <DamagePoint value="0.05" />
        <Backswing value="0.75" />
        <Effect value="RM6_MultiSetWP" />
        <Options index="Disabled" value="1" />
        <Options index="Hidden" value="1" />
    </CWeaponLegacy>
'''
KEYS = {f'Weapon/Name/{W}': 'B-2 고구경 경기관총 /// B-2 High-Cal LMG'}


def ea(ref, val, op=None):
    o = f'Operation="{op}" ' if op else ''
    return f'<EffectArray {o}Reference="{ref}" Value="{val}" />'


def add_to(t, uid, xml):
    """Append EffectArray lines inside the one CUpgrade uid."""
    s = t.index(f'<CUpgrade id="{uid}"'); assert t.count(f'<CUpgrade id="{uid}"') == 1, uid
    e = t.index('</CUpgrade>', s)
    return t[:e] + xml + t[e:]


def upgrades(t):
    K = 'Weapon,KelmorianMinerGaussRifle'
    t = add_to(t, 'RM6_B2LMG', ''.join([ea(f'{K},Options[Disabled]', 1, 'Set'), ea(f'{K},Options[Hidden]', 1, 'Set'),
                                       ea(f'Weapon,{W},Options[Disabled]', 0, 'Set'), ea(f'Weapon,{W},Options[Hidden]', 0, 'Set')]))
    t = add_to(t, 'RM3_Laser', ea(f'Weapon,{W},Range', 1) + ea(f'Weapon,{W},MinScanRange', 1))
    t = add_to(t, 'RM6_Multishot', ea(f'Weapon,{W},DisplayAttackCount', 2, 'Set'))
    for lv in (1, 2, 3):
        t = add_to(t, f'TerranInfantryWeaponsLevel{lv}', ea(f'Weapon,{W},Level', 1) +
                   ea(f'Weapon,{W},Icon', f'Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel{lv}.dds', 'Set'))
    return t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            g = f'{m}.SC2Map/{GD}'
            w = files[g + 'weapondata.xml'].decode('utf-8'); assert W not in w
            files[g + 'weapondata.xml'] = w.replace('</Catalog>', WEAPON + '</Catalog>', 1).encode('utf-8')
            u = files[g + 'unitdata.xml'].decode('utf-8')
            s = u.index('<CUnit id="WarPig"'); assert u.count('<CUnit id="WarPig"') == 1
            e = u.index('</CUnit>', s); assert 'WeaponArray' not in u[s:e]
            u = u[:e] + f'<WeaponArray index="1" Link="{W}" />' + u[e:]
            files[g + 'unitdata.xml'] = u.encode('utf-8')
            files[g + 'upgradedata.xml'] = upgrades(files[g + 'upgradedata.xml'].decode('utf-8')).encode('utf-8')
            changed |= {g + f for f in ('weapondata.xml', 'unitdata.xml', 'upgradedata.xml')}
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], KEYS); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                p = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'
                files[p] = V35.other_locale(ko); changed.add(p)
        import xml.etree.ElementTree as E
        for k in changed:
            if k.endswith('.xml'): E.fromstring(files[k])
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
