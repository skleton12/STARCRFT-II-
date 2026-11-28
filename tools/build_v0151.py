#!/usr/bin/env python3
"""0.14.3 -> 0.15.1: 15번 미션 TTychus02 (The Dig, 발굴 작업 — 질 행성) 추가 (사용자 2026-11-28 "담 미션은 질 행성",
"질행성 미션 오류 발견 유닛들이 용병이 아님", "적용 자체가 않돼있는데" — 질 행성은 TTychus03이 아니라 TTychus02였다).

원본: maps/original_wol/ttychus02 (사용자 드라이브의 블리자드 캠페인 추출본 34개). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 코랄(THorner04, 0.14.3)의 모드 층을 옮긴다 (gf_m12_* -> gf_m15_*, 공성 전차 연구 0.14.2 포함). 코랄 전용은 빼고(0.14.1과 같음).
발굴 작업 맞춤:
  - 원본 플레이어: 1 레이너, 2~6 탈다림 프로토스(적, 6은 공중), 7 버려진 기지(전술 단계 뒤 레이너에게 넘어옴), 8 고대 사원(중립).
    원본 8번을 10번으로 옮긴다 (InitGlobals gv_p8_ANCIENT_TEMPLE, objects 소유자, mapinfo 레코드 번호).
  - 7-1 프로토스 규칙 (4·7번과 같음): 2~6 피해 % 100·RM_EH·지상 공방 최소 1·VH 규칙, 적 AI 한 단계 위(원본 AICampaignStart 앞),
    공세 원본 x1.25(올림, 숫자 21줄).
  - 시작 수송선 화물: 해병 4 -> 전쟁광, 불곰 1 -> 망치 경호대, 의무관 2 -> 용병 의무관. 나중 수송선 공성 전차 2 -> 공성 파괴단.
  - 모드 시작은 기지를 넘겨받은 뒤 원본 gt_StartGameDefensePhase 직전.
  - 레이너 본진 = 버려진 기지 사령부 (53.5,56.5): 광물 7덩이 풍부·+20%, 가스 1곳·정제소 1개 풍부·+100% (시험값).
  - 동맹 집결지 등 기준점은 사령부 동쪽(광물 반대편, 시험값).
Game not run.

Usage: python3 tools/build_v0151.py <0.14.3 zip> <ttychus02 folder> <new output zip>
"""
import argparse, copy, math, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import build_v0514 as V514
from build_v041 import merge
from build_v051 import mapinfo as mapinfo51, sub1, set_strings
from build_v0111 import blocks, FREE, ENV, GD, KO
from build_v0121 import inits_of

OLD, NEW = b'version=0.14.3', b'version=0.15.1'
SRC, DST = 'THorner04.SC2Map/', 'TTychus02.SC2Map/'
CC = (53.5, 56.5)
OLD_CC = '34.5,21.5'
NAMES = {'MapInfo/Player09/Name': ('정화자', 'Purifiers'), 'MapInfo/Player10/Name': ('원시저그', 'Primal Zerg')}
MOVE = {8: 10}
ENEMIES = (2, 3, 4, 5, 6)
MIN_DEFAULT, GAS_DEFAULT = 1500, 2500


def cut(t, start, end):
    a = t.index(start); b = t.index(end, a)
    return t[:a] + t[b:]


