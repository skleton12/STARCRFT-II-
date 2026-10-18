#!/usr/bin/env python3
"""Build CCM 0.4.12 from 0.4.11: 전쟁광 자극제 버튼 두 개 (사용자 보고 2026-10-18).

자날 전쟁광 카드에 원래 자극제(2줄 0칸)가 있고, 모드 자극제 줄(1·2·3단계)을 2줄 1칸에 따로 붙여 같은 자극제가 두 번 보였다.
모드 버튼 세 개를 원래 자극제와 같은 2줄 0칸으로 옮긴다. 한 칸에서 그 단계에 맞는 버튼 하나만 보인다. (3·4번 맵)

Usage: python3 tools/build_v0412.py <0.4.11 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.4.11', b'version=0.4.12'
FACES = {'Stim', 'MarineSuperStimpack', 'RMK_MarineMengskAttackSpeedBoost'}


def units(d):
    root = E.fromstring(d)
    n = 0
    for u in root:
        if u.tag == 'CUnit' and u.get('id') == 'WarPig':
            for b in u.iter('LayoutButtons'):
                if b.get('Face') in FACES and b.get('Row') == '2' and b.get('Column') == '1':
                    b.set('Column', '0'); n += 1
    assert n == 3, n
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


FIX = {f'{m}.SC2Map/base.sc2data/gamedata/unitdata.xml': units for m in ('TRaynor03', 'TTychus01')}
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
