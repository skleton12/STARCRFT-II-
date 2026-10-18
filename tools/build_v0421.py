#!/usr/bin/env python3
"""Build CCM 0.4.21 from 0.4.20: 3번 맵에서 기술실 자극제 연구 줄을 뺀다 (사용자 지시 2026-10-18 "3번 맵 스팀팩 없으니 지웁세").

3번 맵만: 병영 기술실의 전투 자극제·초 전투 자극제·멩스크 자극제 연구 버튼과 전쟁광의 모드 자극제 버튼을 지운다.
자날 원래 자극제 버튼은 능력 조건(RM3_Stim1Use)을 채울 수 없어 계속 숨는다 → 3번 맵에는 자극제가 없다.
전투 방패·레이저 조준·4번 이후 자극제 줄은 그대로.

Usage: python3 tools/build_v0421.py <0.4.20 zip> <new output zip>
"""
import argparse, copy, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.4.20', b'version=0.4.21'
UD = 'TRaynor03.SC2Map/base.sc2data/gamedata/unitdata.xml'
LAB = {'RM3_Stim1', 'RM3_Stim2', 'RM3_Stim3'}
REQ = {'RM3_Stim1Use', 'RM3_Stim2Use', 'RM3_Stim3Use'}


def units(d):
    root = E.fromstring(d)
    n = 0
    for u in root:
        if u.tag != 'CUnit' or u.get('id') not in ('BarracksTechLab', 'WarPig'): continue
        for card in u.findall('CardLayouts'):
            for b in list(card):
                if b.tag == 'LayoutButtons' and (b.get('Face') in LAB or (u.get('id') == 'WarPig' and b.get('Requirements') in REQ)):
                    card.remove(b); n += 1
    assert n == 6, n
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


FIX = {UD: units, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
