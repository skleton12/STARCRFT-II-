#!/usr/bin/env python3
"""0.5.12 -> 0.5.13: 레드스톤 지원 = 진짜 명령 패널 + 4분 뒤·120초 + 연출 뒤 등장 (사용자 2026-10-27).

사용자: "역시나 커서는 없음 모드 보면서 참고해봐", "4분 뒤에 열리게 하고 120초 대기시간",
"투하나 소환이 완료된 뒤 나와야 하는데 그게 아닌 듯".

- 커서: 대화 상자 버튼 + UISetTargetingOrder는 게임에서 커서를 열지 못했다 (0.5.10~0.5.12).
  RaynorRogue 모드는 UI 레이아웃(SC2Layout)에 CommandPanel 틀을 정의하고, 게임 화면 위 칸
  (UIContainer/FullscreenUpperContainer)에 걸어 상단 유닛의 명령 카드를 보여 준다. 진짜 명령 버튼이라
  지점 능력을 누르면 게임이 직접 지점 커서를 연다. 같은 구조를 이 모드용으로 새로 썼다
  (data/rm5_topbar.SC2Layout → 맵 base.sc2data/ui/layout/RM5Topbar.SC2Layout + DescIndex). 그 모드 파일은 가져오지 않는다.
  시전 유닛 RM5_AllyCaster의 카드(0.5.11부터 RM5_AllySupport·RM5_PrimalSupport)를 패널에 연결한다.
  아래 대화 상자는 남은 시간 글자만 둔다. Ctrl+V·Ctrl+B와 지도 클릭 대체는 그대로.
- 재사용 대기: 첫 사용 임무 시간 4분(240초), 이후 120초 (시험값). 스크립트가 시전 유닛의 쿨다운(RM5_CD8/9)도
  같이 맞춰 버튼에 대기 표시가 나온다. 실패한 호출은 대기를 쓰지 않는다.
- 연출: 정화자는 차원 소환 연출 2.5초 뒤, 원시저그는 낙하 주머니 3초 뒤(2번 미션 투하와 같은 값)에 유닛이 나온다.

Usage: python3 tools/build_v0513.py <0.5.12 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
OLD, NEW = b'version=0.5.12', b'version=0.5.13'
S = 'TTosh01.SC2Map/mapscript.galaxy'
LOC = 'TTosh01.SC2Map/{}.sc2data/localizeddata/gamestrings.txt'
LOCS = 'kokr dede enus eses esmx frfr itit plpl ptbr ruru zhcn zhtw'.split()
LAYOUT = 'TTosh01.SC2Map/base.sc2data/ui/layout/RM5Topbar.SC2Layout'
DESC = 'TTosh01.SC2Map/base.sc2data/ui/layout/DescIndex.SC2Layout'
DESC_XML = ('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\r\n<Desc>\r\n'
            '    <Include path="UI/Layout/RM5Topbar.SC2Layout"/>\r\n</Desc>\r\n').encode('utf-8')

CDSET = '''void gf_m5_CdSet (int p, fixed v) {
    if (p==8) { UnitModifyCooldown(gv_m5_caster,"RM5_CD8",v,c_cooldownOperationSet); }
    else { UnitModifyCooldown(gv_m5_caster,"RM5_CD9",v,c_cooldownOperationSet); }
}

'''
BUTTON_OLD_START = 'void gf_m5_CallButton (int p, int x, string icon, string tip) {\n'
BUTTON_NEW = '''void gf_m5_CallButton (int p, int x) {
    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeLabel);
    gv_m5_callLblP[p]=DialogControlLastCreated();
    DialogControlSetSize(gv_m5_callLblP[p],PlayerGroupAll(),96,24);
    DialogControlSetPosition(gv_m5_callLblP[p],PlayerGroupAll(),c_anchorTopLeft,x,0);
}
'''

SCRIPT = [
    ('int[16] gv_m5_callImgP;\n', 'int[16] gv_m5_callImgP;\nint gv_m5_callPanel;\n'),
    ('bool gf_m5_CallAt (int p, point c) {\n', CDSET + 'bool gf_m5_CallAt (int p, point c) {\n'),
    ('    gv_m5_callAt[p]=GameGetMissionTime()+90.0;\n',
     '    gv_m5_callAt[p]=GameGetMissionTime()+120.0;\n    gf_m5_CdSet(p,120.0);\n'),
    ('    gv_m5_callAt[8]=GameGetMissionTime()+55.0;\n    gv_m5_callAt[9]=GameGetMissionTime()+55.0;\n',
     '    // 0.5.13: first use at mission time 4:00, then 120 s each (user 2026-10-27, trial).\n'
     '    gv_m5_callAt[8]=MaxF(240.0,GameGetMissionTime());\n    gv_m5_callAt[9]=gv_m5_callAt[8];\n'),
    ('    UnitGroupAdd(gv_m5_casterGroup,gv_m5_caster);\n'
     '    DialogCreate(176,100,c_anchorTop,0,0,false);\n'
     '    gv_m5_callDlg=DialogLastCreated();\n'
     '    DialogSetImageVisible(gv_m5_callDlg,false);\n'
     '    gf_m5_CallButton(8,16,"Assets\\\\Textures\\\\btn-ability-spearofadun-warpinreinforcements.dds","Button/Tooltip/RM5_AllySupport");\n'
     '    gf_m5_CallButton(9,96,"Assets\\\\Textures\\\\btn-unit-collection-primal-Zergling.dds","Button/Tooltip/RM5_PrimalSupport");\n'
     '    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),true);\n',
     '    UnitGroupAdd(gv_m5_casterGroup,gv_m5_caster);\n'
     '    gf_m5_CdSet(8,gv_m5_callAt[8]-GameGetMissionTime());\n'
     '    gf_m5_CdSet(9,gv_m5_callAt[9]-GameGetMissionTime());\n'
     '    // 0.5.13: a real command panel (map UI layout RM5Topbar) shows the caster card, so its buttons open the game target cursor.\n'
     '    DialogCreate(240,26,c_anchorTop,0,86,false);\n'
     '    gv_m5_callDlg=DialogLastCreated();\n'
     '    DialogSetImageVisible(gv_m5_callDlg,false);\n'
     '    gf_m5_CallButton(8,30);\n'
     '    gf_m5_CallButton(9,114);\n'
     '    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),true);\n'
     '    DialogControlHookupStandard(c_triggerControlTypePanel,"UIContainer/FullscreenUpperContainer/RM5SupportHolder");\n'
     '    gv_m5_callPanel=DialogControlLastCreated();\n'
     '    DialogControlSetVisible(gv_m5_callPanel,PlayerGroupSingle(1),true);\n'
     '    DialogControlCreateInPanelFromTemplate(gv_m5_callPanel,c_triggerControlTypeCommandPanel,"RM5Topbar/RM5CommandPanelTemplate");\n'
     '    libNtve_gf_SetDialogItemUnitGroup(DialogControlLastCreated(),gv_m5_casterGroup,PlayerGroupSingle(1));\n'),
    ('        DialogControlSetPropertyAsBool(gv_m5_callImgP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),true);\n', ''),
    ('        DialogControlSetPropertyAsBool(gv_m5_callImgP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),false);\n', ''),
    ('    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);\n',
     '    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);\n'
     '    DialogControlSetVisible(gv_m5_callPanel,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);\n'),
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t


WAIT_OLD = '    if (p==8) { Wait(0.5,c_timeGame); } else { Wait(1.5,c_timeGame); }\n'
WAIT_NEW = ('    // 0.5.13: units appear after the warp-in / drop-pod effect (user 2026-10-27).\n'
            '    if (p==8) { Wait(2.5,c_timeGame); } else { Wait(3.0,c_timeGame); }\n')


def script(t):
    assert t.count(WAIT_OLD) == 2  # old automatic support (unused since 0.5.6) and the call
    t = sub(t.replace(WAIT_OLD, WAIT_NEW), SCRIPT)
    a = t.index(BUTTON_OLD_START)
    b = t.index('\n}\n', a) + 3
    return t[:a] + BUTTON_NEW + t[b:]


def locale(t, ko):
    pairs = [('In one minute, press', 'After 4 minutes, press'), ('90-second cooldown each', '120-second cooldown each')]
    if ko: pairs += [('1분 뒤부터 화면 위', '4분 뒤부터 화면 위'), ('각각 재사용 대기 90초', '각각 재사용 대기 120초')]
    return sub(t, pairs)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        assert LAYOUT not in files and DESC not in files
        jobs = [(S, script)] + [(LOC.format(l), (lambda k: lambda t: locale(t, k))(l == 'kokr')) for l in LOCS]
        for name, fn in jobs:
            t = files[name].decode('utf-8')
            nl = '\r\n' if '\r\n' in t else '\n'
            files[name] = fn(t.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        layout = (HERE / 'data/rm5_topbar.SC2Layout').read_text(encoding='utf-8').replace('\r\n', '\n').replace('\n', '\r\n').encode('utf-8')
        changed = {S, 'metadata.txt'} | {LOC.format(l) for l in LOCS}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    out.writestr(copy.copy(info), files[info.filename])
                    if info.filename == S:
                        for n, d in ((DESC, DESC_XML), (LAYOUT, layout)):
                            zi = copy.copy(info); zi.filename = n; out.writestr(zi, d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                assert set(out.namelist()) == set(prev.namelist()) | {LAYOUT, DESC}
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
