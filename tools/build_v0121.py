#!/usr/bin/env python3
"""0.11.9 -> 0.12.1: 12번 미션 THorner04 (Media Blitz, 코랄 미디어 전격전) 추가 (사용자 2026-11-26 "다음 미션 코랄").

원본: maps/original_wol/thorner04 (사용자 드라이브의 블리자드 캠페인 추출본). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 발할라(THorner03, 0.11.9)의 모드 층을 옮긴다 (gf_m11_* -> gf_m12_*: 지원 버튼·연구 점수 지원·용사·연구 건물·용병·
고갈되지 않는 자원·기술실 2개·아스테리아 망령·적 수비대 연구 점수 강화·정화자 정찰기 외형 등). 발할라 전용(창고 침투대 용병 바꿈·
타이커스 동맹·초기화 스레드)은 옮기지 않는다.
코랄 맞춤:
  - 원본 플레이어: 1 레이너(1단계는 오딘만), 2~5 자치령(적), 6 코랄 민간인(중립), 7 호너 기지(아군 AI, 2단계에 레이너에게 넘어옴),
    8 자치령(적). 원본 8번을 11번으로 옮긴다 (스크립트 상수 gv_p08, objects 소유자 3개, mapinfo 레코드 번호).
    mapinfo 레코드 순서 = 0~7, 11, 8, 9 → 동맹 이름 키 Player09/Player10.
  - 모드 시작(7-1 강화·동맹 지원·용병 처리)은 2단계 시작(기지를 넘겨받은 뒤) — 1단계 오딘 돌진은 원본 그대로.
  - 7-1 테란 규칙: 적 2~5·11. 적 AI 한 단계 위는 원본 Start AI의 AICampaignStart 바로 앞. 공세 수 x1.25(올림, 40줄).
  - 동맹(8·9)은 레이너(1)·호너 기지(7)와 동맹.
  - 레이너 본진 = 호너 기지 사령부 (34.5,21.5): 광물 8덩이 풍부·+20%, 가스 2곳 풍부·+100%, 정제소도 풍부한 정제소 (시험값).
  - 동맹 집결지 등 기준점은 사령부 북동쪽(광물 반대편, 시험값).
Game not run.

Usage: python3 tools/build_v0121.py <0.11.9 zip> <thorner04 folder> <new output zip>
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

OLD, NEW = b'version=0.11.9', b'version=0.12.1'
SRC, DST = 'THorner03.SC2Map/', 'THorner04.SC2Map/'
CC = (34.5, 21.5)
OLD_CC = '56.5,80.5'
NAMES = {'MapInfo/Player09/Name': ('정화자', 'Purifiers'), 'MapInfo/Player10/Name': ('원시저그', 'Primal Zerg')}
MOVE = {8: 11}
ENEMIES = (2, 3, 4, 5, 11)
WAVE_MULT = 1.25
MIN_DEFAULT, GAS_DEFAULT = 1500, 2500   # Liberty defaults when the object has no Resources value (0.3.1)


def inits_of(t):
    t = t.replace('\r\n', '\n')
    a = t.index('void InitMap () {')
    body = t[a:t.index('\n}\n', a)].split('\n')[1:]
    skip = ('InitLibs();', 'AchievementsDisable(1);', 'InitGlobals();', 'InitTriggers();', '//')
    return ''.join(l + '\n' for l in body if l.strip() and not l.strip().startswith(skip) and 'gt_rmDefBoost' not in l)


def adapt(block):
    t = re.sub(r'\b(g[vft])_m11_', r'\1_m12_', block)
    t = sub1(t, "// Mission 11 = THorner03 (Engine of Destruction, Valhalla), ported from mission 9 (0.10.6). Allies: 8 Purifiers, 9 Primal Zerg\n"
                "// (the original player 8 Dominion infantry B moved to 11). Enemies: 3-7, 10 Loki, 11 (Terran). 2 = Tychus (Odin, ally).\n"
                "// Coordinates and timings are trial values (docs/missions/11_engine_of_destruction.md).",
             "// Mission 12 = THorner04 (Media Blitz, Korhal), ported from mission 11 (0.11.9). Allies: 8 Purifiers, 9 Primal Zerg\n"
             "// (the original player 8 Dominion moved to 11). Enemies: 2-5, 11 (Terran). 6 = civilians, 7 = Horner's base (ally).\n"
             "// Coordinates and timings are trial values (docs/missions/12_media_blitz.md).")
    t = sub1(t, '    return ((p>=3 && p<=7) || p==10 || p==11);', '    return ((p>=2 && p<=5) || p==11);')
    t = sub1(t, f'Point({OLD_CC})', f'Point({CC[0]},{CC[1]})', 4)
    t = sub1(t, 'rally=Point(55.0,74.0);', 'rally=Point(40.0,27.0);')
    t = sub1(t, 'rally=Point(58.0,74.0);', 'rally=Point(43.0,26.0);')
    t = sub1(t, 'Point(56.5,75.0)', 'Point(40.5,24.0)')
    t = sub1(t, 'Point(55.5+1.0*i,75.0)', 'Point(39.5+1.0*i,24.0)')
    t = sub1(t, 'Point(54.5,76.0)', 'Point(38.5,25.0)')
    t = sub1(t, '                else if (p==1 || p==2 || (p>=8 && p<=9)) {', '                else if (p==1 || p==7 || (p>=8 && p<=9)) {')
    t = sub1(t, '// Mission 11 has no lava (Redstone only)', '// Mission 12 has no lava (Redstone only)')
    t = sub1(t, '    for (p=3;p<=11;p+=1) {\n        if (!gf_m12_IsEnemy(p)) { continue; }\n',
             '    for (p=2;p<=11;p+=1) {\n        if (!gf_m12_IsEnemy(p)) { continue; }\n', 3)
    t = sub1(t, '    gf_rmEnemyFastProd(3,7);\n    gf_rmEnemyFastProd(10,11);\n', '    gf_rmEnemyFastProd(2,5);\n    gf_rmEnemyFastProd(11,11);\n')
    # Valhalla only: Raynor <-> Tychus (2) alliance at the escort start.
    t = sub1(t, '    gv_m12_started=true;\n'
                '    libNtve_gf_SetAlliance(1,2,libNtve_ge_AllianceSetting_AllyWithSharedVision);\n'
                '    libNtve_gf_SetAlliance(2,1,libNtve_ge_AllianceSetting_AllyWithSharedVision);\n'
                '    PlayerSetAlliance(1,c_allianceIdPushable,2,true);\n',
             '    gv_m12_started=true;\n')
    for bad in ('_m11_', OLD_CC, 'Loki', 'Tychus (Odin', '(1,2,', 'p==1 || p==2', 'p=3;p<=11', 'EnemyFastProd(3,7)'):
        assert bad not in t, bad
    return t


def waves(t):
    def up(m):
        return m.group(1) + ', '.join(str(math.ceil(int(n) * WAVE_MULT)) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n == 40, n
    return t.replace('AIAttackWaveAddUnits4(', 'gf_rmWave4(')


def script(raw, mod):
    a, b, c, _ = blocks(mod)
    inits = re.sub(r'\b(g[vft])_m11_', r'\1_m12_', inits_of(mod))
    assert '_m11_' not in inits and 'gf_rmLabInit();' in inits
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = sub1(t, 'const int gv_p08_DOMINION = 8;', 'const int gv_p08_DOMINION = 11;  // RM 0.12.1: moved from 8 (ally slot)')
    t = waves(t)
    inc = 'include "TriggerLibs/CampaignLib"\n'
    mark = '\n// @@RM_SPLIT@@\n'
    a, b, c = adapt(a + mark + b + mark + c + mark).split(mark)[:3]
    t = sub1(t, inc, inc + a)
    t = sub1(t, 'void InitGlobals () {', b + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner04);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner04);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m12_Init();\n')
    t = sub1(t, '    AICampaignStart(gv_p02_DOMINION_INFANTRY);\n', '    // 7-1: enemy AI one step up (0.6.18), before the campaign AI starts.\n'
             + ''.join(f'    gf_rmAIUp({p});\n' for p in ENEMIES) + '    AICampaignStart(gv_p02_DOMINION_INFANTRY);\n')
    # Mod start (7-1, ally support, mercs) once Raynor owns Horner's base (stage 2).
    t = sub1(t, '    TriggerExecute(gt_StartGameStage2, true, false);\n', '    gf_m12_Start();\n    TriggerExecute(gt_StartGameStage2, true, false);\n')
    defb = mod.replace('\r\n', '\n')
    k0 = defb.index('// 0.11.9 (user 2026-11-26): enemy base defenders grow')
    assert k0 >= defb.index('// 0.8.2 (user 2026-11-23): Ultra-Capacitors')  # already inside block c
    # Codex: gt_RecreateBase removes the geyser and builds a normal Refinery; keep the rich one (+100%).
    t = sub1(t, 'UnitGroup("VespeneGeyser", c_playerAny, RegionFromId(34),', 'UnitGroup("RichVespeneGeyser", c_playerAny, RegionFromId(34),')
    t = sub1(t, '    libNtve_gf_CreateUnitsWithDefaultFacing(1, "Refinery", 0, lv_player, RegionGetCenter(RegionFromId(34)));\n',
             '    libNtve_gf_CreateUnitsWithDefaultFacing(1, "RefineryRich", 0, lv_player, RegionGetCenter(RegionFromId(34)));\n'
             '    UnitSetPropertyFixed(UnitLastCreated(), c_unitPropResources, 5000.0);  // RM 0.12.1: rich, +100%\n')
    t = sub1(t, 'void InitMap () {\n', c + 'void InitMap () {\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n    InitGlobals();\n    InitTriggers();\n}',
             'void InitMap () {\n    InitLibs();\n'
             '    TriggerAddEventTimePeriodic(TriggerCreate("gt_rmDefBoost_Func"), 2.0, c_timeGame);  // 0.11.9\n'
             '    AchievementsDisable(1);\n    InitGlobals();\n    InitTriggers();\n'
             '    // 0.11.3: mod set-up after the original triggers are registered (a mod error cannot stop them).\n' + inits + '}')
    for bad in ('_m11_', 'THorner03'):
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
    assert (rich, gas, ref, moved) == (8, 2, 1, 3), (rich, gas, ref, moved)
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
        if k in have or k in orig_src_keys or k.startswith('MapInfo/'): continue
        add[k] = v
    out = (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')
    return set_strings(out, {k: f'{ko} /// {en}' for k, (ko, en) in NAMES.items()})


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(DST) for n in prev.namelist())
        files = dict(orig)
        mod = {n[len(SRC):]: prev.read(n) for n in prev.namelist() if n.startswith(SRC)}
        osrc = HERE.parent / 'maps/original_wol/thorner03'
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
                    zi = zipfile.ZipInfo(DST + name, date_time=(2026, 11, 26, 0, 0, 0))
                    zi.external_attr = 0o644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
                    out.writestr(zi, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'THorner04 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
