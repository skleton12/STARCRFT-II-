#!/usr/bin/env python3
"""0.4.97 -> 0.4.98: 0.4.97에서 비운 이동 가능 층(CellAttribute_Pgr)을 되돌린다 (4번, 사용자 보고 2026-10-24 "다 막히게 해놓으면 어떡함").

0.4.97 판단 오류: Pgr은 붓 칠이 아니라 편집기가 저장한 지도의 기본 이동 가능 땅이었다(초록 모양이 호수·구멍까지 지형과 같음).
비우자 지도 전체가 막혔다. Pgr을 사용자 편집본 값으로 되돌리고, 0.4.97에서 복구한 막힘 칠(Pnp 68칸)은 유지한다.

Usage: python3 tools/build_v0498.py <0.4.97 zip> <edited .SC2Map> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path
import mpyq

OLD, NEW = b'version=0.4.97', b'version=0.4.98'
KEY = 'TTychus01.SC2Map/cellattribute_pgr'


def build(source, edited, output):
    if output.exists(): raise ValueError('Output must be new')
    pgr = mpyq.MPQArchive(str(edited)).read_file('CellAttribute_Pgr')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        assert len(pgr) == len(files[KEY]) and not any(files[KEY][4:])
        files[KEY] = pgr
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt', KEY}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('edited', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.edited, a.output)
