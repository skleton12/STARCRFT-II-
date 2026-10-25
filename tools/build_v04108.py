#!/usr/bin/env python3
"""0.4.107 -> 0.4.108: 동맹 군사 건물을 기지에서 조금 떨어져 짓기 (3·4번) + 어부지리 가스 매장량 +65% -> +100% (사용자 2026-10-25).

1) 사용자 "동맹 군사건물 기지에서 조금 멀찍이 건설": 0.4.93 자동 건설은 넥서스·원시 군락 바로 옆 빈자리부터 골라
   일꾼 길(광물 줄)과 기지 둘레가 막혔다. 수정탑(→관문)과 원시 감시자는 기지에서 광물 반대쪽으로 AWAY(8, 시험값)만큼
   떨어진 점 둘레에 짓는다. 그 둘레에 자리가 없으면 예전처럼 기지 둘레에 짓는다. 광자포·원시 벌레(방어 건물)는 그대로.
   수정탑·광자포·원시 벌레 개수를 세는 반경은 12/14 -> 20으로 넓힌다 (멀리 지은 건물을 못 세서 계속 짓는 일 방지).
2) 사용자 "자원은 많은데 가스가 적음": 어부지리 레이너 본진 풍부한 가스 2곳 매장량 4125(+65%) -> 5000(+100%, 시험값).

Usage: python3 tools/build_v04108.py <0.4.107 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.107', b'version=0.4.108'
AWAY = 8.0  # 시험값
FN_ANCHOR = 'int gf_rmNear (int p, string kind, point at, fixed r) {'
FN = f'''// 0.4.108: a point AWAY from the base on the side opposite its resources, so army buildings stand a little off the base.
point gf_rmAwayPt (int p) {{
    unitgroup ore=UnitGroup(null,0,RegionCircle(gv_rmBasePt[p],12.0),UnitFilter((1 << c_targetFilterRawResource),0,0,0),0);
    if (UnitGroupCount(ore,c_unitCountAll)==0) {{ return gv_rmBasePt[p]; }}
    return PointWithOffsetPolar(gv_rmBasePt[p],{AWAY},AngleBetweenPoints(UnitGroupCenterOfGroup(ore),gv_rmBasePt[p]));
}}

''' + FN_ANCHOR
PAIRS = [
    ('py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],12.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);\n'
     '        if (UnitGroupCount(py,c_unitCountAlive)==0) { gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gv_rmBasePt[pp],10.0); }',
     'py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],20.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);\n'
     '        if (UnitGroupCount(py,c_unitCountAlive)==0) { if (!gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gf_rmAwayPt(pp),6.0)) { gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gv_rmBasePt[pp],10.0); } }'),
    ('py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],12.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))),0);',
     'py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],20.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))),0);'),
    ('at=UnitGetPosition(UnitGroupClosestToPoint(py,gv_rmBasePt[pp]));',
     'at=UnitGetPosition(UnitGroupClosestToPoint(py,gf_rmAwayPt(pp)));'),
    ('{ gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gv_rmBasePt[pp],14.0); }',
     '{ gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gf_rmAwayPt(pp),10.0); }'),
    ('gf_rmNear(pp,"PhotonCannon",gv_rmBasePt[pp],14.0)', 'gf_rmNear(pp,"PhotonCannon",gv_rmBasePt[pp],20.0)'),
    ('{ gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",0,"DehakaBarracks",gv_rmBasePt[pz],10.0); }',
     '{ if (!gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",0,"DehakaBarracks",gf_rmAwayPt(pz),6.0)) { gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",0,"DehakaBarracks",gv_rmBasePt[pz],10.0); } }'),
    ('gf_rmNear(pz,"DehakaNydusDestroyer",gv_rmBasePt[pz],14.0)', 'gf_rmNear(pz,"DehakaNydusDestroyer",gv_rmBasePt[pz],20.0)'),
]
OBJ = 'TTychus01.SC2Map/objects'
GAS = [('<ObjectUnit Id="43" Position="85.5,27.5,0" Scale="1,1,1" UnitType="RichVespeneGeyser" Resources="4125">',
        '<ObjectUnit Id="43" Position="85.5,27.5,0" Scale="1,1,1" UnitType="RichVespeneGeyser" Resources="5000">'),
       ('<ObjectUnit Id="40" Position="81.5,13.5,0" Scale="1,1,1" UnitType="RichVespeneGeyser" Resources="4125" />',
        '<ObjectUnit Id="40" Position="81.5,13.5,0" Scale="1,1,1" UnitType="RichVespeneGeyser" Resources="5000" />')]


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt', OBJ}
        for m in ('TRaynor03', 'TTychus01'):
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            assert t.count(FN_ANCHOR) == 1 and 'gf_rmAwayPt' not in t
            t = t.replace(FN_ANCHOR, FN)
            for a, b in PAIRS:
                assert t.count(a) == 1, (m, a)
                t = t.replace(a, b)
            files[s] = t.encode('utf-8'); changed.add(s)
        o = files[OBJ].decode('utf-8')
        for a, b in GAS:
            assert o.count(a) == 1, a
            o = o.replace(a, b)
        assert 'Resources="4125"' not in o
        files[OBJ] = o.encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
