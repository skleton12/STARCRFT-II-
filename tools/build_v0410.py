#!/usr/bin/env python3
"""Build CCM 0.4.10 from 0.4.9: 4번 정제소 두 개 문제 (사용자 보고 2026-10-18 "가스실 2개, 덮어 씌워야").

0.4.7은 원본의 미리 지은 정제소를 지우고 그 자리에 풍부한 가스를 둔 뒤, 스크립트로 정제소를 다시 세웠다.
스크립트 생성 정제소가 가스 위에 붙지 않고 옆에 따로 생긴 것으로 본다 → 스크립트 생성을 지운다.
그 자리에는 풍부한 가스(4125)만 남는다. 레이너가 SCV로 정제소를 지어 덮는다.

Usage: python3 tools/build_v0410.py <0.4.9 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.9', b'version=0.4.10'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'


def script(d):
    pat = re.compile(rb'\r?\n    // Raynor\'s starting Refinery stands on the rich geyser[^\n]*\r?\n    UnitCreate\(1,"Refinery",0,1,Point\(81\.5,13\.5\),270\.0\);')
    d, n = pat.subn(b'', d)
    assert n == 1
    return d


FIX = {SCRIPT: script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
