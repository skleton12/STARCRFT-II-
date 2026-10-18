#!/usr/bin/env python3
"""Build CCM 0.4.8 from 0.4.7: 레이너 본진 가스 +65%·무기고 구매와 미션 내 연구 겹침 정리.

1. 규칙 변경 (사용자 2026-10-18 "가스 좀 적은 듯, 기본 2500이면 60~70% 늘려도"):
   레이너 본진 가스 매장량 = 원본 × 1.65 (시험값, 이전 × 1.2). 광물은 × 1.2 그대로.
   2번 3254→5369, 3번 2100→3465, 4번 2500→4125 (두 곳). 원본 값은 현재 값 ÷ 1.2 (올림)으로 되찾는다.
2. 무기고 겹침 (사용자 보고 "무기고 스팀팩 연구하면 중첩", CLAUDE.md 4장: 산 것을 다시 사게 하거나 같은 효과를 겹치지 않는다), 3·4번:
   - 히페리온에서 자극제(MarineStimpack)를 샀으면 미션 내 전투 자극제 1단계(RM3_Stim1)를 완료로 준다 → 초 전투 자극제부터.
   - 히페리온에서 전투 방패(CombatShield, 전쟁광 생명력 +10)를 샀으면 미션 내 전투 방패 연구(+10)를 막는다.

Usage: python3 tools/build_v048.py <0.4.7 zip> <new output zip>
"""
import argparse, copy, math, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.4.7', b'version=0.4.8'
GAS = {'TRaynor02': 1, 'TRaynor03': 1, 'TTychus01': 2}
ARMORY = '''
    // Hyperion armory purchases count as the matching mission research (no re-buy, no double effect).
    if (TechTreeUpgradeCount(1,"MarineStimpack",c_techCountCompleteOnly)>0) { TechTreeUpgradeAddLevel(1,"RM3_Stim1",MaxI(0,1-TechTreeUpgradeCount(1,"RM3_Stim1",c_techCountCompleteOnly))); }
    if (TechTreeUpgradeCount(1,"CombatShield",c_techCountCompleteOnly)>0) { TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",3),false); }'''


def gas(expect):
    def fix(data):
        root = E.fromstring(data)
        n = 0
        for el in root:
            if el.tag == 'ObjectUnit' and el.get('UnitType') == 'RichVespeneGeyser':
                orig = math.ceil(int(el.get('Resources')) / 1.2)
                el.set('Resources', str(orig * 165 // 100)); n += 1
        assert n == expect, n
        return E.tostring(root, encoding='utf-8', xml_declaration=True)
    return fix


def script(anchor):
    def fix(d):
        nl = '\r\n' if b'\r\n' in d else '\n'
        a = anchor.encode()
        assert d.count(a) == 1
        return d.replace(a, a + ARMORY.replace('\n', nl).encode(), 1)
    return fix


FIX = {f'{m}.SC2Map/objects': gas(n) for m, n in GAS.items()}
FIX['TRaynor03.SC2Map/mapscript.galaxy'] = script('gv_m3_started=true;')
FIX['TTychus01.SC2Map/mapscript.galaxy'] = script('gv_m4_started=true;')
FIX['metadata.txt'] = lambda d: d.replace(OLD, NEW)


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
