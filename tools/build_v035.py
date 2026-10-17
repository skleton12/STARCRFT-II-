#!/usr/bin/env python3
"""Build CCM 0.3.5 from 0.3.4 — 룰(DECISIONS 2026-10-14·15) 재적용.

1. 문자열: 맵 문자열은 '한국어 /// English' (확정 2026-10-14). 0.3.2~0.3.4에서 영어를 빼먹은 줄에 영어를 붙인다.
   영어 출처 순서: 0.3.1의 같은 키 → 원본 enus 데이터 → 아래 EN 표 (직접 작성).
   다른 11개 언어 파일은 kokr의 영어 부분으로 채운다 (patch_mission01.write_other_locales와 같은 규칙).
   3번 맵에 없던 언어 폴더도 만든다.
2. 동맹 AI가 건설·생산 (사용자 지시 2026-10-15 "둘다 섞어", 기본 지상 병력 위주):
   - 정화자(10): 엔진 캠페인 AI가 탐사정·수정탑·융화소·관문·인공제어소를 짓고 광전사/추적자를 생산,
     CatalogLinkReplace로 파수병(ZealotPurifier)·피닉스 사도(AdeptFenix)로 나온다.
   - 원시저그(11): 데하카 알 생산은 엔진 AI가 다루지 못해 스크립트가 AI 자원을 써서 일벌레·추출장·
     원시 감시자 추가 건설·원시 저글링/바퀴/히드라 생산을 한다. 무료 보충은 없앤다.
   수량·간격·위치는 시험값.

Usage: python3 tools/build_v035.py <0.3.4 zip> <0.3.1 zip (영어 출처)> <new output zip>
"""
import argparse
import copy
import os
import re
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import port_units as P  # noqa: E402

