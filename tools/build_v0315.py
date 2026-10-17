#!/usr/bin/env python3
"""Build CCM 0.3.15 from 0.3.13: 원시저그 기지를 사용자가 표시한 레이너 본진 언덕 위 동쪽으로 (3번 미션).

사용자 지정 (2026-10-17): 0.3.14 확대 그림에 "내가 생각한 원시저그 위치"로 x 101~107, y 40~49 영역을 표시.
0.3.14(저지대 시험 배치)는 쓰지 않고 0.3.13에서 다시 만든다.
- 원시 군락 (104.5,45.5). 광물 8: 동쪽 절벽 쪽 세로 6 (111, 42.5~47.5) + 북쪽 2 (101,51.5)(103,51.5), 군락과 3칸 간격.
- 가스 (106.5,39.5). 원시 감시자 (98.5,45.5), 추가 감시자 (98.5,49.5) — 레이너 공학 연구소(98.5,40.5)·병영(92.5,40.5) 피함.
- 투하 (92~96.5, 44~47), 드롭포드 (94,45.5), 일벌레 등장 (100,44).
- 남서쪽 옛 원시저그 자원(광물 8·가스 1) 삭제. 정화자 기지·정화 광선은 그대로. 건설 순서·시간·비용은 0.3.12 그대로.

Usage: python3 tools/build_v0315.py <0.3.13 zip> <new output zip>
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.3.13', b'version=0.3.15'
M3 = 'TRaynor03.SC2Map/'
MINERALS = [(111, y + 0.5) for y in range(42, 48)] + [(101, 51.5), (103, 51.5)]
GAS = (106.5, 39.5)
REMOVE_IDS = {str(i) for i in range(30000, 30008)} | {'30009'}

SCRIPT = [
    ('pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(34.0,35.0));', 'pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(94.0,45.5));'),
    ('UnitCreate(1,kind,0,11,Point(32.0+1.5*(i%4),33.0+2.0*(i/4)),0.0);', 'UnitCreate(1,kind,0,11,Point(92.0+1.5*(i%4),44.0+1.5*(i/4)),0.0);'),
    ('UnitCreate(6,"DehakaDrone",0,11,Point(36.0,31.0),270.0);', 'UnitCreate(6,"DehakaDrone",0,11,Point(100.0,44.0),270.0);'),
    ('    site[1]=Point(42.5,29.5);\n    site[2]=Point(37.5,25.5);\n', '    site[1]=Point(104.5,45.5);\n    site[2]=Point(98.5,45.5);\n'),
    ('    gf_m3_AI(11,Point(42.5,29.5));', '    gf_m3_AI(11,Point(104.5,45.5));'),
    ('gf_m3_Build("Extractor",11,Point(35.5,28.5),30)', 'gf_m3_Build("Extractor",11,Point(106.5,39.5),30)'),
    ('UnitGroup("Extractor",11,RegionCircle(Point(35.5,28.5),2.0)', 'UnitGroup("Extractor",11,RegionCircle(Point(106.5,39.5),2.0)'),
    ('gf_m3_Build("DehakaBarracks",11,Point(44.5,25.5),60)', 'gf_m3_Build("DehakaBarracks",11,Point(98.5,49.5),60)'),
]


def script(data):
    text = data.decode('utf-8')
    for old, new in SCRIPT:
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new, 1)
    return text.encode('utf-8')


def objects(data):
    root = E.fromstring(data)
    gone = [el for el in root if el.get('Id') in REMOVE_IDS]
    assert len(gone) == len(REMOVE_IDS)
    for el in gone: root.remove(el)
    oid = 30010
    for x, y in MINERALS:
        E.SubElement(root, 'ObjectUnit', Id=str(oid), Position=f'{x},{y},0', Scale='1,1,1', UnitType='RichMineralField', Resources='1800'); oid += 1
    E.SubElement(root, 'ObjectUnit', Id=str(oid), Position=f'{GAS[0]},{GAS[1]},0', Scale='1,1,1', UnitType='RichVespeneGeyser', Resources='3000')
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


FIX = {M3 + 'mapscript.galaxy': script, M3 + 'objects': objects, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX: data = FIX[info.filename](data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path)
    a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
