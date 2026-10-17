#!/usr/bin/env python3
"""Build CCM 0.3.16 from 0.3.15: 적 강화를 종족별로 (3번 미션 = 저그 → 물량).

사용자 보고·확정 (2026-10-17): "저그가 세서 내 건물이 무너짐" 뒤 "강화를 이렇게 하자: 저그는 물량, 프로토스와 테란은 강화 받는 쪽으로".
3번 적은 저그(2~5번)이므로:
  - 피해 % 강화(0/5/15/35)와 최소 업그레이드 1 (0.3.12 gf_m3_EnemyRules) 호출 제거.
  - 원본 240초 공격 업그레이드 +1은 원본대로 되돌림 (최소 업그레이드를 안 주므로 겹칠 일이 없음).
  - 물량: 원본 공세 생성 4곳 +50% (0.3.12 시험값) 유지.
1·2번(적 테란)은 능력치 강화 그대로.

Usage: python3 tools/build_v0316.py <0.3.15 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.15', b'version=0.3.16'
M3 = 'TRaynor03.SC2Map/'
EDITS = [
    ('    if (gv_gameOver) { return true; }\n    gf_m3_EnemyRules();\n', '    if (gv_gameOver) { return true; }\n'),
    ('        // 0.3.12: fill up to the level the original grants here instead of stacking on the 7-1 minimum.\n'
     '        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMeleeWeaponsLevel1", MaxI(0, 1 - TechTreeUpgradeCount(autoAC0A0760_var, "ZergMeleeWeaponsLevel1", c_techCountCompleteOnly)));\n'
     '        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMissileWeaponsLevel1", MaxI(0, 1 + libNtve_gf_DifficultyValueInt(0, 0, 0, 1) - TechTreeUpgradeCount(autoAC0A0760_var, "ZergMissileWeaponsLevel1", c_techCountCompleteOnly)));\n',
     '        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMeleeWeaponsLevel1", 1);\n'
     '        TechTreeUpgradeAddLevel(autoAC0A0760_var, "ZergMissileWeaponsLevel1", 1);\n'),
]


def script(data):
    text = data.decode('utf-8')
    for old, new in EDITS:
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new, 1)
    assert 'gf_m3_EnemyRules();' not in text and text.count('lp_qty + lp_qty / 2') == 2 and text.count('lp_quantity + lp_quantity / 2') == 2
    return text.encode('utf-8')


FIX = {M3 + 'mapscript.galaxy': script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
