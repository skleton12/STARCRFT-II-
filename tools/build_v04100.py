#!/usr/bin/env python3
"""0.4.99 -> 0.4.100: 블리자드 원본 어부지리 + 자원 지대만 (4번, 사용자 2026-10-24 "원래 블리자드 어부지리에 자원 쪽만 수정").

- 지형: 사용자 첫 편집본(maps/edits/TTychus01_resources_2026-10-24.SC2Map)의 t3* — 서쪽 테두리 절벽을 낮춘 자리(19~40, 13~45).
- 경로: 블리자드 원본 paintedpathinglayer 그대로. 새 형식 칠하기(CellAttribute_*)는 넣지 않는다.
  사용자가 붓으로 칠한 '이동 가능' 층이 테두리 절벽 위까지 덮어 유닛이 벽을 타던 원인이었다.
- 배치: 첫 편집본 Objects 기준. 자원 A(26,16~24, 가스 27.5,25.5)는 그대로.
  자원 B는 테두리 절벽(192) 위라 걸어서 못 가므로 같은 모양으로 (+14, −4) 옮겨 낮춘 땅(64) 안에 둔다
  (모든 광물·가스 칸과 주변 1칸이 같은 높이). 옮긴 자리와 겹치는 장식물(반경 1.6)만 지운다.
- 스크립트·데이터·맵 정보는 0.4.99 그대로.

Usage: python3 tools/build_v04100.py <0.4.99 zip> <edited .SC2Map> <new output zip>
"""
import argparse, copy, math, re, zipfile
from pathlib import Path
import mpyq

OLD, NEW = b'version=0.4.99', b'version=0.4.100'
M = 'TTychus01.SC2Map/'
TERRAIN = ['t3CellFlags', 't3HeightMap', 't3SyncCliffLevel', 't3SyncHeightMap', 't3SyncTextureInfo',
           't3Terrain.version', 't3Terrain.xml', 't3VertCol', 't3Water']
DX, DY = 14, -4


def is_b(tag, ut, x, y):
    return tag == 'ObjectUnit' and ('MineralField' in ut or 'VespeneGeyser' in ut) and x < 21 and 30 < y < 47


def move_b(objs):
    blocks = re.findall(r'\s*<Object\w+ [^>]*?(?:/>|>.*?</Object\w+>)', objs, re.S)
    moved, cells, out = 0, [], []
    for b in blocks:
        tag = re.search(r'<(Object\w+)', b).group(1)
        ut = (re.search(r'(?:UnitType|Type)="([^"]+)"', b) or [None, ''])[1]
        pos = re.search(r'Position="([^"]+)"', b)
        x, y, z = map(float, pos.group(1).split(','))
        if is_b(tag, ut, x, y):
            nx, ny = x + DX, y + DY
            b = b.replace(pos.group(0), f'Position="{nx:g},{ny:g},{z:g}"'); moved += 1
            cells.append((nx, ny, 'Vespene' in ut))
        out.append([tag, b, x, y])
    removed = 0
    final = []
    for tag, b, x, y in out:
        if tag == 'ObjectDoodad' and any(math.hypot(x - cx, y - cy) < (2.6 if gas else 1.6) for cx, cy, gas in cells):
            removed += 1; continue
        final.append(b)
    head = objs[:objs.index(blocks[0])]
    tail = objs[objs.rindex(blocks[-1]) + len(blocks[-1]):]
    return head + ''.join(final) + tail, moved, removed


def build(source, edited, output):
    if output.exists(): raise ValueError('Output must be new')
    ed = mpyq.MPQArchive(str(edited))
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        lower = {n.lower(): n for n in files}
        changed = {'metadata.txt'}
        for f in TERRAIN:
            k = lower[(M + f).lower()]; files[k] = ed.read_file(f); changed.add(k)
        objs, moved, removed = move_b(ed.read_file('Objects').decode('utf-8'))
        assert moved == 13, moved
        k = lower[(M + 'objects').lower()]; files[k] = objs.encode('utf-8'); changed.add(k)
        k = lower[(M + 'objects.version').lower()]; files[k] = ed.read_file('Objects.version'); changed.add(k)
        assert not any(n.lower().startswith(M.lower() + 'cellattribute') for n in files) and (M + 'paintedpathinglayer') in files
        print('B moved', moved, 'doodads removed', removed)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
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
