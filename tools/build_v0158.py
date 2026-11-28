#!/usr/bin/env python3
"""0.15.7 -> 0.15.8: 원시저그 땅무지 숙주의 날벌레(DehakaCreeperFlying)가 공격을 안 하던 것 (사용자 2026-11-28).
데이터는 협동전 원본과 같다. 날벌레는 보급을 안 써서 동맹 병력 판별('보급 사용')에 안 들어가 공격 이동 명령을 못 받고,
그냥 떠 있었다. 1초마다 8·9번(동맹) 날벌레 중 명령이 없는 것은 25칸 안 가장 가까운 적 지상 유닛·건물 자리로 공격 이동한다(시험값).
10개 공장 맵(날벌레 데이터가 있는 맵). Usage: build_v0158.py <0.15.7 zip> <out>"""
import copy, sys, zipfile
from pathlib import Path
OLD, NEW = b'version=0.15.7', b'version=0.15.8'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04', 'TTychus03', 'TTychus02']
HOOK = 'void gf_rm14TankInit () {\n    if (gt_rm14Tank != null) { return; }\n'
FUNC = '''// 0.15.8: ally swarm-host flying creepers have no supply, so the ally army loop never orders them; send idle ones at the nearest enemy.
trigger gt_rmCreeper;

bool gt_rmCreeper_Func (bool testConds, bool runActions) {
    unitgroup g;
    unitgroup e;
    unit u;
    unit t;
    int i;
    int p;
    if (!runActions) { return true; }
    for (p = 8; p <= 9; p += 1) {
        g = UnitGroup("DehakaCreeperFlying", p, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0);
        i = UnitGroupCount(g, c_unitCountAll);
        for ( ; i > 0; i -= 1) {
            u = UnitGroupUnit(g, i);
            if (UnitOrderCount(u) > 0) { continue; }
            e = UnitGroupAlliance(p, c_unitAllianceEnemy, RegionCircle(UnitGetPosition(u), 25.0), UnitFilter((1 << c_targetFilterGround) | (1 << c_targetFilterVisible), 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterStasis - 32)) | (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);
            t = UnitGroupClosestToPoint(e, UnitGetPosition(u));
            if (t != null) { UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), UnitGetPosition(t)), c_orderQueueReplace); }
        }
    }
    return true;
}

'''
REG = '    if (gt_rmCreeper == null) { gt_rmCreeper = TriggerCreate("gt_rmCreeper_Func"); TriggerAddEventTimePeriodic(gt_rmCreeper, 1.0, c_timeGame); }\n'


def build(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        for m in MAPS:
            n = f'{m}.SC2Map/mapscript.galaxy'; raw = z.read(n).decode('utf-8')
            nl = '\r\n' if '\r\n' in raw else '\n'; s = raw.replace('\r\n', '\n')
            assert s.count(HOOK) == 1 and 'gt_rmCreeper' not in s, m
            k = s.index('void gf_rm14TankInit () {')
            s = s[:k] + FUNC + s[k:].replace(HOOK, HOOK.replace('    if (gt_rm14Tank', REG + '    if (gt_rm14Tank'), 1)
            rep[n] = s.replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__': build(*sys.argv[1:])
