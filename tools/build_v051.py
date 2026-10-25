#!/usr/bin/env python3
"""Build CCM 0.5.1 from 0.4.109: 5번 미션 TTosh01 (Devil's Playground, 레드스톤 III) 추가 (사용자 2026-10-25).

원본: maps/original_wol/ttosh01 (사용자 드라이브의 블리자드 캠페인 추출본). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 4번 어부지리(0.4.109)의 모드 층을 그대로 옮긴다:
  - 데이터·에셋·모드 문자열·단축키 (어부지리 고유 환경 light/terrain/water/gamedata.xml은 레드스톤 원본 것을 쓴다)
  - 스크립트 공통 묶음 (gf_m4_* -> gf_m5_*): 용병 생산·연구, 동맹 8 정화자 / 9 원시저그(넥서스·원시 군락만 플레이어가,
    그 뒤는 동맹이 짓고 생산·채굴, 채굴량 50%는 레이너에게), 핑, 레이너 해금 -> 동맹 해금, 공방업 연동, 용병 계약 무료.
레드스톤 맞춤:
  - 플레이어: 1 레이너, 2·4 저그(적), 3 용암(적), 5 토시(아군), 6 스완(중립). 동맹 8·9를 새로 넣는다.
  - 7-1 저그 규칙: 2·4 능력치 10% + 공세(AIAttackWaveAddUnits4) +50% (시험값).
  - 레이너 본진 (41.5,88.5): 풍부한 광물 9덩이 매장량 +20%, 가스 2곳 풍부한 가스·+100% (4번 이후 공통 규칙).
  - 사신 -> 죽음의 우두머리(MercReaper, 군심 캠페인 데이터를 port_units.py로 이식). 토시가 넘겨준 사신도 바꾼다.
사용자 지시 (2026-10-25):
  - 동맹 일꾼 1기 추가: 탐사정 1 -> 2, 원시 일벌레 4 -> 5.
  - 동맹은 자원을 캐서 레이너를 지원하고(기존 50%), 적대 지역에 전투 유닛을 보낸다(기존 공격 판단).
  - 용암이 차오를 때(차오르기 LAVA_LEAD초 전부터 가라앉을 때까지) 동맹 병력·채굴 일꾼은 높은 곳으로 피한다.
    원본 용암 피해는 지상 높이 8.5 이하. 높이 SAFE_H 이하에 있으면 가장 가까운 높은 곳(SAFE_H 초과, 길로 이어진 곳)으로 이동.

Usage: python3 tools/build_v051.py <0.4.109 zip> <ttosh01 folder> <work dir (new)> <new output zip>
"""
import argparse, copy, re, shutil, subprocess, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import patch_mission01 as m1
from build_v041 import merge

OLD, NEW = b'version=0.4.109', b'version=0.5.1'
M4, M5 = 'TTychus01.SC2Map/', 'TTosh01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ENV = {GD + 'lightdata.xml', GD + 'terraindata.xml', GD + 'waterdata.xml', GD + 'gamedata.xml'}
ALLIES = [(8, b'Prot', '정화자', 'Purifiers'), (9, b'Zerg', '원시저그', 'Primal Zerg')]
CC = (41.5, 88.5)          # Raynor's Command Center / start location
RALLY8, RALLY9 = (52.0, 85.0), (52.0, 90.0)   # ally gathering points (trial)
PROBE_AT, DRONE_AT, POD_AT = (45.0, 81.0), (46.0, 80.0), (47.0, 80.0)  # worker landing (trial)
LAVA_LEAD = 25.0           # seconds before the surge the allies start to leave (trial)
SAFE_H = 9.5               # lava hurts ground at height <= 8.5 (original LavaDamage)
STRINGS = {
    'rm5/Adj3': '용암이 차오르기 전에 동맹 병력과 채굴 일꾼은 높은 곳으로 피합니다. 낮은 땅의 동맹 건물은 용암에 피해를 입으니 동맹 기지는 높은 곳에 지으세요. /// '
                'Allied forces and miners move to high ground before the lava rises. Allied structures on low ground take lava damage, so build allied bases on high ground.',
    'Unit/Name/MercReaper': '죽음의 우두머리 /// Death Head',
    'Button/Name/RM_MercReaper': '죽음의 우두머리 훈련 /// Train Death Head',
    'Button/Tooltip/RM_MercReaper': '용병 사신 죽음의 우두머리를 훈련합니다. 절벽을 뛰어넘고 D-8 폭약을 던집니다. /// Trains a Death Head mercenary reaper. Jumps cliffs and throws D-8 charges.',
}

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

