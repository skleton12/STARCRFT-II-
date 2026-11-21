#!/usr/bin/env python3
"""0.6.42 -> 0.6.43: enemy unit researches done from the start on Hard and up (user 2026-11-21 "캠페인 유닛들은 해병방패 같은
연구 다 되있게 할 수 없음?" -> enemy units, Hard and up).

All missions (1~6), every enemy player that gets the 7-1 buffs (gf_rmVHTerran/Zerg/Protoss), Hard and Very Hard only.
Each gets its race's unit researches once at mission start (only the ones it lacks; levels 1~3 weapon/armor are separate):
- Terran: combat shield (CombatShield, ShieldWall), stimpack (Stimpack, MarineStimpack), concussive shells (PunisherGrenades),
  marauder life (MarauderLifeBoost), juggernaut plating (JuggernautPlating, FirebatJuggernautPlating), siege tech (SiegeTech),
  Hi-Sec auto tracking, building armor (TerranBuildingArmor), neosteel frame (NeosteelFrame).
- Zerg: zergling speed/attack speed, roach speed (GlialReconstitution), tunneling claws, organic carapace, hydralisk speed,
  baneling speed (CentrificalHooks), ultralisk armor/speed (ChitinousPlating, AnabolicSynthesis), overlord speed,
  infestor energy (InfestorEnergyUpgrade, InfestorPeristalsis).
- Protoss: charge, blink, gravitic drive, extended thermal lance, psionic storm, Khaydarin amulet.
Raynor and the allies are untouched.

Usage: python3 tools/build_v0643.py <0.6.42 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.42', b'version=0.6.43'
MAPS = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
UPG = {
    'Terran': ['CombatShield', 'ShieldWall', 'Stimpack', 'MarineStimpack', 'PunisherGrenades', 'MarauderLifeBoost',
               'JuggernautPlating', 'FirebatJuggernautPlating', 'SiegeTech', 'HiSecAutoTracking', 'TerranBuildingArmor', 'NeosteelFrame'],
    'Zerg': ['zerglingmovementspeed', 'zerglingattackspeed', 'GlialReconstitution', 'TunnelingClaws', 'OrganicCarapace',
             'hydraliskspeed', 'CentrificalHooks', 'ChitinousPlating', 'AnabolicSynthesis', 'overlordspeed',
             'InfestorEnergyUpgrade', 'InfestorPeristalsis'],
    'Protoss': ['Charge', 'BlinkTech', 'GraviticDrive', 'ExtendedThermalLance', 'PsiStormTech', 'HighTemplarKhaydarinAmulet'],
}
ANCHOR = 'void gf_rmVHTerran (int p) {\n'


def block():
    races = ''.join(
        f'void gf_rmUnitUpg{r} (int p) {{\n'
        '    if (libNtve_gf_DifficultyValueInt(0, 0, 1, 1) == 0) { return; }\n'
        + ''.join(f'    gf_rmUnitUpgAdd(p, "{u}");\n' for u in ups) + '}\n\n'
        for r, ups in UPG.items())
    return ('// 0.6.43 (user 2026-11-21): Hard and up - enemy unit researches (combat shield, stim, zergling speed...) done from the start.\n'
            'void gf_rmUnitUpgAdd (int p, string u) {\n'
            '    if (TechTreeUpgradeCount(p, u, c_techCountCompleteOnly) < 1) { TechTreeUpgradeAddLevel(p, u, 1); }\n'
            '}\n\n' + races)


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
            assert t.count(ANCHOR) == 1 and 'gf_rmUnitUpg' not in t, m
            t = t.replace(ANCHOR, block() + ANCHOR)
            for r in UPG:
                a = f'void gf_rmVH{r} (int p) {{\n    gf_rmAIUp(p);\n'
                assert t.count(a) == 1, (m, r)
                t = t.replace(a, a + f'    gf_rmUnitUpg{r}(p);\n')
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
