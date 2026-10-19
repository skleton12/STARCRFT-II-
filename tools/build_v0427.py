#!/usr/bin/env python3
"""Build CCM 0.4.27 from 0.4.26: 3번 동맹 병력 상한 인구 100 → 60 (시험값).

사용자 보고 (2026-10-19, 3번 실행): 동맹 병력이 생각보다 많이 쌓이고 후반에 너무 물량으로 밀어붙인다.
정화자(10)·원시저그(11) 생산 상한 검사 네 곳만 바꾼다. 4번은 그대로.

Usage: python3 tools/build_v0427.py <0.4.26 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.26', b'version=0.4.27'
CAP = '60.0'  # trial
SUBS = ['if (gf_m3_Food(p)+gf_m3_UnitFood(kind)>100.0)', 'if (gf_m3_Food(11)+2.0>100.0 ',
        'if (!UnitIsAlive(gate) || gf_m3_Food(10)+2.0>100.0)', 'if (gf_m3_Food(p)+food>100.0 ']


def script(d):
    for s in SUBS:
        a = s.encode()
        assert d.count(a) == 1, s
        d = d.replace(a, s.replace('100.0', CAP).encode())
    return d


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), 'TRaynor03.SC2Map/mapscript.galaxy': script}


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