LAVA_FN = f'''// 0.5.1: lava (user 2026-10-25): allies leave low ground before the surge and stay up until it is gone.
point gf_m5_HighGround (point from) {{
    int r;
    int a;
    point p;
    for (r=3;r<=30;r+=3) {{
        for (a=0;a<360;a+=30) {{
            p=PointWithOffsetPolar(from,IntToFixed(r),IntToFixed(a));
            if (WorldHeight(c_heightMapGround,p)>{SAFE_H} && PointPathingPassable(p) && PointPathingIsConnected(from,p)) {{ return p; }}
        }}
    }}
    return null;
}}

bool gf_m5_LavaSoon () {{
    if (!gv_lowGroundIsSafe) {{ return true; }}
    return TimerGetDuration(gv_lavaTimer)>0.0 && TimerGetRemaining(gv_lavaTimer)<={LAVA_LEAD};
}}

bool gf_m5_Lava () {{
    unitgroup g;
    unit u;
    int pl;
    int i;
    string t;
    point to;
    if (!gf_m5_LavaSoon()) {{ return false; }}
    for (pl=8;pl<=9;pl+=1) {{
        g=UnitGroup(null,pl,RegionEntireMap(),UnitFilter(0,0,(1 << c_targetFilterStructure) | (1 << c_targetFilterAir),(1 << (c_targetFilterDead - 32))),0);
        i=UnitGroupCount(g,c_unitCountAll);
        for (;i>0;i-=1) {{
            u=UnitGroupUnit(g,i);
            t=UnitGetType(u);
            // Workers still in the player's hands are the player's call.
            if ((t=="Probe" || t=="DehakaDrone") && !UnitHasBehavior2(u,"RM_AllyMiner") && !gv_rmBaseUp[pl]) {{ continue; }}
            if (WorldHeight(c_heightMapGround,UnitGetPosition(u))>{SAFE_H}) {{
                // Already safe: do not walk back down while the lava is coming.
                if (UnitOrderCount(u)>0 && AbilityCommandGetAbility(OrderGetAbilityCommand(UnitOrder(u,0)))!="move" && OrderGetTargetType(UnitOrder(u,0))==c_orderTargetPoint
                    && WorldHeight(c_heightMapGround,OrderGetTargetPoint(UnitOrder(u,0)))<={SAFE_H}) {{
                    UnitIssueOrder(u,Order(AbilityCommand("stop",0)),c_orderQueueReplace);
                }}
                continue;
            }}
            if (UnitOrderCount(u)>0 && AbilityCommandGetAbility(OrderGetAbilityCommand(UnitOrder(u,0)))=="move") {{ continue; }}
            to=gf_m5_HighGround(UnitGetPosition(u));
            if (to!=null) {{ UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("move",0),to),c_orderQueueReplace); }}
        }}
    }}
    return true;
}}

// 0.5.1: Tosh hands his reapers to Raynor; Raynor's reapers are the Death Head mercenary.
void gf_m5_Reapers () {{
    unitgroup g=UnitGroup("Reaper",1,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    int i=UnitGroupCount(g,c_unitCountAll);
    if (gv_inCinematic) {{ return; }}
    for (;i>0;i-=1) {{ libNtve_gf_ReplaceUnit(UnitGroupUnit(g,i),"MercReaper",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }}
}}

'''


def m4_block(script):
    t = script.replace('\r\n', '\n')
    a = t.index('\n// Common pack for missions after 3')
    b = t.index('\n}\n', t.index('void gf_m4_Init () {')) + 3
    return t[a + 1:b]


def sub1(t, a, b, n=1):
    assert t.count(a) == n, (a, t.count(a))
    return t.replace(a, b)


