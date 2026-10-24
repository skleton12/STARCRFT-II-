#!/usr/bin/env python3
"""0.4.101 -> 0.4.102: 어부지리 레이너 본진 광물 매장량 +5% (4번, 사용자 2026-10-24 "광물 매장량 5% 좀 늘려서 새 버전").

레이너 본진의 풍부한 광물(RichMineralField) 8덩이의 매장량 값(Resources)을 1.05배(정수 미만 버림).
다른 광물·가스·지형은 그대로. 사용자는 설치 덮어쓰기 문제를 의심해 새 버전으로 확인하려 한다.

Usage: python3 tools/build_v04102.py <0.4.101 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.101', b'version=0.4.102'
OBJ = 'TTychus01.SC2Map/objects'


def bump(m):
    return f'{m.group(1)}"{int(int(m.group(2)) * 1.05)}"'


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[OBJ].decode('utf-8')
        n = 0
        def unit(m):
            nonlocal n
            n += 1
            return re.sub(r'(Resources=)"(\d+)"', bump, m.group(0))
        t = re.sub(r'<ObjectUnit [^>]*UnitType="RichMineralField"[^>]*?(?:/>|>.*?</ObjectUnit>)', unit, t, flags=re.S)
        assert n == 8, n
        files[OBJ] = t.encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {OBJ, 'metadata.txt'}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for nm in prev.namelist():
                    if nm not in changed: assert out.read(nm) == prev.read(nm), nm
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
