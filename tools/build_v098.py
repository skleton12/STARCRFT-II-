#!/usr/bin/env python3
"""0.9.7 -> 0.9.8 (사용자 2026-11-25 "망자의 항구 올란에게 자치령 지원군 투하(방어용)").

9번 망자의 항구(THorner02)만: 올란(2번) 본진에 레이너·동맹 병력이 들어오면 자치령(4번, 올란과 동맹)이
본진 안에 투하 캡슐(자날 궤도 사령부 투하 모델 DropPodFalling)로 방어 병력을 떨어뜨린다.
- 3초마다 확인: 올란 용병 요새가 살아 있고, 본진 중심 (50,125) 25칸 안에 레이너·동맹 지상/공중 병력이 3기 이상이면 투하.
- 한 번에 해병 4/6/8/10·불곰 1/2/3/4·의무관 1/1/2/2 (쉬움/보통/어려움/아주 어려움), 다음 투하까지 60초.
- 투하 병력은 동시에 30기까지(남은 자리만큼), 스크립트 조종(공세에 안 빠짐), 가장 가까운 침입자 쪽으로 공격 이동.
- 투하 지점은 (50,122) 둘레 4~8칸, 지나갈 수 있고 레이너 본진과 길이 이어진 곳만. 캡슐이 떨어지고 2.5초 뒤 등장.
모두 시험값. Game not run.

Usage: python3 tools/build_v098.py <0.9.7 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.9.7', b'version=0.9.8'
K = 'THorner02.SC2Map/mapscript.galaxy'

SCRIPT = r'''// 0.9.8 (user 2026-11-25): Dominion drops defenders into Orlan's main base when Raynor or the allies push in (trial values).
const fixed gv_m9_domCD = 60.0;
const int gv_m9_domCap = 30;
const int gv_m9_domMinIntruders = 3;
trigger gt_m9_DomDrop;
fixed gv_m9_domNext;
unitgroup gv_m9_domUnits;

int gf_m9_DomAlive () {
    if (gv_m9_domUnits == null) { gv_m9_domUnits = UnitGroupEmpty(); }
    return UnitGroupCount(UnitGroupFilter(null, 4, gv_m9_domUnits, UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive);
}

unitgroup gf_m9_DomIntruders (point c) {
    unitgroup g = UnitGroupEmpty();
    unitfilter f = UnitFilter(0, 0, (1 << c_targetFilterStructure) | (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)));
    UnitGroupAddUnitGroup(g, UnitGroup(null, 1, RegionCircle(c, 25.0), f, 0));
    UnitGroupAddUnitGroup(g, UnitGroup(null, 8, RegionCircle(c, 25.0), f, 0));
    UnitGroupAddUnitGroup(g, UnitGroup(null, 9, RegionCircle(c, 25.0), f, 0));
    return g;
}

bool gt_m9_DomDrop_Func (bool testConds, bool runActions) {
    point c = Point(50.0, 125.0);
    point home = gf_rmVHTarget();
    unitgroup intr;
    string[24] kind;
    point[24] at;
    actor[24] fx;
    int n = 0;
    int room;
    int i;
    int t;
    int k;
    int cnt;
    point p;
    point go;
    unit u;
    if (!runActions || gv_gameOver || !gv_m9_started) { return true; }
    if (GameGetMissionTime() < gv_m9_domNext) { return true; }
    if (UnitGroupCount(UnitGroup("MercenaryFortress", 2, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) == 0) { return true; }
    intr = gf_m9_DomIntruders(c);
    if (UnitGroupCount(intr, c_unitCountAlive) < gv_m9_domMinIntruders) { return true; }
    room = gv_m9_domCap - gf_m9_DomAlive();
    if (room <= 0) { return true; }
    gv_m9_domNext = GameGetMissionTime() + gv_m9_domCD;
    for (k = 0; k < 3; k += 1) {
        if (k == 0) { cnt = libNtve_gf_DifficultyValueInt(4, 6, 8, 10); }
        else if (k == 1) { cnt = libNtve_gf_DifficultyValueInt(1, 2, 3, 4); }
        else { cnt = libNtve_gf_DifficultyValueInt(1, 1, 2, 2); }
        for (i = 0; i < cnt && n < 24 && n < room; i += 1) {
            p = null;
            for (t = 0; t < 10; t += 1) {
                p = PointWithOffsetPolar(Point(50.0, 122.0), RandomFixed(4.0, 8.0), RandomFixed(0.0, 360.0));
                if (PointPathingPassable(p) && (home == null || PointPathingIsConnected(p, home))) { break; }
                p = null;
            }
            if (p == null) { continue; }
            if (k == 0) { kind[n] = "Marine"; } else if (k == 1) { kind[n] = "Marauder"; } else { kind[n] = "Medic"; }
            at[n] = p;
            fx[n] = libNtve_gf_CreateModelAtPoint("DropPodFalling", p);
            n += 1;
        }
    }
    if (n == 0) { gv_m9_domNext = GameGetMissionTime() + 3.0; return true; }
    // units appear after the pod lands
    Wait(2.5, c_timeGame);
    u = UnitGroupClosestToPoint(gf_m9_DomIntruders(c), c);
    go = null;
    if (u != null) { go = UnitGetPosition(u); }
    for (i = 0; i < n; i += 1) {
        if (fx[i] != null) { ActorSend(fx[i], "AnimBracketStop BSD"); }
        if (gv_gameOver) { continue; }
        UnitCreate(1, kind[i], 0, 4, at[i], 270.0);
        if (UnitLastCreated() == null) { continue; }
        AISetUnitScriptControlled(UnitLastCreated(), true);
        UnitGroupAdd(gv_m9_domUnits, UnitLastCreated());
        // Medics have no attack ability: they move with the squad instead (Codex review)
        if (go != null && kind[i] == "Medic") { UnitIssueOrder(UnitLastCreated(), OrderTargetingPoint(AbilityCommand("move", 0), go), c_orderQueueReplace); }
        else if (go != null) { UnitIssueOrder(UnitLastCreated(), OrderTargetingPoint(AbilityCommand("attack", 0), go), c_orderQueueReplace); }
    }
    // TriggerModel starts the BSD bracket itself and removes the pod after the closing animation (Codex review)
    return true;
}

void gf_m9_DomInit () {
    if (gt_m9_DomDrop != null) { return; }
    gv_m9_domUnits = UnitGroupEmpty();
    gt_m9_DomDrop = TriggerCreate("gt_m9_DomDrop_Func");
    TriggerAddEventTimePeriodic(gt_m9_DomDrop, 3.0, c_timeGame);
}

'''


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt', K}
        s = files[K]; nl = b'\r\n' if b'\r\n' in s else b'\n'
        a = nl + b'void InitMap () {'; assert s.count(a) == 1 and b'gt_m9_DomDrop' not in s
        s = s.replace(a, SCRIPT.encode().replace(b'\n', nl) + a)
        a = b'    AchievementsDisable(1);' + nl; assert s.count(a) == 1
        files[K] = s.replace(a, a + b'    gf_m9_DomInit();' + nl)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
