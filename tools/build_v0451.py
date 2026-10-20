#!/usr/bin/env python3
"""Build CCM 0.4.51 from 0.4.50: 기술실 숨김 3차 진단 + 파편탄 아이콘 (4번, 진단판).

0.4.50 결과 (사용자 스크린샷 2026-10-20): 파편탄 요구조건을 비우면 보이고(실험 A), 자날판 전투 안정제에 고급 의무관
훈련의 요구조건을 넣으면 보인다(실험 B). 무기고 구매와 무관(사용자: 무기고 연구 안 함). → 원인은 우리 표시 조건.
충격탄 Show 와 파편탄 Show 는 모양이 같고 '업그레이드를 몇 개 가졌나' 세는 노드만 다르다.
3차: 각 연구의 Show 를 그 세는 노드(…Queued, QueuedOrBetter) 하나로 바꿔치기한다 (플레이어 1, 진단판 한정).
  hid=0 이면 엔진이 그 업그레이드를 이미 1 이상으로 센다는 뜻. 대조군 충격탄·고급 의무관 훈련은 hid=1 이어야 정상.
  줄마다 스크립트 쪽 개수(q)와 엔진이 읽은 노드의 Count.Link/State 도 찍는다.
사용자 요청: 파편탄 아이콘을 보내 준 그림(폭발성 파편탄, btn-upgrade-terran-explosiveshrapnelshells)으로 바꾼다.

Usage: python3 tools/build_v0451.py <0.4.50 zip> <0.4.49 zip (mapscript source)> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.50', b'version=0.4.51'
M4 = 'TTychus01.SC2Map/'
SCRIPT = M4 + 'mapscript.galaxy'
GD = M4 + 'base.sc2data/gamedata/'
ICON_OLD = b'Assets\\Textures\\btn-techupgrade-terran-clusterwarheads.dds'
ICON_NEW = b'Assets\\Textures\\btn-upgrade-terran-explosiveshrapnelshells.dds'
# (ResearchN, label, CRequirement, count node)
ITEMS = [(6, 'Concussive(ctl)', 'RM4_ConcussiveLearn', 'RM4_ConcussiveQueued'),
         (12, 'AMT(ctl)', 'RMA_AdvancedMedicTrainingLearn', 'RMA_AdvancedMedicTrainingQueued'),
         (9, 'Shrapnel', 'RM4_ShrapnelLearn', 'RM4_ShrapnelQueued'),
         (10, 'KineticFoam', 'RM4_KineticFoamLearn', 'RM4_KineticFoamQueued'),
         (11, 'StabWoL', 'RMA_StabilizerMedPacksLearn', 'RMA_StabilizerMedPacksQueued'),
         (15, 'StabCoop', 'RMC_StabilizerCoopLearn', 'RMC_StabilizerCoopQueued')]

DIAG = '''
// 0.4.51 diagnostic: each research Show is swapped to its own upgrade-count node (player 1, diagnostic only).
// hid=0 means the engine counts that upgrade as already >= 1.
fixed gv_m4_diagNext;

string gf_m4_DiagB (bool b) {
    if (b) { return "1"; }
    return "0";
}

void gf_m4_DiagLine (unit u,int n,string label,string node) {
    string up=CatalogFieldValueGet(c_gameCatalogAbil,"RM3_TechResearch","InfoArray[Research"+IntToString(n)+"].Upgrade",1);
    string s="R"+IntToString(n)+" "+label
        +" hid="+gf_m4_DiagB(UnitCheckAbilCmdState(u,AbilityCommand("RM3_TechResearch",n-1),c_cmdStateHidden))
        +" q="+IntToString(TechTreeUpgradeCount(1,up,c_techCountQueuedOrBetter))
        +" node="+CatalogFieldValueGet(c_gameCatalogRequirementNode,node,"Count.Link",1)
        +"/"+CatalogFieldValueGet(c_gameCatalogRequirementNode,node,"Count.State",1);
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText(s));
}

bool gt_m4_Diag_Func (bool testConds,bool runActions) {
    unit u=EventUnit();
    if (!runActions || UnitGetType(u)!="BarracksTechLab" || UnitGetOwner(u)!=1) { return true; }
    if (GameGetMissionTime()<gv_m4_diagNext) { return true; }
    gv_m4_diagNext=GameGetMissionTime()+5.0;
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("[RM 0.4.51 diag3] hid=0 -> counted as >=1"));
%s    return true;
}

'''


def script(d):
    t = d.decode('utf-8')
    lines = ''.join(f'    gf_m4_DiagLine(u,{n},"{lab}","{node}");\n' for n, lab, _, node in ITEMS)
    sets = ''.join(f'    CatalogFieldValueSet(c_gameCatalogRequirement,"{req}","NodeArray[Show].Link",1,"{node}");\n'
                   for _, _, req, node in ITEMS)
    anchor = 'void gf_m4_Init () {'
    assert t.count(anchor) == 1 and 'gt_m4_Diag_Func' not in t
    t = t.replace(anchor, DIAG % lines + anchor)
    reg = '    libNtve_gf_SetUpgradeLevelForPlayer(1,"RM4_Shrapnel",0);\n'
    assert t.count(reg) == 1
    t = t.replace(reg, reg + '    t=TriggerCreate("gt_m4_Diag_Func");\n    TriggerAddEventUnitSelected(t,null,1,true);\n' + sets)
    return t.encode('utf-8')


def icon(d):
    assert d.count(ICON_OLD) == 1
    return d.replace(ICON_OLD, ICON_NEW)


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'buttondata.xml': icon, GD + 'upgradedata.xml': icon}


def build(source, script_src, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(script_src) as base:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert b'version=0.4.49' in base.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        files[SCRIPT] = script(base.read(SCRIPT))
        changed = set(FIX) | {SCRIPT}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('script_src', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.script_src, a.output)
