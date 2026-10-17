#!/usr/bin/env python3
"""Build CCM 0.3.21 from 0.3.20: 동맹 역할 — 방어 후 적 기지 공격 (3번 미션).

사용자 지시 (2026-10-17): "정화자: 기지 방어 후 적 기지 공격, 원시저그: 레이너 기지 방어 후 적 기지 공격".
  정화자: 자기 기지 (29,31) 반경 16 위협 → 방어. 없으면 병력 10기 이상일 때 가장 가까운 적 건물 공격, 아니면 (30,37) 대기.
  원시저그: 레이너 구역((92,38) 반경 24, (65,47) 반경 12)·자기 기지 (104.5,45.5) 반경 12 위협 → 레이너 본진에 가장 가까운 적부터 방어.
            없으면 병력 인구 16 이상일 때 레이너 본진에서 가장 가까운 적 건물 공격, 아니면 레이너 언덕길 앞 (80,46) 대기.
  적 건물 = 2~4번(원본 AI 저그)의 살아 있는 건물, 점막 종양 제외. 공격 시작 병력 수는 시험값.
  핑 30초 우선은 그대로.

Usage: python3 tools/build_v0321.py <0.3.20 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.20', b'version=0.3.21'
M3 = 'TRaynor03.SC2Map/'

FIND_OLD_START = 'void gf_m3_FindThreat () {\n    unitgroup raynor;'
FIND_OLD_END = '    gv_m3_hasThreat=(gv_m3_has10 || gv_m3_has11);\n}\n'
FIND_NEW = '''point gv_m3_rally10;
point gv_m3_rally11;

bool gf_m3_EnemyBase (point from) {
    unitgroup g;
    unitgroup all;
    unit u;
    int p;
    int i;
    string t;
    // Nearest live enemy structure of the original AI Zerg (players 2-4), creep tumors excluded.
    all=UnitGroupEmpty();
    for (p=2;p<=4;p+=1) {
        g=UnitGroup(null,p,RegionEntireMap(),UnitFilter((1 << c_targetFilterStructure),0,0,(1 << (c_targetFilterDead - 32))),0);
        i=UnitGroupCount(g,c_unitCountAll);
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            t=UnitGetType(u);
            if (t!="CreepTumor" && t!="CreepTumorBurrowed" && t!="CreepTumorQueen") { UnitGroupAdd(all,u); }
        }
    }
    if (UnitGroupCount(all,c_unitCountAlive)==0) { return false; }
    gv_m3_enemyBase=UnitGetPosition(UnitGroupClosestToPoint(all,from));
    return true;
}

void gf_m3_FindThreat () {
    unitgroup raynor;
    unitgroup pz;
    // Purifiers: defend own base, then attack. Primal Zerg: defend Raynor's base (and own), then attack.
    raynor=gf_m3_Enemies(Point(92.0,38.0),24.0);
    UnitGroupAddUnitGroup(raynor,gf_m3_Enemies(Point(65.0,47.0),12.0));
    UnitGroupAddUnitGroup(raynor,gf_m3_Enemies(Point(104.5,45.5),12.0));
    pz=gf_m3_Enemies(Point(29.0,31.0),16.0);
    gv_m3_rally10=Point(30.0,37.0);
    gv_m3_rally11=Point(80.0,46.0);
    gv_m3_has10=true;
    if (UnitGroupCount(pz,c_unitCountAlive)>0) { gv_m3_threat10=UnitGetPosition(UnitGroupClosestToPoint(pz,Point(29.0,31.0))); }
    else if (UnitGroupCount(gf_m3_Army(10),c_unitCountAlive)>=10 && gf_m3_EnemyBase(Point(29.0,31.0))) { gv_m3_threat10=gv_m3_enemyBase; }
    else { gv_m3_has10=false; }
    gv_m3_has11=true;
    if (UnitGroupCount(raynor,c_unitCountAlive)>0) { gv_m3_threat11=UnitGetPosition(UnitGroupClosestToPoint(raynor,Point(92.0,38.0))); }
    else if (gf_m3_Supply()>=16.0 && gf_m3_EnemyBase(Point(92.0,38.0))) { gv_m3_threat11=gv_m3_enemyBase; }
    else { gv_m3_has11=false; }
    gv_m3_hasThreat=(gv_m3_has10 || gv_m3_has11);
}
'''
RALLY_OLD = '    target=Point(80.0,46.0);\n    for (;i>0;i-=1) {'
RALLY_NEW = '    if (p==10) { target=gv_m3_rally10; } else { target=gv_m3_rally11; }\n    for (;i>0;i-=1) {'
GLOBAL_ANCHOR = 'point gv_m3_threat10;\n'
GLOBAL_NEW = 'point gv_m3_threat10;\npoint gv_m3_enemyBase;\n'


def script(data):
    text = data.decode('utf-8')
    a = text.index(FIND_OLD_START); b = text.index(FIND_OLD_END, a) + len(FIND_OLD_END)
    text = text[:a] + FIND_NEW + text[b:]
    for old, new in [(RALLY_OLD, RALLY_NEW), (GLOBAL_ANCHOR, GLOBAL_NEW)]:
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new, 1)
    return text.encode('utf-8')


FIX = {M3 + 'mapscript.galaxy': script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX: data = FIX[info.filename](data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path)
    a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
