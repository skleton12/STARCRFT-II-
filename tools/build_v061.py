#!/usr/bin/env python3
"""Build CCM 0.6.1 from 0.5.22: 6번 미션 THanson01 (The Evacuation, 대피) 추가 (사용자 2026-10-28).

사용자: "화염방사병 쪽으로 갈게", "한번 만들어보산". 고른 것: 동맹은 레드스톤처럼 지원 버튼(일꾼 없음, 화면 위
[정화자 지원]·[원시저그 지원] + 지도 클릭 투하, 4분 뒤·120초, 연구실 5단계), 저그 기지 지원도 넣기(6분·150초·2곳씩 번갈아,
본 건물이 부서지면 그 기지 지원 끊김).

원본: maps/original_wol/thanson01 (사용자 드라이브의 블리자드 캠페인 추출본). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 레드스톤(TTosh01, 0.5.22)의 모드 층을 그대로 옮긴다 (gf_m5_* -> gf_m6_*):
  데이터·에셋·모드 문자열·단축키, 용병 생산·연구, 동맹 8 정화자 / 9 원시저그, 핑, 해금 연동, 공방업 연동, 용병 계약 무료,
  지원 버튼, 연구실 5단계, 저그 기지 지원.
대피 맞춤:
  - 플레이어: 1 레이너, 2·3·5·6 저그(적), 4 아그리아 거주민(아군). 동맹 8·9를 새로 넣는다 (mapinfo 7·8번째 레코드 -> 이름 키 Player07/08).
  - 레드스톤 전용(용암 대피, 저그 전멸 승리, 용암 안내)은 넣지 않는다.
  - 7-1 저그 규칙: 2·3·5·6 능력치 10% + 공세(AIAttackWaveAddUnits4) +50% (시험값).
  - 레이너 본진 = 핸슨에게 넘겨받는 거주지 사령부 (33.5,44.5): 광물 7덩이 풍부한 광물·매장량 +20%, 가스 1곳 풍부한 가스·+100%,
    이미 지어진 정제소 매장량도 +100% (4번 이후 공통 규칙).
  - 화염방사병 수송선이 내려 주는 화염방사병·의무관 -> 악마의 개·용병 의무관. 넘겨받는 벙커 안 해병 등도 내리면 용병으로 바꾼다.
  - 저그 기지 = 시작 때 2·3·5번의 부화장·번식지·군락 7곳.

Usage: python3 tools/build_v061.py <0.5.22 zip> <thanson01 folder> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import build_v0514 as V514
import patch_mission01 as m1
from build_v041 import merge
from build_v051 import mapinfo as mapinfo51, sub1, waves, set_strings

OLD, NEW = b'version=0.5.22', b'version=0.6.1'
M5, M6 = 'TTosh01.SC2Map/', 'THanson01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ENV = {GD + 'lightdata.xml', GD + 'terraindata.xml', GD + 'waterdata.xml', GD + 'gamedata.xml'}
ALLIES = [(8, b'Prot', '정화자', 'Purifiers'), (9, b'Zerg', '원시저그', 'Primal Zerg')]
CC = (33.5, 44.5)          # Hanson's colony Command Center, handed to Raynor
RALLY8, RALLY9 = (40.0, 50.0), (41.0, 52.0)   # trial
NAMES = {'MapInfo/Player07/Name': ('정화자', 'Purifiers'), 'MapInfo/Player08/Name': ('원시저그', 'Primal Zerg')}

FREE_MERC_FN = '''// 0.4.109: Hyperion mercenary contracts bought for free (user 2026-10-25). Status only, no credits.
void gf_rmFreeMercContracts () {
    int i=libCamp_gv_TSC_MERC_FIRST;
    int m;
    for (;i<=libCamp_gv_TSC_MERC_LAST;i+=1) {
        m=libCamp_gv_tS_MercID[i];
        if (!libCamp_gf_MercStatusCheck(m,libCamp_ge_StoryMercStatus_Locked)) {
            libCamp_gf_SetMercStatus(m,libCamp_ge_StoryMercStatus_Purchased);
        }
    }
}

'''

NO_LAVA = '''// Mission 6 has no lava (Redstone only); these stay so the shared pack reads the same.
bool gf_m6_LavaSoon () {
    return false;
}

bool gf_m6_Lava () {
    return false;
}

// 0.6.1: every Raynor infantry unit is a mercenary, also units handed over (Hanson's bunkers, the Firebat dropship).
// Units inside bunkers or transports are hidden; they are swapped once they come out.
void gf_m6_Reapers () {
    unitgroup g;
    unit u;
    string t;
    int i;
    if (gv_inCinematic) { return; }
    g=UnitGroup(null,1,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))),0);
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        t=UnitGetType(u);
        if (t=="Marine") { libNtve_gf_ReplaceUnit(u,"WarPig",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }
        else if (t=="Medic") { libNtve_gf_ReplaceUnit(u,"MercMedic",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }
        else if (t=="Marauder") { libNtve_gf_ReplaceUnit(u,"HammerSecurity",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }
        else if (t=="Firebat") { libNtve_gf_ReplaceUnit(u,"DevilDog",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }
        else if (t=="Reaper") { libNtve_gf_ReplaceUnit(u,"MercReaper",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }
    }
}

'''

ENEMY_LOOP = '    for (p=2;p<=6;p+=1) {\n        if (!gf_m6_IsEnemy(p)) { continue; }\n'


def m5_block(script):
    t = script.replace('\r\n', '\n')
    a = t.index('\n// Common pack for missions after 3')
    b = t.index('\n}\n', t.index('void gf_m5_Init () {')) + 3
    return t[a + 1:b]


def cut(t, start, end):
    a = t.index(start)
    b = t.index(end, a)
    return t[:a] + t[b:]


def adapt(block):
    t = re.sub(r'\b(g[vft])_m5_', r'\1_m6_', block)
    t = sub1(t, "// Mission 5 = TTosh01 (Devil's Playground). Allies: 8 Purifiers, 9 Primal Zerg. Enemies: 2, 4 Zerg; 3 lava.\n"
                "// 5 Tosh (ally), 6 Swann (neutral). Coordinates and timings are trial values (docs/missions/05_devils_playground.md).",
             '// Mission 6 = THanson01 (The Evacuation), ported from mission 5 (0.5.22). Allies: 8 Purifiers, 9 Primal Zerg.\n'
             '// Enemies: 2, 3, 5, 6 Zerg; 4 Agria colonists (ally). Coordinates and timings are trial values (docs/missions/06_evacuation.md).')
    t = sub1(t, '    return (p==2 || p==4);', '    return (p==2 || p==3 || p==5 || p==6);')
    t = sub1(t, '    for (p=2;p<=4;p+=2) {\n', ENEMY_LOOP, 3)
    t = sub1(t, 'Point(41.5,88.5)', f'Point({CC[0]},{CC[1]})', 4)
    t = sub1(t, 'rally=Point(52.0,85.0);', f'rally=Point({RALLY8[0]},{RALLY8[1]});')
    t = sub1(t, 'rally=Point(52.0,90.0);', f'rally=Point({RALLY9[0]},{RALLY9[1]});')
    # Unused worker drop spots (no ally workers here), kept valid next to the colony.
    t = sub1(t, 'Point(47.0,80.0)', 'Point(38.0,49.0)')
    t = sub1(t, 'Point(46.0+1.0*i,80.0)', 'Point(37.0+1.0*i,49.0)')
    t = sub1(t, 'Point(45.0,81.0)', 'Point(36.0,50.0)')
    t = cut(t, '// 0.5.1: lava (user 2026-10-25)', 'string[9] gv_m6_supWarp;')
    t = sub1(t, 'string[9] gv_m6_supWarp;', NO_LAVA + 'string[9] gv_m6_supWarp;')
    t = sub1(t, '    if (WorldHeight(c_heightMapGround,c)<=9.5 || !PointPathingPassable(c)) {\n        h=gf_m6_HighGround(c);\n        if (h!=null) { c=h; }\n    }\n',
             '    if (!PointPathingPassable(c)) { c=gv_rmBasePt[p]; }\n')
    t = sub1(t, '// Bases = the Zerg (2, 4) town halls at the start.', '// Bases = the Zerg (2, 3, 5) town halls at the start.')
    t = sub1(t, '    gf_rmEnemyFastProd(2,2);\n    gf_rmEnemyFastProd(4,4);\n', '    gf_rmEnemyFastProd(2,3);\n    gf_rmEnemyFastProd(5,6);\n')
    a = t.index('void gf_m6_EnemyRules () {')
    b = t.index('\n}\n', a) + 3
    t = t[:a] + ('void gf_m6_EnemyRules () {\n'
                 '    // 7-1 Zerg (user 2026-10-17/24): more units (attack waves +50% in the original triggers) and a flat 10% stat buff.\n'
                 '    gf_rmZergBuff(2);\n    gf_rmZergBuff(3);\n    gf_rmZergBuff(5);\n    gf_rmZergBuff(6);\n}\n') + t[b:]
    t = sub1(t, '    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm4/AdjName"),StringExternal("rm5/Adj3"),7.0,c_transmissionDurationSet,true);\n', '')
    t = sub1(t, '                if (gf_m6_IsEnemy(p) || p==3) {', '                if (gf_m6_IsEnemy(p)) {')
    t = sub1(t, '                else if (p==1 || p==5 || p>=8) {', '                else if (p==1 || p==4 || p>=8) {')
    t = sub1(t, '    gv_rmMinBuildH=9.5;\n', '')
    for bad in ('_m5_', 'gv_lavaTimer', 'gv_lowGroundIsSafe', 'HighGround', '41.5,88.5', 'p<=4;p+=2'):
        assert bad not in t, bad
    return t


def script(raw, block):
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = waves(t)
    # Firebat dropship: mercenary Devil Dogs and medics (and the move trigger that sorts them).
    t = sub1(t, 'UnitCargoCreate(UnitFromId(290), "Firebat", 2);', 'UnitCargoCreate(UnitFromId(290), "DevilDog", 2);')
    t = sub1(t, 'UnitCargoCreate(UnitFromId(290), "Medic", 2);', 'UnitCargoCreate(UnitFromId(290), "MercMedic", 2);')
    t = sub1(t, '        if (!(((UnitGetType(EventUnitCargo()) == "Firebat") || (UnitGetType(EventUnitCargo()) == "Medic")))) {',
             '        if (!(((UnitGetType(EventUnitCargo()) == "DevilDog") || (UnitGetType(EventUnitCargo()) == "MercMedic")))) {')
    t = sub1(t, '    if ((UnitGetType(EventUnitCargo()) == "Firebat")) {', '    if ((UnitGetType(EventUnitCargo()) == "DevilDog")) {')
    t = sub1(t, '    if ((UnitGetType(EventUnitCargo()) == "Medic")) {', '    if ((UnitGetType(EventUnitCargo()) == "MercMedic")) {')
    t = sub1(t, 'void InitGlobals () {', adapt(block) + '\n' + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE_MERC_FN + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHanson01);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHanson01);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m6_Init();\n')
    t = sub1(t, '    TriggerExecute(gt_StartGame, true, false);\n', '    gf_m6_Start();\n    TriggerExecute(gt_StartGame, true, false);\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n', 'void InitMap () {\n    InitLibs();\n    AchievementsDisable(1);\n')
    return t.replace('\n', '\r\n').encode('utf-8')


def objects(data):
    import math
    root = E.fromstring(data)
    rich = gas = 0
    for el in root:
        if el.tag != 'ObjectUnit': continue
        ut = el.get('UnitType')
        x, y = (float(v) for v in el.get('Position').split(',')[:2])
        if math.hypot(x - CC[0], y - CC[1]) > 16: continue
        if ut == 'MineralField':
            el.set('UnitType', 'RichMineralField'); el.set('Resources', str(int(el.get('Resources')) * 120 // 100)); rich += 1
        elif ut == 'VespeneGeyser':
            el.set('UnitType', 'RichVespeneGeyser'); el.set('Resources', str(int(el.get('Resources')) * 2)); gas += 1
        elif ut == 'Refinery':
            el.set('Resources', str(int(el.get('Resources')) * 2)); gas += 1
    assert (rich, gas) == (7, 2), (rich, gas)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def strings(orig6, mod5, orig5_keys):
    text = orig6.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod5.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig5_keys or k.startswith('MapInfo/'): continue
        add[k] = v
    out = (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')
    return set_strings(out, {k: f'{ko} /// {en}' for k, (ko, en) in NAMES.items()})


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig and len(orig) == 39, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(M6) for n in prev.namelist())
        files = dict(orig)
        mod5 = {n[len(M5):]: prev.read(n) for n in prev.namelist() if n.startswith(M5)}
        o5 = HERE.parent / 'maps/original_wol/ttosh01'
        for rel, data in mod5.items():
            low = rel.lower()
            if low.startswith('assets/'):
                files[rel] = data
            elif low.startswith(GD) and rel not in ENV:
                files[rel] = merge(data, orig[rel]) if rel in orig else data
            elif low.endswith('gamehotkeys.txt'):
                files[rel] = data
        o5k = {l.split('=', 1)[0] for l in (o5 / KO).read_text(encoding='utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], mod5[KO], o5k)
        files['objects'] = objects(files['objects'])
        files['mapinfo'] = mapinfo51(files['mapinfo'])
        saved = m1.ALLY_PLAYERS
        m1.ALLY_PLAYERS = ALLIES
        try: files['documentheader'] = m1.patch_header(files['documentheader'])
        finally: m1.ALLY_PLAYERS = saved
        saved = V514.NAMES
        V514.NAMES = NAMES
        try: files['documentheader'] = V514.set_header(files['documentheader'])
        finally: V514.NAMES = saved
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'], m5_block(mod5['mapscript.galaxy'].decode('utf-8-sig')))
        V35.gate('kokr', files[KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[KO])
        for name, data in orig.items():
            if name.startswith('t3') or name in ('triggers', 'regions', 'paintedpathinglayer', 'documentinfo', 'minimap.tga'):
                assert files[name] == data, name
        for name, data in files.items():
            if name.endswith('.xml') or name == 'objects': E.fromstring(data)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    out.writestr(copy.copy(info), d)
                for name in sorted(files): out.writestr(M6 + name, files[name])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'THanson01 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
