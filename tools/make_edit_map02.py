#!/usr/bin/env python3
"""2번 미션 편집용 맵: 원본 traynor02에 동맹 슬롯(8 정화자, 9 원시 저그)만 추가한다.

사용자가 편집기에서 지형·배치를 고치는 용도다. 스크립트(동맹 AI·용병 교체)는 넣지 않으므로
이 맵은 편집기로 저장해도 된다. 고친 맵을 돌려받으면 이후 패치 도구의 원본으로 쓴다.
출력: build/TRaynor02_edit.SC2Map, build/TRaynor02_edit.zip
편집기용 단일 파일: tools/pack_sc2map.py 로 build/TRaynor02_Edit.SC2Map (MPQ) 을 만든다.
"""
import os, shutil, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import patch_mission01 as m1

SRC = os.path.join(ROOT, 'source', 'liberty.sc2campaign', 'base.sc2maps', 'maps', 'campaign', 'traynor02.sc2map')
OUT = os.path.join(ROOT, 'build', 'TRaynor02_edit.SC2Map')


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    for name, fn in (('mapinfo', m1.patch_mapinfo), ('documentheader', m1.patch_header)):
        p = os.path.join(OUT, name)
        d = open(p, 'rb').read()
        open(p, 'wb').write(fn(d))
    z = OUT[:-len('.SC2Map')] + '.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for base, _, files in os.walk(OUT):
            for f in files:
                full = os.path.join(base, f)
                zf.write(full, os.path.relpath(full, os.path.dirname(OUT)))
    print(OUT, z)


if __name__ == '__main__':
    main()
