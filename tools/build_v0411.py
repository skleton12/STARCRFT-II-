#!/usr/bin/env python3
"""Build CCM 0.4.11 from 0.4.10: 4번 불곰 연구 버튼이 여전히 안 보임 (사용자 보고 2026-10-18).

원인 후보 두 가지를 함께 없앤다:
  1. 자날 기술실 카드의 원래 버튼(0줄 1~3칸: 자극제·충격탄·사신 연구)이 같은 칸을 먼저 차지한다
     → 불곰 연구를 비어 있는 1줄 2~4칸으로 옮긴다 (충격탄·억제탄 2칸, 자기가속 3칸, 파편탄 4칸).
  2. 해금 확인이 생산 명령만 보면 스완이 데려온 망치 경호대만 있을 때 막힐 수 있다
     → 생산 명령이 열렸거나 망치 경호대를 한 기라도 가진 적이 있으면 연다.

Usage: python3 tools/build_v0411.py <0.4.10 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.10', b'version=0.4.11'
M4 = 'TTychus01.SC2Map/'
SLOTS = {b'Research6': b'2', b'Research7': b'2', b'Research8': b'3', b'Research9': b'4'}
GATE = b'TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",3))'


def units(d):
    n = 0
    for idx, col in SLOTS.items():
        pat = re.compile(rb'(AbilCmd="RM3_TechResearch,' + idx + rb'" )Row="0" Column="\d"')
        d, k = pat.subn(rb'\1Row="1" Column="' + col + rb'"', d); n += k
    assert n == 4, n
    return d


def script2(d):
    # Research buttons: open when the train command is allowed or Raynor has owned a Hammer Security.
    lines = d.split(b'\n')
    out, n = [], 0
    for line in lines:
        if b'AbilityCommand("RM3_TechResearch",' in line and GATE in line:
            line = line.replace(GATE, b'(' + GATE + b' || TechTreeUnitCount(1,"HammerSecurity",c_techCountCompleteOnly)>0)'); n += 1
        out.append(line)
    assert n == 4, n
    return b'\n'.join(out)


FIX = {M4 + 'base.sc2data/gamedata/unitdata.xml': units, M4 + 'mapscript.galaxy': script2,
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
