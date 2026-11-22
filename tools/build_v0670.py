#!/usr/bin/env python3
"""Build CCM 0.6.70 from 0.6.69: 7번 미션 TTosh02 (Welcome to the Jungle, 정글의 법칙 - 벨시르) 추가 (사용자 2026-11-22 "벨시르 미션").

원본: maps/original_wol/ttosh02 (사용자 드라이브의 블리자드 캠페인 추출본, 36개 파일). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 대피(THanson01, 0.6.69)의 모드 층을 그대로 옮긴다 (gf_m6_* -> gf_m7_*):
  데이터·에셋·모드 문자열·단축키, 용병 생산·연구, 동맹 8 정화자 / 9 원시저그(지원 버튼 방식, 일꾼 없음), 핑, 해금·공방업 연동,
  용병 계약 무료, 연구실 단계, 고갈되지 않는 자원, 동맹 연구 건물(정화자 대의회·데하카의 굴), 적 7-1 규칙 모듈.
정글의 법칙 맞춤:
  - 플레이어: 1 레이너, 2·3·4 탈다림(프로토스, 적), 5 테라진(중립). 동맹 8·9 = mapinfo 7·8번째 레코드 -> 이름 키 Player06/07.
  - 7-1 프로토스 규칙(4번 탈다림과 같음): 피해 % 100, 적 무기 업그레이드 +50%(RM_EH), 지상 공방 최소 1단계, 공세 수 x1.25(올림).
    저그 기지 지원·저그 10%는 적이 프로토스라 쓰지 않는다 (저그 기지가 없어 그 모듈은 아무것도 안 한다).
  - 레이너 본진 = 사령부 (79.5,25.5): 광물 8덩이 풍부한 광물·매장량 +20%, 가스 1곳 풍부한 가스·+100%, 이미 지어진 정제소 +100%.
  - 골리앗은 용병 스파르타 중대(SpartanCompany, 대응표): 시작 골리앗 3기와 군수 공장 골리앗 칸(플레이어 1만). 공성 전차는 공성 파괴단.
Game not run.

Usage: python3 tools/build_v0670.py <0.6.69 zip> <ttosh02 folder> <new output zip>
"""
import argparse, copy, math, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import build_v0514 as V514
import patch_mission01 as m1
from build_v041 import merge
from build_v051 import mapinfo as mapinfo51, sub1, set_strings

OLD, NEW = b'version=0.6.69', b'version=0.6.70'
M6, M7 = 'THanson01.SC2Map/', 'TTosh02.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ENV = {GD + 'lightdata.xml', GD + 'terraindata.xml', GD + 'waterdata.xml', GD + 'gamedata.xml'}
ALLIES = [(8, b'Prot', '정화자', 'Purifiers'), (9, b'Zerg', '원시저그', 'Primal Zerg')]
CC = (79.5, 25.5)                              # Raynor's Command Center (minerals to the east)
RALLY8, RALLY9 = (72.0, 30.0), (73.0, 32.0)    # trial, west of the CC
NAMES = {'MapInfo/Player06/Name': ('정화자', 'Purifiers'), 'MapInfo/Player07/Name': ('원시저그', 'Primal Zerg')}
WAVE_MULT = 1.25
STRS = {
    'Button/Name/RM_SpartanCompany': '스파르타 중대 /// Spartan Company',
    'Button/Tooltip/RM_SpartanCompany': '용병 골리앗입니다. 지상과 공중을 모두 공격합니다. /// Mercenary Goliath. Attacks ground and air units.',
    'Button/Name/RM_SiegeBreaker': '공성 파괴단 /// Siege Breakers',
    'Button/Tooltip/RM_SiegeBreaker': '용병 공성 전차입니다. 공성 모드로 먼 거리의 지상 유닛을 공격합니다. /// Mercenary Siege Tank. Siege Mode attacks distant ground units.',
}


