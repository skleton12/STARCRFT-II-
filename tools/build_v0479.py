#!/usr/bin/env python3
"""0.4.78 -> 0.4.79: 정화자(협동전 동맹) 유닛에 넣은 연구 패시브 아이콘 제거 (4번, 사용자 2026-10-24).

사용자: "협동전 유닛은 아이콘 필요없을듯, 알아서 나오긴함". 0.4.73이 정화자 사도(사이오닉 투영)·폭풍함(분해)·파수병(돌진)에 넣은
명령 카드 패시브 버튼 LayoutButtons RMP_* 만 뺀다. 레이너 병력(전쟁광·코랄·망치·이지스·의무관·악마의 개) 아이콘은 그대로.
버튼·요구조건·문자열 정의는 남겨 둔다(참조만 끊김).

Usage: python3 tools/build_v0479.py <0.4.78 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.78', b'version=0.4.79'
UNITS = 'TTychus01.SC2Map/base.sc2data/gamedata/unitdata.xml'
DROP = ['AdeptFenixShadeSpawn', 'TempestDisintegration', 'Charge']


def units(d):
    t = d.decode('utf-8')
    for up in DROP:
        t, n = re.subn(rf'<LayoutButtons Face="RMP_{up}" [^>]*/>', '', t)
        assert n == 1, up
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), UNITS: units}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
