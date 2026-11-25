#!/usr/bin/env python3
"""0.10.2 -> 0.10.3: 영웅 배치 바꿈 (사용자 2026-11-25 "데하카는 노바미션 피닉스는 토시미션에 나오는걸로 바꿔").
탈옥(TTosh03A, 토시)에는 피닉스만 나온다. 데하카 생성 호출을 빼고 합류 자막을 피닉스만으로 바꾼다.
데하카 데이터는 맵에 남겨 둔다(쓰이지 않음). 데하카는 유령의 기회(TTosh03B, 노바) 맵을 만들 때 넣는다. Game not run.
Usage: python3 tools/build_v0103.py <0.10.2 zip> <new output zip>"""
import copy, sys, tempfile, zipfile
from pathlib import Path
OLD, NEW = b'version=0.10.2', b'version=0.10.3'
SP = 'TTosh03A.SC2Map/mapscript.galaxy'
KO = 'TTosh03A.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'
LOC = ['enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
def main(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        s = z.read(SP); a = b'    gf_rmHero("DehakaCoop", 3.0);'
        nl = b'\r\n' if b'\r\n' in s else b'\n'
        assert s.count(a + nl) == 1; rep[SP] = s.replace(a + nl, b'')
        for p, old, new in [(KO, 'Param/Value/RM10_Heroes=피닉스와 데하카가 합류했습니다. /// Fenix and Dehaka have joined you.',
                             'Param/Value/RM10_Heroes=피닉스가 합류했습니다. /// Fenix has joined you.')] + \
            [(f'TTosh03A.SC2Map/{l}.sc2data/localizeddata/gamestrings.txt', 'Param/Value/RM10_Heroes=Fenix and Dehaka have joined you.',
              'Param/Value/RM10_Heroes=Fenix has joined you.') for l in LOC]:
            t = z.read(p).decode('utf-8-sig'); assert t.count(old) == 1, p
            rep[p] = t.replace(old, new).encode('utf-8-sig' if z.read(p).startswith(b'\xef\xbb\xbf') else 'utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                for i in z.infolist(): o.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)))
            with zipfile.ZipFile(out) as o: assert o.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out, len(rep), 'files changed')
if __name__ == '__main__': main(*sys.argv[1:])
