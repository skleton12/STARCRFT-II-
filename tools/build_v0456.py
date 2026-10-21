#!/usr/bin/env python3
"""Build CCM 0.4.56 from 0.4.55: 공학 연구소의 무기고 건물 연구 8개를 지운다 (4번, 사용자 지시 2026-10-21).

0.4.54 에서 Not 노드를 고친 뒤 공학 연구소 첫 화면에 0.4.40 의 무기고 건물 연구가 모두 보이게 됐다.
사용자: "건물쪽 연구 … 본래 그것까지 생각한건 아닌데 일단 그거 다 지워줘". 협동전 건물 연구(2페이지)는 그대로.
지우는 것 (RM3_BayResearch Research10~17): 신소재 강철 벙커, 탄환 가속기, 이중 핵융합 용접기, 협동 건설,
  화재 진압 시스템, 궤도 사령부, 티타늄 외피, 지옥폭풍 미사일 포 — 명령 카드 버튼·연구 항목·스크립트 허용 줄.
남기는 것: 보급 벙커 건설·건물 장갑(3번부터, 사용자 확정), 협동전 2페이지(신소재 강화 장갑·조준 지원 총안·
  KMC 자동장전기·정밀 보안 자동추적). 히페리온 무기고에서 산 효과는 원래 캠페인대로 적용된다.
쓰지 않게 된 버튼·요구조건·문자열 정의는 남겨 둔다 (참조만 끊김, 다른 연결 보호).

Usage: python3 tools/build_v0456.py <0.4.55 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.55', b'version=0.4.56'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
SCRIPT = M4 + 'mapscript.galaxy'
# (ResearchN, button face, upgrade)
GONE = [(10, 'RMA_NeoSteelFrame', 'NeoSteelFrame'), (11, 'RMA_ProjectileAccelerators', 'ProjectileAccelerators'),
        (12, 'RMA_DualFusionWelders', 'DualFusionWelders'), (13, 'RMA_AdvancedConstruction', 'AdvancedConstruction'),
        (14, 'RMA_FireSuppressionSystems', 'FireSuppressionSystems'), (15, 'RMA_OrbitalRelay', 'OrbitalRelay'),
        (16, 'RMA_ReinforcedSuperstructure', 'ReinforcedSuperstructure'), (17, 'RMA_HailstormMissilePods', 'HailstormMissilePods')]


def units(d):
    t = d.decode('utf-8')
    for n, face, _ in GONE:
        t, k = re.subn(rf'\s*<LayoutButtons Face="{face}" Type="AbilCmd" AbilCmd="RM3_BayResearch,Research{n}" [^>]*/>', '', t)
        assert k == 1, face
    return t.encode('utf-8')


def abil(d):
    t = d.decode('utf-8')
    m = re.search(r'<CAbilResearch id="RM3_BayResearch">.*?</CAbilResearch>', t, re.S)
    b = m.group(0)
    for n, face, up in GONE:
        b, k = re.subn(rf'\s*<InfoArray index="Research{n}"[^>]*Upgrade="{up}">.*?</InfoArray>', '', b, flags=re.S)
        assert k == 1, up
    return (t[:m.start()] + b + t[m.end():]).encode('utf-8')


def script(d):
    t = d.decode('utf-8')
    for n, _, up in GONE:
        for line in (f'    TechTreeAbilityAllow(1,AbilityCommand("RM3_BayResearch",{n - 1}),true);\n',
                     f'    TechTreeUpgradeAllow(1,"{up}",true);\n'):
            assert t.count(line) == 1, line
            t = t.replace(line, '')
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'unitdata.xml': units, GD + 'abildata.xml': abil, SCRIPT: script}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
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
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
