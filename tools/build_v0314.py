#!/usr/bin/env python3
"""Build CCM 0.3.14 from 0.3.13: 원시저그 기지를 레이너 구역 옆 저지대로 (3번 미션). 0.3.15에서 대체됨 (build_v0315.py).

사용자 제안 (2026-10-17): "원시저그는 내 구역 옆에 넣는 건 어떰, 만들어보고 맵 이미지 보여줘".
- 원시저그 기지를 남서쪽(42.5,29.5)에서 레이너 본진 언덕 서쪽 아래 저지대로: 원시 군락 (69.5,35.5).
  레이너 본진 언덕길(x 79~85, y 43~49) 앞, 동맹 기본 방어 지점 (65,47) 바로 옆.
- 광물 8: 군락 서쪽 절벽 쪽 한 줄 (63, 31.5~38.5), 가스: (65.5,29.5). 군락과 3칸 간격.
- 원시 감시자 (69.5,41.5), 추가 감시자 (65.5,41.5), 투하 (66~70.5, 43~46), 드롭포드 (68,44), 일벌레 등장 (66,40).
- 남서쪽 옛 원시저그 광물 8·가스 1 삭제 (정화자 기지 쪽 자원은 그대로). 광물 길을 막는 주민 가로등 1개 (64.5,34.5) 삭제.
- 정화 광선 진입·정화자 기지는 그대로. 원시저그 건설 순서·시간·비용은 0.3.12 그대로.
위치는 시험 배치 (사용자 확인 대기).

Usage: python3 tools/build_v0314.py <0.3.13 zip> <new output zip>
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.3.13', b'version=0.3.14'
M3 = 'TRaynor03.SC2Map/'
HIVE = (69.5, 35.5)
MINERALS = [(63, y + 0.5) for y in range(31, 39)]
GAS = (65.5, 29.5)
REMOVE_IDS = {str(i) for i in range(30000, 30008)} | {'30009'}
REMOVE_STREETLIGHT = (64.4975, 34.4802)

SCRIPT = [
    ('pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(34.0,35.0));', 'pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(68.0,44.0));'),
    ('UnitCreate(1,kind,0,11,Point(32.0+1.5*(i%4),33.0+2.0*(i/4)),0.0);', 'UnitCreate(1,kind,0,11,Point(66.0+1.5*(i%4),43.0+1.5*(i/4)),0.0);'),
    ('UnitCreate(6,"DehakaDrone",0,11,Point(36.0,31.0),270.0);', 'UnitCreate(6,"DehakaDrone",0,11,Point(66.0,40.0),270.0);'),
    ('    site[1]=Point(42.5,29.5);\n    site[2]=Point(37.5,25.5);\n', '    site[1]=Point(69.5,35.5);\n    site[2]=Point(69.5,41.5);\n'),
    ('    gf_m3_AI(11,Point(42.5,29.5));', '    gf_m3_AI(11,Point(69.5,35.5));'),
    ('gf_m3_Build("Extractor",11,Point(35.5,28.5),30)', 'gf_m3_Build("Extractor",11,Point(65.5,29.5),30)'),
    ('UnitGroup("Extractor",11,RegionCircle(Point(35.5,28.5),2.0)', 'UnitGroup("Extractor",11,RegionCircle(Point(65.5,29.5),2.0)'),
    ('gf_m3_Build("DehakaBarracks",11,Point(44.5,25.5),60)', 'gf_m3_Build("DehakaBarracks",11,Point(65.5,41.5),60)'),
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
    light = [el for el in root if el.tag == 'ObjectUnit' and el.get('UnitType') == 'DestructibleStreetlight'
             and el.get('Position', '').startswith(f'{REMOVE_STREETLIGHT[0]},{REMOVE_STREETLIGHT[1]}')]
    assert len(light) == 1
    for el in gone + light: root.remove(el)
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
