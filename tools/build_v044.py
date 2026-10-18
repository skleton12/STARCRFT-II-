#!/usr/bin/env python3
"""Build CCM 0.4.4 from 0.4.3: 4번 레이너 본진 자원 규칙 적용 (빠뜨린 것).

2·3번 규칙 (사용자 지시 2026-10-16): 레이너 본진 광물·가스를 풍부한 자원으로, 매장량 +20% (정수 미만 버림).
4번 본진 (x 60~100, y 32 이하): 광물 8덩이, 가스 1곳. 매장량이 비어 있으면 Liberty 기본값(광물 1500·가스 2500) 기준.

Usage: python3 tools/build_v044.py <0.4.3 zip> <new output zip>
"""
import argparse, copy, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.4.3', b'version=0.4.4'
OBJ = 'TTychus01.SC2Map/objects'


def objects(data):
    root = E.fromstring(data)
    n = 0
    for el in root:
        t = el.get('UnitType')
        if el.tag != 'ObjectUnit' or t not in ('MineralField', 'VespeneGeyser'): continue
        x, y, _ = map(float, el.get('Position').split(','))
        if not (60 <= x <= 100 and y <= 32): continue
        el.set('UnitType', 'Rich' + t)
        el.set('Resources', str(int(el.get('Resources', '1500' if t == 'MineralField' else '2500')) * 6 // 5))
        n += 1
    assert n == 9, n
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        fix = {OBJ: objects, 'metadata.txt': lambda d: d.replace(OLD, NEW)}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), fix[info.filename](d) if info.filename in fix else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in fix: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
