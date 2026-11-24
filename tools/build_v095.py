#!/usr/bin/env python3
"""0.9.4 -> 0.9.5 (사용자 2026-11-24): 기술실 동시 연구 표시, 시간 가속 원작풍, 건물 감염 3중첩·대기 단축.

(1) 2~9번 RM9_TechLab2: 원작 반응로 ReactorQueue처럼 QueueCount 1 + QueueSize 3 (대기열 칸을 늘려 두 연구가 모두 보이게, 시험).
(2) 4~9번 시간 가속 RM9_Chrono: 자날 원작 시간 왜곡(TimeWarpProduction)처럼 TimeScale 1.5(건물 전체가 빨라짐),
    원작 시간 왜곡 연출(TimeWarp 모델)·소리(Obelisk_TimeWarpImpact)를 새 액터로 붙임. 재사용 40 -> 30초(시험값).
(3) 4~9번 건물 감염 RM9_Infest: 같은 건물에 최대 3중첩(행동 MaxStackCount 3, 중첩마다 공생충·회복 따로),
    충전 3회(60초마다 1회 회복), 사용 간격 1초 (시험값).
(4) 4~9번 원시저그 뮤탈(DehakaMutaliskLevel2, 맵에 유닛 액터가 없어 오류 구) 대신 감시군주(Overseer):
    연구 점수 10번째 칸은 감시군주가 없을 때 1기, 있으면 히드라 1기. 히드라 2기 -> 뮤탈 합체는 뺌. 감시군주는 동맹 병력으로 셈.
(5) 9번 망자의 항구: 올란(2번) 본진 수비 강화 — 시작 때 벙커(해병 4) 2/3/4/4, 공성 전차(시즈) 1/2/3/4,
    미사일 포탑 1/1/2/2, 수비 병력 해병 6/8/12/16·불곰 2/3/4/6·골리앗 1/1/2/3 (스크립트 조종이라 공세에 안 빠짐),
    90초마다 수비 병력만 처음 수까지 보충(레이너·동맹 병력이 본진(50,125) 25칸 안에 있으면 미룸, 용병 요새가 서 있을 때만). 모두 시험값. Game not run.

Usage: python3 tools/build_v095.py <0.9.4 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.9.4', b'version=0.9.5'
LAB_MAPS = ['TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02']
ABIL_MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02']
G = '{}.SC2Map/base.sc2data/gamedata/{}'
LANGS = ['dede', 'enus', 'eses', 'esmx', 'frfr', 'itit', 'kokr', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']

LAB_OLD = b'<CBehaviorBuff id="RM9_TechLab2"><BehaviorFlags index="Permanent" value="1" /><InfoFlags index="Hidden" value="1" /><Modification QueueCount="1" /></CBehaviorBuff>'
LAB_NEW = b'<CBehaviorBuff id="RM9_TechLab2"><BehaviorFlags index="Permanent" value="1" /><InfoFlags index="Hidden" value="1" /><Modification QueueCount="1" QueueSize="3" /></CBehaviorBuff>'
CH_OLD = b'<Modification><RateMultiplierArray index="Charge" value="1.5" /><RateMultiplierArray index="Cooldown" value="1.5" /><RateMultiplierArray index="Morph" value="1.5" /><RateMultiplierArray index="Progress" value="1.5" /><RateMultiplierArray index="Queueable" value="1.5" /><RateMultiplierArray index="Spawn" value="1.5" /><RateMultiplierArray index="Creep" value="1.5" /></Modification>'
CH_NEW = b'<Modification TimeScale="1.5" /><BehaviorCategories index="Fast" value="1" />'
CA_OLD = b'<CAbilEffectTarget id="RM9_Chrono"><Effect index="0" value="RM9_ChronoAB" /><Cost><Cooldown TimeUse="40" /></Cost>'
CA_NEW = b'<CAbilEffectTarget id="RM9_Chrono"><Effect index="0" value="RM9_ChronoAB" /><Cost><Cooldown TimeUse="30" /></Cost>'
IA_OLD = b'<CAbilEffectTarget id="RM9_Infest"><Effect index="0" value="RM9_InfestSet" /><Cost><Cooldown TimeUse="90" /></Cost>'
IA_NEW = b'<CAbilEffectTarget id="RM9_Infest"><Effect index="0" value="RM9_InfestSet" /><Cost><Charge CountMax="3" CountStart="3" CountUse="1" TimeUse="60" /><Cooldown TimeUse="1" /></Cost>'
STACK = b'<TimeScaleSource Value="Global" /><Duration value="20" /><Period value="2" />'
STACK_NEW = b'<MaxStackCount value="3" /><TimeScaleSource Value="Global" /><Duration value="20" /><Period value="2" />'
ACTORS = (b'<CActorModel id="RM9_ChronoFX" parent="ModelAnimationStyleContinuous"><AutoScaleFactor value="0.750000" />'
          b'<Inherits index="BaseModelScale" value="1" /><Inherits index="CloakEffect" value="1" /><Inherits index="Scale" value="1" />'
          b'<On Terms="ActorCreation" Send="SetScale 0.300000" /><On Terms="Behavior.RM9_Chrono.On" Send="Create" />'
          b'<On Terms="Behavior.RM9_Chrono.Off" Send="Destroy" /><Model value="TimeWarp" /><Host Subject="_Unit" /></CActorModel>'
          b'<CActorSound id="RM9_ChronoSound" parent="SoundOneShot"><Sound value="Obelisk_TimeWarpImpact" />'
          b'<On Terms="Behavior.RM9_Chrono.On" Send="Create" /><Host Subject="_Unit" /></CActorSound>\n</Catalog>')
MERC_MAPS = ABIL_MAPS
PFX = {'TTychus01': 'm4', 'TTosh01': 'm5', 'THanson01': 'm6', 'TTosh02': 'm7', 'THorner01': 'm8', 'THorner02': 'm9'}
FORT = r'''
// 0.9.5: Orlan main base hard defence (user 2026-11-24 "올란 본기지 빡세게 방어", trial values).
unitgroup gv_m9_orlanGuards;
int gv_m9_orlanMar;
int gv_m9_orlanMrd;
int gv_m9_orlanGol;
point gf_m9_OrlanSpot (string k, point want, fixed r) {
    point home = gf_rmVHTarget();
    point pt = UnitTypePlacementFromPoint(k, 2, want, r);
    if (pt == null || !PointPathingPassable(pt) || DistanceBetweenPoints(pt, want) > r) { return null; }
    if (home != null && !PointPathingIsConnected(pt, home)) { return null; }
    return pt;
}
void gf_m9_OrlanMake (string k, int n, point want, bool guard) {
    point pt; unitgroup g; int i;
    for (i = 0; i < n; i += 1) {
        pt = gf_m9_OrlanSpot(k, want, 6.0);
        if (pt == null) { return; }
        g = UnitCreate(1, k, c_unitCreateIgnorePlacement, 2, pt, 270.0);
        if (UnitGroupCount(g, c_unitCountAll) == 0) { return; }
        AISetGroupScriptControlled(g, true);
        if (guard) { UnitGroupAddUnitGroup(gv_m9_orlanGuards, g); }
        if (k == "Bunker") { UnitCargoCreate(UnitGroupUnit(g, 1), "Marine", 4); }
    }
}
void gf_m9_OrlanFort () {
    int b = libNtve_gf_DifficultyValueInt(2, 3, 4, 4);
    int t = libNtve_gf_DifficultyValueInt(1, 2, 3, 4);
    int m = libNtve_gf_DifficultyValueInt(1, 1, 2, 2);
    gv_m9_orlanGuards = UnitGroupEmpty();
    gv_m9_orlanMar = libNtve_gf_DifficultyValueInt(6, 8, 12, 16);
    gv_m9_orlanMrd = libNtve_gf_DifficultyValueInt(2, 3, 4, 6);
    gv_m9_orlanGol = libNtve_gf_DifficultyValueInt(1, 1, 2, 3);
    if (b >= 1) { gf_m9_OrlanMake("Bunker", 1, Point(44.0, 116.0), false); }
    if (b >= 2) { gf_m9_OrlanMake("Bunker", 1, Point(55.0, 110.0), false); }
    if (b >= 3) { gf_m9_OrlanMake("Bunker", 1, Point(61.0, 121.0), false); }
    if (b >= 4) { gf_m9_OrlanMake("Bunker", 1, Point(37.0, 108.0), false); }
    if (t >= 1) { gf_m9_OrlanMake("SiegeTankSieged", 1, Point(46.0, 121.0), false); }
    if (t >= 2) { gf_m9_OrlanMake("SiegeTankSieged", 1, Point(53.0, 120.0), false); }
    if (t >= 3) { gf_m9_OrlanMake("SiegeTankSieged", 1, Point(40.0, 119.0), false); }
    if (t >= 4) { gf_m9_OrlanMake("SiegeTankSieged", 1, Point(58.0, 126.0), false); }
    if (m >= 1) { gf_m9_OrlanMake("MissileTurret", 1, Point(50.0, 114.0), false); }
    if (m >= 2) { gf_m9_OrlanMake("MissileTurret", 1, Point(42.0, 112.0), false); }
    gf_m9_OrlanMake("Marine", gv_m9_orlanMar, Point(48.0, 118.0), true);
    gf_m9_OrlanMake("Marauder", gv_m9_orlanMrd, Point(50.0, 120.0), true);
    gf_m9_OrlanMake("Goliath", gv_m9_orlanGol, Point(46.0, 119.0), true);
}
int gf_m9_OrlanCount (string k) {
    return UnitGroupCount(UnitGroupFilter(k, 2, gv_m9_orlanGuards, UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive);
}
'''
FORT_TRIG = r'''
trigger gt_m9_OrlanRefill;
bool gt_m9_OrlanRefill_Func (bool testConds, bool runActions) {
    point a = Point(48.0, 118.0);
    if (!runActions || !gv_m9_started || gv_m9_orlanGuards == null) { return true; }
    if (UnitGroupCount(UnitGroup("MercenaryFortress", 2, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) == 0) { return true; }
    if (UnitGroupCount(UnitGroup(null, 1, RegionCircle(Point(50.0, 125.0), 25.0), UnitFilter(0, 0, (1 << c_targetFilterStructure), (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive)
      + UnitGroupCount(UnitGroup(null, 8, RegionCircle(Point(50.0, 125.0), 25.0), UnitFilter(0, 0, (1 << c_targetFilterStructure), (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive)
      + UnitGroupCount(UnitGroup(null, 9, RegionCircle(Point(50.0, 125.0), 25.0), UnitFilter(0, 0, (1 << c_targetFilterStructure), (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) > 0) { return true; }
    gf_m9_OrlanMake("Marine", gv_m9_orlanMar - gf_m9_OrlanCount("Marine"), a, true);
    gf_m9_OrlanMake("Marauder", gv_m9_orlanMrd - gf_m9_OrlanCount("Marauder"), Point(50.0, 120.0), true);
    gf_m9_OrlanMake("Goliath", gv_m9_orlanGol - gf_m9_OrlanCount("Goliath"), Point(46.0, 119.0), true);
    return true;
}
'''
OV = r'''
// 0.9.5: the primal Overseer (detector) has no attack; keep it moving with the primal army.
trigger gt_XX_OvFollow;
bool gt_XX_OvFollow_Func (bool testConds, bool runActions) {
    unitgroup ov;
    unitgroup a;
    unit u;
    unit t;
    int i;
    if (!runActions) { return true; }
    ov = UnitGroup("Overseer", 9, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0);
    if (UnitGroupCount(ov, c_unitCountAlive) == 0) { return true; }
    a = gf_XX_Army(9);
    t = null;
    for (i = UnitGroupCount(a, c_unitCountAll); i > 0; i -= 1) {
        if (UnitGetType(UnitGroupUnit(a, i)) != "Overseer") { t = UnitGroupUnit(a, i); break; }
    }
    if (t == null) { return true; }
    for (i = UnitGroupCount(ov, c_unitCountAll); i > 0; i -= 1) {
        u = UnitGroupUnit(ov, i);
        if (DistanceBetweenPoints(UnitGetPosition(u), UnitGetPosition(t)) > 4.0) {
            UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("move", 0), UnitGetPosition(t)), c_orderQueueReplace);
        }
    }
    return true;
}
'''
STR = {
 b'Button/Tooltip/RM9_Chrono': ('레이너의 건물 하나를 20초 동안 50% 빠르게 합니다(원작 시간 왜곡과 같음: 생산·연구·능력 모두). 재사용 대기시간 30초.',
                               "Makes one of Raynor's structures work 50% faster for 20 seconds (like the original Time Warp: production, research and abilities). Cooldown 30 seconds."),
 b'Behavior/Tooltip/RM9_Chrono': ('모든 동작 속도 +50%.', 'All actions 50% faster.'),
 b'Button/Tooltip/RM9_Infest': ('건물 하나를 20초 동안 감염시킵니다. 2초마다 공생충 2기가 나옵니다. 적 건물은 능력을 쓰지 못하고, 아군 건물은 초당 생명력을 25 회복합니다. 같은 건물에 3번까지 겹칩니다(겹칠수록 공생충·회복 증가). 충전 3회, 60초마다 1회 회복.',
                              'Infests a structure for 20 seconds, spawning 2 Broodlings every 2 seconds. Enemy structures cannot use abilities; friendly structures regenerate 25 life per second. Stacks up to 3 times on the same structure. 3 charges, one recharges every 60 seconds.'),
}


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = set()
        def rep(k, a, b, n=1):
            t = files[k]; assert t.count(a) == n, (k, a[:60], t.count(a))
            files[k] = t.replace(a, b); changed.add(k)
        rep('metadata.txt', OLD, NEW)
        for m in LAB_MAPS:
            rep(G.format(m, 'behaviordata.xml'), LAB_OLD, LAB_NEW)
        for m in ABIL_MAPS:
            b = G.format(m, 'behaviordata.xml')
            rep(b, CH_OLD, CH_NEW); rep(b, STACK, STACK_NEW, 2)
            a = G.format(m, 'abildata.xml'); rep(a, CA_OLD, CA_NEW); rep(a, IA_OLD, IA_NEW)
            ac = G.format(m, 'actordata.xml')
            assert b'RM9_ChronoFX' not in files[ac] and files[ac].rstrip().endswith(b'</Catalog>')
            files[ac] = files[ac].rstrip()[:-len(b'</Catalog>')] + ACTORS + b'\n'; changed.add(ac)
            for lang in LANGS:
                k = f'{m}.SC2Map/{lang}.sc2data/localizeddata/gamestrings.txt'
                lines = files[k].split(b'\n'); hit = set()
                for i, ln in enumerate(lines):
                    key = ln.split(b'=', 1)[0]
                    if key in STR:
                        ko, en = STR[key]
                        v = f'{ko} /// {en}' if lang == 'kokr' else en
                        lines[i] = key + b'=' + v.encode(); hit.add(key)
                assert hit == set(STR), (k, hit)
                files[k] = b'\n'.join(lines); changed.add(k)
        for m in MERC_MAPS:
            x = PFX[m]; k = f'{m}.SC2Map/mapscript.galaxy'
            rep(k, f'if (k==10) {{ gf_{x}_SupAdd(p,"DehakaMutaliskLevel2"); }}'.encode(),
                (f'if (k==10) {{ if (UnitGroupCount(UnitGroup("Overseer",p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0),c_unitCountAlive)==0) '
                 f'{{ gf_{x}_SupAdd(p,"Overseer"); }} else {{ gf_{x}_SupAdd(p,"DehakaHydraliskLevel2"); }} }}').encode())
            NL = b'\r\n' if b'\r\n' in files[k] else b'\n'
            rep(k, (f'if (gf_{x}_Unl(4) && (!gf_{x}_Unl(6) || ModI(gv_{x}_turn9,2)==0)) {{ gf_{x}_MergeOne("DehakaHydraliskLevel2","PrimalHydraliskToMutalisk"); }}').encode() + NL + b'    else if (',
                b'// 0.9.5: no primal Mutalisk merge (missing actor); Impaler merge stands alone.' + NL + b'    if (')
            rep(k, NL + b'void InitMap () {', OV.replace('XX', x).encode().replace(b'\n', NL) + NL + b'void InitMap () {')
            rep(k, b'    AchievementsDisable(1);' + NL, b'    AchievementsDisable(1);' + NL + (f'    gt_{x}_OvFollow = TriggerCreate("gt_{x}_OvFollow_Func");\n    TriggerAddEventTimePeriodic(gt_{x}_OvFollow, 2.0, c_timeGame);\n').encode().replace(b'\n', NL))
            rep(k, b'if (t=="Probe" || t=="DehakaDrone"', b'if (t=="Overseer") { return true; }\n    if (t=="Probe" || t=="DehakaDrone"')
        k = 'THorner02.SC2Map/mapscript.galaxy'
        N = b'\r\n'
        c = lambda t: t.encode().replace(b'\n', N)
        rep(k, N + b'void gf_m9_Start () {', c(FORT) + N + b'void gf_m9_Start () {')
        rep(k, b'    gf_m9_EnemyRules();' + N + b'    gf_m9_ZergBasesInit();', b'    gf_m9_EnemyRules();' + N + b'    gf_m9_OrlanFort();' + N + b'    gf_m9_ZergBasesInit();')
        rep(k, N + b'void InitMap () {', c(FORT_TRIG) + N + b'void InitMap () {')
        rep(k, b'    AchievementsDisable(1);' + N, b'    AchievementsDisable(1);' + N + c('    gt_m9_OrlanRefill = TriggerCreate("gt_m9_OrlanRefill_Func");\n    TriggerAddEventTimePeriodic(gt_m9_OrlanRefill, 90.0, c_timeGame);\n'))
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
    print(out, len(changed))


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
