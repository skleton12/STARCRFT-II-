#!/usr/bin/env python3
"""Build CCM 0.3.11 from 0.3.10: 정화 광선이 자연스럽게 움직이게 (3번 미션).

사용자 보고 (2026-10-17): "광선이 너무 딱딱딱딱 움직인다".
원인: 0.3.8~0.3.10은 0.25초마다 광선을 1칸씩 순간이동(UnitSetPosition)시켰고, 남은 적 추적도 적 위치로 바로 옮겼다.
수정: 광선 유닛(비행, 속도 4)에 이동 명령을 주어 엔진이 부드럽게 날게 한다. 스크립트는 0.125초마다 현재 위치만 읽고,
      0.25초마다 그 자리를 태운다 (피해·반경 0.3.8 그대로). 경로는 5줄 왕복의 꺾이는 점 10개.
      남은 적 추적도 가장 가까운 적에게 이동 명령(0.5초마다 갱신).
      이동 명령이 먹지 않아 광선이 멈춰 있으면(0.125초 동안 0.05칸 미만 이동) 그때만 0.5칸씩 보간 이동으로 대신 민다.
경로·속도·시간은 시험값.

Usage: python3 tools/build_v0311.py <0.3.10 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.10', b'version=0.3.11'
M3 = 'TRaynor03.SC2Map/'

HELPER_ANCHOR = 'void gf_m3_Burn (point at) {'
HELPER = '''point gv_m3_beamLast;

void gf_m3_BeamPush (unit beam,point dest) {
    point pos;
    // Fallback only: if the move order is not moving the beam, glide it 0.5 toward the destination.
    pos=UnitGetPosition(beam);
    if (DistanceBetweenPoints(pos,dest)>0.5 && DistanceBetweenPoints(pos,gv_m3_beamLast)<0.05) {
        UnitSetPosition(beam,PointWithOffsetPolar(pos,0.5,AngleBetweenPoints(pos,dest)),true);
    }
    gv_m3_beamLast=pos;
}

void gf_m3_Burn (point at) {'''

DECL_OLD = '    unitgroup left;\n'
DECL_NEW = '    unitgroup left;\n    int t;\n    point dest;\n'

NEW_BLOCK = '''    UnitCreate(1,"RM3_PurifierBeamUnit",0,10,Point(19.0,23.0),0.0);
    beamUnit=UnitLastCreated();
    gv_m3_beamLast=Point(0.0,0.0);
    Wait(2.5,c_timeGame);
    // The beam flies on its own (move orders), the script only reads where it is and burns there.
    for (row=0;row<5 && !gv_gameOver;row+=1) {
        for (k=0;k<2 && !gv_gameOver;k+=1) {
            if (ModI(row,2)==0) { bx=19.0+29.0*k; } else { bx=48.0-29.0*k; }
            by=23.0+5.0*row;
            dest=Point(bx,by);
            UnitIssueOrder(beamUnit,OrderTargetingPoint(AbilityCommand("move",0),dest),c_orderQueueReplace);
            for (t=0;t<400 && !gv_gameOver;t+=1) {
                at=UnitGetPosition(beamUnit);
                if (ModI(t,2)==0) { gf_m3_Burn(at); }
                if (DistanceBetweenPoints(at,dest)<=0.5) { break; }
                Wait(0.125,c_timeGame);
                gf_m3_BeamPush(beamUnit,dest);
            }
        }
    }
    // Anything left on the plateau: the beam flies to the nearest one and burns it (up to 30 s, trial).
    for (t=0;t<240 && !gv_gameOver;t+=1) {
        if (ModI(t,4)==0) {
            left=gf_m3_SiteEnemies();
            if (UnitGroupCount(left,c_unitCountAlive)==0) { break; }
            dest=UnitGetPosition(UnitGroupClosestToPoint(left,UnitGetPosition(beamUnit)));
            UnitIssueOrder(beamUnit,OrderTargetingPoint(AbilityCommand("move",0),dest),c_orderQueueReplace);
        }
        at=UnitGetPosition(beamUnit);
        if (ModI(t,2)==0) { gf_m3_Burn(at); }
        Wait(0.125,c_timeGame);
        gf_m3_BeamPush(beamUnit,dest);
    }
'''


def script(data):
    text = data.decode('utf-8')
    a = text.index('    UnitCreate(1,"RM3_PurifierBeamUnit"')
    b = text.index('    UnitRemove(beamUnit);\n', a)
    old_block = text[a:b]
    assert 'UnitSetPosition(beamUnit,at,true);' in old_block and text.count('UnitCreate(1,"RM3_PurifierBeamUnit"') == 1
    text = text[:a] + NEW_BLOCK + text[b:]
    for old, new in [(HELPER_ANCHOR, HELPER), (DECL_OLD, DECL_NEW)]:
        assert text.count(old) == 1, old
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