def adapt(block):
    t = re.sub(r'\b(g[vft])_m4_', r'\1_m5_', block)
    t = sub1(t, '// Common pack for missions after 3 (docs/missions/nonlinear_design.md). Mission 4 = TTychus01 (Smash and Grab).\n'
                '// Allies: 8 Purifiers, 9 Primal Zerg. Enemies: 2 Zerg, 3-6 Tal\'darim. 7 is the Protoss relic (neutral).\n'
                '// Coordinates and timings are trial values (docs/missions/04_smash_and_grab.md).',
             '// Common pack for missions after 3 (docs/missions/nonlinear_design.md), ported from mission 4 (0.4.109).\n'
             '// Mission 5 = TTosh01 (Devil\'s Playground). Allies: 8 Purifiers, 9 Primal Zerg. Enemies: 2, 4 Zerg; 3 lava.\n'
             '// 5 Tosh (ally), 6 Swann (neutral). Coordinates and timings are trial values (docs/missions/05_devils_playground.md).')
    t = sub1(t, '    return (p>=2 && p<=6);', '    return (p==2 || p==4);')
    t = sub1(t, '    for (p=2;p<=6;p+=1) {', '    for (p=2;p<=4;p+=2) {', 2)
    t = sub1(t, 'Point(78.0,21.0)', f'Point({CC[0]},{CC[1]})', 3)
    t = sub1(t, 'if (p==8) { rally=Point(63.0,29.0);', f'if (p==8) {{ rally=Point({RALLY8[0]},{RALLY8[1]});')
    t = sub1(t, 'else { rally=Point(66.0,30.0);', f'else {{ rally=Point({RALLY9[0]},{RALLY9[1]});')
    # 7-1 Zerg rule only (both Zerg players); no Tal'darim here.
    a = t.index('void gf_m5_EnemyRules () {')
    b = t.index('\n}\n', a) + 3
    t = t[:a] + ('void gf_m5_EnemyRules () {\n'
                 '    // 7-1 Zerg (user 2026-10-17/24): more units (attack waves +50% in the original triggers) and a flat 10% stat buff.\n'
                 '    gf_rmZergBuff(2);\n    gf_rmZergBuff(4);\n}\n') + t[b:]
    t = sub1(t, '    gf_rmEnemyFastProd(2,6);\n', '    gf_rmEnemyFastProd(2,2);\n    gf_rmEnemyFastProd(4,4);\n    gf_m5_Reapers();\n')
    # Worker landing spots in Raynor's base (trial). One more worker each (user 2026-10-25).
    t = sub1(t, 'Point(67.0,27.0)', f'Point({POD_AT[0]},{POD_AT[1]})', 2)
    t = sub1(t, 'Point(66.0+1.0*i,27.0)', f'Point({DRONE_AT[0]}+1.0*i,{DRONE_AT[1]})', 2)
    t = sub1(t, 'Point(64.0,26.0)', f'Point({PROBE_AT[0]},{PROBE_AT[1]})', 3)
    t = sub1(t, '    UnitCreate(1,"Probe",0,8,Point(45.0,81.0),270.0);\n    for (i=0;i<4;i+=1) {',
             '    UnitCreate(2,"Probe",0,8,Point(45.0,81.0),270.0);\n    for (i=0;i<5;i+=1) {')
    t = sub1(t, '    TriggerQueueExit();\n    return true;\n}',
             '    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm4/AdjName"),StringExternal("rm5/Adj3"),7.0,c_transmissionDurationSet,true);\n'
             '    TriggerQueueExit();\n    return true;\n}')
    # Alliances: the lava player is hostile to the allies too; Tosh is friendly, Swann neutral.
    t = sub1(t, '                if (gf_m5_IsEnemy(p)) {', '                if (gf_m5_IsEnemy(p) || p==3) {')
    t = sub1(t, '                else if (p==1 || p>=8) {', '                else if (p==1 || p==5 || p>=8) {')
    # Mercenary reaper (Barracks Train2).
    t = sub1(t, '    TechTreeUnitAllow(1,"DevilDog",TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",5)));\n',
             '    TechTreeUnitAllow(1,"DevilDog",TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",5)));\n'
             '    TechTreeUnitAllow(1,"MercReaper",TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",1)));\n')
    t = sub1(t, '    else if (t=="Firebat") { libNtve_gf_ReplaceUnit(u,"DevilDog",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n',
             '    else if (t=="Firebat") { libNtve_gf_ReplaceUnit(u,"DevilDog",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'
             '    else if (t=="Reaper") { libNtve_gf_ReplaceUnit(u,"MercReaper",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n')
    t = sub1(t, '    CatalogFieldValueSet(c_gameCatalogAbil,"BarracksTrain","InfoArray[Train6].Unit[0]",1,"DevilDog");\n',
             '    CatalogFieldValueSet(c_gameCatalogAbil,"BarracksTrain","InfoArray[Train6].Unit[0]",1,"DevilDog");\n'
             '    CatalogFieldValueSet(c_gameCatalogAbil,"BarracksTrain","InfoArray[Train2].Unit[0]",1,"MercReaper");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"Reaper","Icon",1,"Assets\\\\Textures\\\\btn-unit-terran-reapermercenary.dds");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"Reaper","Name",1,"Button/Name/RM_MercReaper");\n'
             '    CatalogFieldValueSet(c_gameCatalogButton,"Reaper","Tooltip",1,"Button/Tooltip/RM_MercReaper");\n')
    # Lava: before the tick; while it is coming the allies hold high ground instead of attacking.
    t = sub1(t, 'bool gt_m5_Tick_Func (bool testConds,bool runActions) {', LAVA_FN + 'bool gt_m5_Tick_Func (bool testConds,bool runActions) {')
    t = sub1(t, '    gf_rmPhase(8,9,3,3);\n    gf_m5_FindThreat();\n',
             '    gf_rmPhase(8,9,3,3);\n    if (gf_m5_Lava()) { return true; }\n    gf_m5_FindThreat();\n')
    assert '_m4_' not in t and 'Tal\'darim (3-6)' not in t
    return t


