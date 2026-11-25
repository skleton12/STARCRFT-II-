#!/usr/bin/env python3
"""0.10.4 -> 0.10.5: 탈옥(TTosh03A) 지원군이 적 기지를 공격하러 간다 (사용자 2026-11-25 "플토랑 원시저그 지원은 따로 해야된듯 안감",
선택 "기지에만 있음, 적 기지 공격").
정화자(8번)·원시저그(9번) 지원군은 쪽마다 따로 판단한다: 자기 기지 둘레 18칸 안에 적이 있으면 그 적부터(0.10.4 그대로),
없고 살아 있는 지원군이 8기 이상이면 자기 기지에서 가장 가까운 적 건물(무적 제외)로 공격 이동,
8기 미만이면 기지로 돌아와 모인다. 한 번 나가면 3기 아래로 줄 때까지 계속 공격(시험값 8·3). 기지 근처 적 찾기에서 무적 유닛은 뺀다. Game not run.
Usage: python3 tools/build_v0105.py <0.10.4 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path
OLD, NEW = b'version=0.10.4', b'version=0.10.5'
SP = 'TTosh03A.SC2Map/mapscript.galaxy'
A_DECL = '''    unitgroup e;
    unit u;
    int i;
    point tgt;
    if (g == null || UnitGroupCount(g, c_unitCountAlive) < 1) { return; }
'''
B_DECL = '''    unitgroup e;
    unit u;
    int i;
    point tgt;
    unit b;
    if (g == null || UnitGroupCount(g, c_unitCountAlive) < 1) { return; }
    b = null;
    if (UnitGroupCount(g, c_unitCountAlive) >= gv_rmSupPush) { gv_rmSupGo[pl] = true; }
    if (UnitGroupCount(g, c_unitCountAlive) < 3) { gv_rmSupGo[pl] = false; }
    if (gv_rmSupGo[pl]) {
        b = UnitGroupClosestToPoint(UnitGroupAlliance(pl, c_unitAllianceEnemy, RegionEntireMap(), UnitFilter((1 << c_targetFilterStructure), 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0), c);
    }
'''
A_ELSE = '''        else if (DistanceBetweenPoints(UnitGetPosition(u), c) > 8.0) {
            UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), c), c_orderQueueReplace);
        }'''
B_ELSE = '''        else if (b != null) {
            if (UnitOrderCount(u) < 1) {
                UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), UnitGetPosition(b)), c_orderQueueReplace);
            }
        }
        else if (DistanceBetweenPoints(UnitGetPosition(u), c) > 8.0) {
            UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), c), c_orderQueueReplace);
        }'''
A_GLOB = 'unitgroup gv_rmSupG9;\n'
B_GLOB = 'unitgroup gv_rmSupG9;\nint gv_rmSupPush = 8;\nbool[10] gv_rmSupGo;\n'
def main(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        raw = z.read(SP).decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'; s = raw.replace('\r\n', '\n')
        for a, b in ((A_DECL, B_DECL), (A_ELSE, B_ELSE), (A_GLOB, B_GLOB)):
            assert s.count(a) == 1, a[:40]; s = s.replace(a, b)
        # local scan in gf_rmSupGuard: ignore invulnerable enemies too (2 filters)
        lo = '(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0);'
        i = s.index('void gf_rmSupGuard'); j = s.index('for (i = UnitGroupCount(g', i)
        seg = s[i:j]; k = seg.index('b = null;'); head, tail = seg[:k], seg[k:]
        assert tail.count('e = UnitGroupAlliance') == 2 and tail.count(lo) == 2
        tail = tail.replace(lo, '(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);')
        s = s[:i] + head + tail + s[j:]
        rep[SP] = s.replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                for i in z.infolist(): o.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)))
            with zipfile.ZipFile(out) as o: assert o.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)
if __name__ == '__main__': main(*sys.argv[1:])
