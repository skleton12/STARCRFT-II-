#!/usr/bin/env python3
"""0.14.2 -> 0.14.3: 질 행성(TTychus03) 시작 의무수송선 해병 -> 전쟁광 (사용자 2026-11-28 "질행성 미션 오류 발견 유닛들이 용병이 아님").

원본 시작 연출(gt_CreateMedivacIntro)이 뫼비우스 경비대(6번) 의무수송선 2대에 일반 해병(Marine) 2기씩을 실어 보낸다.
6번의 다른 배치 병력은 원본부터 전쟁광·망치 경호대·스파르타 중대라 이 4기만 일반 해병이었다 -> 전쟁광(WarPig).
Game not run. Usage: python3 tools/build_v0143.py <0.14.2 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.14.2', b'version=0.14.3'
K = 'TTychus03.SC2Map/mapscript.galaxy'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        t = files[K].decode('utf-8-sig')
        for m in ('gv_medivac01', 'gv_medivac02'):
            a = f'UnitCargoCreate({m}, "Marine", 2);'
            assert t.count(a) == 1, m
            t = t.replace(a, f'UnitCargoCreate({m}, "WarPig", 2);')
        files[K] = t.encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in ('metadata.txt', K): assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
