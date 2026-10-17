#!/usr/bin/env python3
"""Build CCM 0.3.34 from 0.3.33: 원시 감시자·원시 일벌레·원시 군락의 종족 복구 (3번 미션).

사용자 스크린샷 (2026-10-17): 짓는 중인 원시 감시자가 땅에 보이지 않는다 (선택은 되고 '건설 중' 표시).
확인한 것:
  - 감시자 액터·고치 모델(DehakaBarracksBuild → PrimalZergBuildingBuild)·진행 액터·모델 경로는 협동전 원본과 같다.
  - 다른 점: 협동전 원본은 종족 PZrg(원시 저그)인데, 0.3.4 이식 때 DehakaBarracks·DehakaDrone·DehakaHatchery의
    종족 줄이 통째로 빠졌다. 종족이 없으면 기본값 Neut(중립)가 된다. 0.3.22 이후 이식한 원시 벌레·병력은
    이식 도구 규칙(PZrg → Zerg)대로 Zerg다.
  - 세 유닛에 Zerg를 넣는다 (이식 도구 규칙과 같다). 중립 종족 건물의 건설 표시가 원인인지는 게임에서 확인해야 한다.
배포 전 검사에 '원본에 있는 종족이 빠진 이식 유닛' 검사를 추가했다.

Usage: python3 tools/build_v0334.py <0.3.33 zip> <new output zip>
"""
import argparse
import copy
import re
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.33', b'version=0.3.34'
UNITS = 'TRaynor03.SC2Map/base.sc2data/gamedata/unitdata.xml'
FIX = ('DehakaBarracks', 'DehakaDrone', 'DehakaHatchery')


def units(data):
    nl = b'\r\n' if b'\r\n' in data else b'\n'
    for uid in FIX:
        opens = re.findall(rb'<CUnit id="' + uid.encode() + rb'">', data)
        assert len(opens) == 1, uid
        block = re.search(rb'<CUnit id="' + uid.encode() + rb'">.*?</CUnit>', data, re.S).group(0)
        assert b'<Race ' not in block, uid
        data = data.replace(opens[0], opens[0] + nl + b'        <Race value="Zerg" />', 1)
    return data


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files[UNITS] = units(files[UNITS])
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {UNITS, 'metadata.txt'}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
