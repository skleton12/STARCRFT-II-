#!/usr/bin/env python3
"""0.4.100 -> 0.4.101: 사용자 편집 맵 폐기 — 0.4.99(블리자드 원본 어부지리 + 모드의 원래 자원 변경)로 되돌림 (사용자 2026-10-24).

사용자: "내가 수정한 맵 폐기하라는 거였는데". 0.4.100의 서쪽 지형·자원 지대를 빼고, 0.4.99 내용에 버전만 0.4.101로 올린다.
어부지리 자원은 모드 공통 규칙(레이너 본진 풍부한 자원·매장량)만 적용된 상태.

Usage: python3 tools/build_v04101.py <0.4.99 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path


def build(base, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(base) as b:
        assert b'version=0.4.99' in b.read('metadata.txt')
        with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
            for info in b.infolist():
                d = b.read(info.filename)
                if info.filename == 'metadata.txt': d = d.replace(b'version=0.4.99', b'version=0.4.101')
                out.writestr(copy.copy(info), d)
    with zipfile.ZipFile(output) as out: assert out.testzip() is None
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('base', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.base, a.output)
