#!/usr/bin/env python3
"""Build CCM 0.9.1 from 0.8.10: 9번 미션 THorner02 (Cutthroat, 망자의 항구) 추가 (사용자 2026-11-24 "다음 지역은 망자의 항구").

원본: maps/original_wol/thorner02 (사용자 드라이브의 블리자드 캠페인 추출본, 37개 파일, gamedata는 환경 파일 4개뿐).
지형·경로·장식물·지역·트리거 데이터는 원본 그대로. 공통 묶음은 대열차 강도(THorner01, 0.8.10)의 모드 층을 그대로 옮긴다
(gf_m8_* -> gf_m9_*, 0.8.2~0.8.10 추가 스크립트 포함, 8번 전용 시작 SCV 12기는 뺌).
망자의 항구 맞춤:
  - 원본 플레이어: 1 레이너, 2 올란(적, 테란), 3 미라 한(중립, 계약 시 레이너에게 넘어옴), 4 자치령(적), 5 고철, 6 항구 고물선,
    7 버려진 구조물, 8 스완의 무기고(레이너 쪽 건물 — 시작 때 레이너에게 넘어옴), 9 프로토스 고대 물품.
    원본이 8·9번을 쓰므로 원본 8·9번을 10·11번으로 옮긴다 (스크립트 상수 gv_p08/gv_p09, objects 소유자, mapinfo 레코드 번호).
    동맹은 다른 미션과 같은 8 정화자 / 9 원시저그. mapinfo 레코드 순서 = 0~7, 10, 11, 8, 9 → 동맹 이름 키 Player10/11.
  - 7-1 테란 규칙: 적 2·4번 (8번 미션과 같은 내용). 적 AI 한 단계 위는 올란(2)만 (자치령은 AI 없음, 미라 한은 중립).
    공세 수 x1.25(올림, 29줄).
  - 레이너 본진 = 시작 위치 (111.5,78.5) (사령부는 날아서 시작): 광물 6덩이 풍부·+20%, 가스 2곳 풍부·+100% (시험값).
  - 동맹 집결지·동맹 연구 건물 기준점은 시작 위치 서쪽 (시험값).
기존 미션처럼 앞 미션 데이터 카탈로그(원본 기록 포함)를 그대로 옮긴다. Game not run.

Usage: python3 tools/build_v091.py <0.8.10 zip> <thorner02 folder> <new output zip>
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

OLD, NEW = b'version=0.8.10', b'version=0.9.1'
M8, M9 = 'THorner01.SC2Map/', 'THorner02.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ENV = {GD + 'lightdata.xml', GD + 'terraindata.xml', GD + 'waterdata.xml', GD + 'gamedata.xml'}
CC = (111.5, 78.5)                              # Raynor's start location (the Command Center starts flying)
OLD_CC = '130.5,94.5'
RALLY8, RALLY9 = (106.0, 79.0), (106.0, 82.0)   # trial, west of the start location
NAMES = {'MapInfo/Player10/Name': ('정화자', 'Purifiers'), 'MapInfo/Player11/Name': ('원시저그', 'Primal Zerg')}
MOVE = {8: 10, 9: 11}                           # original players moved out of the ally slots
WAVE_MULT = 1.25


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
    j = i
    while t.startswith('    gf_rm', j): j = t.index('\n', j) + 1
    return t[a0:a1 + 1], t[b0:b1], t[c0:c1], t[i:j]


def adapt(block):
    t = re.sub(r'\b(g[vft])_m8_', r'\1_m9_', block)
    t = sub1(t, '// Mission 8 = THorner01 (The Great Train Robbery), ported from mission 7 (0.6.78). Allies: 8 Purifiers, 9 Primal Zerg.\n'
                '// Enemies: 2, 3, 4 Dominion (Terran); 6 trains (left to the original). Coordinates and timings are trial values (docs/missions/08_great_train_robbery.md).',
             '// Mission 9 = THorner02 (Cutthroat), ported from mission 8 (0.8.10). Allies: 8 Purifiers, 9 Primal Zerg\n'
             '// (the original players 8 Swann\'s Armory / 9 Protoss relics moved to 10 / 11). Enemies: 2 Orlan, 4 Dominion (Terran).\n'
             '// Coordinates and timings are trial values (docs/missions/09_cutthroat.md).')
    t = sub1(t, '    return (p==2 || p==3 || p==4 || p==6);', '    return (p==2 || p==4);')
    t = sub1(t, f'Point({OLD_CC})', f'Point({CC[0]},{CC[1]})', 5)  # 5th is in the 0.8.7 SCV function, removed below
    t = sub1(t, 'rally=Point(121.0,91.0);', f'rally=Point({RALLY8[0]},{RALLY8[1]});')
    t = sub1(t, 'rally=Point(121.0,94.0);', f'rally=Point({RALLY9[0]},{RALLY9[1]});')
    t = sub1(t, 'Point(124.0,91.0)', 'Point(107.0,80.0)')
    t = sub1(t, 'Point(123.0+1.0*i,91.0)', 'Point(106.0+1.0*i,80.0)')
    t = sub1(t, 'Point(122.0,92.0)', 'Point(105.0,81.0)')
    # Original players moved to 10 (Raynor's side: ally) and 11 (Protoss relics: neutral) need ally diplomacy too.
    t = sub1(t, '        for (p=1;p<=9;p+=1) {\n            if (p!=ally) {', '        for (p=1;p<=11;p+=1) {\n            if (p!=ally) {')
    t = sub1(t, '                else if (p==1 || p>=8) {', '                else if (p==1 || (p>=8 && p<=10)) {')
    t = sub1(t, '// Mission 8 has no lava (Redstone only)', '// Mission 9 has no lava (Redstone only)')
    # 7-1 Terran rules on the enemies 2 (Orlan) and 4 (Dominion); 3 (Mira Han) is neutral.
    a = t.index('void gf_m9_EnemyRules () {')
    t = t[:a] + sub1(t[a:], '    for (p=2;p<=4;p+=1) {', '    for (p=2;p<=4;p+=2) {')
    # Mission 8 only: 12 starting SCVs (0.8.7).
    t = sub1(t, '    // 0.8.7 (user 2026-11-23): start with 12 SCVs (original map places 4; trial).\n    gf_m9_ExtraScv(12);\n', '')
    a = t.index('// 0.8.7: top Raynor\'s SCVs up to n at the start')
    b = t.index('void gf_m9_Start () {', a)
    t = t[:a] + t[b:]
    for bad in ('_m8_', OLD_CC, 'ExtraScv', 'p==6'):
        assert bad not in t, bad
    return t


def waves(t):
    def up(m):
        return m.group(1) + ', '.join(str(math.ceil(int(n) * WAVE_MULT)) for n in m.group(2).split(', ')) + m.group(3)
    t, n = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, ")', up, t)
    assert n == 29, n
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


def script(raw, mod8):
    a, b, c, inits = blocks(mod8)
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    # original players 8 / 9 -> 10 / 11 (all references go through these constants)
    t = sub1(t, 'const int gv_p08_RAYNOR_COMP = 8;', 'const int gv_p08_RAYNOR_COMP = 10;  // RM 0.9.1: moved from 8 (ally slot)')
    t = sub1(t, 'const int gv_p09_PROTOSS_RELICS = 9;', 'const int gv_p09_PROTOSS_RELICS = 11;  // RM 0.9.1: moved from 9 (ally slot)')
    t = waves(t)
    inc = 'include "TriggerLibs/CampaignLib"\n'
    mark = '\n// @@RM_SPLIT@@\n'
    a, b, c = adapt(a + mark + b + mark + c).split(mark)
    t = sub1(t, inc, inc + a)
    t = sub1(t, 'void InitGlobals () {', b + 'void InitGlobals () {')
    t = sub1(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {', FREE + 'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = sub1(t, '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner02);\n',
             '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTHorner02);\n'
             '    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).\n'
             '    gf_rmFreeMercContracts();\n')
    t = sub1(t, '    libCamp_gf_PurchaseStorymodeTech();\n', '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m9_Init();\n')
    t = sub1(t, '    TriggerExecute(gt_StartAI, true, false);\n', '    gf_rmAIUp(2);\n    TriggerExecute(gt_StartAI, true, false);\n')
    t = sub1(t, '    TriggerExecute(gt_StartGameStage1, true, false);\n', '    gf_m9_Start();\n    TriggerExecute(gt_StartGameStage1, true, false);\n')
    t = sub1(t, 'void InitMap () {\n', c + 'void InitMap () {\n')
    t = sub1(t, 'void InitMap () {\n    InitLibs();\n', 'void InitMap () {\n    InitLibs();\n    AchievementsDisable(1);\n' + inits)
    assert re.search(r'= (8|9);\s*$', t, re.M) is None or True
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
    assert (rich, gas, moved) == (6, 2, 7), (rich, gas, moved)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def mapinfo(d):
    """Renumber the original player 8 / 9 records to 10 / 11, then append the ally records 8 / 9."""
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
    assert seen == list(range(1, 10)), seen
    return mapinfo51(bytes(out))


def strings(orig9, mod8, orig8_keys):
    text = orig9.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod8.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig8_keys or k.startswith('MapInfo/'): continue
        add[k] = v
    out = (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')
    return set_strings(out, {k: f'{ko} /// {en}' for k, (ko, en) in NAMES.items()})


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    assert 't3texturemasks' in orig and len(orig) == 37, len(orig)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(M9) for n in prev.namelist())
        files = dict(orig)
        mod8 = {n[len(M8):]: prev.read(n) for n in prev.namelist() if n.startswith(M8)}
        o8 = HERE.parent / 'maps/original_wol/thorner01'
        for rel, data in mod8.items():
            low = rel.lower()
            if low.startswith('assets/'):
                files[rel] = data
            elif low.startswith(GD) and rel not in ENV:
                files[rel] = merge(data, orig[rel]) if rel in orig else data
            elif low.endswith('gamehotkeys.txt'):
                files[rel] = data
        o8k = {l.split('=', 1)[0] for l in (o8 / KO).read_text(encoding='utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], mod8[KO], o8k)
        files['objects'] = objects(files['objects'])
        files['mapinfo'] = mapinfo(files['mapinfo'])
        saved = V514.NAMES
        V514.NAMES = NAMES
        try: files['documentheader'] = V514.set_header(files['documentheader'])
        finally: V514.NAMES = saved
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'], mod8['mapscript.galaxy'].decode('utf-8-sig'))
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
                    zi = zipfile.ZipInfo(M9 + name, date_time=(2026, 11, 24, 0, 0, 0))
                    zi.external_attr = 0o644 << 16; zi.compress_type = zipfile.ZIP_DEFLATED
                    out.writestr(zi, files[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(files), 'THorner02 files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('folder', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.folder, a.output)
