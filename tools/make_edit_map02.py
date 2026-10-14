#!/usr/bin/env python3
"""2번 미션 편집용 맵: 원본 traynor02에 동맹 슬롯(8 정화자, 9 원시 저그)만 추가한다.

사용자가 편집기에서 지형·배치를 고치는 용도다. 스크립트(동맹 AI·용병 교체)는 넣지 않으므로
이 맵은 편집기로 저장해도 된다. 고친 맵을 돌려받으면 이후 패치 도구의 원본으로 쓴다.
출력: build/TRaynor02_edit.SC2Map, build/TRaynor02_edit.zip
편집기용 단일 파일: tools/pack_sc2map.py 로 build/TRaynor02_Edit.SC2Map (MPQ) 을 만든다.
"""
import os, re, shutil, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import patch_mission01 as m1
import expand_map

# 지형 확장 (사용자 지시 2026-10-14: 맵을 키우고 동쪽에 동맹 2). 값은 시험값
EXPAND_SEAM = 104   # 이 x 경계 동쪽을 서쪽 지형의 거울 복사로 바꾼다
EXPAND_WIDTH = 200  # 새 가로 (원본 136). 세로 136은 그대로

# 동맹 시작 위치 표시 지점 (사용자 지시 2026-10-14). 편집기에서 옮기면 패치 도구가 그 위치를 쓴다
ALLY_MARKERS = [
    ('rm Ally1 Purifier Start', 48.0, 78.0),   # 중앙 발굴지(TRaynor02DigSite) 통로
    ('rm Ally2 Primal Start', 125.5, 29.5),    # 동쪽 확장 지역: 레이너 기지의 대칭 위치
]

SRC = os.path.join(ROOT, 'source', 'liberty.sc2campaign', 'base.sc2maps', 'maps', 'campaign', 'traynor02.sc2map')
OUT = os.path.join(ROOT, 'build', 'TRaynor02_edit.SC2Map')


def add_markers(path):
    o = open(path, encoding='utf-8', newline='').read()
    nid = max(int(x) for x in re.findall(r' Id="(\d+)"', o)) + 1
    nl = '\r\n' if '\r\n' in o else '\n'
    add = ''
    for i, (name, x, y) in enumerate(ALLY_MARKERS):
        add += (f'    <ObjectPoint Id="{nid + i}" Position="{x},{y},0" Scale="1,1,1" Type="Normal" '
                f'Name="{name}" Color="255,255,255,255"/>{nl}')
    end = o.rindex('</PlacedObjects>')
    open(path, 'w', encoding='utf-8', newline='').write(o[:end] + add + o[end:])


def main():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    for name, fn in (('mapinfo', m1.patch_mapinfo), ('documentheader', m1.patch_header)):
        p = os.path.join(OUT, name)
        d = open(p, 'rb').read()
        open(p, 'wb').write(fn(d))
    info = expand_map.expand_east(OUT, EXPAND_SEAM, EXPAND_WIDTH)
    print(info)
    add_markers(os.path.join(OUT, 'objects'))
    z = OUT[:-len('.SC2Map')] + '.zip'
    with zipfile.ZipFile(z, 'w', zipfile.ZIP_DEFLATED) as zf:
        for base, _, files in os.walk(OUT):
            for f in files:
                full = os.path.join(base, f)
                zf.write(full, os.path.relpath(full, os.path.dirname(OUT)))
    print(OUT, z)


if __name__ == '__main__':
    main()
