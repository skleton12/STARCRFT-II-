#!/usr/bin/env python3
"""Build CCM 0.3.20 from 0.3.19: 정화자 호위 병력 + 동맹별 자기 기지 우선 방어 (3번 미션).

사용자 지시 (2026-10-17): "정화자 유닛도 소환해줘, 아니면 땅굴벌레가 그곳에 못 오게".
원인: 원본 2번 저그 땅굴벌레 등장 지점(지역 22, (23,43.1))이 정화자 기지 바로 북쪽이다. 정화자 병력은 건물 완성(약 165초) 뒤에야
      나오고, 나온 뒤에도 레이너 본진 쪽 위협부터 쫓아 자기 기지를 비웠다.
원본 공세 흐름을 바꾸지 않으려고 '소환' 쪽을 택함:
  - 일꾼 도착 때 정화자 호위 병력 소환: 파수병 4 + 피닉스 사도 2 (시험값), 연결체 북쪽 (25~35, 37).
  - 동맹마다 자기 기지 위협을 먼저 막는다. 정화자: 자기 기지 (29,31) 반경 16 → 레이너 구역 → 원시저그 기지.
    원시저그: 자기 기지 (104.5,45.5) 반경 12 → 레이너 구역 → 정화자 기지.
땅굴 위치는 그대로 (원본 유지).

Usage: python3 tools/build_v0320.py <0.3.19 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.19', b'version=0.3.20'
M3 = 'TRaynor03.SC2Map/'

FIND_START = 'void gf_m3_FindThreat () {'
FIND_NEW = '''point gv_m3_threat10;
point gv_m3_threat11;
bool gv_m3_has10;
bool gv_m3_has11;

unitgroup gf_m3_Enemies (point c,fixed r) {
    unitgroup e;
    int p;
    e=UnitGroupEmpty();
    for (p=2;p<=5;p+=1) {
        UnitGroupAddUnitGroup(e,UnitGroup(null,p,RegionCircle(c,r),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
    }
    return e;
}

void gf_m3_FindThreat () {
    unitgroup raynor;
    unitgroup pz;
    unitgroup zz;
    // Each ally defends its own base first, then Raynor's area, then the other ally (trial radii).
    raynor=gf_m3_Enemies(Point(92.0,38.0),24.0);
    UnitGroupAddUnitGroup(raynor,gf_m3_Enemies(Point(65.0,47.0),12.0));
    pz=gf_m3_Enemies(Point(29.0,31.0),16.0);
    zz=gf_m3_Enemies(Point(104.5,45.5),12.0);
    gv_m3_has10=true;
    if (UnitGroupCount(pz,c_unitCountAlive)>0) { gv_m3_threat10=UnitGetPosition(UnitGroupClosestToPoint(pz,Point(29.0,31.0))); }
    else if (UnitGroupCount(raynor,c_unitCountAlive)>0) { gv_m3_threat10=UnitGetPosition(UnitGroupClosestToPoint(raynor,Point(92.0,38.0))); }
    else if (UnitGroupCount(zz,c_unitCountAlive)>0) { gv_m3_threat10=UnitGetPosition(UnitGroupClosestToPoint(zz,Point(104.5,45.5))); }
    else { gv_m3_has10=false; }
    gv_m3_has11=true;
    if (UnitGroupCount(zz,c_unitCountAlive)>0) { gv_m3_threat11=UnitGetPosition(UnitGroupClosestToPoint(zz,Point(104.5,45.5))); }
    else if (UnitGroupCount(raynor,c_unitCountAlive)>0) { gv_m3_threat11=UnitGetPosition(UnitGroupClosestToPoint(raynor,Point(92.0,38.0))); }
    else if (UnitGroupCount(pz,c_unitCountAlive)>0) { gv_m3_threat11=UnitGetPosition(UnitGroupClosestToPoint(pz,Point(29.0,31.0))); }
    else { gv_m3_has11=false; }
    gv_m3_hasThreat=(gv_m3_has10 || gv_m3_has11);
}

void gf_m3_GuardWarp () {
    int i;
    point at;
    actor fx;
    // Purifier guard squad that arrives with the probes (trial: 4 Sentinels + 2 Fenix Adepts).
    for (i=0;i<6;i+=1) {
        at=Point(25.0+2.0*i,37.0);
        fx=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at);
        ActorSend(fx,"AnimPlay Warp Birth NonLooping");
        if (i<4) { UnitCreate(1,"ZealotPurifier",0,10,at,270.0); }
        else { UnitCreate(1,"AdeptFenix",0,10,at,270.0); }
    }
}

void gf_m3_OldFindThreat () {'''
ATTACK_OLD = '    if (gv_m3_hasThreat) {\n        target=gv_m3_threat;\n'
ATTACK_NEW = '    if ((p==10 && gv_m3_has10) || (p==11 && gv_m3_has11)) {\n        if (p==10) { target=gv_m3_threat10; } else { target=gv_m3_threat11; }\n'
GUARD_OLD = '    drones=UnitLastCreatedGroup();\n'
GUARD_NEW = '    drones=UnitLastCreatedGroup();\n    gf_m3_GuardWarp();\n'


def script(data):
    text = data.decode('utf-8')
    for old, new in [(FIND_START, FIND_NEW), (ATTACK_OLD, ATTACK_NEW), (GUARD_OLD, GUARD_NEW)]:
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
