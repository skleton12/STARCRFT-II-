#!/usr/bin/env python3
"""0.4.103 -> 0.4.104: 사용자 두 번째 어부지리 편집본 적용 (사용자 2026-10-24 "이걸로 적용해").

원본 편집본: maps/edits/TTychus01_west_2026-10-24.SC2Map (사용자 업로드, 단일 MPQ).
편집 내용(확인): 서쪽 포켓(x 0~35, y 19~68) 지형을 낮춤, 그 위 장식물 35개 높이만 따라 바뀜, 걸을 수 있음 칠하기(Pgr 497칸)·
이동 불가 칠하기(Pnp, 서쪽 맵 가장자리)·건설 불가(Pnb). 자원·유닛·스크립트·데이터는 0.4.103과 같다.
가져오는 것: Objects, 지형 t3*·t3Terrain.xml/.version, CellAttribute_Pgr/Pnb/Pnp (paintedpathinglayer는 편집기가 이 형식으로 바꿔 뺀다).
가져오지 않는 것: mapscript·데이터(같음, 확인), DocumentHeader·MapInfo(의존성 같음).

벽 넘기 방지: Pgr(걸을 수 있음 덧칠)은 절벽 판정을 무시하게 하므로, 절벽 가장자리 칸(둘레 8칸 중 절벽 높이가 다른 칸이 있는 칸)의
Pgr만 지운다 (사용자 2026-10-24 "벽쪽만 막히게"). 평지에 칠한 Pgr은 그대로 둔다.

Usage: python3 tools/build_v04104.py <0.4.103 zip> <edited .SC2Map> <new output zip>
"""
import argparse, copy, struct, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.103', b'version=0.4.104'
M = 'TTychus01.SC2Map/'
TAKE = ['Objects', 'Objects.version', 't3CellFlags', 't3HeightMap', 't3SyncCliffLevel', 't3SyncHeightMap',
        't3SyncTextureInfo', 't3Terrain.version', 't3Terrain.xml', 't3VertCol', 't3Water']
NEWF = ['CellAttribute_Pgr', 'CellAttribute_Pnb', 'CellAttribute_Pnp']
DROP = ['paintedpathinglayer']
W, H = 208, 120


def strip_cliff_edges(pgr, cliff):
    lv = struct.unpack_from('<%dH' % (W * H), cliff, len(cliff) - W * H * 2)
    body = bytearray(pgr[4:])
    assert len(body) == W * H
    cut = 0
    for y in range(H):
        for x in range(W):
            i = y * W + x
            if not body[i]: continue
            if any(lv[(y + dy) * W + x + dx] != lv[i] for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                   if 0 <= x + dx < W and 0 <= y + dy < H):
                body[i] = 0; cut += 1
    return pgr[:4] + bytes(body), cut


def build(source, edited, output):
    import mpyq
    if output.exists(): raise ValueError('Output must be new')
    ed = mpyq.MPQArchive(str(edited))
    edfiles = {n.decode(): ed.read_file(n.decode()) or b'' for n in ed.files}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        lower = {n.lower(): n for n in files}
        for f in ('MapScript.galaxy', 'Base.SC2Data/GameData/UnitData.xml', 'koKR.SC2Data/LocalizedData/GameStrings.txt'):
            assert edfiles[f.replace('/', '\\')] == files[lower[(M + f).lower()]], f'edited map changed {f}'
        changed = {'metadata.txt'}
        for f in TAKE:
            key = lower[(M + f).lower()]
            files[key] = edfiles[f]; changed.add(key)
        for f in DROP:
            del files[lower[(M + f).lower()]]
        added = {}
        for f in NEWF:
            assert (M + f).lower() not in lower
            added[M + f.lower()] = edfiles[f]
        pgr, cut = strip_cliff_edges(edfiles['CellAttribute_Pgr'], edfiles['t3SyncCliffLevel'])
        added[M + 'cellattribute_pgr'] = pgr
        print('Pgr cliff-edge cells cleared:', cut)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    if info.filename in files: out.writestr(copy.copy(info), files[info.filename])
                for n, d in added.items(): out.writestr(n, d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n in files and n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('edited', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.edited, a.output)
