#!/usr/bin/env python3
"""Build CCM 0.3.19 from 0.3.18: SCV 건설 메뉴의 용병 고용소 버튼 중복 제거 (3번 미션).

사용자 보고 (2026-10-17): "용병 건설소 2개인 거 하나 지워".
원인: 자날 스토리 데이터(LibertyStory)가 이미 고급 건설 메뉴(TBl2) 0행 1열에 고용소 버튼을 두는데,
0.3.1 build_mission03이 기본 건설 메뉴(TBl1) 1행 2열에 같은 버튼을 하나 더 붙였다.
→ 0.3.1에서 붙인 기본 메뉴 쪽 버튼만 지운다. 원본 고급 메뉴 버튼·건설 요구 조건(병영)은 그대로.

Usage: python3 tools/build_v0319.py <0.3.18 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.18', b'version=0.3.19'
M3 = 'TRaynor03.SC2Map/'
LINE = '            <LayoutButtons Face="MercCompound" Type="AbilCmd" AbilCmd="TerranBuild,Build13" Row="1" Column="2" />\n'


def units(data):
    text = data.decode('utf-8')
    assert text.count(LINE) == 1
    return text.replace(LINE, '', 1).encode('utf-8')


FIX = {M3 + 'base.sc2data/gamedata/unitdata.xml': units, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX: data = FIX[info.filename](data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path)
    a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
