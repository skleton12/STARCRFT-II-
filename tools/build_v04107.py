#!/usr/bin/env python3
"""0.4.106 -> 0.4.107: 어부지리 맵을 블리자드 원본으로 (사용자 2026-10-25 "맵을 원본 블리자드맵 써, 맵 수정 없음").

ZIP 안 TTychus01.SC2Map/ 폴더를 통째로 지우고 0.4.103의 폴더로 다시 만든다. 0.4.103 맵 = 블리자드 원본
(maps/original_wol/ttychus01, 드라이브 추출본과 바이트 동일)에서 모드 공통 규칙만 바꾼 것:
레이너 본진 풍부한 광물·가스(매장량 +20%·+65%), 시작 병력 용병(해병→전쟁광, 의무관→용병 의무관),
그리고 데이터·스크립트(연구·동맹 등). 지형·경로·장식물은 원본 그대로이고 경로 칠하기(CellAttribute) 파일은 없다.
스크립트·데이터는 0.4.106과 같다 (빌드 때 확인).

Usage: python3 tools/build_v04107.py <0.4.106 zip> <0.4.103 zip> <new output zip>
"""
import argparse, copy, os, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.106', b'version=0.4.107'
M = 'TTychus01.SC2Map/'
ORIG = Path(__file__).resolve().parent.parent / 'maps/original_wol/ttychus01'
TERRAIN = ['t3cellflags', 't3heightmap', 't3syncclifflevel', 't3syncheightmap', 't3synctextureinfo', 't3terrain.xml',
           't3vertcol', 't3water', 't3texturemasks', 'paintedpathinglayer', 'regions', 'triggers']


def build(source, ref, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(ref) as r:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert b'version=0.4.103' in r.read('metadata.txt').splitlines()
        mapfiles = {n: r.read(n) for n in r.namelist() if n.startswith(M)}
        for f in TERRAIN:
            assert mapfiles[M + f] == (ORIG / f).read_bytes(), f
        assert not any('cellattribute' in n for n in mapfiles)
        assert mapfiles[M + 'mapscript.galaxy'] == prev.read(M + 'mapscript.galaxy')
        assert mapfiles[M + 'base.sc2data/gamedata/unitdata.xml'] == prev.read(M + 'base.sc2data/gamedata/unitdata.xml')
        meta = prev.read('metadata.txt').replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    if info.filename.startswith(M): continue
                    out.writestr(copy.copy(info), meta if info.filename == 'metadata.txt' else prev.read(info.filename))
                for info in r.infolist():
                    if info.filename.startswith(M): out.writestr(copy.copy(info), mapfiles[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                assert {n for n in out.namelist() if n.startswith(M)} == set(mapfiles)
                for n, v in mapfiles.items(): assert out.read(n) == v, n
                for n in prev.namelist():
                    if not n.startswith(M) and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(mapfiles), 'map files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('ref', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.ref, a.output)
