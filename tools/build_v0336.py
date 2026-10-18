#!/usr/bin/env python3
"""Build CCM 0.3.36 from 0.3.35: 히페리온 무기고·연구실의 벙커 업그레이드를 보급 벙커에도 반영 (3번 미션).

사용자 결정 (2026-10-18): "일반 벙커는 일반 벙커 외형으로, 보급 벙커는 보급 벙커 그대로.
대신 무기고에서 돈으로 업그레이드하면 업그레이드 반영."
  - 일반 벙커: 모드가 바꾼 데이터가 없다 (원작 그대로). 이번에도 건드리지 않는다.
  - 보급 벙커(BunkerDepotMengsk): 모델·건설 방식은 협동전 그대로 둔다 (사용자 확인).
  - 자날 캠페인에서 사는 벙커 업그레이드가 보급 벙커에도 걸리게 한다:
      신소재 강철 벙커(무기고, NeoSteelFrame): 일반 벙커처럼 탑승 칸 +2 (6 → 8)
      강화 벙커(연구실, FortifiedBunkerCarapace): 일반 벙커처럼 생명력 +150 (400 → 550)
      화재 진압 시스템(FireSuppressionSystem): 일반 벙커와 같은 행동(생명력 절반 아래면 초당 4 회복)을 붙인다.
        구매 조건(FireSuppressionSystemsResearched)은 원작 그대로 따른다.
      탄환 가속기(무기고): 협동전 보급 벙커의 사거리 행동이 원래부터 자날 탄환 가속기 효과를 쓴다
        (BunkerMengskWeaponRangeBonus의 InitialEffect ProjectileAccelerators). 구매하면 이미 적용된다 — 바꿀 것 없음.
        일반 벙커와 같이 기본 +1, 구매 시 +1 더.
      까치날개 포탑(연구실): 보급 벙커 모델에 포탑을 붙일 자리가 일반 벙커와 달라 이번에는 넣지 않는다 (미정).
  - 업그레이드는 원작처럼 히페리온에서 산 플레이어에게만 임무 시작 때 주어진다. 사지 않으면 변화 없다.

Usage: python3 tools/build_v0336.py <0.3.35 zip> <new output zip>
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.3.35', b'version=0.3.36'
GD = 'TRaynor03.SC2Map/base.sc2data/gamedata/'
UPGRADES = ('<CUpgrade id="NeoSteelFrame">'
            '<EffectArray Reference="Abil,BunkerMengskTransport,MaxCargoCount" Value="2" />'
            '<EffectArray Reference="Abil,BunkerMengskTransport,TotalCargoSpace" Value="2" /></CUpgrade>'
            '<CUpgrade id="FortifiedBunkerCarapace">'
            '<EffectArray Reference="Unit,BunkerDepotMengsk,LifeMax" Value="150" />'
            '<EffectArray Reference="Unit,BunkerDepotMengsk,LifeStart" Value="150" /></CUpgrade>')


def upgrades(data):
    root = E.fromstring(data)
    have = {e.get('id') for e in root}
    assert 'NeoSteelFrame' not in have and 'FortifiedBunkerCarapace' not in have
    for el in E.fromstring('<C>' + UPGRADES + '</C>'):
        root.append(el)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def units(data):
    root = E.fromstring(data)
    u = [e for e in root if e.tag == 'CUnit' and e.get('id') == 'BunkerDepotMengsk']
    assert len(u) == 1
    assert not any(b.get('Link') == 'FireSuppressionSystem' for b in u[0].findall('BehaviorArray'))
    E.SubElement(u[0], 'BehaviorArray', Link='FireSuppressionSystem')
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


FIX = {GD + 'upgradedata.xml': upgrades, GD + 'unitdata.xml': units, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for name, fn in FIX.items(): files[name] = fn(files[name])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