def adapt(block):
    t = re.sub(r'\b(g[vft])_m12_', r'\1_m15_', block)
    t = sub1(t, "// Mission 12 = THorner04 (Media Blitz, Korhal), ported from mission 11 (0.11.9). Allies: 8 Purifiers, 9 Primal Zerg\n"
                "// (the original player 8 Dominion moved to 11). Enemies: 2-5, 11 (Terran). 6 = civilians, 7 = Horner's base (ally).\n"
                "// Coordinates and timings are trial values (docs/missions/12_media_blitz.md).",
             "// Mission 15 = TTychus02 (The Dig, Xil), ported from mission 12 (0.14.3). Allies: 8 Purifiers, 9 Primal Zerg\n"
             "// (the original player 8 ancient temple moved to 10). Enemies: 2-6 Tal'darim (Protoss). 7 = abandoned base (Raynor's later).\n"
             "// Coordinates and timings are trial values (docs/missions/15_the_dig.md).")
    t = sub1(t, '    return ((p>=2 && p<=5) || p==11);', '    return (p>=2 && p<=6);')
    t = sub1(t, f'Point({OLD_CC})', f'Point({CC[0]},{CC[1]})', 4)
    t = sub1(t, 'rally=Point(40.0,27.0);', 'rally=Point(61.0,62.0);')
    t = sub1(t, 'rally=Point(43.0,26.0);', 'rally=Point(63.0,60.0);')
    t = sub1(t, 'Point(40.5,24.0)', 'Point(61.5,59.0)')
    t = sub1(t, 'Point(39.5+1.0*i,24.0)', 'Point(60.5+1.0*i,59.0)')
    t = sub1(t, 'Point(38.5,25.0)', 'Point(59.5,60.0)')
    t = sub1(t, '    gf_rmEnemyFastProd(2,5);\n    gf_rmEnemyFastProd(11,11);\n', '    gf_rmEnemyFastProd(2,6);\n')
    # 7-1 Zerg (missions 5-6): flat stat buff by difficulty + level/research/AI rules (gf_rmZergBuff -> gf_rmVHZerg)
    a = t.index('void gf_m15_EnemyRules () {'); b = t.index('\n}\n', a) + 3
    t = t[:a] + ('void gf_m15_EnemyRules () {\n    int p;\n'
                 '    // 7-1 Protoss (user 2026-10-17, as Tal\'darim in missions 4 and 7): weapon upgrades +50% (RM_EH), level-1 ground\n'
                 '    // upgrades without stacking on what the original gave; damage % stays 100 (0.6.29).\n'
                 '    for (p=2;p<=6;p+=1) {\n'
                 '        PlayerModifyPropertyInt(p,c_playerPropDamageDealtPercent,c_playerPropOperSetTo,100);\n'
                 '        gf_rmEHStart(p);\n'
                 '        PlayerModifyPropertyInt(p,c_playerPropDamageTakenPercent,c_playerPropOperSetTo,100);\n'
                 '        TechTreeUpgradeAddLevel(p,"ProtossGroundWeaponsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ProtossGroundWeaponsLevel1",c_techCountCompleteOnly)));\n'
                 '        TechTreeUpgradeAddLevel(p,"ProtossGroundArmorsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ProtossGroundArmorsLevel1",c_techCountCompleteOnly)));\n'
                 '        gf_rmVHProtoss(p);\n    }\n}\n') + t[b:]
    # Korhal only: stage-2 ally money catch-up, Odin-stage heroes, +50% defenders
    t = cut(t, '    // 0.12.13: Korhal stage 2 starts after 4:00', '    // Primal Zerg have no supply building;')
    t = sub1(t, 'void gf_rm12Leave ();\nvoid gf_m15_Start () {', 'void gf_m15_Start () {')
    t = sub1(t, '    gf_rm12Leave();\n', '')
    t = cut(t, '// 0.12.8 (user 2026-11-27): Korhal', '// 0.11.9 (user 2026-11-26): enemy base defenders grow')
    t = sub1(t, ' + gv_rm12DefBase;', ';')
    t = sub1(t, 'if (gf_rm12DefOn(p))', 'if (gv_rmEHOn[p])', 2)
    for bad in ('_m12_', OLD_CC, 'rm12Leave', 'rm12Heroes', 'rm12DefOn', 'rm12DefBase', 'gv_rm12Clo', 'Korhal stage 2', 'gf_rmZergBuff(',
                'EnemyFastProd(11,11)', 'TerranInfantryWeaponsLevel1",MaxI'):
        assert bad not in t, bad
    return t


def waves(t):
    def up(m):
        return m.group(1) + ', '.join(str(math.ceil(int(n) * 1.25)) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n == 21, n  # plus one variable-count call (lv_qty) left as is
    return t.replace('AIAttackWaveAddUnits4(', 'gf_rmWave4(')


def script(raw, mod):
    a, b, c, _ = blocks(mod)
    inits = re.sub(r'\b(g[vft])_m12_', r'\1_m15_', inits_of(mod))
    assert '_m12_' not in inits and 'gf_rmLabInit();' in inits and 'rm12Heroes' not in inits
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = sub1(t, '    gv_p8_ANCIENT_TEMPLE = 8;', '    gv_p8_ANCIENT_TEMPLE = 10;  // RM 0.15.1: moved from 8 (ally slot)')
    t = waves(t)
    # Raynor's units are mercenaries (CLAUDE.md 3): opening dropship cargo and the later Siege Tank drop
    for a_, b_ in (('"Marauder", 1);', '"HammerSecurity", 1);'), ('"Marine", 4);', '"WarPig", 4);'), ('"Medic", 2);', '"MercMedic", 2);')):
        t = sub1(t, 'UnitCargoCreate(UnitFromId(317), ' + a_, 'UnitCargoCreate(UnitFromId(317), ' + b_)
    t = sub1(t, 'UnitCargoCreate(UnitLastCreated(), "SiegeTank", 2);', 'UnitCargoCreate(UnitLastCreated(), "SiegeBreaker", 2);')
    # Codex: the base hand-over move and the victory kill count look for Siege Tanks only
    for v, op, j in (('libNtve_gf_KillingUnit()', '==', ' || '), ('auto2DB2A002_var', '!=', ' && ')):
        o = f'(UnitGetType({v}) {op} "SiegeTankSieged"){j}(UnitGetType({v}) {op} "SiegeTank")'
        t = sub1(t, o, o + f'{j}(UnitGetType({v}) {op} "SiegeBreakerSieged"){j}(UnitGetType({v}) {op} "SiegeBreaker")')
    inc = 'include "TriggerLibs/CampaignLib"\n'
    mark = '\n// @@RM_SPLIT@@\n'
    a, b, c = adapt(a + mark + b + mark + c + mark).split(mark)[:3]
    t = sub1(t, inc, inc + a)
    t = sub1(t, 'void InitGlobals () {', b + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTychus02);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTychus02);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m15_Init();\n')
    t = sub1(t, '    AICampaignStart(gv_p2_NE_PROTOSSMiddle);\n', '    // 7-1: enemy AI one step up (0.6.18), before the campaign AI starts.\n'
             + ''.join(f'    gf_rmAIUp({p});\n' for p in ENEMIES) + '    AICampaignStart(gv_p2_NE_PROTOSSMiddle);\n')
    t = sub1(t, '    TriggerExecute(gt_StartGameDefensePhase, true, false);\n', '    gf_m15_Start();\n    TriggerExecute(gt_StartGameDefensePhase, true, false);\n')
    t = sub1(t, 'void InitMap () {\n', c + 'void InitMap () {\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n    InitGlobals();\n    InitTriggers();\n}',
             'void InitMap () {\n    InitLibs();\n'
             '    TriggerAddEventTimePeriodic(TriggerCreate("gt_rmDefBoost_Func"), 2.0, c_timeGame);  // 0.11.9\n'
             '    AchievementsDisable(1);\n    InitGlobals();\n    InitTriggers();\n'
             '    // 0.11.3: mod set-up after the original triggers are registered (a mod error cannot stop them).\n' + inits + '}')
    for bad in ('_m12_', 'THorner04', 'rm12Heroes', 'rm12Leave', 'TTychus03'):
        assert bad not in t, bad
    return t.replace('\n', '\r\n').encode('utf-8')


