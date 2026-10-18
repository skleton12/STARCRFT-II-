#!/usr/bin/env python3
"""Build CCM 0.4.13 from 0.4.12: 불곰 연구가 여전히 안 보임·불곰 자극제 (사용자 2026-10-18).

1. 불곰 연구 버튼: 충격탄은 자날 캠페인 업그레이드(PunisherGrenades)라 캠페인 기술 제한에 잠길 수 있다.
   매 틱 네 업그레이드를 허용한다 (TechTreeUpgradeAllow). 히페리온 무기고 충격탄(JackhammerConcussionGrenades)을
   샀으면 충격탄 1단계를 완료로 준다 (CLAUDE.md 4장, 다시 사지 않게).
2. 망치 경호대 자극제: 원래 카드에 자극제 버튼이 없다. 전쟁광과 같은 자극제 줄
   (원작 자극제 → 초 전투 자극제 → 멩스크 자극제, 같은 연구)을 2줄 3칸 한 자리에 붙인다.
   1단계는 전쟁광과 같은 Stimpack 능력(생명력 10 소모)이다 — 캠페인 불곰 자극제(StimpackMarauder)는 캠페인 데이터에서 효과가 비어 있다.

Usage: python3 tools/build_v0413.py <0.4.12 zip> <new output zip>
"""
import argparse, copy, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.4.12', b'version=0.4.13'
M4 = 'TTychus01.SC2Map/'
ANCHOR = b'    // Hammer Security research needs the original Marauder unlock (nonlinear rule).'
ALLOW = b'''    // Campaign tech limits must not hide the mission research (0.4.13).
    TechTreeUpgradeAllow(1,"PunisherGrenades",true);
    TechTreeUpgradeAllow(1,"RM4_Suppression",true);
    TechTreeUpgradeAllow(1,"MarauderMagrailMunitions",true);
    TechTreeUpgradeAllow(1,"RM4_Shrapnel",true);
'''
START = b'gv_m4_started=true;'
BOUGHT = b'''
    if (TechTreeUpgradeCount(1,"JackhammerConcussionGrenades",c_techCountCompleteOnly)>0) { TechTreeUpgradeAddLevel(1,"PunisherGrenades",MaxI(0,1-TechTreeUpgradeCount(1,"PunisherGrenades",c_techCountCompleteOnly))); }'''
STIM = [('Stim', 'Stimpack,Execute', 'RM3_Stim1Use'), ('MarineSuperStimpack', 'SuperStimpackMarine,Execute', 'RM3_Stim2Use'),
        ('RMK_MarineMengskAttackSpeedBoost', 'RMK_MarineMengskAttackSpeedBoost,Execute', 'RM3_Stim3Use')]


def script(d):
    nl = b'\r\n' if b'\r\n' in d else b'\n'
    assert d.count(ANCHOR) == 1 and d.count(START) == 1
    d = d.replace(ANCHOR, ALLOW.replace(b'\n', nl) + ANCHOR)
    return d.replace(START, START + BOUGHT.replace(b'\n', nl))


def units(d):
    root = E.fromstring(d)
    hs = [u for u in root if u.tag == 'CUnit' and u.get('id') == 'HammerSecurity']
    assert len(hs) == 1
    u = hs[0]
    for abil in ('Stimpack', 'SuperStimpackMarine', 'RMK_MarineMengskAttackSpeedBoost'):
        E.SubElement(u, 'AbilArray', Link=abil)
    card = u.find('CardLayouts')
    for face, cmd, req in STIM:
        E.SubElement(card, 'LayoutButtons', Face=face, Type='AbilCmd', AbilCmd=cmd, Requirements=req, Row='2', Column='3')
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


FIX = {M4 + 'mapscript.galaxy': script, M4 + 'base.sc2data/gamedata/unitdata.xml': units,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), FIX[info.filename](d) if info.filename in FIX else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
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
