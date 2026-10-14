#!/usr/bin/env python3
"""source/ (블리자드 원본 데이터)를 다른 컴퓨터로 옮기기 위한 zip으로 묶는다.

저장소가 공개라 source/는 git에 올리지 않는다. 이 zip은 개인 드라이브 등 비공개 위치에만 둔다.
사용: python3 tools/make_source_pack.py   → build/source_pack.zip
"""
import os, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source')
OUT = os.path.join(ROOT, 'build', 'source_pack.zip')


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    n = 0
    with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for base, _, files in os.walk(SRC):
            for f in sorted(files):
                p = os.path.join(base, f)
                z.write(p, os.path.relpath(p, ROOT).replace(os.sep, '/'))
                n += 1
    print(OUT, n, 'files', os.path.getsize(OUT) // 1024, 'KB')


if __name__ == '__main__':
    main()
