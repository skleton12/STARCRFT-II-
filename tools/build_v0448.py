#!/usr/bin/env python3
"""Build CCM 0.4.48 from 0.4.47: 기술실 연구 표시 진단 (4번, 데이터 변경 없음).

사용자 보고 (2026-10-20, 0.4.47 새 임무): 파편탄·자날판 전투 안정제가 병영 기술실에 안 보인다.
요구조건·명령 허용·버튼 칸을 정적으로는 모두 확인했고 원인을 못 찾았다 (0.4.38·0.4.44 때도 같은 증상).
그래서 플레이어 1이 병영 기술실을 고르면 RM3_TechResearch 각 연구의 실제 게임 상태를 채팅창에 찍는다:
  업그레이드 단계(대기 포함/완료), 업그레이드 허용, 명령 허용, 엔진이 버튼을 숨겼는지(c_cmdStateHidden),
  그리고 망치 경호대·악마의 개 해금 표식.
5초에 한 번만 찍는다. 화면용 진단이라 문자열 파일은 건드리지 않는다. 게임 데이터·요구조건·배치는 그대로.
원인을 찾으면 다음 판에서 진단을 뺀다.

Usage: python3 tools/build_v0448.py <0.4.47 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.47', b'version=0.4.48'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'
# (command index, upgrade) — RM3_TechResearch ResearchN = index N-1
ITEMS = [(0, 'RM3_Stim1'), (3, 'RM3_Shield'), (4, 'RM3_Laser'), (5, 'PunisherGrenades'), (6, 'RM4_Suppression'),
         (8, 'RM4_Shrapnel'), (9, 'MarauderLifeBoost'), (10, 'StabilizerMedPacks'), (11, 'AdvancedMedicTraining'),
         (12, 'BearclawNozzles'), (13, 'FirebatJuggernautPlating'), (14, 'RMC_StabilizerCoop'), (15, 'RMC_JuggernautCoop')]

DIAG = '''
// 0.4.48 diagnostic: print live Tech Lab research state when player 1 selects a Barracks Tech Lab.
fixed gv_m4_diagNext;

string gf_m4_DiagB (bool b) {
    if (b) { return "1"; }
    return "0";
}

void gf_m4_DiagLine (unit u,int i,string up) {
    abilcmd c=AbilityCommand("RM3_TechResearch",i);
    string s="R"+IntToString(i+1)+" "+up
        +" q="+IntToString(TechTreeUpgradeCount(1,up,c_techCountQueuedOrBetter))
        +" c="+IntToString(TechTreeUpgradeCount(1,up,c_techCountCompleteOnly))
        +" upOK="+gf_m4_DiagB(TechTreeUpgradeIsAllowed(1,up))
        +" cmdOK="+gf_m4_DiagB(TechTreeAbilityIsAllowed(1,c))
        +" hidden="+gf_m4_DiagB(UnitCheckAbilCmdState(u,c,c_cmdStateHidden));
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText(s));
}

bool gt_m4_Diag_Func (bool testConds,bool runActions) {
    unit u=EventUnit();
    if (!runActions || UnitGetType(u)!="BarracksTechLab" || UnitGetOwner(u)!=1) { return true; }
    if (GameGetMissionTime()<gv_m4_diagNext) { return true; }
    gv_m4_diagNext=GameGetMissionTime()+5.0;
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("[RM 0.4.48 diag] hammer="
        +IntToString(TechTreeUpgradeCount(1,"RM4_HammerUnlocked",c_techCountCompleteOnly))
        +" devildog="+IntToString(TechTreeUpgradeCount(1,"RMA_DevilDogUnlocked",c_techCountCompleteOnly))
        +" hasAbil="+gf_m4_DiagB(UnitAbilityExists(u,"RM3_TechResearch"))));
%s    return true;
}

'''


def script(d):
    t = d.decode('utf-8')
    lines = ''.join(f'    gf_m4_DiagLine(u,{i},"{up}");\n' for i, up in ITEMS)
    anchor = 'void gf_m4_Init () {'
    assert t.count(anchor) == 1 and 'gt_m4_Diag_Func' not in t
    t = t.replace(anchor, DIAG % lines + anchor)
    reg = '    libNtve_gf_SetUpgradeLevelForPlayer(1,"RM4_Shrapnel",0);\n'
    assert t.count(reg) == 1
    t = t.replace(reg, reg + '    t=TriggerCreate("gt_m4_Diag_Func");\n    TriggerAddEventUnitSelected(t,null,1,true);\n')
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
