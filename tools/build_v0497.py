#!/usr/bin/env python3
"""0.4.96 -> 0.4.97: 어부지리 벽 넘어 다니는 문제 수정 (4번, 사용자 보고 2026-10-24 "막혀 있는 구간에 벽을 올라 타 갈 수 있음").

원인(데이터로 확인): 사용자 편집본의 새 경로 칠하기 층 CellAttribute_Pgr(이동 가능 칠하기)이 큰 둥근 붓으로 지도 거의 전체
(208×120 칸 중 약 14,000칸)에 칠해져 벽·장식물 발자국의 막힘을 덮었다. 또 옛 paintedpathinglayer의 '막힘' 칠(값 0,
1/4칸 253개, 벽을 따라 그은 가는 선)이 새 형식으로 바뀌며 사라졌다(새 이동 불가 층 Pnp에는 1칸뿐).
수정: Pgr을 모두 비우고, 옛 막힘 칠이 있던 칸을 Pnp(이동 불가)에 다시 칠한다(칸 단위라 조금 넓게 막힐 수 있음).
건설 불가 층 Pnb와 배치·지형은 그대로. 새 자원 자리에 건물이 안 지어지면 그 자리만 작은 붓으로 칠해야 한다.

Usage: python3 tools/build_v0497.py <0.4.96 zip> <original 0.4.95-era paintedpathinglayer source zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.96', b'version=0.4.97'
M = 'TTychus01.SC2Map/'
W, H = 208, 120


def build(source, old_zip, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(old_zip) as oz:
        painted = oz.read(M + 'paintedpathinglayer')[16:]
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        pgr, pnp = files[M + 'cellattribute_pgr'], bytearray(files[M + 'cellattribute_pnp'])
        assert len(pgr) == len(pnp) == 4 + W * H
        files[M + 'cellattribute_pgr'] = pgr[:4] + bytes(W * H)
        n = 0
        for i, v in enumerate(painted):
            x, y = (i % 512) // 4, (i // 512) // 4
            if v == 0 and x < W and y < H and pnp[4 + y * W + x] != 255:
                pnp[4 + y * W + x] = 255; n += 1
        files[M + 'cellattribute_pnp'] = bytes(pnp)
        print('blocked cells restored:', n)
        changed = {'metadata.txt', M + 'cellattribute_pgr', M + 'cellattribute_pnp'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
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
    p.add_argument('source', type=Path); p.add_argument('old_zip', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.old_zip, a.output)
