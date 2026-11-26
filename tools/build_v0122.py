#!/usr/bin/env python3
"""0.12.1 -> 0.12.2: 아스테리아 망령 크기 1.3 -> 1.0 (사용자 2026-11-26 "망령크기가좀"). 발할라·코랄 HHWraith 모델 첫 정의만.
Game not run.  Usage: python3 tools/build_v0122.py <0.12.1 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.12.1', b'version=0.12.2'
FILES = [f'{m}.SC2Map/base.sc2data/gamedata/modeldata.xml' for m in ('THorner03', 'THorner04')]


def fix(t):
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    a = t.index('<CModel id="HHWraith" parent="Unit">'); b = t.index('</CModel>', a)
    body = t[a:b]
    for k in ('ScaleMax', 'ScaleMin'):
        s = f'<{k} value="1.300000,1.300000,1.300000" />'
        assert body.count(s) == 1, k
        body = body.replace(s, f'<{k} value="1.000000,1.000000,1.000000" />')
    t = t[:a] + body + t[b:]
    return t.replace('\n', '\r\n') if crlf else t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    elif info.filename in FILES: d = fix(d.decode('utf-8')).encode('utf-8')
                    o.writestr(copy.copy(info), d, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as o:
                assert o.testzip() is None
                for n in prev.namelist():
                    if n != 'metadata.txt' and n not in FILES: assert o.read(n) == prev.read(n), n
        except BaseException:
            out.unlink(missing_ok=True); raise


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
