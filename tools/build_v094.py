#!/usr/bin/env python3
"""0.9.3 -> 0.9.4: 테란 적 추가 SCV 4기 제거 (사용자 2026-11-24 "그건 빼 어쩐지 빠르더라" — 올란 광물이 빨리 참).

어려움 이상 적 추가 생산기지(0.6.50, 8·9번은 0.8.1/0.9.1에서 같은 코드)가 테란 적 본진에 SCV 4기를 더 만들던 줄을 지운다
(2·8·9번). 추가 병영·군수 공장과 AI 수리는 그대로. Game not run.

Usage: python3 tools/build_v094.py <0.9.3 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.9.3', b'version=0.9.4'
MAPS = ['TRaynor02', 'THorner01', 'THorner02']
LINE = b'UnitCreate(4, "SCV", 0, p, UnitTypePlacementFromPoint("SCV", p, c, 8.0), 270.0);'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            k = f'{m}.SC2Map/mapscript.galaxy'; t = files[k]
            assert t.count(LINE) == 1, m
            files[k] = t.replace(LINE, b'// 0.9.4: no extra SCVs (user 2026-11-24, enemy mined too fast).'); changed.add(k)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
