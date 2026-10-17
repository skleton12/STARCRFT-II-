#!/usr/bin/env python3
"""Build CCM 0.3.22 from 0.3.21: 보급 벙커 건설 정상화 (3번 미션).

사용자 보고 (2026-10-17): "보급 벙커 건설 왜 그따위로 돼 있음".
원인 (코드·데이터 검토):
  1. 발판(Footprint2x2CreepNormalContour / Footprint2x2CreepNormal)이 협동전 전용 ID라 자날 맵 데이터에 없음.
  2. 액터가 일반 벙커 템플릿(TerranBuildingEx)을 물려받아 '##unitName##Build·Placement·Portrait'와
     아이콘 btn-building-terran-RM3_SupplyBunker.dds를 찾는데, 그 이름의 모델·그림이 없음
     (건설 중 모습·배치 미리보기·초상화·아이콘 깨짐).
  3. 건설 시간 30초 — 원작 멩스크 보급 벙커(BunkerDepotMengsk, SCV 건설 Time 20)와 다름.
수정:
  - 발판을 보급고와 같은 자날 2×2 (Footprint2x2Contour / Footprint2x2)로.
  - 모델 RM3_SupplyBunkerBuild(벙커 건설 모습 축소), RM3_SupplyBunkerPlacement(벙커 배치 모습 0.75, 원작과 같음),
    RM3_SupplyBunkerPortrait(벙커 초상화) 추가. 아이콘은 자날 데이터의 btn-building-terran-supplybunkermengsk.dds.
  - 건설 시간 20 (원작). 보급 12·수용 6·광물 100·체력 400은 그대로.

Usage: python3 tools/build_v0322.py <0.3.21 zip> <new output zip>
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.3.21', b'version=0.3.22'
GD = 'TRaynor03.SC2Map/base.sc2data/gamedata/'
ICON = r'Assets\Textures\btn-building-terran-supplybunkermengsk.dds'
MODELS = ('<CModel id="RM3_SupplyBunkerBuild" parent="BunkerBuild"><ScaleMax value="0.670000,0.670000,0.670000" /><ScaleMin value="0.670000,0.670000,0.670000" /></CModel>'
          '<CModel id="RM3_SupplyBunkerPlacement" parent="BunkerPlacement"><ScaleMax value="0.750000,0.750000,0.750000" /><ScaleMin value="0.750000,0.750000,0.750000" /></CModel>'
          '<CModel id="RM3_SupplyBunkerPortrait" parent="BunkerPortrait" />')


def units(data):
    text = data.decode('utf-8')
    for old, new in [('<Footprint value="Footprint2x2CreepNormalContour" />', '<Footprint value="Footprint2x2Contour" />'),
                     ('<PlacementFootprint value="Footprint2x2CreepNormal" />', '<PlacementFootprint value="Footprint2x2" />')]:
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    return text.encode('utf-8')


def abils(data):
    text = data.decode('utf-8')
    old = 'InfoArray index="Build17" Unit="RM3_SupplyBunker" Time="30"'
    assert text.count(old) == 1
    return text.replace(old, 'InfoArray index="Build17" Unit="RM3_SupplyBunker" Time="20"', 1).encode('utf-8')


def models(data):
    text = data.decode('utf-8')
    assert 'id="RM3_SupplyBunkerBuild"' not in text
    out = text.replace('</Catalog>', MODELS + '</Catalog>', 1).encode('utf-8')
    E.fromstring(out)
    return out


def actors(data):
    root = E.fromstring(data)
    el = [e for e in root if e.tag == 'CActorUnit' and e.get('id') == 'RM3_SupplyBunker']
    assert len(el) == 1
    E.SubElement(el[0], 'UnitIcon', value=ICON)
    E.SubElement(el[0], 'HeroIcon', value=ICON)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


FIX = {GD + 'unitdata.xml': units, GD + 'abildata.xml': abils, GD + 'modeldata.xml': models, GD + 'actordata.xml': actors,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
