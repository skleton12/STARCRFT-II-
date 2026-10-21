#!/usr/bin/env python3
"""Build CCM 0.4.55 from 0.4.54: 원시저그 출발 기준을 문서대로 인구 16 (4번, 사용자 지시 2026-10-21 "수정").

사용자 보고: 원시저그가 병력이 나오자마자 공격하러 가는 것 같다.
확인: docs/missions/04_smash_and_grab.md 는 '원시저그 인구 16 이상이면 적 건물 공격'인데, 0.4.14 코드는
대기 자리 (66,30) 반경 8 안에 8기(마리 수)만 모이면 출발시켰다. 원시 감시자 최대 3개가 저글링 알을 15초마다 낳아
8기는 금방 찬다. 원시저그(9)는 대기 자리에 모인 병력의 인구 합이 16 이상일 때 출발한다 (시험값, 문서값).
정화자(8) 10기 기준, 레이너 본진 반경 20 위협 시 전원 방어, 핑 30초 우선은 그대로.

Usage: python3 tools/build_v0455.py <0.4.54 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.54', b'version=0.4.55'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'
PAIRS = [
    ('    int need;\n    unit u;\n    point rally;\n    // Ping first (30 s);',
     '    int need;\n    fixed food;\n    unit u;\n    point rally;\n    // Ping first (30 s);'),
    ('sent=gv_m4_sent9; need=8; }', 'sent=gv_m4_sent9; need=16; }'),
    ('    if (gv_m4_hasBase && UnitGroupCount(ready,c_unitCountAlive)>=need) {',
     '    // Purifiers leave at 10 units; Primal Zerg at 16 supply (mission doc, trial; 0.4.55, was 8 units).\n'
     '    food=IntToFixed(UnitGroupCount(ready,c_unitCountAlive));\n'
     '    if (p==9) {\n'
     '        food=0.0;\n'
     '        i=UnitGroupCount(ready,c_unitCountAll);\n'
     '        for (;i>0;i-=1) { food+=gf_m4_UnitFood(UnitGetType(UnitGroupUnit(ready,i))); }\n'
     '    }\n'
     '    if (gv_m4_hasBase && food>=IntToFixed(need)) {'),
]


def script(d):
    t = d.decode('utf-8')
    for a, b in PAIRS:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), SCRIPT: script}


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
