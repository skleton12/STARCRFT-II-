#!/usr/bin/env python3
"""0.4.89 -> 0.4.90: 동맹 자동 건설 철회, 플레이어가 짓고 돈은 동맹 것 (3·4번, 사용자 2026-10-24).

사용자: "막 짓는다. 그냥 내가 짓게 해줘. 돈은 동맹 걸로 사용."
1) 0.4.89 자동 건설(gf_rmAutoBuild)을 뺀다. 핑은 공격 그대로.
2) 정산(B안): 플레이어가 동맹 일꾼으로 지은 동맹 건물이 건설을 시작했을 때, 그 순간 레이너 돈이 건물 값만큼 빠졌으면
   레이너가 낸 것으로 보고 동맹 돈에서 그만큼 레이너에게 돌려준다. 동맹 돈이 모자라면 그 건물을 취소하고 레이너에게 환불한다
   ("동맹 자원이 부족합니다" 안내). 엔진이 처음부터 동맹 돈을 썼다면 레이너 돈이 줄지 않으므로 아무것도 하지 않는다.
   판별: 레이너 광물·가스가 줄어든 양과 시각을 기록해, 건설 시작 ±0.25초 안에 건물 값과 같은 양이 줄었는지 본다.

Usage: python3 tools/build_v0490.py <0.4.89 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines
from build_v0489 import FN as AUTO_FN, MAPS as AUTO_MAPS

OLD, NEW = b'version=0.4.89', b'version=0.4.90'
FN = '''
// 0.4.90: the player builds with ally workers and the ally pays (user 2026-10-24). If the engine took Raynor's money
// for an ally structure, move that cost from the ally back to Raynor; if the ally cannot pay, cancel and refund.
int gv_rmP1Min;
int gv_rmP1Gas;
int gv_rmP1MinDrop;
int gv_rmP1GasDrop;
fixed gv_rmP1MinAt;
fixed gv_rmP1GasAt;
int gv_rmPayA;
int gv_rmPayB;

bool gt_rmP1Money_Func (bool testConds,bool runActions) {
    int m=PlayerGetPropertyInt(1,c_playerPropMinerals);
    int g=PlayerGetPropertyInt(1,c_playerPropVespene);
    if (!runActions) { return true; }
    if (m<gv_rmP1Min) { gv_rmP1MinDrop=gv_rmP1Min-m; gv_rmP1MinAt=GameGetMissionTime(); }
    if (g<gv_rmP1Gas) { gv_rmP1GasDrop=gv_rmP1Gas-g; gv_rmP1GasAt=GameGetMissionTime(); }
    gv_rmP1Min=m;
    gv_rmP1Gas=g;
    return true;
}

bool gf_rmPaidBy1 (int cost, int drop, fixed at, fixed t) {
    if (cost<=0) { return true; }
    return drop==cost && AbsF(at-t)<=0.25;
}

bool gt_rmAllyBuildPay_Func (bool testConds,bool runActions) {
    unit u=EventUnitProgressUnit();
    int p=UnitGetOwner(u);
    string k=UnitGetType(u);
    int m=UnitTypeGetCost(k,c_unitCostMinerals);
    int g=UnitTypeGetCost(k,c_unitCostVespene);
    fixed t=GameGetMissionTime();
    if (!runActions || (p!=gv_rmPayA && p!=gv_rmPayB) || (m<=0 && g<=0)) { return true; }
    Wait(0.0625,c_timeGame);
    if (!gf_rmPaidBy1(m,gv_rmP1MinDrop,gv_rmP1MinAt,t) || !gf_rmPaidBy1(g,gv_rmP1GasDrop,gv_rmP1GasAt,t)) { return true; }
    gv_rmP1MinAt=-10.0;
    gv_rmP1GasAt=-10.0;
    if (PlayerGetPropertyInt(p,c_playerPropMinerals)<m || PlayerGetPropertyInt(p,c_playerPropVespene)<g) {
        if (UnitIsAlive(u)) { UnitRemove(u); }
        UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaError,StringExternal("rm/AllyNoMoney"));
    }
    else {
        PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,m);
        PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);
    }
    PlayerModifyPropertyInt(1,c_playerPropMinerals,c_playerPropOperAdd,m);
    PlayerModifyPropertyInt(1,c_playerPropVespene,c_playerPropOperAdd,g);
    return true;
}

void gf_rmPayInit (int a, int b) {
    trigger t;
    gv_rmPayA=a;
    gv_rmPayB=b;
    gv_rmP1MinAt=-10.0;
    gv_rmP1GasAt=-10.0;
    gv_rmP1Min=PlayerGetPropertyInt(1,c_playerPropMinerals);
    gv_rmP1Gas=PlayerGetPropertyInt(1,c_playerPropVespene);
    t=TriggerCreate("gt_rmP1Money_Func");
    TriggerAddEventPlayerPropChange(t,1,c_playerPropMinerals);
    TriggerAddEventPlayerPropChange(t,1,c_playerPropVespene);
    t=TriggerCreate("gt_rmAllyBuildPay_Func");
    TriggerAddEventUnitConstructProgress(t,null,c_unitProgressStageStart);
}
'''
MAPS = {'TRaynor03': (10, 11), 'TTychus01': (8, 9)}
STR = {'rm/AllyNoMoney': '동맹 자원이 부족해 건설을 취소했습니다. /// Not enough ally resources; construction cancelled.'}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, (a, b) in MAPS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            tick, anchor, call = AUTO_MAPS[m]
            assert t.count(AUTO_FN) == 1 and t.count(call) == 1
            t = t.replace(AUTO_FN, FN).replace(call, '')
            spend = f'    PlayerSetAlliance({b},c_allianceIdSpend,1,true);\n'
            assert t.count(spend) == 1 and 'gf_rmAutoBuild' not in t
            t = t.replace(spend, spend + f'    gf_rmPayInit({a},{b});\n')
            files[s] = t.encode('utf-8'); changed.add(s)
            for loc in ('kokr',) + LOCALES:
                p = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'
                vals = STR if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in STR.items()}
                files[p] = update_lines(files[p], vals); changed.add(p)
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
