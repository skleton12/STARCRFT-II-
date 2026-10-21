#!/usr/bin/env python3
"""Build CCM 0.4.59 from 0.4.58: 정화자 수정탑 선택 원·드래그 선택 (사용자 보고 2026-10-21).

1. 수정탑을 클릭하면 선택 원이 작다 (사용자 선택: '선택 원이 작음'). 4번 맵은 동맹 소유 수정탑에만 협동전 정화자 모델
   Pylon_Purifier_COOP 를 씌우는데 (ModelSwap), 이 모델 정의에 SelectionRadius 가 없어 기본(작은) 원이 나온다.
   원작 PylonBase 값(SelectionRadius·ShadowRadius 1.1762)을 넣는다. 정화자 광자포 모델(PhotonCannon_Purifier_COOP)도
   같은 누락이라 원작 PhotonCannonBase 값(1.1762)을 넣는다 (3·4번). 관문·연결체·융화소는 이미 값이 있다.
2. 드래그에 수정탑이 같이 잡힘 (사용자 선택: '드래그에 수정탑 안 잡힘'). 데이터에는 드래그에서만 빼는 플래그가 없어
   스크립트로 처리한다: 플레이어 1의 선택이 바뀔 때 선택에 동맹(8) 수정탑과 다른 유닛이 함께 있으면 수정탑만 뺀다.
   수정탑 하나만 클릭하면 그대로 선택된다. 4번 맵만 (3번은 수정탑이 전역 모델 교체 방식이라 확인 후).

Usage: python3 tools/build_v0459.py <0.4.58 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.58', b'version=0.4.59'
M3, M4 = 'TRaynor03.SC2Map/', 'TTychus01.SC2Map/'
SCRIPT = M4 + 'mapscript.galaxy'
ADD = {'Pylon_Purifier_COOP': '<SelectionRadius value="1.176200" /><ShadowRadius value="1.176200" />',
       'PhotonCannon_Purifier_COOP': '<SelectionRadius value="1.176200" />'}

DRAG = '''
// 0.4.59: an allied (Purifier) Pylon is dropped from player 1's selection when other units are selected with it.
bool gt_m4_PylonDrag_Func (bool testConds,bool runActions) {
    unitgroup sel;
    unitgroup pylons;
    unit u;
    int i;
    if (!runActions) { return true; }
    sel=UnitGroupSelected(1);
    pylons=UnitGroupEmpty();
    i=UnitGroupCount(sel,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(sel,i);
        if (UnitGetType(u)=="Pylon" && UnitGetOwner(u)==8) { UnitGroupAdd(pylons,u); }
    }
    if (UnitGroupCount(pylons,c_unitCountAll)==0 || UnitGroupCount(pylons,c_unitCountAll)>=UnitGroupCount(sel,c_unitCountAll)) { return true; }
    i=UnitGroupCount(pylons,c_unitCountAll);
    for (;i>0;i-=1) { UnitSelect(UnitGroupUnit(pylons,i),1,false); }
    return true;
}

'''


def models(names):
    def fn(d):
        t = d.decode('utf-8')
        for mid in names:
            m = re.search(rf'<CModel id="{mid}"[^>]*>.*?</CModel>', t, re.S)
            if not m:
                continue
            b = m.group(0)
            assert 'SelectionRadius' not in b, mid
            b = b.replace('</CModel>', ADD[mid] + '</CModel>')
            t = t[:m.start()] + b + t[m.end():]
        return t.encode('utf-8')
    return fn


def script(d):
    t = d.decode('utf-8')
    anchor = 'void gf_m4_Init () {'
    assert t.count(anchor) == 1 and 'gt_m4_PylonDrag_Func' not in t
    t = t.replace(anchor, DRAG + anchor)
    reg = '    t=TriggerCreate("gt_m4_Ping_Func");\n'
    assert t.count(reg) == 1
    t = t.replace(reg, '    t=TriggerCreate("gt_m4_PylonDrag_Func");\n    TriggerAddEventUnitSelected(t,null,1,true);\n' + reg)
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW),
       M4 + 'base.sc2data/gamedata/modeldata.xml': models(['Pylon_Purifier_COOP', 'PhotonCannon_Purifier_COOP']),
       M3 + 'base.sc2data/gamedata/modeldata.xml': models(['PhotonCannon_Purifier_COOP']),
       SCRIPT: script}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
