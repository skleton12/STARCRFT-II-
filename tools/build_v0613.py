#!/usr/bin/env python3
"""0.6.12 -> 0.6.13: 적 강화 상향 (사용자 2026-10-31 "적군들 AI난이도 높히고 물량이랑 아주 어려움 난이도는 1렙 업합세").

모든 임무 맵(1~6번)의 적 플레이어(원본 적 슬롯)에만 적용한다. 레이너·동맹·중립은 건드리지 않는다. 모두 시험값.
- 테란·프로토스 적 난이도별 피해 % (ENEMY_BUFF_PERCENT): 0/5/15/35 -> 5/15/30/60 (1·2·4번 탈다림).
- 저그 적 능력치 (ZERG_BUFF_PERCENT): 고정 10 -> 난이도별 10/15/20/30 (3·4·5·6번).
- 물량 (WAVE_MULT): 원본 공세(AIAttackWaveAddUnits4) 수를 한 번 더 x1.25 (올림, 0은 그대로). 2~6번.
  저그 공세는 기존 +50% 위에 곱해져 원본의 약 1.9배가 된다. 1번은 공세 트리거가 없어 그대로.
- 아주 어려움 +1단계 (VERY_HARD_EXTRA_LEVELS): 아주 어려움에서만 적 공격·방어 업그레이드를
  '원본(과 7-1 최소 업그레이드)이 준 가장 높은 단계 + 1'까지 채운다 (최대 3). 원본이 나중에 단계를 주는 맵도
  10초마다 다시 확인해 계속 +1을 유지한다 (첫 확인은 10초 뒤 — 원본 시작 업그레이드를 먼저 원본으로 센다). 모드가 준 단계는 따로 기억해 원본 단계로 세지 않는다 (중복 상승 방지).
  저그도 아주 어려움에서는 이 +1을 받는다 (7-1 '저그는 최소 업그레이드 없음'의 예외, 사용자 지시).

Usage: python3 tools/build_v0613.py <0.6.12 zip> <new output zip>
"""
import argparse, copy, math, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.12', b'version=0.6.13'

ENEMY_BUFF_PERCENT = (5, 15, 30, 60)       # was (0, 5, 15, 35)
ZERG_BUFF_EXTRA = (0, 5, 10, 20)           # added to gv_rmZergBuffPercent (10) -> 10/15/20/30
WAVE_MULT = 1.25
VERY_HARD_EXTRA_LEVELS = 1

LINES = {
    'Terran': ['TerranInfantryWeaponsLevel', 'TerranInfantryArmorsLevel', 'TerranVehicleWeaponsLevel', 'TerranVehicleArmorsLevel'],
    'Zerg': ['ZergMeleeWeaponsLevel', 'ZergMissileWeaponsLevel', 'ZergGroundArmorsLevel', 'ZergFlyerWeaponsLevel', 'ZergFlyerArmorsLevel'],
    'Protoss': ['ProtossGroundWeaponsLevel', 'ProtossGroundArmorsLevel', 'ProtossShieldsLevel', 'ProtossAirWeaponsLevel', 'ProtossAirArmorsLevel'],
}


def vh_block():
    races = '\n'.join(
        f'void gf_rmVH{race} (int p) {{\n' + ''.join(f'    gf_rmVHAdd(p,"{l}");\n' for l in lines) + '}\n'
        for race, lines in LINES.items())
    return f'''// 0.6.13 (user 2026-10-31): on Very Hard, enemy upgrades stay one level above what the original
// (and the 7-1 minimum) gives, up to 3. Levels given here are remembered so they never count as original.
const int gv_rmVeryHardExtraLevels = {VERY_HARD_EXTRA_LEVELS};
int[16][8][4] gv_rmVHGave;
string[16][8] gv_rmVHLine;
int[16] gv_rmVHLines;
trigger gt_rmVH;

void gf_rmVHLevel (int p, int s) {{
    string line = gv_rmVHLine[p][s];
    int n;
    int orig = 0;
    int want;
    for (n=1;n<=3;n+=1) {{
        if (TechTreeUpgradeCount(p,line+IntToString(n),c_techCountCompleteOnly)>gv_rmVHGave[p][s][n]) {{ orig=n; }}
    }}
    want=MinI(3,orig+gv_rmVeryHardExtraLevels);
    for (n=1;n<=want;n+=1) {{
        if (TechTreeUpgradeCount(p,line+IntToString(n),c_techCountCompleteOnly)==0) {{
            TechTreeUpgradeAddLevel(p,line+IntToString(n),1);
            gv_rmVHGave[p][s][n]=1;
        }}
    }}
}}

bool gt_rmVH_Func (bool testConds, bool runActions) {{
    int p;
    int s;
    if (!runActions) {{ return true; }}
    for (p=0;p<=15;p+=1) {{
        for (s=0;s<gv_rmVHLines[p];s+=1) {{ gf_rmVHLevel(p,s); }}
    }}
    return true;
}}

void gf_rmVHAdd (int p, string line) {{
    if (libNtve_gf_DifficultyValueInt(0,0,0,1)==0 || gv_rmVHLines[p]>=8) {{ return; }}
    gv_rmVHLine[p][gv_rmVHLines[p]]=line;
    gv_rmVHLines[p]+=1;
    // First check after 10 s, so the original start-up upgrade grants are counted as original first.
    if (gt_rmVH==null) {{
        gt_rmVH=TriggerCreate("gt_rmVH_Func");
        TriggerAddEventTimePeriodic(gt_rmVH,10.0,c_timeGame);
    }}
}}

{races}
'''


