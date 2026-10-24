#!/usr/bin/env python3
"""0.4.102 -> 0.4.103: 어부지리 맵을 0.4.95 맵으로 되돌림 (사용자 지시 2026-10-24 "0.4.95 맵으로 바꿔").

0.4.102와 0.4.95의 맵 파일 차이는 TTychus01 objects(풍부한 광물 +5%)뿐이다. 그 파일을 0.4.95 것으로 바꾼다.
지형·경로·스크립트·데이터는 이미 0.4.95와 같다 (빌드 때 확인).

Usage: python3 tools/build_v04103.py <0.4.102 zip> <0.4.95 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.102', b'version=0.4.103'
OBJ = 'TTychus01.SC2Map/objects'


def build(source, ref, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(ref) as r95:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert b'version=0.4.95' in r95.read('metadata.txt').splitlines()
        assert set(prev.namelist()) == set(r95.namelist())
        for n in prev.namelist():
            if n not in ('metadata.txt', OBJ): assert prev.read(n) == r95.read(n), n
        files = {n: prev.read(n) for n in prev.namelist()}
        files[OBJ] = r95.read(OBJ)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == r95.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('ref', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.ref, a.output)
