#!/usr/bin/env python3
"""Build CCM 0.4.23 from 0.4.22: 원시 알이 쌓이기만 하고 부화하지 않음 (사용자 스크린샷 2026-10-18, 3번 5:19).

협동전 원시 감시자는 알을 공짜로 낳고, 알이 부화할 때(DehakaTrainEggMorphTo*) 비용을 낸다.
스크립트가 자원만 보고 알을 계속 낳게 해서, 부화 비용을 기다리는 알이 쌓였다
(0.4.21까지는 양방향 자원 공유로 레이너 돈이 부화에 쓰였다).
부화를 기다리는 알이 감시자 하나당 2개 이상이면 새 알을 낳지 않는다 (시험값). 3·4번 맵.

Usage: python3 tools/build_v0423.py <0.4.22 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.22', b'version=0.4.23'
MAPS = {'TRaynor03.SC2Map/mapscript.galaxy': ('m3', 11), 'TTychus01.SC2Map/mapscript.galaxy': ('m4', 9)}
GATE = '''    n=UnitGroupCount(posts,c_unitCountAll);
    // Eggs pay when they hatch (co-op). Do not lay more while 2+ eggs per Warden still wait for money (0.4.23, trial).
    if (UnitGroupCount(UnitGroup("DehakaTrainEggZergling",{p},RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)+UnitGroupCount(UnitGroup("DehakaTrainEggRoach",{p},RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)+UnitGroupCount(UnitGroup("DehakaTrainEggHydralisk",{p},RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)>=2*n) {{ return; }}
'''


def patch(t, tag, p):
    head = f'void gf_{tag}_Hatch () {{'
    i = t.index(head); j = t.index('\n}\n', i)
    body = t[i:j]
    old = '    n=UnitGroupCount(posts,c_unitCountAll);\n'
    assert body.count(old) == 1
    body = body.replace(old, GATE.format(p=p))
    return t[:i] + body + t[j:]


def fix(tag, p):
    def f(d):
        crlf = b'\r\n' in d
        t = patch(d.decode('utf-8').replace('\r\n', '\n'), tag, p)
        return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')
    return f


FIX = {n: fix(*v) for n, v in MAPS.items()}
FIX['metadata.txt'] = lambda d: d.replace(OLD, NEW)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), FIX[info.filename](d) if info.filename in FIX else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    sup = HERE / 'data/mission04_support.galaxy'
    sup.write_text(patch(sup.read_text(), 'm4', 9))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