def blocks(mod):
    """The two mod blocks of mission 6: after the includes, and the common pack right before InitGlobals."""
    t = mod.replace('\r\n', '\n')
    inc = 'include "TriggerLibs/CampaignLib"\n'
    a0 = t.index(inc) + len(inc)
    a1 = t.index('\n//--------------------------------------------------------------------------------------------------\n// Library Initialization', a0)
    b0 = t.index('\n// Common pack for missions after 3') + 1
    b1 = t.index('void InitGlobals () {')
    return t[a0:a1 + 1], t[b0:b1]


def adapt(block):
    t = re.sub(r'\b(g[vft])_m6_', r'\1_m7_', block)
    t = sub1(t, '// Mission 6 = THanson01 (The Evacuation), ported from mission 5 (0.5.22). Allies: 8 Purifiers, 9 Primal Zerg.\n'
                '// Enemies: 2, 3, 5, 6 Zerg; 4 Agria colonists (ally). Coordinates and timings are trial values (docs/missions/06_evacuation.md).',
             '// Mission 7 = TTosh02 (Welcome to the Jungle), ported from mission 6 (0.6.69). Allies: 8 Purifiers, 9 Primal Zerg.\n'
             '// Enemies: 2, 3, 4 Tal\'darim (Protoss); 5 Terrazine (neutral). Coordinates and timings are trial values (docs/missions/07_welcome_to_the_jungle.md).')
    t = sub1(t, '    return (p==2 || p==3 || p==5 || p==6);', '    return (p==2 || p==3 || p==4);')
    t = sub1(t, 'Point(33.5,44.5)', f'Point({CC[0]},{CC[1]})', 4)
    t = sub1(t, 'rally=Point(40.0,50.0);', f'rally=Point({RALLY8[0]},{RALLY8[1]});')
    t = sub1(t, 'rally=Point(41.0,52.0);', f'rally=Point({RALLY9[0]},{RALLY9[1]});')
    t = sub1(t, 'Point(38.0,49.0)', 'Point(73.0,27.0)')
    t = sub1(t, 'Point(37.0+1.0*i,49.0)', 'Point(72.0+1.0*i,27.0)')
    t = sub1(t, 'Point(36.0,50.0)', 'Point(71.0,28.0)')
    t = sub1(t, '// Mission 6 has no lava (Redstone only)', '// Mission 7 has no lava (Redstone only)')
    t = sub1(t, '    gf_rmEnemyFastProd(2,3);\n    gf_rmEnemyFastProd(5,6);\n', '    gf_rmEnemyFastProd(2,4);\n')
    a = t.index('void gf_m7_EnemyRules () {')
    b = t.index('\n}\n', a) + 3
    t = t[:a] + ('void gf_m7_EnemyRules () {\n'
                 '    int p;\n'
                 '    // 7-1 Protoss (user 2026-10-17, as Tal\'darim in mission 4): weapon upgrades +50% (RM_EH), level-1 ground\n'
                 '    // upgrades without stacking on what the original gave; damage % stays 100 (0.6.29).\n'
                 '    for (p=2;p<=4;p+=1) {\n'
                 '        PlayerModifyPropertyInt(p,c_playerPropDamageDealtPercent,c_playerPropOperSetTo,100);\n'
                 '        gf_rmEHStart(p);\n'
                 '        PlayerModifyPropertyInt(p,c_playerPropDamageTakenPercent,c_playerPropOperSetTo,100);\n'
                 '        TechTreeUpgradeAddLevel(p,"ProtossGroundWeaponsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ProtossGroundWeaponsLevel1",c_techCountCompleteOnly)));\n'
                 '        TechTreeUpgradeAddLevel(p,"ProtossGroundArmorsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ProtossGroundArmorsLevel1",c_techCountCompleteOnly)));\n'
                 '        gf_rmVHProtoss(p);\n'
                 '    }\n}\n') + t[b:]
    t = sub1(t, '                else if (p==1 || p==4 || p>=8) {', '                else if (p==1 || p>=8) {')
    # Codex review: the 0.6.40 extra production buildings came over Zerg-only (mission 6). Tal'darim get the mission 4 set.
    t = sub1(t, '        if (gf_rmVHBaseBuild(p,"RoachWarren",c)) { n += 1; }\n    }\n',
             '        if (gf_rmVHBaseBuild(p,"RoachWarren",c)) { n += 1; }\n    }\n'
             '    else if (r=="Prot") {\n'
             '        if (gf_rmVHBaseBuild(p,"Pylon",c)) { n += 1; }\n'
             '        if (gf_rmVHBaseBuild(p,"Gateway",c)) { n += 1; }\n'
             '        if (gf_rmVHBaseBuild(p,"Gateway",c)) { n += 1; }\n    }\n')
    t = sub1(t, '    if (k=="RoachWarren") {\n        gf_rmVHBaseUnits(b,"Roach",2,s);\n    }\n',
             '    if (k=="RoachWarren") {\n        gf_rmVHBaseUnits(b,"Roach",2,s);\n    }\n'
             '    if (k=="Gateway") {\n        gf_rmVHBaseUnits(b,"Zealot",2,s);\n        gf_rmVHBaseUnits(b,"Stalker",1,s);\n    }\n')
    # Goliath / Siege Tank -> Spartan Company / Siege Breakers (merc table), placed and trained.
    for fn in ('gf_m7_Reapers', 'gt_m7_TrainMerc_Func'):
        a = t.index(fn + ' (')
        old = '        else if (t=="Reaper") { libNtve_gf_ReplaceUnit(u,"MercReaper",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'
        if fn.startswith('gt'): old = old[4:]
        i = t.index(old, a)
        ind = old[:len(old) - len(old.lstrip())]
        add = (f'{ind}else if (t=="Goliath") {{ libNtve_gf_ReplaceUnit(u,"SpartanCompany",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }}\n'
               f'{ind}else if (t=="SiegeTank") {{ libNtve_gf_ReplaceUnit(u,"SiegeBreaker",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }}\n')
        t = t[:i + len(old)] + add + t[i + len(old):]
    t = sub1(t, '    CatalogFieldValueSet(c_gameCatalogAbil,"BarracksTrain","InfoArray[Train2].Unit[0]",1,"MercReaper");\n',
             '    CatalogFieldValueSet(c_gameCatalogAbil,"BarracksTrain","InfoArray[Train2].Unit[0]",1,"MercReaper");\n'
             '    // 0.6.70: Raynor\'s factory trains Spartan Company / Siege Breakers (player 1 only data).\n'
             '    CatalogFieldValueSet(c_gameCatalogAbil,"FactoryTrain","InfoArray[Train7].Unit[0]",1,"SpartanCompany");\n'
             '    CatalogFieldValueSet(c_gameCatalogAbil,"FactoryTrain","InfoArray[Train2].Unit[0]",1,"SiegeBreaker");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"Goliath","Icon",1,"Assets\\\\Textures\\\\btn-unit-terran-goliathmercenary.dds");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"Goliath","Name",1,"Button/Name/RM_SpartanCompany");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"Goliath","Tooltip",1,"Button/Tooltip/RM_SpartanCompany");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"SiegeTank","Icon",1,"Assets\\\\Textures\\\\btn-unit-terran-siegetankmercenary-tank.dds");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"SiegeTank","Name",1,"Button/Name/RM_SiegeBreaker");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"SiegeTank","Tooltip",1,"Button/Tooltip/RM_SiegeBreaker");\n')
    t = sub1(t, '    TechTreeUnitAllow(1,"MercReaper",TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",1)));\n',
             '    TechTreeUnitAllow(1,"MercReaper",TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",1)));\n'
             '    TechTreeUnitAllow(1,"SpartanCompany",TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",6)));\n'
             '    TechTreeUnitAllow(1,"SiegeBreaker",TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",1)));\n')
    for bad in ('_m6_', '33.5,44.5', 'p==4 ||', 'gf_rmZergBuff(2)'):
        assert bad not in t, bad
    return t


