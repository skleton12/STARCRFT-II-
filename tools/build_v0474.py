#!/usr/bin/env python3
"""0.4.73 -> 0.4.74: 전투 방패 연구 후 병사가 방패를 드는 모습 (3·4번, 사용자 2026-10-23 "방패 업글하면 방패 착용 않하넹").

원인: 전쟁광(액터 KelmorianMiner)·코랄의 후예 액터는 원작 업그레이드 ShieldWall/CombatShield 가 없으면 방패를 숨기는
'Cover' 애니메이션을 틀고, 그 업그레이드가 들어올 때만 지운다. 모드 연구 RM3_Shield 는 이름이 달라 외형이 안 바뀐다.
수정: RM3_Shield 를 마친 뒤 2초 틱마다 레이너의 전쟁광·코랄의 후예에게 한 번 'AnimClear Cover' 를 보내 방패를 보이게 한다.
한 번만 보내도록 표시 없는 표식 버프 RM4_ShieldShown 을 붙인다. 능력치·연구 조건은 그대로.

Usage: python3 tools/build_v0474.py <0.4.73 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.73', b'version=0.4.74'
MAPS = {'TRaynor03': ('gt_m3_Tick_Func', '    if (!runActions || gv_gameOver || gv_inCinematic) { return true; }\n    gf_m3_Skin(10);\n'),
        'TTychus01': ('gt_m4_Tick_Func', '    if (!runActions || gv_gameOver) { return true; }\n    gf_m4_Mercs();\n')}
FN = '''
// 0.4.74: show the shield on Raynor's War Pigs / Sons of Korhal once the mod Combat Shield research is done.
void gf_rmShieldLook () {
    unitgroup g;
    unit u;
    int i;
    int k;
    string[2] kinds;
    if (TechTreeUpgradeCount(1,"RM3_Shield",c_techCountCompleteOnly)==0) { return; }
    kinds[0]="WarPig";
    kinds[1]="RMK_MarineMengsk";
    for (k=0;k<2;k+=1) {
        g=UnitGroup(kinds[k],1,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
        i=UnitGroupCount(g,c_unitCountAll);
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            if (!UnitHasBehavior2(u,"RM4_ShieldShown")) {
                UnitBehaviorAdd(u,"RM4_ShieldShown",u,1);
                libNtve_gf_SendActorMessageToUnit(u,"AnimClear Cover");
            }
        }
    }
}

bool %s (bool testConds,bool runActions) {'''


def script(name, anchor):
    def fn(d):
        t = d.decode('utf-8')
        head = f'\nbool {name} (bool testConds,bool runActions) {{'
        assert t.count(head) == 1 and 'gf_rmShieldLook' not in t
        t = t.replace(head, FN % name)
        assert t.count(anchor) == 1, anchor
        first, rest = anchor.split('\n', 1)
        t = t.replace(anchor, first + '\n    gf_rmShieldLook();\n' + rest)
        return t.encode('utf-8')
    return fn


def behaviors(d):
    t = d.decode('utf-8')
    assert 'id="RM4_ShieldShown"' not in t
    i = t.rindex('</Catalog>')
    return (t[:i] + '<CBehaviorBuff id="RM4_ShieldShown"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" /></CBehaviorBuff>' + t[i:]).encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, (name, anchor) in MAPS.items():
            s, b = f'{m}.SC2Map/mapscript.galaxy', f'{m}.SC2Map/base.sc2data/gamedata/behaviordata.xml'
            files[s] = script(name, anchor)(files[s]); files[b] = behaviors(files[b]); changed |= {s, b}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
