#!/usr/bin/env python3
"""0.10.6 -> 0.11.1: 11번 미션 THorner03 (Engine of Destruction, 발할라) 추가 (사용자 2026-11-25 "발할라 ㄱㄱ").

원본: maps/original_wol/thorner03 (사용자 드라이브의 블리자드 캠페인 추출본). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 망자의 항구(THorner02, 0.10.6)의 모드 층을 그대로 옮긴다 (gf_m9_* -> gf_m11_*, 지원 버튼·연구실 단계·용사·연구 건물·
용병·고갈되지 않는 자원·기술실 2개 등 3~9번과 같음). 9번 전용인 올란 본진 수비(0.9.5)·자치령 방어 투하(0.9.8)는 뺀다.
발할라 맞춤:
  - 원본 플레이어: 1 레이너, 2 타이커스(오딘, 아군), 3~8 자치령(적), 10 로키(적). 원본이 8번을 써서 원본 8번을 11번으로 옮긴다
    (스크립트 상수 gv_p08, objects 소유자 51개, mapinfo 레코드 번호). 동맹은 다른 미션과 같은 8 정화자 / 9 원시저그.
    mapinfo 레코드 순서 = 0~7, 11, 10, 8, 9 → 동맹 이름 키 Player10/11 (Player09는 원본 그대로 로키).
  - 7-1 테란 규칙: 적 3~7·10·11. 적 AI 한 단계 위는 원본 CampaignInitAI 바로 앞에서 3~7·10·11에 적용. 공세 수 x1.25(올림, 87줄).
  - 동맹(8·9)은 타이커스(2)와 레이너(1)의 동맹.
  - 레이너 본진 사령부 (56.5,80.5): 광물 7덩이 풍부·+20%, 가스 2곳 풍부·+100% (시험값).
  - 동맹 집결지·연구 건물 기준점은 사령부 남쪽(광물 반대편, 시험값).
Game not run.

Usage: python3 tools/build_v0111.py <0.10.6 zip> <thorner03 folder> <new output zip>
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

OLD, NEW = b'version=0.10.6', b'version=0.11.1'
M9, M11 = 'THorner02.SC2Map/', 'THorner03.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ENV = {GD + 'lightdata.xml', GD + 'terraindata.xml', GD + 'waterdata.xml', GD + 'gamedata.xml'}
CC = (56.5, 80.5)
OLD_CC = '111.5,78.5'
NAMES = {'MapInfo/Player10/Name': ('정화자', 'Purifiers'), 'MapInfo/Player11/Name': ('원시저그', 'Primal Zerg')}
MOVE = {8: 11}
ENEMIES = (3, 4, 5, 6, 7, 10, 11)
WAVE_MULT = 1.25


def cut(t, start, end_marker):
    a = t.index(start); b = t.index(end_marker, a)
    return t[:a] + t[b:]


def blocks(mod):
    t = mod.replace('\r\n', '\n')
    inc = 'include "TriggerLibs/CampaignLib"\n'
    a0 = t.index(inc) + len(inc)
    a1 = t.index('\n//--------------------------------------------------------------------------------------------------\n// Library Initialization', a0)
    b0 = t.index('\n// Common pack for missions after 3') + 1
    b1 = t.index('void InitGlobals () {')
    c0 = t.index('// 0.8.2 (user 2026-11-23): Ultra-Capacitors')
    c1 = t.index('void InitMap () {')
    ach = '    AchievementsDisable(1);\n'
    i = t.index(ach) + len(ach)
    j = t.index('    InitGlobals();\n', i)
    return t[a0:a1 + 1], t[b0:b1], t[c0:c1], t[i:j]


def adapt(block):
    t = re.sub(r'\b(g[vft])_m9_', r'\1_m11_', block)
    t = sub1(t, "// Mission 9 = THorner02 (Cutthroat), ported from mission 8 (0.8.10). Allies: 8 Purifiers, 9 Primal Zerg\n"
                "// (the original players 8 Swann's Armory / 9 Protoss relics moved to 10 / 11). Enemies: 2 Orlan, 4 Dominion (Terran).\n"
                "// Coordinates and timings are trial values (docs/missions/09_cutthroat.md).",
             "// Mission 11 = THorner03 (Engine of Destruction, Valhalla), ported from mission 9 (0.10.6). Allies: 8 Purifiers, 9 Primal Zerg\n"
             "// (the original player 8 Dominion infantry B moved to 11). Enemies: 3-7, 10 Loki, 11 (Terran). 2 = Tychus (Odin, ally).\n"
             "// Coordinates and timings are trial values (docs/missions/11_engine_of_destruction.md).")
    t = sub1(t, '    return (p==2 || p==4);', '    return ((p>=3 && p<=7) || p==10 || p==11);')
    t = sub1(t, f'Point({OLD_CC})', f'Point({CC[0]},{CC[1]})', 4)
    t = sub1(t, 'rally=Point(106.0,79.0);', 'rally=Point(55.0,74.0);')
    t = sub1(t, 'rally=Point(106.0,82.0);', 'rally=Point(58.0,74.0);')
    t = sub1(t, 'Point(107.0,80.0)', 'Point(56.5,75.0)')
    t = sub1(t, 'Point(106.0+1.0*i,80.0)', 'Point(55.5+1.0*i,75.0)')
    t = sub1(t, 'Point(105.0,81.0)', 'Point(54.5,76.0)')
    t = sub1(t, '                else if (p==1 || (p>=8 && p<=10)) {', '                else if (p==1 || p==2 || (p>=8 && p<=9)) {')
    t = sub1(t, '// Mission 9 has no lava (Redstone only)', '// Mission 11 has no lava (Redstone only)')
    a = t.index('void gf_m11_EnemyRules () {')
    t = t[:a] + sub1(t[a:], '    for (p=2;p<=4;p+=2) {\n', '    for (p=3;p<=11;p+=1) {\n        if (!gf_m11_IsEnemy(p)) { continue; }\n')
    t = sub1(t, '    gf_rmEnemyFastProd(2,4);\n', '    gf_rmEnemyFastProd(3,7);\n    gf_rmEnemyFastProd(10,11);\n')
    # Codex: the warehouse phase checks gv_raynorsRaidingForce for defeat; replacing its Marines/Medics with mercs
    # empties that group. The pack's tick (mercs, enemy fast production) waits until the escort phase (gf_m11_Start).
    a = t.index('bool gt_m11_Tick_Func (bool testConds,bool runActions) {')
    g = '    if (!runActions || gv_gameOver) { return true; }\n'
    k = t.index(g, a); assert k - a < 120
    t = t[:k] + '    if (!runActions || gv_gameOver || !gv_m11_started) { return true; }\n' + t[k + len(g):]
    # mission 9 only: Orlan main base defence (0.9.5) and Dominion defence drops (0.9.8)
    t = cut(t, '// 0.9.5: Orlan main base hard defence', 'void gf_m11_Start () {')
    t = sub1(t, '    gf_m11_OrlanFort();\n', '')
    t = cut(t, 'trigger gt_m11_OrlanRefill;\n', '// 0.9.7 (user 2026-11-24): research the lab option')
    t = cut_dom(t)
    for bad in ('_m9_', OLD_CC, 'Orlan', 'DomDrop', 'DomInit', 'p==2 || p==4'):
        assert bad not in t, bad
    return t


def cut_dom(t):
    a = t.index('// 0.9.8 (user 2026-11-25): Dominion drops defenders')
    b = t.index('\n// @@RM_SPLIT@@\n', a)
    return t[:a] + t[b:]


def waves(t):
    def up(m):
        return m.group(1) + ', '.join(str(math.ceil(int(n) * WAVE_MULT)) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n == 87, n
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


def script(raw, mod9):
    a, b, c, inits = blocks(mod9)
    for bad in ('    gf_m9_DomInit();\n',
                '    gt_m9_OrlanRefill = TriggerCreate("gt_m9_OrlanRefill_Func");\n    TriggerAddEventTimePeriodic(gt_m9_OrlanRefill, 90.0, c_timeGame);\n'):
        inits = sub1(inits, bad, '')
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = sub1(t, 'const int gv_p08_DOMINION_INFANTRY_B = 8;', 'const int gv_p08_DOMINION_INFANTRY_B = 11;  // RM 0.11.1: moved from 8 (ally slot)')
    t = waves(t)
    inc = 'include "TriggerLibs/CampaignLib"\n'
    mark = '\n// @@RM_SPLIT@@\n'
    a, b, c = adapt(a + mark + b + mark + c + mark).split(mark)[:3]
    inits = re.sub(r'\b(g[vft])_m9_', r'\1_m11_', inits)
    assert '_m9_' not in inits
    t = sub1(t, inc, inc + a)
    t = sub1(t, 'void InitGlobals () {', b + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner03);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner03);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m11_Init();\n')
    t = sub1(t, '    CampaignInitAI();\n', '    // 7-1: enemy AI one step up (0.6.18), before the campaign AI starts.\n'
             + ''.join(f'    gf_rmAIUp({p});\n' for p in ENEMIES) + '    CampaignInitAI();\n')
    # Codex: the rich geyser 430 is replaced at the escort transition by a normal Refinery with 2400 gas.
    t = sub1(t, '    libNtve_gf_CreateUnitsWithDefaultFacing(1, "Refinery", 0, gv_p01_USER, PointFromId(2249));\n    UnitSetPropertyFixed(UnitLastCreated(), c_unitPropResources, 2400.0);\n',
             '    libNtve_gf_CreateUnitsWithDefaultFacing(1, "RefineryRich", 0, gv_p01_USER, PointFromId(2249));\n    UnitSetPropertyFixed(UnitLastCreated(), c_unitPropResources, 4800.0);  // RM 0.11.1: rich, +100%\n')
    t = sub1(t, '    TriggerExecute(gt_StartGameEscort, true, false);\n', '    gf_m11_Start();\n    TriggerExecute(gt_StartGameEscort, true, false);\n')
    t = sub1(t, 'void InitMap () {\n', c + 'void InitMap () {\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n', 'void InitMap () {\n    InitLibs();\n    AchievementsDisable(1);\n' + inits)
    return t.replace('\n', '\r\n').encode('utf-8')


def objects(data):
    root = E.fromstring(data)
    rich = gas = moved = 0
    for el in root:
        if el.tag != 'ObjectUnit': continue
        p = int(el.get('Player', '0'))
        if p in MOVE:
            el.set('Player', str(MOVE[p])); moved += 1
        ut = el.get('UnitType')
        x, y = (float(v) for v in el.get('Position').split(',')[:2])
        if math.hypot(x - CC[0], y - CC[1]) > 16: continue
        if ut == 'MineralField':
            el.set('UnitType', 'RichMineralField'); el.set('Resources', str(int(el.get('Resources')) * 120 // 100)); rich += 1
        elif ut == 'VespeneGeyser':
            el.set('UnitType', 'RichVespeneGeyser'); el.set('Resources', str(int(el.get('Resources')) * 2)); gas += 1
        else: continue
        k = ut == 'VespeneGeyser'
        for r in el.findall('Resources'):
            v = int(r.get('Value')); r.set('Value', str(v * 2 if k else v * 120 // 100))
    assert (rich, gas, moved) == (7, 2, 51), (rich, gas, moved)
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
    assert seen == [1, 2, 3, 4, 5, 6, 7, 8, 10], seen
    return mapinfo51(bytes(out))


def strings(orig, mod9, orig9_keys):
    text = orig.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod9.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig9_keys or k.startswith('MapInfo/'): continue
        add[k] = v
    out = (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')
    return set_strings(out, {k: f'{ko} /// {en}' for k, (ko, en) in NAMES.items()})


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(M11) for n in prev.namelist())
        files = dict(orig)
        mod9 = {n[len(M9):]: prev.read(n) for n in prev.namelist() if n.startswith(M9)}
        o9 = HERE.parent / 'maps/original_wol/thorner02'
        for rel, data in mod9.items():
            low = rel.lower()
            if low.startswith('assets/'):
                files[rel] = data
            elif low.startswith(GD) and rel not in ENV:
                files[rel] = merge(data, orig[rel]) if rel in orig else data
            elif low.endswith('gamehotkeys.txt'):
                files[rel] = data
        o9k = {l.split('=', 1)[0] for l in (o9 / KO).read_text(encoding='utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], mod9[KO], o9k)
        files['objects'] = objects(files['objects'])
        files['mapinfo'] = mapinfo(files['mapinfo'])
        saved = V514.NAMES
        V514.NAMES = NAMES
        try: files['documentheader'] = V514.set_header(files['documentheader'])
        finally: V514.NAMES = saved
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'], mod9['mapscript.galaxy'].decode('utf-8-sig'))
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
                    zi = zipfile.ZipInfo(M11 + name, date_time=(2026, 11, 25, 0, 0, 0))
                    zi.external_attr = 0o644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
                    out.writestr(zi, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'THorner03 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