def waves(t):
    def up(m):
        return m.group(1) + ', '.join(str(math.ceil(int(n) * WAVE_MULT)) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n == 59, n
    return t.replace('AIAttackWaveAddUnits4(', 'gf_rmWave4(')


FREE = '''// 0.4.109: Hyperion mercenary contracts bought for free (user 2026-10-25). Status only, no credits.
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


def script(raw, mod6):
    a, b = blocks(mod6)
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = waves(t)
    inc = 'include "TriggerLibs/CampaignLib"\n'
    mark = '\n// @@RM_SPLIT@@\n'
    a, b = adapt(a + mark + b).split(mark)
    t = sub1(t, inc, inc + a)
    t = sub1(t, 'void InitGlobals () {', b + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTosh02);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTosh02);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m7_Init();\n')
    # Codex review: enemy AI one slot up before the original starts the campaign AI and registers the first waves
    # (gf_rmAIUp runs once per player; the later call from gf_m7_EnemyRules does nothing).
    t = sub1(t, '    TriggerExecute(gt_StartAI, true, false);\n',
             '    gf_rmAIUp(2);\n    gf_rmAIUp(3);\n    gf_rmAIUp(4);\n    TriggerExecute(gt_StartAI, true, false);\n')
    t = sub1(t, '    TriggerExecute(gt_StartGame, true, false);\n', '    gf_m7_Start();\n    TriggerExecute(gt_StartGame, true, false);\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n', 'void InitMap () {\n    InitLibs();\n    AchievementsDisable(1);\n')
    return t.replace('\n', '\r\n').encode('utf-8')


def objects(data):
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
        elif ut == 'Refinery':  # 0.6.74: rich refinery too
            el.set('UnitType', 'RefineryRich'); el.set('Resources', str(int(el.get('Resources')) * 2)); gas += 1
        else: continue
        k = 2 if ut in ('VespeneGeyser', 'Refinery') else None  # 0.6.74: per-difficulty reserves (Index 3/4) too
        for r in el.findall('Resources'):
            v = int(r.get('Value')); r.set('Value', str(v * 2 if k else v * 120 // 100))
    assert (rich, gas) == (8, 2), (rich, gas)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def strings(orig7, mod6, orig6_keys):
    text = orig7.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod6.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig6_keys or k.startswith('MapInfo/'): continue
        add[k] = v
    add.update(STRS)
    out = (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')
    return set_strings(out, {k: f'{ko} /// {en}' for k, (ko, en) in NAMES.items()})


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig and len(orig) == 36, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(M7) for n in prev.namelist())
        files = dict(orig)
        mod6 = {n[len(M6):]: prev.read(n) for n in prev.namelist() if n.startswith(M6)}
        o6 = HERE.parent / 'maps/original_wol/thanson01'
        for rel, data in mod6.items():
            low = rel.lower()
            if low.startswith('assets/'):
                files[rel] = data
            elif low.startswith(GD) and rel not in ENV:
                files[rel] = merge(data, orig[rel]) if rel in orig else data
            elif low.endswith('gamehotkeys.txt'):
                files[rel] = data
        o6k = {l.split('=', 1)[0] for l in (o6 / KO).read_text(encoding='utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], mod6[KO], o6k)
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
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'], mod6['mapscript.galaxy'].decode('utf-8-sig'))
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
                for name in sorted(files):
                    zi = zipfile.ZipInfo(M7 + name, date_time=(2026, 11, 22, 0, 0, 0))
                    zi.external_attr = 0o644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
                    out.writestr(zi, files[name])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'TTosh02 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