def objects(data):
    root = E.fromstring(data)
    rich = gas = ref = moved = 0
    for el in root:
        if el.tag != 'ObjectUnit': continue
        p = int(el.get('Player', '0'))
        if p in MOVE:
            el.set('Player', str(MOVE[p])); moved += 1
        ut = el.get('UnitType')
        x, y = (float(v) for v in el.get('Position').split(',')[:2])
        if math.hypot(x - CC[0], y - CC[1]) > 16: continue
        if ut == 'MineralField':
            el.set('UnitType', 'RichMineralField'); mult, base = (6, 5), MIN_DEFAULT; rich += 1
        elif ut == 'VespeneGeyser':
            el.set('UnitType', 'RichVespeneGeyser'); mult, base = (2, 1), GAS_DEFAULT; gas += 1
        elif ut == 'Refinery':
            el.set('UnitType', 'RefineryRich'); mult, base = (2, 1), GAS_DEFAULT; ref += 1
        else: continue
        el.set('Resources', str(int(el.get('Resources') or base) * mult[0] // mult[1]))
        for r in el.findall('Resources'):
            r.set('Value', str(int(r.get('Value')) * mult[0] // mult[1]))
    assert (rich, gas, ref, moved) == (7, 1, 1, 1), (rich, gas, ref, moved)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def mapinfo(d):
    shift = d.index(b'\x01\x01\x00\x00\x00', 0x90) - 0xa2
    co = 0x87 + shift
    count = int.from_bytes(d[co:co + 4], 'little')
    pos = 0xa2 + shift
    out = bytearray(d)
    seen = []
    for _ in range(1, count):
        seen.append(out[pos])
        if out[pos] in MOVE: out[pos] = MOVE[out[pos]]
        pos = d.index(0, pos + 26) + 1
    assert seen == [1, 2, 3, 4, 5, 6, 7, 8], seen
    return mapinfo51(bytes(out))


def strings(orig, mod, orig_src_keys):
    text = orig.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig_src_keys or k.startswith('MapInfo/') or k.startswith('Param/Value/RM12_'): continue
        add[k] = v
    out = (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')
    fix = dict(NAMES)
    return set_strings(out, {k: f'{ko} /// {en}' for k, (ko, en) in fix.items()})


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(DST) for n in prev.namelist())
        files = dict(orig)
        mod = {n[len(SRC):]: prev.read(n) for n in prev.namelist() if n.startswith(SRC)}
        osrc = HERE.parent / 'maps/original_wol/thorner04'
        for rel, data in mod.items():
            low = rel.lower()
            if low.startswith('assets/'):
                files[rel] = data
            elif low.startswith(GD) and rel not in ENV:
                files[rel] = merge(data, orig[rel]) if rel in orig else data
            elif low.endswith('gamehotkeys.txt'):
                files[rel] = data
        osk = {l.split('=', 1)[0] for l in (osrc / KO).read_text(encoding='utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], mod[KO], osk)
        files['objects'] = objects(files['objects'])
        files['mapinfo'] = mapinfo(files['mapinfo'])
        saved = V514.NAMES
        V514.NAMES = NAMES
        try: files['documentheader'] = V514.set_header(files['documentheader'])
        finally: V514.NAMES = saved
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'], mod['mapscript.galaxy'].decode('utf-8-sig'))
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
                    zi = zipfile.ZipInfo(DST + name, date_time=(2026, 11, 28, 0, 0, 0))
                    zi.external_attr = 0o644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
                    out.writestr(zi, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'TTychus02 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
