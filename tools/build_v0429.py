#!/usr/bin/env python3
"""Build CCM 0.4.29 from 0.4.28: 동맹 공격 목표에서 가짜·연출 건물 빼기 (maps 3·4).

사용자 확인 (2026-10-19): 동맹이 적 기지를 공격하지 않는 경우 조사 → 수정.
  원인: '가장 가까운 적 건물'에 원본의 숨은 인구 건물(Food1000, 맵 구석·가장자리)과 4번 탈다림 대형 차원문
  (SuperWarpGate, 맵 모서리 연출용)이 들어가 동맹이 갈 수 없는 곳으로 행군해 멈췄다.
  수정: 두 종류를 빼고, 무적·숨김 건물도 목표에서 뺀다.

Usage: python3 tools/build_v0429.py <0.4.28 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.28', b'version=0.4.29'
SUBS = [
    ('UnitFilter((1 << c_targetFilterStructure),0,0,(1 << (c_targetFilterDead - 32)))',
     'UnitFilter((1 << c_targetFilterStructure),0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterInvulnerable - 32)))'),
    ('if (t!="CreepTumor" && t!="CreepTumorBurrowed" && t!="CreepTumorQueen") { UnitGroupAdd(all,u); }',
     '// Food1000 = hidden AI supply dummies at map edges; SuperWarpGate = scripted warp-in gates in a corner (0.4.29).\n'
     '            if (t!="CreepTumor" && t!="CreepTumorBurrowed" && t!="CreepTumorQueen" && t!="Food1000" && t!="SuperWarpGate") { UnitGroupAdd(all,u); }'),
]


def patch(d):
    t = d.decode('utf-8')
    for a, b in SUBS:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW),
       'TRaynor03.SC2Map/mapscript.galaxy': patch, 'TTychus01.SC2Map/mapscript.galaxy': patch}


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
