#!/usr/bin/env python3
"""Build CCM 0.4.18 from 0.4.17: 동맹 소환에 레이너 자원이 나가던 것 (사용자 보고 2026-10-18).

동맹 일꾼 조종을 위해 동맹→레이너 관계를 '공유 시야·조종·자원 공유'로 했는데, 자원 공유 때문에 레이너 자원이 섞여 나갔다.
'공유 시야·조종'만 남긴다 (3·4번 맵, 공통 스크립트). 동맹 건물·병력 값은 동맹 자기 자원에서만 나간다.

Usage: python3 tools/build_v0418.py <0.4.17 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.17', b'version=0.4.18'
A, B = b'AllyWithSharedVisionControlAndSpending', b'AllyWithSharedVisionAndControl'


def script(d):
    assert d.count(A) == 2, d.count(A)
    return d.replace(A, B)


FIX = {'TRaynor03.SC2Map/mapscript.galaxy': script, 'TTychus01.SC2Map/mapscript.galaxy': script,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        for n in prev.namelist():
            if n.endswith('mapscript.galaxy') and n not in FIX: assert A not in prev.read(n), n
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
    sup.write_bytes(sup.read_bytes().replace(A, B))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
