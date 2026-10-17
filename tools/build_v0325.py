#!/usr/bin/env python3
"""Build CCM 0.3.25 from 0.3.24: 원시저그 보급 (3번 미션).

사용자 보고 (2026-10-17): "원시 감시자 소환 불가, 보급 부족".
원인: 원시 감시자(DehakaBarracks)는 협동전 데이터대로 보급 2를 쓰는데(일벌레 1), 0.3.24에서는 원시저그(11번)에게
보급을 주는 건물이 없다 (군락을 짓지 않음). 그래서 보급 0인 상태로 건설이 막힌다.
수정: 일꾼이 도착할 때 원시저그의 보급을 200으로 준다 (보급 생산·상한 200). 동맹 병력 상한 100은 스크립트가 그대로 지킨다.
감시자 4기(8)·일벌레 4(4)·병력 100을 합쳐도 모자라지 않는 값이다. 정화자는 수정탑이 보급을 주므로 그대로 둔다.

Usage: python3 tools/build_v0325.py <0.3.24 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.24', b'version=0.3.25'
SCRIPT = 'TRaynor03.SC2Map/mapscript.galaxy'
ANCHOR = '    PlayerModifyPropertyInt(11,c_playerPropVespene,c_playerPropOperSetTo,0);\n'
ADD = ('    // Primal Zerg have no supply building here; Primal Wardens use 2 supply each (co-op data). Grant 200.\n'
       '    PlayerModifyPropertyInt(11,c_playerPropSuppliesMade,c_playerPropOperSetTo,200);\n'
       '    PlayerModifyPropertyInt(11,c_playerPropSuppliesLimit,c_playerPropOperSetTo,200);\n')


def script(data):
    text = data.decode('utf-8')
    assert text.count(ANCHOR) == 1 and 'c_playerPropSuppliesMade' not in text
    return text.replace(ANCHOR, ANCHOR + ADD, 1).encode('utf-8')


FIX = {SCRIPT: script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
