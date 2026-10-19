#!/usr/bin/env python3
"""Build CCM 0.4.38 from 0.4.37: 파편탄 버튼이 기술실에 안 보이던 것 (4번).

원인: 0.4.35에서 파편탄을 0행 3열로 옮겼는데, 원작 기술실 카드의 같은 칸에 MercCompoundResearch(죽음의 머리 속도 연구)가
먼저 있다. 같은 칸은 먼저 적힌 버튼이 보이므로 파편탄이 가려졌다. 빈 칸인 1행 2열로 옮긴다 (1행 0·1열은 전투 방패·레이저 조준).

Usage: python3 tools/build_v0438.py <0.4.37 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.37', b'version=0.4.38'
UNITS = 'TTychus01.SC2Map/base.sc2data/gamedata/unitdata.xml'
A = b'<LayoutButtons Face="RM4_Shrapnel" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research9" Row="0" Column="3" />'
B = b'<LayoutButtons Face="RM4_Shrapnel" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research9" Row="1" Column="2" />'


def units(d):
    assert d.count(A) == 1
    return d.replace(A, B)


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), UNITS: units}


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
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
