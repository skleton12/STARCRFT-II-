#!/usr/bin/env python3
"""0.5.21 -> 0.5.22: 레드스톤 저그 기지 지원 늦춤 (사용자 2026-10-28 "적 지원군이 빨리 오는 것 같음, 조금 늦춰줘").

첫 지원 임무 4분 → 6분, 간격 120초 → 150초 (시험값). 번갈아 투하·부대 구성·목적지·기지 파괴 시 중지는 그대로.

Usage: python3 tools/build_v0522.py <0.5.21 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.21', b'version=0.5.22'
S = 'TTosh01.SC2Map/mapscript.galaxy'

SCRIPT = [
    ('// Bases = the Zerg (2, 4) town halls at the start. First wave at 4:00, then every 120 s; held back around lava (trial).\n',
     '// Bases = the Zerg (2, 4) town halls at the start. First wave at 6:00, then every 150 s; held back around lava (0.5.22, trial).\n'),
    ('    gv_m5_zNext=MaxF(240.0,GameGetMissionTime());\n', '    gv_m5_zNext=MaxF(360.0,GameGetMissionTime());\n'),
    ('    gv_m5_zNext=GameGetMissionTime()+120.0;\n', '    gv_m5_zNext=GameGetMissionTime()+150.0;\n'),
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[S].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = sub(t.replace('\r\n', '\n'), SCRIPT)
        files[S] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (S, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
