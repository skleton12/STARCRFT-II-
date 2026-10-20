#!/usr/bin/env python3
"""Build CCM 0.4.50 from 0.4.49: 기술실 연구 숨김 2차 진단 (4번, 진단판).

0.4.49(And 피연산자 번호 제거)로도 그대로 숨는다 (사용자 스크린샷 2026-10-20). 충격탄(보임)과 파편탄(숨음)은
요구조건 모양이 같고, 협동전 전투 안정제는 0.4.44에 Not 하나로 바꿨는데도 숨었다 → 요구조건 모양 탓이 아니다.
엔진이 실제로 읽은 값을 본다. 플레이어 1이 병영 기술실을 고르면 (5초에 한 번) 대조군(충격탄·고급 의무관 훈련)과
숨는 연구(파편탄·충격완화복·전투 안정제 두 판)마다 한 줄:
  hid=엔진 숨김, up=능력의 업그레이드 값, st=버튼 상태, rq=버튼 요구조건, ok=업그레이드·요구조건 카탈로그 유효
실험 두 개 (진단판에서만, 맵 시작 때 플레이어 1 값만 바꿈):
  A. 파편탄(Research9) 요구조건을 비운다 → 보이면 요구조건 쪽, 그래도 숨으면 업그레이드·능력 쪽.
  B. 자날판 전투 안정제(Research11) 요구조건을 보이는 고급 의무관 훈련의 것으로 바꾼다.
원인을 찾으면 다음 판에서 진단과 실험을 뺀다.

Usage: python3 tools/build_v0450.py <0.4.49 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.49', b'version=0.4.50'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'
# (ResearchN, short label)
ITEMS = [(6, 'Concussive'), (12, 'AMT'), (9, 'Shrapnel*A'), (10, 'KineticFoam'), (11, 'StabWoL*B'), (15, 'StabCoop')]

DIAG = '''
// 0.4.50 diagnostic: engine-side values of Tech Lab research commands (player 1).
fixed gv_m4_diagNext;

string gf_m4_DiagB (bool b) {
    if (b) { return "1"; }
    return "0";
}

void gf_m4_DiagLine (unit u,int n,string label) {
    string k="InfoArray[Research"+IntToString(n)+"]";
    string up=CatalogFieldValueGet(c_gameCatalogAbil,"RM3_TechResearch",k+".Upgrade",1);
    string rq=CatalogFieldValueGet(c_gameCatalogAbil,"RM3_TechResearch",k+".Button.Requirements",1);
    string s="R"+IntToString(n)+" "+label
        +" hid="+gf_m4_DiagB(UnitCheckAbilCmdState(u,AbilityCommand("RM3_TechResearch",n-1),c_cmdStateHidden))
        +" up="+up
        +" st="+CatalogFieldValueGet(c_gameCatalogAbil,"RM3_TechResearch",k+".Button.State",1)
        +" rq="+rq
        +" ok="+gf_m4_DiagB(CatalogEntryIsValid(c_gameCatalogUpgrade,up))+gf_m4_DiagB(rq=="" || CatalogEntryIsValid(c_gameCatalogRequirement,rq));
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText(s));
}

bool gt_m4_Diag_Func (bool testConds,bool runActions) {
    unit u=EventUnit();
    if (!runActions || UnitGetType(u)!="BarracksTechLab" || UnitGetOwner(u)!=1) { return true; }
    if (GameGetMissionTime()<gv_m4_diagNext) { return true; }
    gv_m4_diagNext=GameGetMissionTime()+5.0;
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("[RM 0.4.50 diag2]"));
%s    return true;
}

'''


def script(d):
    t = d.decode('utf-8')
    lines = ''.join(f'    gf_m4_DiagLine(u,{n},"{lab}");\n' for n, lab in ITEMS)
    anchor = 'void gf_m4_Init () {'
    assert t.count(anchor) == 1 and 'gt_m4_Diag_Func' not in t
    t = t.replace(anchor, DIAG % lines + anchor)
    reg = '    libNtve_gf_SetUpgradeLevelForPlayer(1,"RM4_Shrapnel",0);\n'
    assert t.count(reg) == 1
    t = t.replace(reg, reg
                  + '    t=TriggerCreate("gt_m4_Diag_Func");\n    TriggerAddEventUnitSelected(t,null,1,true);\n'
                  + '    CatalogFieldValueSet(c_gameCatalogAbil,"RM3_TechResearch","InfoArray[Research9].Button.Requirements",1,"");\n'
                  + '    CatalogFieldValueSet(c_gameCatalogAbil,"RM3_TechResearch","InfoArray[Research11].Button.Requirements",1,"RMA_AdvancedMedicTrainingLearn");\n')
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), SCRIPT: script}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
