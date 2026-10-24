#!/usr/bin/env python3
"""0.4.82 -> 0.4.83: 적 생산 속도 5% 빠르게 (3·4번, 사용자 2026-10-24 "우리 적 유닛 생산속도 5% 빠르게").

숨긴 영구 버프 RM_EnemyFastProd(진행·대기열·생성·변태 속도 ×1.05, 원작 시간 증폭과 같은 RateMultiplierArray 방식,
재사용 대기·공격 속도는 그대로)를 2초 틱마다 적 플레이어의 건물과 저그 알·고치에 한 번 붙인다.
대상: 3번 제로 아워 적 2~5번, 4번 어부지리 적 2~6번. 연구·상위 건물 변태도 같은 진행 속도라 함께 5% 빨라진다.
1·2번은 동맹 틱 구조가 달라 이번에 넣지 않았다. 값은 시험값 ENEMY_PROD_SPEED = 1.05.

Usage: python3 tools/build_v0483.py <0.4.82 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.82', b'version=0.4.83'
ENEMY_PROD_SPEED = '1.05'
BUFF = ('<CBehaviorBuff id="RM_EnemyFastProd"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" />'
        '<InfoFlags index="Hidden" value="1" /><Modification>'
        + ''.join(f'<RateMultiplierArray index="{k}" value="{ENEMY_PROD_SPEED}" />' for k in ['Progress', 'Queueable', 'Spawn', 'Morph'])
        + '</Modification></CBehaviorBuff>')
FN = '''
// 0.4.83: enemy production +5% (user 2026-10-24, trial): hidden buff on enemy structures and Zerg eggs/cocoons, once.
void gf_rmFastProdGroup (unitgroup g) {
    unit u;
    int i;
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (!UnitHasBehavior2(u,"RM_EnemyFastProd")) { UnitBehaviorAdd(u,"RM_EnemyFastProd",u,1); }
    }
}

void gf_rmEnemyFastProd (int first, int last) {
    int p;
    for (p=first;p<=last;p+=1) {
        gf_rmFastProdGroup(UnitGroup(null,p,RegionEntireMap(),UnitFilter((1 << c_targetFilterStructure),0,0,(1 << (c_targetFilterDead - 32))),0));
        gf_rmFastProdGroup(UnitGroup("Egg",p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
        gf_rmFastProdGroup(UnitGroup("BanelingCocoon",p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
        gf_rmFastProdGroup(UnitGroup("BroodLordCocoon",p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0));
    }
}
'''
MAPS = {
    'TRaynor03': ('gt_m3_Tick_Func', '    gf_rmShieldLook();\n', 2, 5),
    'TTychus01': ('gt_m4_Tick_Func', '    gf_rmShieldLook();\n', 2, 6),
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, (tick, anchor, a, b) in MAPS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            head = f'\nbool {tick} (bool testConds,bool runActions) {{'
            assert t.count(head) == 1 and t.count(anchor) == 1 and 'gf_rmEnemyFastProd' not in t
            t = t.replace(head, FN + head)
            t = t.replace(anchor, anchor + f'    gf_rmEnemyFastProd({a},{b});\n')
            files[s] = t.encode('utf-8'); changed.add(s)
            bp = f'{m}.SC2Map/base.sc2data/gamedata/behaviordata.xml'
            bt = files[bp].decode('utf-8')
            i = bt.rindex('</Catalog>')
            files[bp] = (bt[:i] + BUFF + bt[i:]).encode('utf-8'); changed.add(bp)
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
