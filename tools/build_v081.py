#!/usr/bin/env python3
"""Build CCM 0.8.1 from 0.6.78: 8번 미션 THorner01 (The Great Train Robbery, 대열차 강도) 추가 (사용자 2026-11-23 "다음미션 열차 강도").

원본: maps/original_wol/thorner01 (사용자 드라이브의 블리자드 캠페인 추출본, 40개 파일). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 정글의 법칙(TTosh02, 0.6.78)의 모드 층을 그대로 옮긴다 (gf_m7_* -> gf_m8_*):
  데이터·에셋·모드 문자열·단축키, 용병 생산·연구(스파르타 중대·공성 파괴단·방벽 중대 포함), 동맹 8 정화자 / 9 원시저그(지원 버튼, 일꾼 없음),
  핑, 해금·공방업 연동, 용병 계약 무료, 연구실 단계·피닉스 용사, 고갈되지 않는 자원, 동맹 연구 건물, 적 7-1 규칙 모듈.
열차 강도 맞춤:
  - 플레이어: 1 레이너, 2·3·4 자치령(테란, 적), 5 버려진 차량(중립), 6 열차(적, 원본이 따로 다룸 - 7-1 강화 안 걸음), 7 뼈 표본(중립).
    mapinfo 레코드가 0~7번 모두 있어 동맹 8·9 이름 키 = Player08/09.
  - 7-1 테란 규칙(2번 미션과 같은 종류): 피해 % 100, 적 무기 업그레이드 +50%(RM_EH), 보병 공방 최소 1단계(원본과 안 겹침),
    공세 수 x1.25(올림), 적 AI 한 단계 위, 어려움 이상 유닛 연구·추가 생산 건물(병영 1·군수 공장 1, SCV 4·수리;
    병영 해병 3·의무관 1 / 군수 공장 화염방사병 대신 이 미션 공세에 나오는 공성 전차 1 - 시험값).
  - 레이너 본진 = 사령부 (130.5,94.5): 광물 8덩이 풍부한 광물·매장량 +20%, 가스 1곳·정제소 1개 풍부·+100%.
  - 동맹 집결지는 사령부 서쪽 시작 해병 자리 근처 (시험값).
Game not run.

Usage: python3 tools/build_v081.py <0.6.78 zip> <thorner01 folder> <new output zip>
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

OLD, NEW = b'version=0.6.78', b'version=0.8.1'
M7, M8 = 'TTosh02.SC2Map/', 'THorner01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ENV = {GD + 'lightdata.xml', GD + 'terraindata.xml', GD + 'waterdata.xml', GD + 'gamedata.xml'}
ALLIES = [(8, b'Prot', '정화자', 'Purifiers'), (9, b'Zerg', '원시저그', 'Primal Zerg')]
CC = (130.5, 94.5)                              # Raynor's Command Center (minerals to the north-east)
OLD_CC = '79.5,25.5'
RALLY8, RALLY9 = (121.0, 91.0), (121.0, 94.0)   # trial, west of the CC where the starting marines stand
NAMES = {'MapInfo/Player08/Name': ('정화자', 'Purifiers'), 'MapInfo/Player09/Name': ('원시저그', 'Primal Zerg')}
WAVE_MULT = 1.25


def blocks(mod):
    """The two mod blocks of mission 7: after the includes, and the common pack right before InitGlobals."""
    t = mod.replace('\r\n', '\n')
    inc = 'include "TriggerLibs/CampaignLib"\n'
    a0 = t.index(inc) + len(inc)
    a1 = t.index('\n//--------------------------------------------------------------------------------------------------\n// Library Initialization', a0)
    b0 = t.index('\n// Common pack for missions after 3') + 1
    b1 = t.index('void InitGlobals () {')
    return t[a0:a1 + 1], t[b0:b1]


def adapt(block):
    t = re.sub(r'\b(g[vft])_m7_', r'\1_m8_', block)
    t = sub1(t, '// Mission 7 = TTosh02 (Welcome to the Jungle), ported from mission 6 (0.6.69). Allies: 8 Purifiers, 9 Primal Zerg.\n'
                '// Enemies: 2, 3, 4 Tal\'darim (Protoss); 5 Terrazine (neutral). Coordinates and timings are trial values (docs/missions/07_welcome_to_the_jungle.md).',
             '// Mission 8 = THorner01 (The Great Train Robbery), ported from mission 7 (0.6.78). Allies: 8 Purifiers, 9 Primal Zerg.\n'
             '// Enemies: 2, 3, 4 Dominion (Terran); 6 trains (left to the original). Coordinates and timings are trial values (docs/missions/08_great_train_robbery.md).')
    # Codex review: the trains (player 6) are what the mission is about - allies must treat them as enemies too
    # (diplomacy, attack targets). 7-1 buffs stay on 2-4 only (gf_m8_EnemyRules).
    t = sub1(t, '    return (p==2 || p==3 || p==4);', '    return (p==2 || p==3 || p==4 || p==6);')
    t = sub1(t, f'Point({OLD_CC})', f'Point({CC[0]},{CC[1]})', 4)
    t = sub1(t, 'rally=Point(72.0,30.0);', f'rally=Point({RALLY8[0]},{RALLY8[1]});')
    t = sub1(t, 'rally=Point(73.0,32.0);', f'rally=Point({RALLY9[0]},{RALLY9[1]});')
    t = sub1(t, 'Point(73.0,27.0)', 'Point(124.0,91.0)')
    t = sub1(t, 'Point(72.0+1.0*i,27.0)', 'Point(123.0+1.0*i,91.0)')
    t = sub1(t, 'Point(71.0,28.0)', 'Point(122.0,92.0)')
    t = sub1(t, '// Mission 7 has no lava (Redstone only)', '// Mission 8 has no lava (Redstone only)')
    a = t.index('void gf_m8_EnemyRules () {')
    b = t.index('\n}\n', a) + 3
    t = t[:a] + ('void gf_m8_EnemyRules () {\n'
                 '    int p;\n'
                 '    // 7-1 Terran (user 2026-10-14, as the Dominion in missions 1-2): weapon upgrades +50% (RM_EH), level-1 infantry\n'
                 '    // upgrades without stacking on what the original gave; damage % stays 100 (0.6.29). Trains (6) are left to the original.\n'
                 '    for (p=2;p<=4;p+=1) {\n'
                 '        PlayerModifyPropertyInt(p,c_playerPropDamageDealtPercent,c_playerPropOperSetTo,100);\n'
                 '        gf_rmEHStart(p);\n'
                 '        PlayerModifyPropertyInt(p,c_playerPropDamageTakenPercent,c_playerPropOperSetTo,100);\n'
                 '        TechTreeUpgradeAddLevel(p,"TerranInfantryWeaponsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"TerranInfantryWeaponsLevel1",c_techCountCompleteOnly)));\n'
                 '        TechTreeUpgradeAddLevel(p,"TerranInfantryArmorsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"TerranInfantryArmorsLevel1",c_techCountCompleteOnly)));\n'
                 '        gf_rmVHTerran(p);\n'
                 '    }\n}\n') + t[b:]
    # Extra production buildings (0.6.40/0.6.47): the pack came with Zerg and Protoss sets only. Dominion gets mission 2's set.
    t = sub1(t, '        if (gf_rmVHBaseBuild(p,"Gateway",c)) { n += 1; }\n        if (gf_rmVHBaseBuild(p,"Gateway",c)) { n += 1; }\n    }\n',
             '        if (gf_rmVHBaseBuild(p,"Gateway",c)) { n += 1; }\n        if (gf_rmVHBaseBuild(p,"Gateway",c)) { n += 1; }\n    }\n'
             '    else if (r=="Terr") {\n'
             '        // 0.8.1: as mission 2 (0.6.47/0.6.50): 1 Barracks + 1 Factory, 4 extra SCVs and AI repair.\n'
             '        if (gf_rmVHBaseBuild(p,"Barracks",c)) { n += 1; }\n'
             '        if (gf_rmVHBaseBuild(p,"Factory",c)) { n += 1; }\n'
             '        UnitCreate(4, "SCV", 0, p, UnitTypePlacementFromPoint("SCV", p, c, 8.0), 270.0);\n'
             '        AISetDifficulty(p, c_diffRepairDamage, true);\n    }\n')
    t = sub1(t, '    if (k=="Gateway") {\n        gf_rmVHBaseUnits(b,"Zealot",2,s);\n        gf_rmVHBaseUnits(b,"Stalker",1,s);\n    }\n',
             '    if (k=="Gateway") {\n        gf_rmVHBaseUnits(b,"Zealot",2,s);\n        gf_rmVHBaseUnits(b,"Stalker",1,s);\n    }\n'
             '    // 0.8.1: units from this mission\'s waves (trial).\n'
             '    if (k=="Barracks") {\n        gf_rmVHBaseUnits(b,"Marine",3,s);\n        gf_rmVHBaseUnits(b,"Medic",1,s);\n    }\n'
             '    if (k=="Factory") {\n        gf_rmVHBaseUnits(b,"SiegeTank",1,s);\n    }\n')
    for bad in ('_m7_', OLD_CC, 'gf_rmVHProtoss(p);\n    }\n}'):
        assert bad not in t, bad
    return t


def waves(t):
    def up(m):
        return m.group(1) + ', '.join(str(math.ceil(int(n) * WAVE_MULT)) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n == 37, n
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


def script(raw, mod7):
    a, b = blocks(mod7)
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = waves(t)
    inc = 'include "TriggerLibs/CampaignLib"\n'
    mark = '\n// @@RM_SPLIT@@\n'
    a, b = adapt(a + mark + b).split(mark)
    t = sub1(t, inc, inc + a)
    t = sub1(t, 'void InitGlobals () {', b + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner01);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner01);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m8_Init();\n')
    # Enemy AI one slot up before the original starts the campaign AI (as mission 7).
    t = sub1(t, '    TriggerExecute(gt_StartAI, true, false);\n',
             '    gf_rmAIUp(2);\n    gf_rmAIUp(3);\n    gf_rmAIUp(4);\n    TriggerExecute(gt_StartAI, true, false);\n')
    t = sub1(t, '    TriggerExecute(gt_StartGame, true, false);\n', '    gf_m8_Start();\n    TriggerExecute(gt_StartGame, true, false);\n')
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
        elif ut == 'Refinery':
            el.set('UnitType', 'RefineryRich'); el.set('Resources', str(int(el.get('Resources')) * 2)); gas += 1
        else: continue
        k = ut in ('VespeneGeyser', 'Refinery')
        for r in el.findall('Resources'):
            v = int(r.get('Value')); r.set('Value', str(v * 2 if k else v * 120 // 100))
    assert (rich, gas) == (8, 2), (rich, gas)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def strings(orig8, mod7, orig7_keys):
    text = orig8.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod7.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig7_keys or k.startswith('MapInfo/'): continue
        add[k] = v
    out = (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')
    vals = {k: f'{ko} /// {en}' for k, (ko, en) in NAMES.items()}
    # Original untranslated fragment (unused by the script): Korean part for the 3-1 rule.
    vals['Param/Value/41368F16'] = ' (이전 ///  (was '
    return set_strings(out, vals)


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig and len(orig) == 40, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(M8) for n in prev.namelist())
        files = dict(orig)
        mod7 = {n[len(M7):]: prev.read(n) for n in prev.namelist() if n.startswith(M7)}
        o7 = HERE.parent / 'maps/original_wol/ttosh02'
        for rel, data in mod7.items():
            low = rel.lower()
            if low.startswith('assets/'):
                files[rel] = data
            elif low.startswith(GD) and rel not in ENV:
                files[rel] = merge(data, orig[rel]) if rel in orig else data
            elif low.endswith('gamehotkeys.txt'):
                files[rel] = data
        o7k = {l.split('=', 1)[0] for l in (o7 / KO).read_text(encoding='utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], mod7[KO], o7k)
        # Original dead actor (unit 'Bogus', model WreckedBarracks defined nowhere): dropped so check_release passes.
        ad, n = re.subn(rb'[ \t]*<CActorUnit id="WreckedBunker" unitName="Bogus">\s*<Model value="WreckedBarracks" ?/>\s*</CActorUnit>\r?\n',
                        b'', files[GD + 'actordata.xml'])
        assert n == 1, n
        files[GD + 'actordata.xml'] = ad
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
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'], mod7['mapscript.galaxy'].decode('utf-8-sig'))
        V35.gate('kokr', files[KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[KO])
        for name, data in orig.items():
            if name.startswith('t3') or name in ('triggers', 'regions', 'paintedpathinglayer', 'documentinfo', 'minimap.tga'):
                assert files[name] == data, name
        for name, data in files.items():
            if name.endswith('.xml') or name == 'objects': E.fromstring(data)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    out.writestr(copy.copy(info), d, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                for name in sorted(files):
                    zi = zipfile.ZipInfo(M8 + name, date_time=(2026, 11, 23, 0, 0, 0))
                    zi.external_attr = 0o644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
                    out.writestr(zi, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'THorner01 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
