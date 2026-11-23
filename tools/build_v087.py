#!/usr/bin/env python3
"""0.8.6 -> 0.8.7: 8번 대열차 강도 시작 SCV 4 -> 12 (사용자 2026-11-23 "12기로 늘려줘 적들이 공성전차랑 바이오닉부대 끌고와서 방어하기 빡셈").

THorner01만: 임무 시작(gf_m8_Start, 한 번만) 때 레이너 사령부 (130.5,94.5) 옆에 SCV를 더 만들어 레이너 SCV가 12기가 되게 하고
(원본 배치 4기 + 8기, 이미 12기 이상이면 안 만듦), 새 SCV는 사령부에서 가장 가까운 광물을 캐러 보낸다. 시험값. Game not run.

Usage: python3 tools/build_v087.py <0.8.6 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.8.6', b'version=0.8.7'
K = 'THorner01.SC2Map/mapscript.galaxy'
A = '    gv_m8_started=true;\n'
B = A + '''    // 0.8.7 (user 2026-11-23): start with 12 SCVs (original map places 4; trial).
    gf_m8_ExtraScv(12);
'''
FN = '''// 0.8.7: top Raynor's SCVs up to n at the start and send the new ones to mine.
void gf_m8_ExtraScv (int n) {
    point cc = Point(130.5,94.5);
    unitgroup made;
    unitgroup fields;
    unit f;
    int have = UnitGroupCount(UnitGroup("SCV", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive);
    point at;
    if (have >= n) { return; }
    at = UnitTypePlacementFromPoint("SCV", 1, PointWithOffset(cc, 3.0, 3.0), 8.0);
    if (at == null) { at = cc; }
    UnitCreate(n - have, "SCV", 0, 1, at, 270.0);
    made = UnitLastCreatedGroup();
    fields = UnitGroup("RichMineralField", 0, RegionCircle(cc, 14.0), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0);
    if (UnitGroupCount(fields, c_unitCountAlive) == 0) {
        fields = UnitGroup("MineralField", 0, RegionCircle(cc, 14.0), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0);
    }
    f = UnitGroupClosestToPoint(fields, cc);
    if (f != null) { UnitGroupIssueOrder(made, OrderTargetingUnit(AbilityCommand("SCVHarvest", 0), f), c_orderQueueReplace); }
}

'''


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        t = files[K].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
        assert t.count(A) == 1 and 'gf_m8_ExtraScv' not in t
        t = t.replace(A, B)
        i = t.index('void gf_m8_Start () {')
        t = t[:i] + FN + t[i:]
        files[K] = t.replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in ('metadata.txt', K): assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
