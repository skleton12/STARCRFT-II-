#!/usr/bin/env python3
"""0.13.2 -> 0.14.1: 14번 미션 TTychus03 (The Moebius Factor, 위기의 뫼비우스 — 질 행성) 추가 (사용자 2026-11-28 "담 미션은 질 행성").

원본: maps/original_wol/ttychus03 (사용자 드라이브의 블리자드 캠페인 추출본 35개). 지형·경로·장식물·지역·트리거 데이터는 원본 그대로.
공통 묶음은 코랄(THorner04, 0.13.2 = 0.12.14 기능)의 모드 층을 옮긴다 (gf_m12_* -> gf_m14_*: 지원 버튼·연구 점수 지원·용사·
연구 건물(시간 가속 10초·건물 감염)·용병·고갈되지 않는 자원·기술실 2개·아스테리아 망령·연구실 재설계·적 공방 3/3·적 수비대·
수비대 연구 점수 강화·코랄의 후예 전투 방패 등). 코랄 전용(오딘 단계 영웅 클로라리온·무르바르·수리 드론, 수비대 기본 +50%,
2단계 동맹 자금 보정)은 옮기지 않는다.
뫼비우스 맞춤:
  - 원본 플레이어: 1 레이너, 2·5 저그, 7 케리건(저그), 3 뫼비우스 데이터 코어(레이너의 적, 목표), 4 공격 가능한 도시·6 뫼비우스 경비대
    (중립), 8 중립 도시 건물. 원본 8번을 10번으로 옮긴다 (스크립트 상수 gv_p08, objects 소유자 9개, mapinfo 레코드 번호).
    mapinfo 레코드 순서 = 0~7, 10, 8, 9 → 동맹 이름 키 Player09/Player10.
  - 7-1 저그 규칙 (5·6번과 같음): 2·5·7 능력치(난이도별 %)·적 AI 한 단계 위(원본 AICampaignStart 앞)·공세 원본 x1.5(올림) 뒤 x1.25(올림, 19줄).
    동맹은 2·5·7을 적으로, 3(데이터 코어)·4·6·10은 중립으로 본다.
  - 모드 시작은 원본 gt_StartGame 직전 (기지가 처음부터 있음).
  - 레이너 본진 사령부 (180.5,77.5): 광물 11덩이 풍부·+20%, 가스 1곳·정제소 1개 풍부·+100% (시험값).
  - 동맹 집결지 등 기준점은 사령부 남서쪽(광물 반대편, 시험값).
Game not run.

Usage: python3 tools/build_v0141.py <0.13.2 zip> <ttychus03 folder> <new output zip>
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

OLD, NEW = b'version=0.13.2', b'version=0.14.1'
SRC, DST = 'THorner04.SC2Map/', 'TTychus03.SC2Map/'
CC = (180.5, 77.5)
OLD_CC = '34.5,21.5'
NAMES = {'MapInfo/Player09/Name': ('정화자', 'Purifiers'), 'MapInfo/Player10/Name': ('원시저그', 'Primal Zerg')}
MOVE = {8: 10}
ENEMIES = (2, 5, 7)
MIN_DEFAULT, GAS_DEFAULT = 1500, 2500


def cut(t, start, end):
    a = t.index(start); b = t.index(end, a)
    return t[:a] + t[b:]


def adapt(block):
    t = re.sub(r'\b(g[vft])_m12_', r'\1_m14_', block)
    t = sub1(t, "// Mission 12 = THorner04 (Media Blitz, Korhal), ported from mission 11 (0.11.9). Allies: 8 Purifiers, 9 Primal Zerg\n"
                "// (the original player 8 Dominion moved to 11). Enemies: 2-5, 11 (Terran). 6 = civilians, 7 = Horner's base (ally).\n"
                "// Coordinates and timings are trial values (docs/missions/12_media_blitz.md).",
             "// Mission 14 = TTychus03 (The Moebius Factor, Xil), ported from mission 12 (0.13.2). Allies: 8 Purifiers, 9 Primal Zerg\n"
             "// (the original player 8 neutral city moved to 10). Enemies: 2, 5, 7 Kerrigan (Zerg). 3 = Moebius data cores (Raynor's target).\n"
             "// Coordinates and timings are trial values (docs/missions/14_moebius_factor.md).")
    t = sub1(t, '    return ((p>=2 && p<=5) || p==11);', '    return (p==2 || p==5 || p==7);')
    t = sub1(t, f'Point({OLD_CC})', f'Point({CC[0]},{CC[1]})', 4)
    t = sub1(t, 'rally=Point(40.0,27.0);', 'rally=Point(174.0,72.0);')
    t = sub1(t, 'rally=Point(43.0,26.0);', 'rally=Point(177.0,71.0);')
    t = sub1(t, 'Point(40.5,24.0)', 'Point(175.5,73.0)')
    t = sub1(t, 'Point(39.5+1.0*i,24.0)', 'Point(174.5+1.0*i,73.0)')
    t = sub1(t, 'Point(38.5,25.0)', 'Point(173.5,74.0)')
    t = sub1(t, '                else if (p==1 || p==7 || (p>=8 && p<=9)) {', '                else if (p==1 || (p>=8 && p<=9)) {')
    t = sub1(t, '    gf_rmEnemyFastProd(2,5);\n    gf_rmEnemyFastProd(11,11);\n', '    gf_rmEnemyFastProd(2,2);\n    gf_rmEnemyFastProd(5,5);\n')
    # 7-1 Zerg (missions 5-6): flat stat buff by difficulty + level/research/AI rules (gf_rmZergBuff -> gf_rmVHZerg)
    a = t.index('void gf_m14_EnemyRules () {'); b = t.index('\n}\n', a) + 3
    t = t[:a] + ('void gf_m14_EnemyRules () {\n'
                 '    // 7-1 Zerg (user 2026-10-17/24): more units (attack waves +50% in the original triggers) and a flat stat buff.\n'
                 '    gf_rmZergBuff(2);\n    gf_rmZergBuff(5);\n    gf_rmZergBuff(7);\n}\n') + t[b:]
    # Korhal only: stage-2 ally money catch-up, Odin-stage heroes, +50% defenders
    t = cut(t, '    // 0.12.13: Korhal stage 2 starts after 4:00', '    // Primal Zerg have no supply building;')
    t = sub1(t, 'void gf_rm12Leave ();\nvoid gf_m14_Start () {', 'void gf_m14_Start () {')
    t = sub1(t, '    gf_rm12Leave();\n', '')
    t = cut(t, '// 0.12.8 (user 2026-11-27): Korhal', '// 0.11.9 (user 2026-11-26): enemy base defenders grow')
    t = sub1(t, ' + gv_rm12DefBase;', ';')
    t = sub1(t, 'if (gf_rm12DefOn(p))', 'if (gv_rmEHOn[p])', 2)
    for bad in ('_m12_', OLD_CC, 'rm12Leave', 'rm12Heroes', 'rm12DefOn', 'rm12DefBase', 'gv_rm12Clo', 'Korhal stage 2', 'p==1 || p==7',
                'EnemyFastProd(11,11)', 'TerranInfantryWeaponsLevel1",MaxI'):
        assert bad not in t, bad
    return t


def waves(t):
    def up(m):
        return m.group(1) + ', '.join(str(math.ceil(math.ceil(int(n) * 1.5) * 1.25)) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n == 19, n
    return t.replace('AIAttackWaveAddUnits4(', 'gf_rmWave4(')


def script(raw, mod):
    a, b, c, _ = blocks(mod)
    inits = re.sub(r'\b(g[vft])_m12_', r'\1_m14_', inits_of(mod))
    assert '_m12_' not in inits and 'gf_rmLabInit();' in inits and 'rm12Heroes' not in inits
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    t = sub1(t, 'const int gv_p08_NEUTRAL_CITY = 8;', 'const int gv_p08_NEUTRAL_CITY = 10;  // RM 0.14.1: moved from 8 (ally slot)')
    t = waves(t)
    inc = 'include "TriggerLibs/CampaignLib"\n'
    mark = '\n// @@RM_SPLIT@@\n'
    a, b, c = adapt(a + mark + b + mark + c + mark).split(mark)[:3]
    t = sub1(t, inc, inc + a)
    t = sub1(t, 'void InitGlobals () {', b + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTychus03);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTTychus03);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m14_Init();\n')
    t = sub1(t, '    AICampaignStart(gv_p05_ZERG_BASE);\n', '    // 7-1: enemy AI one step up (0.6.18), before the campaign AI starts.\n'
             + ''.join(f'    gf_rmAIUp({p});\n' for p in ENEMIES) + '    AICampaignStart(gv_p05_ZERG_BASE);\n')
    t = sub1(t, '    TriggerExecute(gt_StartGame, true, false);\n', '    gf_m14_Start();\n    TriggerExecute(gt_StartGame, true, false);\n')
    t = sub1(t, 'void InitMap () {\n', c + 'void InitMap () {\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n    InitGlobals();\n    InitTriggers();\n}',
             'void InitMap () {\n    InitLibs();\n'
             '    TriggerAddEventTimePeriodic(TriggerCreate("gt_rmDefBoost_Func"), 2.0, c_timeGame);  // 0.11.9\n'
             '    AchievementsDisable(1);\n    InitGlobals();\n    InitTriggers();\n'
             '    // 0.11.3: mod set-up after the original triggers are registered (a mod error cannot stop them).\n' + inits + '}')
    for bad in ('_m12_', 'THorner04', 'rm12Heroes', 'rm12Leave'):
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
    assert (rich, gas, ref, moved) == (11, 1, 1, 9), (rich, gas, ref, moved)
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
    fix = {**NAMES, 'Param/Value/C51B7699': ('유닛 없음', 'NO UNIT')}  # original leaves this one English only
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
    print(output, len(files), 'TTychus03 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
