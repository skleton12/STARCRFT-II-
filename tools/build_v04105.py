#!/usr/bin/env python3
"""0.4.104 -> 0.4.105: 사용자 편집본 어부지리를 손대지 않고 그대로 (사용자 2026-10-25 "재대로 하라고").

0.4.104는 편집본의 '걸을 수 있음' 칠하기(CellAttribute_Pgr) 중 절벽 가장자리 168칸을 임의로 지웠다. 그 변경을 되돌려
편집본의 Pgr을 바이트 그대로 넣는다. 맵의 다른 파일은 0.4.104에서 이미 편집본과 같다 (빌드 때 확인).

Usage: python3 tools/build_v04105.py <0.4.104 zip> <edited .SC2Map> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.104', b'version=0.4.105'
M = 'TTychus01.SC2Map/'
SAME = ['Objects', 't3CellFlags', 't3HeightMap', 't3SyncCliffLevel', 't3SyncHeightMap', 't3SyncTextureInfo',
        't3Terrain.xml', 't3VertCol', 't3Water', 'CellAttribute_Pnb', 'CellAttribute_Pnp', 'MapScript.galaxy']


def build(source, edited, output):
    import mpyq
    if output.exists(): raise ValueError('Output must be new')
    ed = mpyq.MPQArchive(str(edited))
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for f in SAME:
            assert files[M + f.lower()] == ed.read_file(f), f
        pgr = M + 'cellattribute_pgr'
        files[pgr] = ed.read_file('CellAttribute_Pgr')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in ('metadata.txt', pgr): assert out.read(n) == prev.read(n), n
                assert out.read(pgr) == ed.read_file('CellAttribute_Pgr')
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('edited', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.edited, a.output)