BUFF_OLD_SP = 'libNtve_gf_DifficultyValueInt(0, 5, 15, 35)'
BUFF_OLD = 'libNtve_gf_DifficultyValueInt(0,5,15,35)'
BUFF_NEW = 'libNtve_gf_DifficultyValueInt({},{},{},{})'.format(*ENEMY_BUFF_PERCENT)

ZERG_ANCHOR = '// 0.4.82: Zerg enemies keep the +50% waves'
ZERG_OLD = '''void gf_rmZergBuff (int p) {
    PlayerModifyPropertyInt(p,c_playerPropDamageDealtPercent,c_playerPropOperSetTo,100+gv_rmZergBuffPercent);
    PlayerModifyPropertyInt(p,c_playerPropDamageTakenPercent,c_playerPropOperSetTo,10000/(100+gv_rmZergBuffPercent));
}
'''
ZERG_NEW = '''void gf_rmZergBuff (int p) {
    // 0.6.13: difficulty-scaled on top of the base (trial, user 2026-10-31).
    int b = gv_rmZergBuffPercent+libNtve_gf_DifficultyValueInt(%d,%d,%d,%d);
    PlayerModifyPropertyInt(p,c_playerPropDamageDealtPercent,c_playerPropOperSetTo,100+b);
    PlayerModifyPropertyInt(p,c_playerPropDamageTakenPercent,c_playerPropOperSetTo,10000/(100+b));
    gf_rmVHZerg(p);
}
''' % ZERG_BUFF_EXTRA

# Terran maps: enemy players that get the Terran +1 on Very Hard
T1_ANCHOR = '// Difficulty-scaled Dominion damage dealt / taken'
T1_OLD = ('    PlayerModifyPropertyInt(gv_p2_DOMINION_RED, c_playerPropDamageTakenPercent, c_playerPropOperSetTo, 10000 / (100 + lv_buff));\n}\n')
T1_NEW = T1_OLD[:-2] + '    gf_rmVHTerran(gv_p2_DOMINION_RED);\n}\n'
T2_ANCHOR = '// ---- Enemy rules (CLAUDE.md 7-1) ----'
T2_OLD = ('    PlayerModifyPropertyInt(gv_pLAYER_05_PATROL, c_playerPropDamageTakenPercent, c_playerPropOperSetTo, 10000 / (100 + lv_buff));\n}\n')
T2_NEW = T2_OLD[:-2] + '    gf_rmVHTerran(gv_pLAYER_02_DOMINION);\n    gf_rmVHTerran(gv_pLAYER_05_PATROL);\n}\n'
P4_OLD = '        TechTreeUpgradeAddLevel(p,"ProtossGroundArmorsLevel1",MaxI(0,1-TechTreeUpgradeCount(p,"ProtossGroundArmorsLevel1",c_techCountCompleteOnly)));\n'
P4_NEW = P4_OLD + '        gf_rmVHProtoss(p);\n'


def scale_waves(t):
    def up(m):
        nums = [int(x) for x in m.group(2).split(',')]
        return m.group(1) + ', '.join(str(math.ceil(n * WAVE_MULT)) for n in nums) + m.group(3)
    return re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, *\d+){3})(, *")', up, t)


def once(t, old, new):
    assert t.count(old) == 1, old[:60]
    return t.replace(old, new)


def edit_script(m, t):
    if m == 'TRaynor01':
        t = once(t, BUFF_OLD_SP, BUFF_NEW)
        t = once(t, T1_ANCHOR, vh_block() + T1_ANCHOR)
        t = once(t, T1_OLD, T1_NEW)
    elif m == 'TRaynor02':
        t = once(t, BUFF_OLD_SP, BUFF_NEW)
        t = once(t, T2_ANCHOR, vh_block() + T2_ANCHOR)
        t = once(t, T2_OLD, T2_NEW)
    else:
        t = once(t, ZERG_ANCHOR, vh_block() + ZERG_ANCHOR)
        t = once(t, ZERG_OLD, ZERG_NEW)
        if m == 'TTychus01':
            t = once(t, BUFF_OLD, BUFF_NEW)
            t = once(t, P4_OLD, P4_NEW)
    n = 0
    if m != 'TRaynor01':
        t, n = scale_waves(t)
        assert n > 0, m
    return t, n


MAPS = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        changed = {'metadata.txt'}
        for m in MAPS:
            p = root / f'{m}.SC2Map' / 'mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8')
            nl = '\r\n' if '\r\n' in raw else '\n'
            t, n = edit_script(m, raw.replace('\r\n', '\n'))
            p.write_bytes(t.replace('\n', nl).encode('utf-8'))
            changed.add(f'{m}.SC2Map/mapscript.galaxy')
            print(f'{m}: waves scaled {n}')
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n not in changed:
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
