#!/usr/bin/env python3
"""Build CCM 0.4.25 from 0.4.24: 원시저그 광물 수입 2초당 25 → 40 (시험값, maps 3·4).

사용자 지시 (2026-10-19): 원시저그 자원이 빨리 빠지니 원시저그만 광물을 더 준다. 가스·정화자 수입은 그대로.

Usage: python3 tools/build_v0425.py <0.4.24 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.24', b'version=0.4.25'
PRIMAL_MINERALS = 40  # trial
FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW)}
for m, p in (('TRaynor03', 11), ('TTychus01', 9)):
    a = f'PlayerModifyPropertyInt({p},c_playerPropMinerals,c_playerPropOperAdd,25);'.encode()
    b = f'PlayerModifyPropertyInt({p},c_playerPropMinerals,c_playerPropOperAdd,{PRIMAL_MINERALS});'.encode()
    def fn(d, a=a, b=b):
        assert d.count(a) == 1, a
        return d.replace(a, b)
    FIX[m + '.SC2Map/mapscript.galaxy'] = fn


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
