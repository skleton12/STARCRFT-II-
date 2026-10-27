#!/usr/bin/env python3
"""0.5.11 -> 0.5.12: 레드스톤 지원 지점 커서 2차 (사용자 2026-10-27 "커서는 나오지 않음").

협동전 상단 지점 능력(HHBomberPlatformAreaBombTopBarOrder 등)과 비교해 다른 점을 맞춘다.
- 지점 능력 RM5_AllySupport/RM5_PrimalSupport: 명령 버튼에 ToSelection, RequireTargetVision 0 (협동전과 같게).
  안 보이는 곳 거부는 스크립트(CallBad)가 그대로 한다.
- 시전 유닛: NoDraw·Uncursorable 끔 (협동전 전역 시전 유닛에 없는 값; 모델이 Invisible이라 보이지 않음).
- 대화 상자 클릭 처리 안에서 바로 커서를 열면 클릭이 끝나면서 취소될 수 있어, 1/16초 뒤 연다.
지도 클릭 대체는 그대로.

사용자 지시 (2026-10-27): "컴퓨터가 내 기지 근처에 있는데 저 병력 공격하러 가게 해줘 자동으로", "재사용 대기시간 90초로".
- 동맹 병력은 집결지(레이너 기지 앞)에서 정화자 10기·원시저그 인구 16을 기다리지 않고, 바로 가장 가까운 저그 건물로
  공격 이동한다. 핑(30초)·레이너 기지 방어가 먼저인 것은 그대로.
- 지원 호출 재사용 대기 30초 → 90초 (첫 사용 약 1분 뒤는 그대로). 안내 문구도 고친다.

Usage: python3 tools/build_v0512.py <0.5.11 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.11', b'version=0.5.12'
S = 'TTosh01.SC2Map/mapscript.galaxy'
U = 'TTosh01.SC2Map/base.sc2data/gamedata/unitdata.xml'
A = 'TTosh01.SC2Map/base.sc2data/gamedata/abildata.xml'

SCRIPT = [
    ('    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/CallAim"));\n'
     '    UISetTargetingOrder(',
     '    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/CallAim"));\n'
     '    Wait(0.0625,c_timeReal);\n'
     '    if (gv_m5_aimP!=p) { return; }\n'
     '    UISetTargetingOrder('),
    ('    gv_m5_callAt[p]=GameGetMissionTime()+30.0;\n', '    gv_m5_callAt[p]=GameGetMissionTime()+90.0;\n'),
]
GO = '''    // 0.5.12 (user 2026-10-27): no gathering; every ally unit attacks the nearest Zerg structure on its own.
    if (!gv_m5_hasBase) { return; }
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (UnitOrderCount(u)==0 || !UnitGroupHasUnit(sent,u)) {
            UnitGroupAdd(sent,u);
            UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),gv_m5_enemyBase),c_orderQueueReplace);
        }
    }
}
'''


def attack(t):
    a = t.index('void gf_m5_Attack (int p) {')
    s = t.index('    ready=UnitGroupEmpty();\n', a)
    e = t.index('\nbool gt_m5_Ping_Func', a)
    assert t.count('    ready=UnitGroupEmpty();\n') == 1 and s < e
    return t[:s] + GO + t[e:]


LOC = 'TTosh01.SC2Map/{}.sc2data/localizeddata/gamestrings.txt'
LOCS = 'kokr dede enus eses esmx frfr itit plpl ptbr ruru zhcn zhtw'.split()


def locale(t, ko):
    pairs = [('30-second cooldown each', '90-second cooldown each')]
    if ko: pairs.append(('각각 재사용 대기 30초', '각각 재사용 대기 90초'))
    return sub(t, pairs)
UNIT = [
    ('    <FlagArray index="NoDraw" value="1" />\n', ''),
    ('    <FlagArray index="Uncursorable" value="1" />\n', ''),
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t


def abil(t):
    for aid in ('RM5_AllySupport', 'RM5_PrimalSupport'):
        a = t.index(f'<CAbilEffectTarget id="{aid}">')
        b = t.index('</CAbilEffectTarget>', a)
        blk = t[a:b]
        old = f'    <CmdButtonArray index="Execute" DefaultButtonFace="{aid}" />\n'
        assert blk.count(old) == 1 and 'RequireTargetVision' not in blk
        blk = blk.replace(old, '    <Flags index="RequireTargetVision" value="0" />\n'
                          f'    <CmdButtonArray index="Execute" DefaultButtonFace="{aid}">\n'
                          '      <Flags index="ToSelection" value="1" />\n'
                          '    </CmdButtonArray>\n')
        t = t[:a] + blk + t[b:]
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        jobs = [(S, lambda t: attack(sub(t, SCRIPT))), (U, lambda t: sub(t, UNIT)), (A, abil)]
        jobs += [(LOC.format(l), (lambda k: lambda t: locale(t, k))(l == 'kokr')) for l in LOCS]
        for name, fn in jobs:
            t = files[name].decode('utf-8')
            nl = '\r\n' if '\r\n' in t else '\n'
            if name == U:  # only the caster unit block
                t = t.replace('\r\n', '\n')
                a = t.index('<CUnit id="RM5_AllyCaster">'); b = t.index('</CUnit>', a)
                t = t[:a] + fn(t[a:b]) + t[b:]
            else:
                t = fn(t.replace('\r\n', '\n'))
            files[name] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (S, U, A, 'metadata.txt') and n not in [LOC.format(l) for l in LOCS]: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
