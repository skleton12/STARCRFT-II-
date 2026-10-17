#!/usr/bin/env python3
"""드래그 선택 진단판 (배포용 아님, releases/에 넣지 않는다).

사용자 보고 (2026-10-17): 멜리에서는 드래그 선택이 되는데 모드 캠페인에서는 상자로 덮어도 선택이 안 바뀔 때가 있다.
후보: 2·3번 미션이 플레이어 1의 '해병→전쟁광', '의무관→용병 의무관' 데이터 연결을 통째로 바꾼다(CatalogLinkReplace).
전쟁광의 선택 묶음(SelectAlias)이 '해병'을 가리켜, 바뀐 연결과 엉킬 수 있다.

진단판에 넣는 것 (세 맵 모두):
  - 선택 기록: 플레이어 1의 유닛이 선택·해제될 때마다 화면 왼쪽에 '+ 이름' / '- 이름'을 띄운다.
    상자를 끌고 손을 뗐을 때 아무 기록도 없으면 게임이 선택을 안 받은 것이고, '+'가 떴다가 곧 '-'가 뜨면 되돌려진 것이다.
  - 채팅 diag1: 해병·의무관 연결 바꿈을 되돌린다 (2·3번). 그 뒤 드래그가 되면 이것이 원인이다.
  - 채팅 diag2: 3번 동맹 처리(2초 주기)를 멈춘다. 그 뒤 드래그가 되면 동맹 처리 쪽이 원인이다.

Usage: python3 tools/build_diag_select.py <release zip> <output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

MAPS = ['TRaynor01.SC2Map', 'TRaynor02.SC2Map', 'TRaynor03.SC2Map']

DIAG = '''// Selection diagnostics (not for release).
bool gt_diag_Sel_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    UIDisplayMessage(PlayerGroupAll(),c_messageAreaDebug,StringToText("+ ")+UnitTypeGetName(UnitGetType(EventUnit())));
    return true;
}

bool gt_diag_Unsel_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    UIDisplayMessage(PlayerGroupAll(),c_messageAreaDebug,StringToText("- ")+UnitTypeGetName(UnitGetType(EventUnit())));
    return true;
}

bool gt_diag_Alias_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    CatalogLinkReplace(1,c_gameCatalogUnit,"Marine","Marine");
    CatalogLinkReplace(1,c_gameCatalogUnit,"Medic","Medic");
    UIDisplayMessage(PlayerGroupAll(),c_messageAreaDebug,StringToText("diag1: Marine/Medic link replace undone"));
    return true;
}

bool gt_diag_Tick_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    DIAG_TICK_OFF
    UIDisplayMessage(PlayerGroupAll(),c_messageAreaDebug,StringToText("diag2: ally tick stopped"));
    return true;
}

void gf_diag_Init () {
    trigger t;
    t=TriggerCreate("gt_diag_Sel_Func");
    TriggerAddEventUnitSelected(t,null,1,true);
    t=TriggerCreate("gt_diag_Unsel_Func");
    TriggerAddEventUnitSelected(t,null,1,false);
    t=TriggerCreate("gt_diag_Alias_Func");
    TriggerAddEventChatMessage(t,1,"diag1",true);
    t=TriggerCreate("gt_diag_Tick_Func");
    TriggerAddEventChatMessage(t,1,"diag2",true);
}

'''


def patch(name, data):
    text = data.decode('utf-8')
    tick = 'TriggerEnable(gt_m3_tick,false);' if name == 'TRaynor03.SC2Map' else ''
    head = 'void InitTriggers () {'
    assert text.count(head) == 1
    text = text.replace(head, DIAG.replace('DIAG_TICK_OFF', tick) + head + '\n    gf_diag_Init();', 1)
    return text.encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
        for info in prev.infolist():
            data = prev.read(info.filename)
            for m in MAPS:
                if info.filename == m + '/mapscript.galaxy': data = patch(m, data)
            out.writestr(copy.copy(info), data)
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
