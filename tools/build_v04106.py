#!/usr/bin/env python3
"""0.4.105 -> 0.4.106: 어부지리 맵 폴더를 지우고 사용자 편집본으로 다시 만듦 (사용자 2026-10-25 "맵 지우고 다시만들어").

ZIP 안 TTychus01.SC2Map/ 아래 파일을 모두 지우고, 사용자 편집본(maps/edits/TTychus01_west_2026-10-24.SC2Map)의
모든 파일을 바이트 그대로 넣는다 ((listfile)·(attributes) 제외, 이름은 ZIP 관례대로 소문자·'/').
다른 맵은 그대로다.

Usage: python3 tools/build_v04106.py <0.4.105 zip> <edited .SC2Map> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.105', b'version=0.4.106'
M = 'TTychus01.SC2Map/'


def build(source, edited, output):
    import mpyq
    if output.exists(): raise ValueError('Output must be new')
    ed = mpyq.MPQArchive(str(edited))
    mapfiles = {}
    for n in ed.files:
        if n in (b'(listfile)', b'(attributes)'): continue
        key = M + n.decode().replace('\\', '/').lower()
        assert key not in mapfiles, key
        mapfiles[key] = ed.read_file(n) or b''
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        meta = prev.read('metadata.txt').replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    if info.filename.startswith(M): continue
                    out.writestr(copy.copy(info), meta if info.filename == 'metadata.txt' else prev.read(info.filename))
                for k in sorted(mapfiles): out.writestr(k, mapfiles[k])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                got = {n for n in out.namelist() if n.startswith(M)}
                assert got == set(mapfiles), sorted(got ^ set(mapfiles))
                for k, v in mapfiles.items(): assert out.read(k) == v, k
                for n in prev.namelist():
                    if not n.startswith(M) and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(mapfiles), 'map files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('edited', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.edited, a.output)
