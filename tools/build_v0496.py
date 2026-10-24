#!/usr/bin/env python3
"""0.4.95 -> 0.4.96: 사용자가 편집기로 고친 어부지리 지형·배치 적용 (4번, 사용자 2026-10-24 "자원지대 추가").

원본 편집본: maps/edits/TTychus01_resources_2026-10-24.SC2Map (사용자 업로드, 단일 MPQ).
가져오는 것: Objects(배치), 지형 t3*·t3Terrain.xml/.version, 새 경로 칠하기 CellAttribute_Pgr/Pnb/Pnp
(편집기가 옛 paintedpathinglayer를 이 형식으로 바꿨으므로 paintedpathinglayer는 뺀다).
가져오지 않는 것: mapscript.galaxy(편집본과 같음, 확인), DocumentHeader·MapInfo(이름·언어·버전 표기만 다름, 의존성 같음).
편집 내용: 서쪽 장식물 26개 삭제, 덤불 2개 추가, 자원 지대 2곳 — A(26,16~24 광물 9·풍부한 가스 (27.5,25.5), 탈다림 4번 전초 옆),
B(13~18,33~45 광물 12·풍부한 가스 (20.5,45.5)). 광물 4800·가스 4125는 편집본 값 그대로.

Usage: python3 tools/build_v0496.py <0.4.95 zip> <edited .SC2Map> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.95', b'version=0.4.96'
M = 'TTychus01.SC2Map/'
TAKE = ['Objects', 'Objects.version', 't3CellFlags', 't3HeightMap', 't3SyncCliffLevel', 't3SyncHeightMap',
        't3SyncTextureInfo', 't3Terrain.version', 't3Terrain.xml', 't3VertCol', 't3Water']
NEWF = ['CellAttribute_Pgr', 'CellAttribute_Pnb', 'CellAttribute_Pnp']
DROP = ['paintedpathinglayer']


def build(source, edited, output):
    sys.path.insert(0, str(Path(__file__).parent))
    import mpyq
    if output.exists(): raise ValueError('Output must be new')
    ed = mpyq.MPQArchive(str(edited))
    edfiles = {n.decode(): ed.read_file(n.decode()) or b'' for n in ed.files}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        assert edfiles['MapScript.galaxy'] == files[M + 'mapscript.galaxy'], 'edited map changed the script'
        lower = {n.lower(): n for n in files}
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
        objs = edfiles['Objects'].decode('utf-8')
        assert len(re.findall(r'UnitType="MineralField"', objs)) >= 21
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