def waves(t):
    up = lambda m: m.group(1) + ', '.join(str(int(n) + int(n) // 2) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n >= 25, n
    return t


def script(raw, block):
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = waves(t)
    t = sub1(t, 'UnitCreate(1, "Marine", 0, gv_p01_USER,', 'UnitCreate(1, "WarPig", 0, gv_p01_USER,')
    t = sub1(t, 'UnitCreate(1, "Medic", 0, gv_p01_USER,', 'UnitCreate(1, "MercMedic", 0, gv_p01_USER,')
    t = sub1(t, 'void InitGlobals () {', adapt(block) + '\n' + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE_MERC_FN + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTosh01);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTosh01);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m5_Init();\n')
    t = sub1(t, '    TriggerExecute(gt_FirstSurge, true, false);\n', '    gf_m5_Start();\n    TriggerExecute(gt_FirstSurge, true, false);\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n', 'void InitMap () {\n    InitLibs();\n    AchievementsDisable(1);\n')
    return t.replace('\n', '\r\n').encode('utf-8')


def objects(data):
    import math
    root = E.fromstring(data)
    marines = rich = gas = 0
    for el in root:
        if el.tag != 'ObjectUnit': continue
        ut = el.get('UnitType')
        if el.get('Player') == '1' and ut in ('Marine', 'Medic'):
            el.set('UnitType', {'Marine': 'WarPig', 'Medic': 'MercMedic'}[ut]); marines += 1
            continue
        x, y = (float(v) for v in el.get('Position').split(',')[:2])
        if math.hypot(x - CC[0], y - CC[1]) > 16: continue
        if ut == 'RichMineralField':
            el.set('Resources', str(int(el.get('Resources')) * 120 // 100)); rich += 1
        elif ut == 'VespeneGeyser':
            el.set('UnitType', 'RichVespeneGeyser'); el.set('Resources', str(2500 * 2)); gas += 1
    assert (marines, rich, gas) == (2, 9, 2), (marines, rich, gas)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def mapinfo(d):
    shift = d.index(b'\x01\x01\x00\x00\x00', 0x90) - 0xa2   # map-name length moves the player table
    co = 0x87 + shift
    count = int.from_bytes(d[co:co + 4], 'little')
    pos = 0xa2 + shift
    for _ in range(1, count):
        assert 1 <= d[pos] <= 15, (pos, d[pos])
        pos = d.index(0, pos + 26) + 1
    recs = b''.join(bytes([n, 2]) + b'\0' * 3 + (-1).to_bytes(4, 'little', signed=True) + race + b'\0' * 14 for n, race, *_ in ALLIES)
    out = bytearray(d[:pos] + recs + d[pos:])
    out[co:co + 4] = (count + len(ALLIES)).to_bytes(4, 'little')
    return bytes(out)


def strings(orig5, mod4, orig4_keys):
    text = orig5.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod4.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig4_keys: continue
        add[k] = v
    add.update(STRINGS)
    return (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')


def set_strings(raw, vals):
    lines = raw.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n').split('\n')
    keys = {l.split('=', 1)[0]: i for i, l in enumerate(lines) if '=' in l}
    for k, v in vals.items():
        if k in keys: lines[keys[k]] = f'{k}={v}'
        else: lines.append(f'{k}={v}')
    return ('\n'.join(lines) + '\n').replace('\n', '\r\n').encode('utf-8')


def build(source, folder, work, output):
    if output.exists(): raise ValueError('Output must be new')
    if work.exists(): raise ValueError('Work dir must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig and len(orig) == 38, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(M5) for n in prev.namelist())
        files = dict(orig)
        mod4 = {n[len(M4):]: prev.read(n) for n in prev.namelist() if n.startswith(M4)}
        o4 = Path(HERE.parent / 'maps/original_wol/ttychus01')
        for rel, data in mod4.items():
            low = rel.lower()
            if low.startswith('assets/'):
                files[rel] = data
            elif low.startswith(GD) and rel not in ENV:
                files[rel] = merge(data, orig[rel]) if rel in orig else data
            elif low.endswith('gamehotkeys.txt'):
                files[rel] = data
        o4k = {l.split('=', 1)[0] for l in (o4 / KO).read_text(encoding='utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], mod4[KO], o4k)
        files['objects'] = objects(files['objects'])
        files['mapinfo'] = mapinfo(files['mapinfo'])
        saved = m1.ALLY_PLAYERS
        m1.ALLY_PLAYERS = ALLIES
        try: files['documentheader'] = m1.patch_header(files['documentheader'])
        finally: m1.ALLY_PLAYERS = saved
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'], m4_block(mod4['mapscript.galaxy'].decode('utf-8-sig')))
        # Port the mercenary reaper from the Swarm campaign data (same tool as the earlier co-op ports).
        for rel, data in files.items():
            p = work / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), '--liberty-base', '--skip-existing', str(work), 'MercReaper'], check=True)
        (work / 'ported_shared_refs.txt').unlink()
        files = {str(p.relative_to(work)).replace('\\', '/'): p.read_bytes() for p in work.rglob('*') if p.is_file()}
        # Port gaps: the landing sound actor lives in swarm.sc2mod (the sound itself is in Liberty);
        # the co-op Raynor drop-pod look has no base model here and is not used in the campaign.
        ad = files[GD + 'actordata.xml'].decode('utf-8')
        ad = sub1(ad, '        <On Terms="Behavior.MercGroundDropRaynor.Create" Send="Create MercReaperDropModelRaynor" />\n', '')
        ad = sub1(ad, '    <CActorModel id="MercReaperDropModelRaynor" parent="MercDropModelRaynorBase">\n'
                      '        <On Terms="ActorCreation" Send="SetScale 0.800000" />\n    </CActorModel>\n', '')
        assert 'id="Reaper_Land"' not in ad
        ad = sub1(ad, '</Catalog>', '    <CActorSound id="Reaper_Land" parent="SoundOneShot" />\n</Catalog>')
        files[GD + 'actordata.xml'] = ad.encode('utf-8')
        # Swarm-campaign names of the ported reaper (English from SC2GameData 6dd323a; Korean by the mod, not official text).
        files[KO] = set_strings(files[KO], {'Unit/Name/MercReaper': STRINGS['Unit/Name/MercReaper'],
            'Button/Name/MercReaper': '죽음의 우두머리 /// Death Head',
            'Weapon/Name/MercReaperP38ScytheGuassPistol': 'P-55 "사이드" 가우스 권총 /// P-55 "Scythe" Gauss Pistol',
            'Weapon/Name/MercReaperD8Charge': 'D-9 폭약 /// D-9 Charge',
            'Unit/Name/MercReaperD8ChargeWeapon': 'D-9 폭약 /// D-9 Charge',
            'Behavior/Name/MercReaperJump': '제트팩 /// Jet Pack'})
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
                for name in sorted(files): out.writestr(M5 + name, files[name])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'TTosh01 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path)
    p.add_argument('work', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.work, a.output)
