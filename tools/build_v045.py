#!/usr/bin/env python3
"""Build CCM 0.4.5 from 0.4.4: 4번 불곰 연구 버튼 안 보임·레일건 버튼 수정.

사용자 보고 (2026-10-18): "불곰에 레일건이 붙어 있고 기술실에 불곰 연구가 안 보임".
  - 캠페인은 불곰·화염방사병을 유닛이 아니라 병영 생산 명령(BarracksTrain 3, 5)으로 연다 (campaignlib).
    해금 확인을 TechTreeUnitIsAllowed(유닛) → TechTreeAbilityIsAllowed(생산 명령)로 바꾼다.
  - 자기가속 탄약 능력 버튼(HaveMarauderMagrailMunitions)은 연구 전에는 숨긴다 (Show 조건 추가).

Usage: python3 tools/build_v045.py <0.4.4 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.4', b'version=0.4.5'
M4 = 'TTychus01.SC2Map/'
MARAUDER, FIREBAT = b'TechTreeUnitIsAllowed(1,"Marauder")', b'TechTreeUnitIsAllowed(1,"Firebat")'


def script(d):
    assert d.count(MARAUDER) == 5 and d.count(FIREBAT) == 1, (d.count(MARAUDER), d.count(FIREBAT))
    d = d.replace(MARAUDER, b'TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",3))')
    return d.replace(FIREBAT, b'TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",5))')


def reqs(d):
    old = b'<NodeArray index="Use" Link="CountUpgradeMarauderMagrailMunitionsCompleteOnly3722671231" />'
    assert d.count(old) == 1
    return d.replace(old, old + b'<NodeArray index="Show" Link="CountUpgradeMarauderMagrailMunitionsCompleteOnly3722671231" />')


FIX = {M4 + 'mapscript.galaxy': script, M4 + 'base.sc2data/gamedata/requirementdata.xml': reqs,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
