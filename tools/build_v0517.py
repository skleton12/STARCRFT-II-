#!/usr/bin/env python3
"""0.5.16 -> 0.5.17: 레드스톤 지원 = 버튼 → 지점 커서 → 클릭한 곳에 소환·투하 (사용자 2026-10-27).

사용자: "커서가 안 나오고 전처럼 버튼만 존재함", "버튼을 누르면 커서가 나오고 커서 위치를 지정해 주면 그곳에 동맹 유닛이
소환(투하)된다", "클릭 로직이랑 비스무리함".

- 0.5.13의 UI 레이아웃 명령 패널은 게임에서 뜨지 않았다 (0.5.16에서 대체 버튼이 나옴 = 패널 연결 실패). 레이아웃 파일과
  패널 연결을 지우고 아이콘 버튼을 바로 띄운다.
- 지점 커서: UISetTargetingOrder만으로는 커서가 안 열렸다. 평소 능력 클릭과 똑같이 만들기 위해, 버튼(또는 Ctrl+V·Ctrl+B)을
  누르면 보이지 않는 시전 유닛 RM5_AllyCaster를 플레이어 선택으로 잡은 뒤(원래 선택은 기억) 그 유닛의 지점 능력으로
  커서를 연다. 시전 유닛의 명령 카드에도 [정화자 지원]·[원시저그 지원] 버튼이 보이므로, 커서가 자동으로 안 열려도 그 카드
  버튼을 누르면 게임 기본 지점 커서(CursorEffect 반경 3 원)가 나온다.
- 지점을 찍거나(능력 시전 또는 지도 클릭) 오른쪽 클릭으로 취소하면, 시전 유닛이 아직 선택돼 있을 때만 원래 선택으로 돌린다.

Usage: python3 tools/build_v0517.py <0.5.16 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.16', b'version=0.5.17'
S = 'TTosh01.SC2Map/mapscript.galaxy'
DROP = {'TTosh01.SC2Map/base.sc2data/ui/layout/RM5Topbar.SC2Layout', 'TTosh01.SC2Map/base.sc2data/ui/layout/DescIndex.SC2Layout'}

SELBACK = '''// 0.5.17: aiming selects the hidden caster (like a normal ability click); afterwards the old selection comes back.
unitgroup gv_m5_selSaved;

void gf_m5_SelBack () {
    int i;
    if (gv_m5_selSaved==null) { return; }
    if (UnitIsSelected(gv_m5_caster,1)) {
        UnitClearSelection(1);
        i=UnitGroupCount(gv_m5_selSaved,c_unitCountAll);
        for (;i>0;i-=1) {
            if (UnitIsAlive(UnitGroupUnit(gv_m5_selSaved,i))) { UnitSelect(UnitGroupUnit(gv_m5_selSaved,i),1,true); }
        }
    }
    gv_m5_selSaved=null;
}

void gf_m5_Aim (int p) {
'''

SCRIPT = [
    ('void gf_m5_Aim (int p) {\n', SELBACK),
    ('    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/CallAim"));\n'
     '    Wait(0.0625,c_timeReal);\n',
     '    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/CallAim"));\n'
     '    if (gv_m5_selSaved==null) { gv_m5_selSaved=UnitGroupCopy(UnitGroupSelected(1)); }\n'
     '    UnitClearSelection(1);\n'
     '    UnitSelect(gv_m5_caster,1,true);\n'
     '    Wait(0.0625,c_timeReal);\n'),
    ('    if (EventUnitAbility()==AbilityCommand("RM5_PrimalSupport",0)) { p=9; }\n    gv_m5_aimP=0;\n',
     '    if (EventUnitAbility()==AbilityCommand("RM5_PrimalSupport",0)) { p=9; }\n    gv_m5_aimP=0;\n    gf_m5_SelBack();\n'),
    ('    gv_m5_aimP=0;\n    gf_m5_CallAt(p,c);\n    return true;\n',
     '    gv_m5_aimP=0;\n    gf_m5_SelBack();\n    gf_m5_CallAt(p,c);\n    return true;\n'),
    ('bool gt_m5_CallCancel_Func (bool testConds,bool runActions) {\n    if (!runActions) { return true; }\n    gv_m5_aimP=0;\n',
     'bool gt_m5_CallCancel_Func (bool testConds,bool runActions) {\n    if (!runActions) { return true; }\n'
     '    if (gv_m5_aimP!=0) { gf_m5_SelBack(); }\n    gv_m5_aimP=0;\n'),
    ('    gv_m5_panelAt=GameGetMissionTime();\n    TriggerExecute(TriggerCreate("gt_m5_CallPanel_Func"),false,false);\n',
     '    // 0.5.17: the layout command panel did not show in game; the icon buttons are the support buttons.\n'
     '    gv_m5_panelAt=GameGetMissionTime()-10.0;\n    gf_m5_CallFallback();\n'),
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert DROP <= set(prev.namelist())
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[S].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        files[S] = sub(t.replace('\r\n', '\n'), SCRIPT).replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    if info.filename not in DROP: out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and set(out.namelist()) == set(prev.namelist()) - DROP
                for n in out.namelist():
                    if n not in (S, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