OLD, NEW = b'version=0.3.4', b'version=0.3.5'
MAPS = ['TRaynor01.SC2Map', 'TRaynor02.SC2Map', 'TRaynor03.SC2Map']
KO_PATH = 'kokr.sc2data/localizeddata/gamestrings.txt'
OTHER_LOCALES = ['enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
HANGUL = re.compile('[가-힣]')

EN = {
    'Abil/Name/Clone': 'Clone',
    'Abil/Name/NovaEradicatorLaunchMissile': 'Launch Missile',
    'Abil/Name/NovaEradicatorRailgun': 'Eradicator Railgun',
    'Abil/Name/NovaGadgetHolographicDecoy': 'Holo Decoy',
    'Abil/Name/NovaGadgetSwarmGrenades': 'Smoke Grenades',
    'Abil/Name/NovaWeaponInvictusLongshotLockdown': 'Nova - Weapon - Invictus Longshot - Lockdown',
    'Abil/Name/NovaWeaponPlasmaBlastNew': 'Plasma Blast',
    'Abil/Name/Overcharge': 'Overcharge',
    'Abil/Name/PurificationNova': 'Purification Nova',
    'Abil/Name/ZealotPurifierReviveDeath': 'Zealot Purifier Revive Death',
    'Abil/Name/ZealotPurifierReviveRebuild': 'Zealot Purifier Revive Rebuild',
    'Behavior/Name/Overcharge': 'Overcharge',
    'Button/Name/Overcharge': 'Overcharge',
    'Button/Tooltip/NovaWeaponInvictusLongshotLockdown': 'Disables the target unit for 60 seconds.<n/>Cannot target Heroic units.',
    'Effect/Name/NovaPlasmaBlastDamage': 'Plasma Blast',
    'Effect/Name/PurificationNovaSearch': 'Purification Nova',
    'Effect/Name/PurificationNovaTargettedSearch': 'Purification Nova Targeted Search',
    'Unit/Name/LightningBombWeapon': 'Lightning Bomb Weapon',
    'Upgrade/Name/CinematicMode': 'Cinematic Mode',
    'Upgrade/Name/SuperStimpackNova': 'Super Stimpack (Nova)',
    'Weapon/Name/NovaWeaponBlazefireBlade': 'Blazefire Blade',
    'Weapon/Name/NovaWeaponBlazefireBladeGun': 'Blazefire Gun',
    'Weapon/Name/NovaWeaponPlasmaRifle': 'Plasma Rifle',
    'Button/Name/RM3_Stim1': 'Combat Stimpack',
    'Button/Tooltip/RM3_Stim1': 'Attack speed +50%, movement speed +50%, costs 10 life. Lasts 11 seconds.',
    'Button/Name/RM3_Stim2': 'Super Stimpack',
    'Button/Tooltip/RM3_Stim2': 'Replaces Stimpack. Attack speed +75%, movement speed +50%, regenerates 2 life per second. Lasts 15 seconds.',
    'Button/Name/RM3_Stim3': 'Advanced Stimpack',
    'Button/Tooltip/RM3_Stim3': 'Replaces Stimpack. Attack speed +100%, movement speed +50%, regenerates 5 life per second. Lasts 15 seconds.',
    'Button/Name/RM3_Shield': 'Combat Shield',
    'Button/Tooltip/RM3_Shield': 'Marine-role mercenaries gain +10 maximum life. Separate from the Sons of Korhal shield ability.',
    'Button/Name/RM3_Laser': 'Laser Targeting System',
    'Button/Tooltip/RM3_Laser': 'Marine-role mercenaries gain +1 weapon range and +2 dawn/dusk sight bonus.',
    'Button/Name/RM3_SupplyBunker': 'Supply Bunker Construction',
    'Button/Tooltip/RM3_SupplyBunker': 'SCVs can build Supply Bunkers. Construction cost is separate.',
    'Button/Name/RM3_Armor': 'Building Armor',
    'Button/Tooltip/RM3_Armor': 'Terran base structures gain +2 armor, including Bunkers and Supply Bunkers.',
    'Unit/Name/RM3_SupplyBunker': 'Supply Bunker',
    'Button/Name/RM3_BuildSupplyBunker': 'Build Supply Bunker',
    'Button/Tooltip/RM3_BuildSupplyBunker': 'Provides 6 cargo space and 12 supply. Cost: 100 minerals.',
    'Button/Name/RM3_HireKorhal': 'Hire Sons of Korhal',
    'Button/Tooltip/RM3_HireKorhal': 'Hire 4 Sons of Korhal for a fee. Uses the standard campaign hire count and cooldown.',
    'rm3/Arrival': 'Purifiers: Purging the southwest enemy base. Prepare for reinforcements.',
    'rm3/Ready': 'Purifier and Primal Zerg bases secured. Supporting Raynor\'s forces.',
    'MapInfo/Player10/Name': 'Purifiers',
    'MapInfo/Player11/Name': 'Primal Zerg',
    'Abil/Name/AdeptPhaseShiftCancel': 'Psionic Transfer Cancel',
    'Behavior/Name/AdeptPhaseShiftCancelDummy': 'Psionic Transfer Cancel',
    'Behavior/Name/AdeptPhaseShiftCaster': 'Psionic Transfer',
}


def parse(data):
    out = {}
    for line in data.decode('utf-8-sig').splitlines():
        if '=' in line:
            k, v = line.split('=', 1); out[k] = v
    return out


def english_sources():
    en = {}
    roots = [os.path.join(P.S, *(['starcoop', 'starcoop.sc2mod'] if n == 'starcoop' else [n])) for n, _ in P.COPY_LAYERS]
    roots += [os.path.join(P.S, n) for n in ('liberty.sc2mod', 'liberty.sc2campaign', 'libertystory.sc2campaign', 'core.sc2mod')]
    for root in roots:
        for fn in ('gamestrings.txt', 'objectstrings.txt'):
            q = os.path.join(root, 'enus.sc2data', 'localizeddata', fn)
            if os.path.exists(q):
                for line in open(q, encoding='utf-8-sig', errors='replace'):
                    if '=' in line:
                        k, v = line.rstrip('\r\n').split('=', 1); en.setdefault(k, v)
    return en


def english_of(key, old, layers):
    o = old.get(key, '')
    if o:
        left, sep, right = o.partition('///')
        if sep and HANGUL.search(left): return right.strip()
        if not HANGUL.search(left) and left.strip(): return left.strip()
    return EN.get(key) or layers.get(key)


def fix_kokr(data, old, layers):
    text = data.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in text else '\n'
    out, added = [], 0
    for line in text.splitlines():
        k, sep, v = line.partition('=')
        if sep and HANGUL.search(v) and '///' not in v:
            en = english_of(k, old, layers)
            if not en: raise SystemExit(f'영어 없음: {k}')
            line = f'{k}={v} /// {en}'; added += 1
        out.append(line)
    return (nl.join(out) + nl).encode('utf-8'), added


def gate(name, data):
    bad = [k for k, v in parse(data).items() if HANGUL.search(v) and '///' not in v]
    if bad: raise SystemExit(f'{name}: 영어 없는 한국어 줄 {len(bad)}개 {bad[:5]}')


def other_locale(kokr):
    """patch_mission01.write_other_locales와 같은 규칙: 영어 부분, 없으면 ID 이름."""
    text = kokr.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    out = []
    for line in text.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            if ' /// ' in v: v = v.split(' /// ', 1)[1]
            elif HANGUL.search(v): v = k.rsplit('/', 1)[-1]
            line = f'{k}={v}'
        out.append(line)
    return (nl.join(out) + nl).encode('utf-8')


# ---- mission 3 script ----
P_STOCK_OLD = '''    AISetStockUnitNext(10,12,"Probe",false);
    AISetStock(10,1,"Nexus");
    AISetStock(10,2,"Pylon");
    AISetStock(10,1,"Gateway");
'''
P_STOCK_NEW = '''    // Purifier engine AI builds and trains (trial goals). Zealot/Stalker come out as Sentinel/Fenix Adept.
    AISetStockUnitNext(10,16,"Probe",false);
    AISetStock(10,1,"Nexus");
    AISetStock(10,4,"Pylon");
    AISetStock(10,2,"Assimilator");
    AISetStock(10,2,"Gateway");
    AISetStock(10,1,"CyberneticsCore");
    AISetStock(10,MaxI(0,10-TechTreeUnitCount(10,"ZealotPurifier",c_techCountQueuedOrBetter)),"Zealot");
    AISetStock(10,MaxI(0,6-TechTreeUnitCount(10,"AdeptFenix",c_techCountQueuedOrBetter)),"Stalker");
'''
INIT_ANCHOR = '    TechTreeUpgradeAddLevel(10,"ZealotResearchReconstruction",1);\n'
INIT_ADD = '''    CatalogLinkReplace(10,c_gameCatalogUnit,"Zealot","ZealotPurifier");
    CatalogLinkReplace(10,c_gameCatalogUnit,"Stalker","AdeptFenix");
    TechTreeUnitAllow(10,"Probe",true);
    TechTreeUnitAllow(10,"Nexus",true);
    TechTreeUnitAllow(10,"Pylon",true);
    TechTreeUnitAllow(10,"Assimilator",true);
    TechTreeUnitAllow(10,"Gateway",true);
    TechTreeUnitAllow(10,"CyberneticsCore",true);
    TechTreeUnitAllow(10,"Zealot",true);
    TechTreeUnitAllow(10,"Stalker",true);
    gt_m3_zbuild=TriggerCreate("gt_m3_ZBuild_Func");
'''
Z_GLOBALS_ANCHOR = 'unitgroup gv_m3_pending;\n'
Z_GLOBALS = '''unitgroup gv_m3_pending;
trigger gt_m3_zbuild;
bool gv_m3_zBusy;
fixed gv_m3_zNext;
int gv_m3_zTurn;
unit gv_m3_extractor;
unitgroup gv_m3_gas;
'''
Z_OLD_START = 'void gf_m3_PrimalWorkers () {'
Z_OLD_END = '\n}\n\nbool gt_m3_Tick_Func'
Z_NEW = '''bool gf_m3_Pay (int m,int g) {
    if (PlayerGetPropertyInt(11,c_playerPropMinerals)<m || PlayerGetPropertyInt(11,c_playerPropVespene)<g) { return false; }
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,m);
    PlayerModifyPropertyInt(11,c_playerPropVespene,c_playerPropOperSubtract,g);
    return true;
}

bool gt_m3_ZBuild_Func (bool testConds,bool runActions) {
    unitgroup g;
    if (!runActions) { return true; }
    // Primal Zerg construction with its own resources (trial spots near the marked site).
    if (!UnitIsAlive(gv_m3_extractor)) {
        if (gf_m3_Build("Extractor",11,Point(48.5,29.5),20)) {
            g=UnitGroup("Extractor",11,RegionCircle(Point(48.5,29.5),2.0),UnitFilter(0,0,0,0),0);
            gv_m3_extractor=UnitGroupUnit(g,1);
        }
    }
    else { gf_m3_Build("DehakaBarracks",11,Point(38.5,33.5),30); }
    gv_m3_zBusy=false;
    return true;
}

void gf_m3_PrimalWorkers () {
    unitgroup g;
    unitgroup ore;
    unitgroup halls;
    unit u;
    int i;
    int n;
    point home;
    string kind;
    if (!UnitIsAlive(gv_m3_hatchery)) { return; }
    home=UnitGetPosition(gv_m3_hatchery);
    g=UnitGroup("DehakaDrone",11,RegionEntireMap(),UnitFilter(0,0,0,0),0);
    // Primal drones cost 50 minerals each (one per tick), up to 16.
    if (UnitGroupCount(g,c_unitCountAlive)<16 && gf_m3_Pay(50,0)) {
        UnitCreate(1,"DehakaDrone",0,11,home,270.0);
        UnitGroupAdd(g,UnitLastCreated());
    }
    // Build: extractor first (25), then one more Primal Warden (250), max 2 wardens.
    halls=UnitGroup("DehakaBarracks",11,RegionEntireMap(),UnitFilter(0,0,0,0),0);
    if (!gv_m3_zBusy) {
        if (!UnitIsAlive(gv_m3_extractor) && gf_m3_Pay(25,0)) { gv_m3_zBusy=true; TriggerExecute(gt_m3_zbuild,false,false); }
        else if (UnitIsAlive(gv_m3_extractor) && UnitGroupCount(halls,c_unitCountAll)<2 && gf_m3_Pay(250,0)) { gv_m3_zBusy=true; TriggerExecute(gt_m3_zbuild,false,false); }
    }
    // Workers: three on gas, the rest on the nearest minerals.
    ore=UnitGroup(null,0,RegionCircle(home,12.0),UnitFilter((1 << c_targetFilterRawResource),0,0,0),0);
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (!UnitIsAlive(u) || !UnitTestState(u,c_unitStateIdle)) { continue; }
        if (UnitIsAlive(gv_m3_extractor) && UnitGroupCount(gv_m3_gas,c_unitCountAlive)<3 && !UnitGroupHasUnit(gv_m3_gas,u)) { UnitGroupAdd(gv_m3_gas,u); }
        if (UnitGroupHasUnit(gv_m3_gas,u) && UnitIsAlive(gv_m3_extractor)) {
            UnitIssueOrder(u,OrderTargetingUnit(AbilityCommand("DroneHarvest",0),gv_m3_extractor),c_orderQueueReplace);
        }
        else if (UnitGroupCount(ore,c_unitCountAll)>0) {
            UnitIssueOrder(u,OrderTargetingUnit(AbilityCommand("DroneHarvest",0),UnitGroupClosestToPoint(ore,UnitGetPosition(u))),c_orderQueueReplace);
        }
    }
    // Army from Primal Wardens with its own resources: lings, roach, hydra in turn (trial 6 s per warden).
    n=UnitGroupCount(halls,c_unitCountAlive);
    if (n==0 || GameGetMissionTime()<gv_m3_zNext || gf_m3_Supply()>=40.0) { return; }
    if (ModI(gv_m3_zTurn,4)<2) { kind="DehakaZerglingLevel2"; if (!gf_m3_Pay(50,0)) { return; } }
    else if (ModI(gv_m3_zTurn,4)==2) { kind="DehakaRoachLevel2"; if (!gf_m3_Pay(75,25)) { return; } }
    else { kind="DehakaHydraliskLevel2"; if (!gf_m3_Pay(100,50)) { return; } }
    u=UnitGroupUnit(halls,ModI(gv_m3_zTurn,n)+1);
    UnitCreate(1,kind,0,11,UnitGetPosition(u),270.0);
    gv_m3_zTurn+=1;
    gv_m3_zNext=GameGetMissionTime()+6.0/IntToFixed(n);
}

bool gt_m3_Tick_Func'''


def mission3_script(data):
    text = data.decode('utf-8')
    for old in (P_STOCK_OLD, INIT_ANCHOR, Z_GLOBALS_ANCHOR, Z_OLD_START):
        assert text.count(old) == 1, old
    text = text.replace(P_STOCK_OLD, P_STOCK_NEW, 1)
    text = text.replace(INIT_ANCHOR, INIT_ANCHOR + INIT_ADD, 1)
    text = text.replace(Z_GLOBALS_ANCHOR, Z_GLOBALS, 1)
    a = text.index(Z_OLD_START); b = text.index(Z_OLD_END, a)
    text = text[:a] + Z_NEW + text[b + len(Z_OLD_END):]
    # gv_m3_gas must exist before use.
    text = text.replace('    gv_m3_pending=UnitGroupEmpty();\n', '    gv_m3_pending=UnitGroupEmpty();\n    gv_m3_gas=UnitGroupEmpty();\n', 1)
    assert 'gv_m3_gas=UnitGroupEmpty();' in text
    return text.encode('utf-8')


def build(source, english, output):
    if output.exists(): raise ValueError('Output must be new')
    layers = english_sources()
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(english) as z31:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names = prev.namelist()
        files = {n: prev.read(n) for n in names}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            k = f'{m}/{KO_PATH}'
            files[k], added = fix_kokr(files[k], parse(z31.read(k)), layers)
            gate(k, files[k])
            print(m, 'English added', added)
            for loc in OTHER_LOCALES:
                files[f'{m}/{loc}.sc2data/localizeddata/gamestrings.txt'] = other_locale(files[k])
        files['TRaynor03.SC2Map/mapscript.galaxy'] = mission3_script(files['TRaynor03.SC2Map/mapscript.galaxy'])
        order = names + sorted(set(files) - set(names))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                info = {i.filename: i for i in prev.infolist()}
                for n in order:
                    if n in info: out.writestr(copy.copy(info[n]), files[n])
                    else: out.writestr(n, files[n])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == order
        except BaseException:
            output.unlink(missing_ok=True); raise
    print('new files:', len(order) - len(names))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('english', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.english, a.output)
