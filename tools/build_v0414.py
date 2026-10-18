#!/usr/bin/env python3
"""Build CCM 0.4.14 from 0.4.13: 4번 동맹 세 가지 (사용자 보고 2026-10-18).

1. 정화자 관문·차원 관문에서 플레이어가 직접 소환할 수 있었다 (조종 공유 때문) → 정화자(8)의 관문·차원 관문 생산 명령을 막는다.
   동맹 소환은 스크립트가 UnitCreate로 하므로 영향 없다.
2. 정화자가 원시저그보다 많이 나온다 → 정화자 묶음 간격 20초/관문 수 → 40초/관문 수 (시험값).
3. 동맹이 한 기씩 줄줄이 간다 → 공격은 대기 자리에 모였다가 출발: 대기 자리 반경 8 안에
   정화자 10기·원시저그 8기(시험값)가 모이면 그 무리만 가장 가까운 적 건물로 보낸다. 출발한 무리는 계속 공격한다.
   레이너 본진 위협은 지금처럼 모두 바로 막으러 간다. 핑 30초 우선도 그대로.

Usage: python3 tools/build_v0414.py <0.4.13 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.13', b'version=0.4.14'
M4 = 'TTychus01.SC2Map/mapscript.galaxy'

FIND = '''bool gv_m4_raid;
bool gv_m4_hasBase;
unitgroup gv_m4_sent8;
unitgroup gv_m4_sent9;

void gf_m4_FindThreat () {
    unitgroup raynor;
    // Threat inside Raynor's base: everyone defends. Otherwise gathered groups attack the nearest enemy structure.
    raynor=gf_m4_Enemies(Point(78.0,21.0),20.0);
    gv_m4_raid=(UnitGroupCount(raynor,c_unitCountAlive)>0);
    if (gv_m4_raid) { gv_m4_threat8=UnitGetPosition(UnitGroupClosestToPoint(raynor,Point(78.0,21.0))); }
    gv_m4_hasBase=gf_m4_EnemyBase(Point(78.0,21.0));
}'''
ATTACK = '''void gf_m4_Attack (int p) {
    unitgroup g;
    unitgroup ready;
    unitgroup sent;
    int i;
    int need;
    unit u;
    point rally;
    // Ping first (30 s); base threat: everyone defends; else gather at the rally and leave together (user 2026-10-18).
    g=gf_m4_Army(p);
    i=UnitGroupCount(g,c_unitCountAll);
    if (p==8) { rally=Point(63.0,29.0); sent=gv_m4_sent8; need=10; } else { rally=Point(66.0,30.0); sent=gv_m4_sent9; need=8; }
    if (GameGetMissionTime()<gv_m4_pingUntil) {
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            if (UnitOrderCount(u)==0) { UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),gv_m4_ping),c_orderQueueReplace); }
        }
        return;
    }
    if (gv_m4_raid) {
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            if (UnitOrderCount(u)==0 || (gv_m4_threatTick==0 && DistanceBetweenPoints(UnitGetPosition(u),gv_m4_threat8)>6.0)) {
                UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),gv_m4_threat8),c_orderQueueReplace);
            }
        }
        return;
    }
    ready=UnitGroupEmpty();
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (UnitGroupHasUnit(sent,u)) {
            if (gv_m4_hasBase && UnitOrderCount(u)==0) { UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),gv_m4_enemyBase),c_orderQueueReplace); }
            continue;
        }
        if (DistanceBetweenPoints(UnitGetPosition(u),rally)<=8.0) { UnitGroupAdd(ready,u); }
        else if (UnitOrderCount(u)==0) { UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),rally),c_orderQueueReplace); }
    }
    if (gv_m4_hasBase && UnitGroupCount(ready,c_unitCountAlive)>=need) {
        i=UnitGroupCount(ready,c_unitCountAll);
        for (;i>0;i-=1) {
            u=UnitGroupUnit(ready,i);
            UnitGroupAdd(sent,u);
            UnitIssueOrder(u,OrderTargetingPoint(AbilityCommand("attack",0),gv_m4_enemyBase),c_orderQueueReplace);
        }
    }
}'''
INIT_ADD = '''    gv_m4_sent8=UnitGroupEmpty();
    gv_m4_sent9=UnitGroupEmpty();
    // The player shares control of the Purifiers for the Probe; Purifier gates must not train for the player.
    for (ally=0;ally<8;ally+=1) {
        TechTreeAbilityAllow(8,AbilityCommand("GatewayTrain",ally),false);
        TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",ally),false);
    }
'''


def swap_func(t, head, new):
    i = t.index(head)
    j = t.index('\n}\n', i) + 2
    return t[:i] + new + t[j:]


def patch(t):
    assert t.count('void gf_m4_FindThreat () {') == 1 and t.count('void gf_m4_Attack (int p) {') == 1
    t = swap_func(t, 'void gf_m4_FindThreat () {', FIND)
    t = swap_func(t, 'void gf_m4_Attack (int p) {', ATTACK)
    old = 'gv_m4_nextMake8=GameGetMissionTime()+20.0/IntToFixed(n);'
    assert t.count(old) == 1
    t = t.replace(old, 'gv_m4_nextMake8=GameGetMissionTime()+40.0/IntToFixed(n);')
    a = '    gf_m4_Mercs();\n    PlayerSetColorIndex(8,2,true);'
    assert t.count(a) == 1
    return t.replace(a, INIT_ADD + a)


def script(d):
    crlf = b'\r\n' in d
    t = patch(d.decode('utf-8').replace('\r\n', '\n'))
    return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    sup = HERE / 'data/mission04_support.galaxy'
    sup.write_text(patch(sup.read_text()))
    fix = {M4: script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), fix[info.filename](d) if info.filename in fix else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in fix: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
