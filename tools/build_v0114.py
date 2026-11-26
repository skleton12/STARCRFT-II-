#!/usr/bin/env python3
"""0.11.3 -> 0.11.4: 0.9.7부터 3~9번·11번 맵 스크립트 전체가 컴파일되지 않던 원인 수정 (사용자 2026-11-26 "똑같에").

원인: 0.9.7(연구실 고르지 않은 쪽 자동 연구)이 넣은 `bool gv_rmLabDone[16];`는 C식 배열 선언이라 Galaxy 문법이 아니다.
Galaxy가 맵 스크립트 전체를 컴파일하지 못해 원작 트리거까지 하나도 안 돌았다 — 발할라에서 타이커스가 적(동맹 설정 없음)·
창고 인트로 없이 바로 기지, 지원 버튼 없음. 3~9번(TRaynor03·TTychus01·TTosh01·THanson01·TTosh02·THorner01·THorner02)도 같은 상태였다.
`bool[16] gv_rmLabDone;`로 고친다. check_release에 C식 배열 선언 검사를 추가했다. Game not run.
Usage: python3 tools/build_v0114.py <0.11.3 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.11.3', b'version=0.11.4'
BAD, GOOD = b'bool gv_rmLabDone[16];', b'bool[16] gv_rmLabDone;'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    fixed = []
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    elif info.filename.endswith('/mapscript.galaxy') and BAD in d:
                        assert d.count(BAD) == 1; d = d.replace(BAD, GOOD); fixed.append(info.filename.split('/')[0])
                    o.writestr(copy.copy(info), d, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            assert len(fixed) == 8, fixed
        except BaseException:
            out.unlink(missing_ok=True); raise
    print('fixed:', ', '.join(fixed))


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
