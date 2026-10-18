#!/usr/bin/env python3
"""Build CCM 0.4.6 from 0.4.5: 이 모드에서는 업적을 끈다 (사용자 확정 2026-10-18).

네 맵 InitMap에서 InitLibs() 바로 뒤에 AchievementsDisable(1)을 부른다 (공식 네이티브, 플레이어 1 업적 비활성).
원본 AchievementAward 호출은 그대로 두지만 꺼진 상태라 지급되지 않는다.

Usage: python3 tools/build_v046.py <0.4.5 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.5', b'version=0.4.6'
MAPS = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']


def script(d):
    nl = b'\r\n' if b'\r\n' in d else b'\n'
    a = b'void InitMap () {' + nl + b'    InitLibs();' + nl
    assert d.count(a) == 1 and b'AchievementsDisable' not in d
    return d.replace(a, a + b'    AchievementsDisable(1);' + nl)


FIX = {f'{m}.SC2Map/mapscript.galaxy': script for m in MAPS}
FIX['metadata.txt'] = lambda d: d.replace(OLD, NEW)


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
