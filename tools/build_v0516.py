#!/usr/bin/env python3
"""0.5.15 -> 0.5.16: 레드스톤 스크립트 컴파일 오류 수정 (사용자 2026-10-27 "또 로직 망가뜨렸네").

원인: 0.5.13이 `int gv_m5_callPanel;`을 새로 선언했는데 같은 전역 변수가 0.5.7부터 이미 선언돼 있었다.
Galaxy는 전역 변수를 두 번 선언하면 맵 스크립트 전체를 컴파일하지 못한다 (동맹·적 강화·승리 조건·지원이 통째로 안 돎;
0.5.7 gv_m5_callReady와 같은 종류). 0.5.13·0.5.14·0.5.15 모두 해당. 나중에 붙은 선언을 지운다.
check_release에 '전역 변수 두 번 선언·함수 두 번 정의' 검사를 추가했다 (0.5.15에서 이 1건을 잡는 것 확인).

덧붙여 상단 패널 연결이 게임에서 실패해도 다른 로직이 멈추지 않게 한다:
- 동맹 준비(gv_m5_ready)를 패널 만들기보다 먼저 켠다.
- 명령 패널 연결은 따로 실행(TriggerExecute)하고, 끝까지 되면 gv_m5_panelOk. 3초 뒤에도 안 되면 0.5.11식 아이콘 버튼을
  대신 띄운다 (누르고 지도 클릭으로 지점, 사용자 확인으로 동작함).
- 0.5초 타이머는 패널이 된 뒤에만 패널 표시를 바꾼다.

Usage: python3 tools/build_v0516.py <0.5.15 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.15', b'version=0.5.16'
S = 'TTosh01.SC2Map/mapscript.galaxy'

PANEL_OLD = ('    DialogControlHookupStandard(c_triggerControlTypePanel,"UIContainer/FullscreenUpperContainer/RM5SupportHolder");\n'
             '    gv_m5_callPanel=DialogControlLastCreated();\n'
             '    DialogControlSetVisible(gv_m5_callPanel,PlayerGroupSingle(1),true);\n'
             '    DialogControlCreateInPanelFromTemplate(gv_m5_callPanel,c_triggerControlTypeCommandPanel,"RM5Topbar/RM5CommandPanelTemplate");\n'
             '    libNtve_gf_SetDialogItemUnitGroup(DialogControlLastCreated(),gv_m5_casterGroup,PlayerGroupSingle(1));\n')
PANEL_FUNC = '''// 0.5.16: the command panel is hooked in its own thread so a UI failure cannot stop the mission logic.
bool gv_m5_panelOk;
bool gv_m5_fallbackUp;
fixed gv_m5_panelAt;

bool gt_m5_CallPanel_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
''' + PANEL_OLD + '''    gv_m5_panelOk=true;
    return true;
}

// Fallback (0.5.11 style): icon buttons in a dialog; a click aims, the next map click picks the point.
void gf_m5_CallFallbackBtn (int p, int x, string icon, string tip) {
    int img;
    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeButton);
    gv_m5_callBtnP[p]=DialogControlLastCreated();
    DialogControlSetSize(gv_m5_callBtnP[p],PlayerGroupAll(),64,64);
    DialogControlSetPosition(gv_m5_callBtnP[p],PlayerGroupAll(),c_anchorTopLeft,x,26);
    DialogControlSetPropertyAsText(gv_m5_callBtnP[p],c_triggerControlPropertyTooltip,PlayerGroupAll(),StringExternal(tip));
    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeImage);
    img=DialogControlLastCreated();
    DialogControlSetSize(img,PlayerGroupAll(),52,52);
    DialogControlSetPosition(img,PlayerGroupAll(),c_anchorTopLeft,x+6,32);
    DialogControlSetPropertyAsString(img,c_triggerControlPropertyImage,PlayerGroupAll(),icon);
    DialogControlSetPropertyAsInt(img,c_triggerControlPropertyImageType,PlayerGroupAll(),c_triggerImageTypeNormal);
}

void gf_m5_CallFallback () {
    if (gv_m5_panelOk || gv_m5_fallbackUp || GameGetMissionTime()<gv_m5_panelAt+3.0) { return; }
    gv_m5_fallbackUp=true;
    DialogSetSize(gv_m5_callDlg,240,96);
    DialogSetPosition(gv_m5_callDlg,c_anchorTop,0,4);
    gf_m5_CallFallbackBtn(8,46,"Assets\\\\Textures\\\\btn-ability-spearofadun-warpinreinforcements.dds","Button/Tooltip/RM5_AllySupport");
    gf_m5_CallFallbackBtn(9,130,"Assets\\\\Textures\\\\btn-unit-collection-primal-Zergling.dds","Button/Tooltip/RM5_PrimalSupport");
}

'''

SCRIPT = [
    ('int[16] gv_m5_callImgP;\nint gv_m5_callPanel;\n', 'int[16] gv_m5_callImgP;\n'),
    (PANEL_OLD, '    gv_m5_panelAt=GameGetMissionTime();\n    TriggerExecute(TriggerCreate("gt_m5_CallPanel_Func"),false,false);\n'),
    ('void gf_m5_CallUI () {\n', PANEL_FUNC + 'void gf_m5_CallUI () {\n'),
    ('    DialogControlSetVisible(gv_m5_callPanel,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);\n',
     '    if (gv_m5_panelOk) { DialogControlSetVisible(gv_m5_callPanel,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver); }\n'
     '    gf_m5_CallFallback();\n'),
    ('    gf_m5_CallUI();\n    gv_m5_ready=true;\n', '    gv_m5_ready=true;\n    gf_m5_CallUI();\n'),
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
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[S].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = sub(t.replace('\r\n', '\n'), SCRIPT)
        assert t.count('int gv_m5_callPanel;') == 1
        files[S] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (S, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
