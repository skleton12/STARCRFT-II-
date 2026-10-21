#!/usr/bin/env python3
"""Build CCM 0.4.52 from 0.4.51: 기술실 숨김 4차 진단 — 요구조건 조각 시험 (4번, 진단판).

0.4.51 의 '요구조건 노드 바꿔치기'(CatalogFieldValueSet c_gameCatalogRequirement)는 적용되지 않았다
(대조군 고급 의무관 훈련이 그대로 보임) → 결과 무효. 0.4.50 에서 효과가 확인된 방법(능력 버튼의 Requirements
값을 플레이어 1만 바꿈)만 쓴다. 시험용 요구조건 RMT_T1~T6 을 데이터에 추가하고 숨는 연구 칸에 하나씩 붙인다:
  R9  ← T1 Show = And(고급 의무관 훈련 미연구 Not)        : And 노드 자체가 거짓이 되는가
  R10 ← T2 Show = 망치 경호대 해금 (CountUpgrade)
  R11 ← T3 Show = 파편탄 미연구 Not
  R13 ← T4 Show = 협동전 전투 안정제 미연구 Not
  R14 ← T5 Show = And(망치 경호대 해금, 고급 의무관 훈련 미연구 Not)
  R15 ← T6 Show = 동역학 충격완화복 미연구 Not
또 보이는 G 버튼이 우리 충격탄(RM3_TechResearch R6)인지 원작 버튼(BarracksTechLabResearch Research3)인지 찍는다.
진단판이라 시험 칸의 버튼은 원래 조건과 무관하게 보이거나 숨는다. 원인을 찾으면 다음 판에서 모두 뺀다.

Usage: python3 tools/build_v0452.py <0.4.51 zip> <0.4.49 zip (mapscript source)> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.51', b'version=0.4.52'
M4 = 'TTychus01.SC2Map/'
SCRIPT = M4 + 'mapscript.galaxy'
GD = M4 + 'base.sc2data/gamedata/'
# (ResearchN, test id, Show link, label)
TESTS = [(9, 'RMT_T1', 'RMT_T1And', 'And(AMT-Not)'),
         (10, 'RMT_T2', 'RM4_HaveHammer', 'HammerCount'),
         (11, 'RMT_T3', 'RM4_ShrapnelNotQueued', 'Not(Shrapnel)'),
         (13, 'RMT_T4', 'RMC_StabilizerCoopNotQueued', 'Not(StabCoop)'),
         (14, 'RMT_T5', 'RMT_T5And', 'And(Hammer,AMT-Not)'),
         (15, 'RMT_T6', 'RM4_KineticFoamNotQueued', 'Not(KineticFoam)')]
NODES = ('<CRequirementAnd id="RMT_T1And"><OperandArray value="RMA_AdvancedMedicTrainingNotQueued" /></CRequirementAnd>'
         '<CRequirementAnd id="RMT_T5And"><OperandArray value="RM4_HaveHammer" />'
         '<OperandArray value="RMA_AdvancedMedicTrainingNotQueued" /></CRequirementAnd>')
REQS = ''.join(f'<CRequirement id="{t}"><NodeArray index="Show" Link="{link}" /></CRequirement>' for _, t, link, _ in TESTS)

DIAG = '''
// 0.4.52 diagnostic: requirement pieces attached to hidden research slots (player 1, diagnostic only).
fixed gv_m4_diagNext;

string gf_m4_DiagB (bool b) {
    if (b) { return "1"; }
    return "0";
}

void gf_m4_DiagLine (unit u,int n,string label) {
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("R"+IntToString(n)+" "+label
        +" hid="+gf_m4_DiagB(UnitCheckAbilCmdState(u,AbilityCommand("RM3_TechResearch",n-1),c_cmdStateHidden))));
}

bool gt_m4_Diag_Func (bool testConds,bool runActions) {
    unit u=EventUnit();
    if (!runActions || UnitGetType(u)!="BarracksTechLab" || UnitGetOwner(u)!=1) { return true; }
    if (GameGetMissionTime()<gv_m4_diagNext) { return true; }
    gv_m4_diagNext=GameGetMissionTime()+5.0;
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("[RM 0.4.52 diag4] G: ours R6 hid="
        +gf_m4_DiagB(UnitCheckAbilCmdState(u,AbilityCommand("RM3_TechResearch",5),c_cmdStateHidden))
        +" / original hid="+gf_m4_DiagB(UnitCheckAbilCmdState(u,AbilityCommand("BarracksTechLabResearch",2),c_cmdStateHidden))
        +" allowed="+gf_m4_DiagB(TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTechLabResearch",2)))));
%s    return true;
}

'''


def script(d):
    t = d.decode('utf-8')
    lines = ''.join(f'    gf_m4_DiagLine(u,{n},"{lab}");\n' for n, _, _, lab in TESTS)
    sets = ''.join(f'    CatalogFieldValueSet(c_gameCatalogAbil,"RM3_TechResearch","InfoArray[Research{n}].Button.Requirements",1,"{t}");\n'
                   for n, t, _, _ in TESTS)
    anchor = 'void gf_m4_Init () {'
    assert t.count(anchor) == 1 and 'gt_m4_Diag_Func' not in t
    t = t.replace(anchor, DIAG % lines + anchor)
    reg = '    libNtve_gf_SetUpgradeLevelForPlayer(1,"RM4_Shrapnel",0);\n'
    assert t.count(reg) == 1
    t = t.replace(reg, reg + '    t=TriggerCreate("gt_m4_Diag_Func");\n    TriggerAddEventUnitSelected(t,null,1,true);\n' + sets)
    return t.encode('utf-8')


def append(extra):
    def fn(d):
        t = d.decode('utf-8')
        i = t.rindex('</Catalog>')
        return (t[:i] + extra + t[i:]).encode('utf-8')
    return fn


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'requirementnodedata.xml': append(NODES),
       GD + 'requirementdata.xml': append(REQS)}


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
