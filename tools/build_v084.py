#!/usr/bin/env python3
"""0.8.3 -> 0.8.4: 강화 벙커 재생 효과 아이콘 (사용자 2026-11-23 "그 아이콘 그걸로 해줘 스투코프에 그 보라색 벙커 그 아이콘").

1~8번: 연구실 강화 벙커(FortifiedBunkerCarapace)를 가진 레이너의 완성된 벙커·보급 벙커에 효과 아이콘 RM8_BunkerRegen
(협동전 스투코프 감염된 벙커 아이콘 btn-building-stukov-infestedbunker.dds, 경로만 연결)을 붙인다. 2초마다 스크립트가 없는
벙커에 붙인다 (0.6.64 고갈되지 않는 자원 아이콘과 같은 방식). 아이콘만이고 재생 효과(0.8.3, 5초 뒤 초당 5)는 업그레이드 그대로.
Game not run.

Usage: python3 tools/build_v084.py <0.8.3 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD

OLD, NEW = b'version=0.8.3', b'version=0.8.4'
ALL = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01']
ICON = 'Assets\\Textures\\btn-building-stukov-infestedbunker.dds'
BEH = (f'<CBehaviorBuff id="RM8_BunkerRegen"><Alignment value="Positive" /><BehaviorFlags index="Permanent" value="1" />'
       f'<InfoIcon value="{ICON}" /><Name value="Behavior/Name/RM8_BunkerRegen" /><Tooltip value="Behavior/Tooltip/RM8_BunkerRegen" /></CBehaviorBuff>')
STRS = {'Behavior/Name/RM8_BunkerRegen': '강화 벙커 /// Fortified Bunker',
        'Behavior/Tooltip/RM8_BunkerRegen': '생명력 +150. 피해를 받지 않고 5초가 지나면 초당 5씩 생명력을 회복합니다. /// +150 life. Regenerates 5 life per second after 5 seconds without taking damage.'}
SCRIPT = '''// 0.8.4 (user 2026-11-23): Fortified Bunker regen icon (Stukov infested bunker icon) on Raynor's finished bunkers.
trigger gt_rm8Bunker;

bool gt_rm8Bunker_Func (bool testConds, bool runActions) {
    unitgroup g;
    unit u;
    int i;
    if (!runActions) { return true; }
    if (TechTreeUpgradeCount(1, "FortifiedBunkerCarapace", c_techCountCompleteOnly) == 0) { return true; }
    g = UnitGroup("Bunker", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))), 0);
    UnitGroupAddUnitGroup(g, UnitGroup("BunkerDepotMengsk", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))), 0));
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {
        u = UnitGroupUnit(g, i);
        if (UnitBehaviorCount(u, "RM8_BunkerRegen") == 0) { UnitBehaviorAdd(u, "RM8_BunkerRegen", u, 1); }
    }
    return true;
}

void gf_rm8BunkerInit () {
    if (gt_rm8Bunker != null) { return; }
    gt_rm8Bunker = TriggerCreate("gt_rm8Bunker_Func");
    TriggerAddEventTimePeriodic(gt_rm8Bunker, 2.0, c_timeGame);
}

'''


def once(t, a, b, what):
    assert t.count(a) == 1, (what, a[:60], t.count(a))
    return t.replace(a, b)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in ALL:
            p = f'{m}.SC2Map/{GD}behaviordata.xml'
            t = files[p].decode('utf-8'); assert 'RM8_BunkerRegen' not in t
            k = t.rindex('</Catalog>'); files[p] = (t[:k] + BEH + t[k:]).encode('utf-8'); changed.add(p)
            p = f'{m}.SC2Map/mapscript.galaxy'
            t = files[p].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
            sc = SCRIPT
            if b'id="BunkerDepotMengsk"' not in files[f'{m}.SC2Map/{GD}unitdata.xml']:
                sc = '\n'.join(l for l in sc.split('\n') if '"BunkerDepotMengsk"' not in l)
            t = once(t, 'void InitMap () {', sc + 'void InitMap () {', m)
            t = once(t, '    AchievementsDisable(1);\n', '    AchievementsDisable(1);\n    gf_rm8BunkerInit();\n', m)
            files[p] = t.replace('\n', nl).encode('utf-8'); changed.add(p)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], STRS); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
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
