#!/usr/bin/env python3
"""0.15.3 -> 0.15.4: 멩스크 전차 한국어 이름 '충격 사단' -> '충격 전차' (사용자 2026-11-28 "충격 전차다").
10개 맵 kokr 문자열만 바꾼다(영어 부분은 그대로라 다른 11개 언어 파일은 변하지 않음). Usage: build_v0154.py <0.15.3 zip> <out>"""
import copy, sys, zipfile
from pathlib import Path
OLD, NEW = b'version=0.15.3', b'version=0.15.4'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04', 'TTychus03', 'TTychus02']


def build(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        for m in MAPS:
            k = f'{m}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'
            t = z.read(k).decode('utf-8'); n = t.count('충격 사단'); assert n >= 3, (m, n)
            rep[k] = t.replace('충격 사단', '충격 전차').encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__': build(*sys.argv[1:])
