#!/usr/bin/env python3
"""0.4.70 -> 0.4.71: 연구 완료 효과·정화자 협동전 업그레이드를 유닛 정보 칸 아이콘으로 표시 (4번, 사용자 2026-10-23).

사용자: "방어막이라던지 그런거 용병에서 보이는거처럼 적용된 아이콘 같은게 표시되면 좋을듯" → 선택 '연구 완료 효과', '동맹 업그레이드도'.
효과 없는 표시용 영구 버프 RMI_<업그레이드>(InfoIcon·이름·툴팁)를 만들고, 스크립트가 2초 틱마다
그 업그레이드를 마친 플레이어의 해당 유닛에 한 번 붙인다(이미 있으면 안 붙임). 능력치·연구·비용은 바꾸지 않는다.
자극제는 유닛 능력 버튼으로 이미 보여 제외. 아이콘은 연구 버튼·업그레이드 데이터에 있는 원작 아이콘을 쓴다.
원시저그는 받는 유닛 전용 업그레이드가 없어(공방업만 연동) 이번 대상이 아니다.

Usage: python3 tools/build_v0471.py <0.4.70 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines

M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
OLD, NEW = b'version=0.4.70', b'version=0.4.71'
T = 'Assets\\Textures\\'
# (player, upgrade, units, icon, 'ko /// en')
ICONS = [
    (1, 'RM3_Shield', ['WarPig', 'RMK_MarineMengsk'], 'btn-techupgrade-terran-combatshield-color.dds', '전투 방패 /// Combat Shield'),
    (1, 'RM3_Laser', ['WarPig', 'RMK_MarineMengsk'], 'btn-upgrade-terran-hisecautotracking.dds', '레이저 조준 시스템 /// Laser Targeting System'),
    (1, 'PunisherGrenades', ['HammerSecurity'], 'btn-ability-terran-punishergrenade-color.dds', '충격탄 /// Concussive Shells'),
    (1, 'RM4_Suppression', ['HammerSecurity'], 'btn-ability-terran-superconcussive.dds', '억제탄 /// Suppression Shells'),
    (1, 'RM4_Shrapnel', ['HammerSecurity', 'MarauderMengsk'], 'btn-upgrade-terran-explosiveshrapnelshells.dds', '파편탄 /// Shrapnel Shells'),
    (1, 'MarauderLifeBoost', ['HammerSecurity', 'MarauderMengsk'], 'btn-techupgrade-terran-kineticfoam.dds', '동역학 충격완화복 /// Kinetic Foam'),
    (1, 'MarauderMengskSlow', ['MarauderMengsk'], 'btn-ability-mengsk-marauder-superconcussiveshells.dds', '무력화탄 /// Incapacitator Shells'),
    (1, 'StabilizerMedPacks', ['MercMedic'], 'btn-techupgrade-terran-stabilizermedpacks.dds', '전투 안정제 /// Stabilizer Medpacks'),
    (1, 'RMC_StabilizerCoop', ['MercMedic'], 'btn-upgrade-raynor-stabilizermedpacks.dds', '전투 안정제 (협동전) /// Stabilizer Medpacks (Co-op)'),
    (1, 'BearclawNozzles', ['DevilDog'], 'btn-techupgrade-terran-bearclawnozzles.dds', '화염증폭기 /// Incinerator Gauntlets'),
    (1, 'FirebatJuggernautPlating', ['DevilDog'], 'btn-techupgrade-terran-juggernautplating.dds', '철인 장갑 /// Juggernaut Plating'),
    (1, 'RMC_JuggernautCoop', ['DevilDog'], 'btn-upgrade-raynor-juggernautplating.dds', '철인 장갑 (협동전) /// Juggernaut Plating (Co-op)'),
    (1, 'MengskStructureArmor', ['BunkerDepotMengsk'], 'btn-upgrade-mengsk-engineeringbay-neosteelfortifiedarmor.dds', '신소재 강화 장갑 /// Neosteel Fortified Armor'),
    (1, 'BunkerDepotMengskRange', ['BunkerDepotMengsk'], 'btn-upgrade-mengsk-engineeringbay-improvedbunkersights.dds', '조준 지원 총안 /// Aim-assist Embrasures'),
    (8, 'Charge', ['ZealotPurifier'], 'btn-ability-protoss-charge-color.dds', '돌진 /// Charge'),
    (8, 'ZealotResearchReconstruction', ['ZealotPurifier'], 'btn-ability-protoss-reconstruction.dds', '재구축 /// Reconstruction'),
    (8, 'AdeptFenixShadeSpawn', ['AdeptFenix'], 'btn-upgrade-protoss-fenix-adeptchampionshadespawn.dds', '사이오닉 투영 /// Psionic Projection'),
    (8, 'ColossusFireBeam', ['ColossusPurifier'], 'BTN-Ability-Protoss-FireBeam.dds', '화염 광선 /// Fire Beam'),
    (8, 'ExtendedThermalLance', ['ColossusPurifier'], 'btn-upgrade-protoss-extendedthermallance.dds', '확장 열 창 /// Extended Thermal Lance'),
    (8, 'DisruptorCloak', ['Disruptor'], 'btn-ability-protoss-cloakfield-color.dds', '은폐 모듈 /// Cloaking Module'),
    (8, 'MiragePhaseArmor', ['PhoenixPurifier'], 'btn-ability-protoss-phasingarmor.dds', '위상 장갑 /// Phasing Armor'),
    (8, 'PhoenixRangeUpgrade', ['PhoenixPurifier'], 'btn-upgrade-protoss-phoenixrange.dds', '음이온파 수정 /// Anion Pulse-Crystals'),
    (8, 'FenixScoutWeaponRange', ['Scout'], 'btn-upgrade-protoss-fenix-scoutchampionrange.dds', '전투 감지기 배열 /// Combat Sensor Array'),
    (8, 'TempestDisintegration', ['TempestPurifier'], 'btn-ability-protoss-disintegration.dds', '분해 /// Disintegration'),
]


def behaviors(d):
    t = d.decode('utf-8')
    add = ''.join(f'<CBehaviorBuff id="RMI_{up}"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" />'
                  f'<InfoIcon value="{T}{icon}" /></CBehaviorBuff>' for _, up, _, icon, _ in ICONS)
    assert 'id="RMI_' not in t
    i = t.rindex('</Catalog>')
    return (t[:i] + add + t[i:]).encode('utf-8')


SCRIPT_FN = '''
// 0.4.71: research/upgrade info icons (display-only permanent buffs, user 2026-10-23).
void gf_m4_IconOne (int p, string kind, string up, string b) {
    unitgroup g;
    unit u;
    int i;
    if (TechTreeUpgradeCount(p,up,c_techCountCompleteOnly)==0) { return; }
    g=UnitGroup(kind,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (!UnitHasBehavior2(u,b)) { UnitBehaviorAdd(u,b,u,1); }
    }
}

void gf_m4_Icons () {
%s}

bool gt_m4_Tick_Func (bool testConds,bool runActions) {'''


def script(d):
    t = d.decode('utf-8')
    a = '\nbool gt_m4_Tick_Func (bool testConds,bool runActions) {'
    assert t.count(a) == 1 and 'gf_m4_Icons' not in t
    calls = ''.join(f'    gf_m4_IconOne({p},"{u}","{up}","RMI_{up}");\n' for p, up, units, _, _ in ICONS for u in units)
    t = t.replace(a, SCRIPT_FN % calls)
    b = '    gf_m4_Skin(9);\n    if (!gv_m4_ready) { return true; }\n'
    assert t.count(b) == 1
    t = t.replace(b, '    gf_m4_Skin(9);\n    gf_m4_Icons();\n    if (!gv_m4_ready) { return true; }\n')
    return t.encode('utf-8')


def strings():
    s = {}
    for p, up, _, _, name in ICONS:
        ko, en = name.split(' /// ')
        s[f'Behavior/Name/RMI_{up}'] = name
        if p == 1:
            s[f'Behavior/Tooltip/RMI_{up}'] = f'연구 완료: {ko} 효과가 적용 중입니다. /// Researched: {en} is active.'
        else:
            s[f'Behavior/Tooltip/RMI_{up}'] = f'정화자 협동전 업그레이드: {ko} 효과가 적용 중입니다. /// Purifier co-op upgrade: {en} is active.'
    return s


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files[GD + 'behaviordata.xml'] = behaviors(files[GD + 'behaviordata.xml'])
        files[M4 + 'mapscript.galaxy'] = script(files[M4 + 'mapscript.galaxy'])
        S = strings()
        for loc in ('kokr',) + LOCALES:
            path = M4 + loc + '.sc2data/localizeddata/gamestrings.txt'
            values = S if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in S.items()}
            files[path] = update_lines(files[path], values)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for n in files:
            if n != 'metadata.txt' and not n.startswith(M4): assert files[n] == prev.read(n), n
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
