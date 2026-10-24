#!/usr/bin/env python3
"""0.4.98 -> 0.4.99: 어부지리 편집 취소, 원래 맵으로 (4번, 사용자 2026-10-24 "원래 맵으로 걍 하자, 바뀐 거 취소").

0.4.96~0.4.98은 어부지리 지형·배치·경로 칠하기만 바꿨다(서쪽 자원 지대 2곳, 경로 층). 그 밖의 파일은 0.4.95와 같다(확인).
그래서 0.4.95 ZIP의 내용을 그대로 쓰고 버전만 0.4.99로 올린다. 서쪽 자원 지대는 없어진다.
사용자 편집본(maps/edits/)은 기록으로 남긴다.

Usage: python3 tools/build_v0499.py <0.4.98 zip> <0.4.95 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

MAP_ONLY = {'objects', 'objects.version', 't3cellflags', 't3heightmap', 't3syncclifflevel', 't3syncheightmap', 't3synctextureinfo',
            't3terrain.version', 't3terrain.xml', 't3vertcol', 't3water', 'paintedpathinglayer',
            'cellattribute_pgr', 'cellattribute_pnb', 'cellattribute_pnp'}


def build(cur, base, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(cur) as c, zipfile.ZipFile(base) as b:
        assert b'version=0.4.98' in c.read('metadata.txt') and b'version=0.4.95' in b.read('metadata.txt')
        for n in set(c.namelist()) | set(b.namelist()):
            if n == 'metadata.txt' or n.split('/')[-1] in MAP_ONLY and n.startswith('TTychus01.SC2Map/'): continue
            assert c.read(n) == b.read(n), n
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in b.infolist():
                    d = b.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(b'version=0.4.95', b'version=0.4.99')
                    out.writestr(copy.copy(info), d)
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('cur', type=Path); p.add_argument('base', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.cur, a.base, a.output)
