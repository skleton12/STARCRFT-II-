#!/usr/bin/env python3
"""Build CCM 0.4.53 from 0.4.52: 기술실 숨김 5차 진단 — 요구조건 노드 종류별 동작 확인 (4번, 진단판).

0.4.52 결과 (사용자 스크린샷 2026-10-21): 보이던 G 는 원작 충격탄 버튼(BarracksTechLabResearch Research3)이었고
우리 충격탄(R6)도 숨어 있었다. Not 하나짜리 조건(파편탄·협동전 안정제·충격완화복)은 보이고,
And(되는 Not 하나)·And(망치 해금, 되는 Not)·망치 해금 개수 노드 단독은 숨는다 → 이 맵에서 And 가 거짓으로 계산된다.
5차: 결과가 뻔한 시험 업그레이드 RMT_Have(시작 때 1단계)·RMT_None(0)으로 노드 종류마다 확인한다.
  R9  개수(Have)                  → 보여야 정상
  R10 Not(개수(Have)) [index 0]    → 숨어야 정상
  R11 And(개수(Have))             → 보여야 정상
  R13 Or(개수(Have))              → 보여야 정상
  R14 Not(Or(Not(개수(Have))))    → 보여야 정상 (And 대신 쓸 수 있는 형태)
  R15 Not(개수(None))             → 보여야 정상
진단판 한정. 원인을 찾으면 다음 판에서 모두 뺀다.

Usage: python3 tools/build_v0453.py <0.4.52 zip> <0.4.49 zip (mapscript source)> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.52', b'version=0.4.53'
M4 = 'TTychus01.SC2Map/'
SCRIPT = M4 + 'mapscript.galaxy'
GD = M4 + 'base.sc2data/gamedata/'
# (ResearchN, test id, Show link, label)
TESTS = [(9, 'RMT_U1', 'RMT_CHave', 'Count(Have) want0'),
         (10, 'RMT_U2', 'RMT_NotHave', 'Not(Count(Have)) want1'),
         (11, 'RMT_U3', 'RMT_AndHave', 'And(Count(Have)) want0'),
         (13, 'RMT_U4', 'RMT_OrHave', 'Or(Count(Have)) want0'),
         (14, 'RMT_U5', 'RMT_NotOrNotHave', 'Not(Or(Not(Have))) want0'),
         (15, 'RMT_U6', 'RMT_NotNone', 'Not(Count(None)) want0')]
NODES = ('<CRequirementCountUpgrade id="RMT_CHave"><Count Link="RMT_Have" State="CompleteOnly" /></CRequirementCountUpgrade>'
         '<CRequirementCountUpgrade id="RMT_CNone"><Count Link="RMT_None" State="CompleteOnly" /></CRequirementCountUpgrade>'
         '<CRequirementNot id="RMT_NotHave"><OperandArray index="0" value="RMT_CHave" /></CRequirementNot>'
         '<CRequirementNot id="RMT_NotNone"><OperandArray index="0" value="RMT_CNone" /></CRequirementNot>'
         '<CRequirementAnd id="RMT_AndHave"><OperandArray value="RMT_CHave" /></CRequirementAnd>'
         '<CRequirementOr id="RMT_OrHave"><OperandArray value="RMT_CHave" /></CRequirementOr>'
         '<CRequirementOr id="RMT_OrNotHave"><OperandArray value="RMT_NotHave" /></CRequirementOr>'
         '<CRequirementNot id="RMT_NotOrNotHave"><OperandArray index="0" value="RMT_OrNotHave" /></CRequirementNot>')
UPGRADES = '<CUpgrade id="RMT_Have"><MaxLevel value="1" /></CUpgrade><CUpgrade id="RMT_None"><MaxLevel value="1" /></CUpgrade>'
REQS = ''.join(f'<CRequirement id="{t}"><NodeArray index="Show" Link="{link}" /></CRequirement>' for _, t, link, _ in TESTS)

DIAG = '''
// 0.4.53 diagnostic: requirement node kinds with known-value test upgrades (player 1, diagnostic only).
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
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("[RM 0.4.53 diag5] Have="
        +IntToString(TechTreeUpgradeCount(1,"RMT_Have",c_techCountCompleteOnly))
        +" None="+IntToString(TechTreeUpgradeCount(1,"RMT_None",c_techCountCompleteOnly))
        +" hammer="+IntToString(TechTreeUpgradeCount(1,"RM4_HammerUnlocked",c_techCountCompleteOnly))));
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
    t = t.replace(reg, reg + '    TechTreeUpgradeAllow(1,"RMT_Have",true);\n    TechTreeUpgradeAddLevel(1,"RMT_Have",1);\n    t=TriggerCreate("gt_m4_Diag_Func");\n    TriggerAddEventUnitSelected(t,null,1,true);\n' + sets)
    return t.encode('utf-8')


def append(extra):
    def fn(d):
        t = d.decode('utf-8')
        i = t.rindex('</Catalog>')
        return (t[:i] + extra + t[i:]).encode('utf-8')
    return fn


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'requirementnodedata.xml': append(NODES),
       GD + 'requirementdata.xml': append(REQS), GD + 'upgradedata.xml': append(UPGRADES)}


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
