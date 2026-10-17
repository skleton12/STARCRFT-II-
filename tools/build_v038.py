#!/usr/bin/env python3
"""Build CCM 0.3.8 from 0.3.7: 정화 광선이 지역 저그를 실제로 처리하게 수정 (3번 미션).

사용자 보고 (2026-10-17): "광선이 그 지역 저그를 처리하지 못함".
원인 후보 (게임 미확인, 코드 검토):
  1. 피해를 숨긴 수정탑이 UnitDamage 효과로 줬다. 숨긴 유닛이 시전자인 효과는 무시될 수 있다.
  2. 광선 이동을 이동 명령에 맡기고 UnitOrderCount==0이면 멈췄다. 명령이 안 먹으면 곧바로 끝난다.
  3. 줄 간격 7칸 > 피해 반경 3칸이라 줄 사이(최대 3.5칸) 적은 맞지 않았다.
수정:
  - 피해는 효과 대신 생명력을 직접 깎고 0 이하면 처치 (시전자·검증기·경로와 무관).
  - 광선 위치를 스크립트가 경로대로 0.25초마다 옮긴다 (UnitSetPosition 보간). 유닛 명령에 의존하지 않음.
  - 4줄 (y 23·28·33·38), 줄 간격 5, 판정 반경 3.5 → 판정 빈틈 없음. x 19~48.
  - 0.25초마다 생명력 300 (모드 재설계 시험값, 원작 정화 광선 초당 약 50과 다름).
  - 한 번 훑은 뒤에도 기지 터에 적이 남으면 남은 적 위치로 광선이 찾아가 태운다 (최대 20초, 시험값).
  대상은 적 2~5번만. 아군·주민·자원은 제외.

Usage: python3 tools/build_v038.py <0.3.7 zip> <new output zip>
"""
import argparse
import copy
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v037 as V37  # noqa: E402

OLD, NEW = b'version=0.3.7', b'version=0.3.8'
M3 = 'TRaynor03.SC2Map/'

BURN = '''void gf_m3_Burn (point at) {
    unitgroup g;
    unit u;
    int p;
    int i;
    fixed life;
    // Purifier Beam burn (mod value): 300 life per 0.25 s within 3.5 of the beam, enemy players 2-5 only.
    for (p=2;p<=5;p+=1) {
        g=UnitGroup(null,p,RegionCircle(at,3.5),UnitFilter(0,0,0,0),0);
        i=UnitGroupCount(g,c_unitCountAll);
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            if (!UnitIsAlive(u)) { continue; }
            life=UnitGetPropertyFixed(u,c_unitPropLife,c_unitPropCurrent);
            if (life<=300.0) { UnitKill(u); }
            else { UnitSetPropertyFixed(u,c_unitPropLife,life-300.0); }
        }
    }
}

bool gt_m3_Arrive_Func (bool testConds,bool runActions) {'''

DECL_OLD = '    unit beamUnit;\n    point at;\n'
DECL_NEW = '    unit beamUnit;\n    point at;\n    int row;\n    int k;\n    fixed bx;\n    fixed by;\n    unitgroup left;\n'

LOOP = '''    // Spear of Adun Purifier Beam: one beam descends, then the script walks it over the base (trial path/speed).
    UnitCreate(1,"RM3_PurifierBeamUnit",0,10,Point(19.0,23.0),0.0);
    beamUnit=UnitLastCreated();
    Wait(2.5,c_timeGame);
    for (row=0;row<4;row+=1) {
        for (k=0;k<=29;k+=1) {
            if (gv_gameOver) { break; }
            if (ModI(row,2)==0) { bx=19.0+k; } else { bx=48.0-k; }
            by=23.0+5.0*row;
            at=Point(bx,by);
            UnitSetPosition(beamUnit,at,true);
            gf_m3_Burn(at);
            Wait(0.25,c_timeGame);
        }
        for (k=1;k<=5 && row<3;k+=1) {
            if (gv_gameOver) { break; }
            at=Point(bx,23.0+5.0*row+k);
            UnitSetPosition(beamUnit,at,true);
            gf_m3_Burn(at);
            Wait(0.25,c_timeGame);
        }
    }
    // Anything left at the site: the beam goes to it and burns it (up to 20 s, trial).
    for (k=0;k<80 && !gv_gameOver;k+=1) {
        left=UnitGroupEmpty();
        for (p=2;p<=5;p+=1) { UnitGroupAddUnitGroup(left,UnitGroup(null,p,RegionCircle(Point(35.5,31.0),14.0),UnitFilter(0,0,0,0),0)); }
        if (UnitGroupCount(left,c_unitCountAlive)==0) { break; }
        at=UnitGetPosition(UnitGroupClosestToPoint(left,UnitGetPosition(beamUnit)));
        UnitSetPosition(beamUnit,at,true);
        gf_m3_Burn(at);
        Wait(0.25,c_timeGame);
    }
    UnitRemove(beamUnit);
    if (gv_gameOver) { UnitRemove(source); return true; }
'''


def script(data):
    text = data.decode('utf-8')
    head = 'bool gt_m3_Arrive_Func (bool testConds,bool runActions) {'
    for old in (head, DECL_OLD, V37.NEW_LOOP):
        assert text.count(old) == 1, old[:50]
    text = text.replace(head, BURN, 1).replace(DECL_OLD, DECL_NEW, 1).replace(V37.NEW_LOOP, LOOP, 1)
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
