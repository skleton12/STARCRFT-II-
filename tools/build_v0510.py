#!/usr/bin/env python3
"""0.5.9 -> 0.5.10: 레드스톤 상단 지원 버튼이 "눌리기만 하고" 아무 일도 없던 문제 (사용자 2026-10-27).

0.5.7~0.5.9는 화면 위 명령 패널(CommandPanel)에 보이지 않는 시전 유닛을 연결했는데, 게임에서 버튼이 눌린 모양만
나고 명령이 나가지 않았다 (선택하지 않은 유닛의 패널 명령). 명령 패널 의존을 없앤다:
- 화면 위 대화 상자에 아이콘 버튼 두 개(정화자 지원·원시저그 지원)와 그 아래 남은 시간 글자를 직접 만든다.
  대화 상자 버튼 클릭 이벤트는 0.5.6에서 동작한 방식이다.
- 버튼 클릭 또는 Ctrl+V(정화자)·Ctrl+B(원시저그)를 누르면, 협동전처럼 UISetTargetingOrder로 시전 유닛의
  지점 지정 능력 커서를 연다 (V·B 단독은 SCV 건설 메뉴 단축키와 겹쳐서 Ctrl 조합, 시험값).
- 지점을 찍으면 능력 시전 이벤트가 소환한다. 커서가 안 열리는 경우를 대비해, 버튼을 누른 뒤의 다음 지도
  왼쪽 클릭도 지점으로 받는다 (0.25초 기다려 능력 시전이 먼저 처리됐으면 무시). 오른쪽 클릭은 취소.
- 재사용 대기는 스크립트가 잰다 (정화자·원시저그 따로 30초, 첫 사용 약 1분 뒤). 대기 중에 누르면
  "N초 뒤에 부를 수 있습니다"를 띄운다. 실패(못 가는 곳·돈 부족)면 대기 시간을 쓰지 않는다.
- 능력 데이터의 재사용 대기는 0으로 (스크립트가 관리). 패널용 즉시 능력·명령 패널은 쓰지 않는다.

Usage: python3 tools/build_v0510.py <0.5.9 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.5.9', b'version=0.5.10'
M5 = 'TTosh01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ICON_P = r'Assets\\Textures\\btn-ability-spearofadun-warpinreinforcements.dds'
ICON_Z = r'Assets\\Textures\\btn-ability-kerrigan-droppods.dds'

CODE = r'''void gf_m5_CallErr (text msg) {
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaError,msg);
}

// 0.5.10: our own top buttons (dialog clicks work) open the co-op style target cursor with UISetTargetingOrder.
// Cooldowns are kept by the script: 30 s each, first use about 1 minute in (trial). A failed call costs no cooldown.
fixed[16] gv_m5_callAt;
int[16] gv_m5_callBtnP;
int[16] gv_m5_callLblP;
string[16] gv_m5_callAbil;
int gv_m5_aimP;
fixed gv_m5_aimTime;

bool gf_m5_CallAt (int p, point c) {
    if (c==null || !VisIsVisibleForPlayer(1,c) || !PointPathingPassable(c)) {
        gf_m5_CallErr(StringExternal("rm5/CallBad"));
        return false;
    }
    if (!gf_m5_CallPay(p)) {
        gf_m5_CallErr(StringExternal("rm5/CallNoMoney"));
        return false;
    }
    gf_m5_CallSpots(p,c);
    if (p==8) {
        gv_m5_supTurn+=1;
        TriggerExecute(gv_m5_callTrig8,false,false);
    }
    else { TriggerExecute(gv_m5_callTrig9,false,false); }
    gv_m5_callAt[p]=GameGetMissionTime()+30.0;
    return true;
}

void gf_m5_Aim (int p) {
    fixed left;
    if (gv_gameOver || gv_inCinematic || !gv_m5_callUp) { return; }
    left=gv_m5_callAt[p]-GameGetMissionTime();
    if (left>0.0) {
        gf_m5_CallErr(TextReplaceWord(StringExternal("rm5/CallWaitMsg"),StringToText("%s"),IntToText(CeilingI(left)),c_stringReplaceAll,c_stringCase));
        return;
    }
    gv_m5_aimP=p;
    gv_m5_aimTime=GameGetMissionTime();
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/CallAim"));
    UISetTargetingOrder(PlayerGroupSingle(1),gv_m5_casterGroup,OrderTargetingPoint(AbilityCommand(gv_m5_callAbil[p],0),UnitGetPosition(gv_m5_caster)),false);
}

bool gt_m5_CallBtn_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    if (EventDialogControl()==gv_m5_callBtnP[8]) { gf_m5_Aim(8); }
    else if (EventDialogControl()==gv_m5_callBtnP[9]) { gf_m5_Aim(9); }
    return true;
}

bool gt_m5_CallKey_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    if (EventKeyPressed()==c_keyV) { gf_m5_Aim(8); }
    else if (EventKeyPressed()==c_keyB) { gf_m5_Aim(9); }
    return true;
}

// The real target cursor (ability cast on the global caster).
bool gt_m5_CallCast_Func (bool testConds,bool runActions) {
    int p=8;
    point c;
    if (!runActions || gv_gameOver) { return true; }
    if (EventUnitAbility()==AbilityCommand("RM5_PrimalSupport",0)) { p=9; }
    gv_m5_aimP=0;
    if (GameGetMissionTime()<gv_m5_callAt[p]) { return true; }
    c=EventUnitTargetPoint();
    if (EventUnitTargetUnit()!=null) { c=UnitGetPosition(EventUnitTargetUnit()); }
    gf_m5_CallAt(p,c);
    return true;
}

// Backup: if no cursor came up, the next left click on the map after pressing the button is the spot.
bool gt_m5_CallMouse_Func (bool testConds,bool runActions) {
    int p=gv_m5_aimP;
    point c;
    if (!runActions || p==0 || GameGetMissionTime()<gv_m5_aimTime+0.2) { return true; }
    c=Point(EventMouseClickedPosXWorld(),EventMouseClickedPosYWorld());
    Wait(0.25,c_timeGame);
    if (gv_m5_aimP!=p) { return true; }
    gv_m5_aimP=0;
    gf_m5_CallAt(p,c);
    return true;
}

bool gt_m5_CallCancel_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    gv_m5_aimP=0;
    return true;
}

void gf_m5_CallButton (int p, int x, string icon, string tip) {
    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeButton);
    gv_m5_callBtnP[p]=DialogControlLastCreated();
    DialogControlSetSize(gv_m5_callBtnP[p],PlayerGroupAll(),64,64);
    DialogControlSetPosition(gv_m5_callBtnP[p],PlayerGroupAll(),c_anchorTopLeft,x,6);
    DialogControlSetPropertyAsString(gv_m5_callBtnP[p],c_triggerControlPropertyImage,PlayerGroupAll(),icon);
    DialogControlSetPropertyAsText(gv_m5_callBtnP[p],c_triggerControlPropertyTooltip,PlayerGroupAll(),StringExternal(tip));
    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeLabel);
    gv_m5_callLblP[p]=DialogControlLastCreated();
    DialogControlSetSize(gv_m5_callLblP[p],PlayerGroupAll(),80,22);
    DialogControlSetPosition(gv_m5_callLblP[p],PlayerGroupAll(),c_anchorTopLeft,x-8,72);
}

void gf_m5_CallUI () {
    trigger t;
    if (gv_m5_callUp) { return; }
    gv_m5_callUp=true;
    gv_m5_callTrig8=TriggerCreate("gt_m5_CallGo_Func");
    gv_m5_callTrig9=TriggerCreate("gt_m5_CallGo_Func");
    gv_m5_callAbil[8]="RM5_AllySupport";
    gv_m5_callAbil[9]="RM5_PrimalSupport";
    gv_m5_callAt[8]=GameGetMissionTime()+55.0;
    gv_m5_callAt[9]=GameGetMissionTime()+55.0;
    UnitCreate(1,"RM5_AllyCaster",c_unitCreateIgnorePlacement,1,Point(0.5,0.5),270.0);
    gv_m5_caster=UnitLastCreated();
    UnitSetState(gv_m5_caster,c_unitStateSelectable,false);
    gv_m5_casterGroup=UnitGroupEmpty();
    UnitGroupAdd(gv_m5_casterGroup,gv_m5_caster);
    DialogCreate(176,100,c_anchorTop,0,0,false);
    gv_m5_callDlg=DialogLastCreated();
    DialogSetImageVisible(gv_m5_callDlg,false);
    gf_m5_CallButton(8,16,"ICON_P","Button/Tooltip/RM5_AllySupport");
    gf_m5_CallButton(9,96,"ICON_Z","Button/Tooltip/RM5_PrimalSupport");
    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),true);
    t=TriggerCreate("gt_m5_CallBtn_Func");
    TriggerAddEventDialogControl(t,1,c_invalidDialogControlId,c_triggerControlEventTypeClick);
    t=TriggerCreate("gt_m5_CallKey_Func");
    TriggerAddEventKeyPressed(t,1,c_keyV,true,c_keyModifierStateExclude,c_keyModifierStateRequire,c_keyModifierStateExclude);
    TriggerAddEventKeyPressed(t,1,c_keyB,true,c_keyModifierStateExclude,c_keyModifierStateRequire,c_keyModifierStateExclude);
    t=TriggerCreate("gt_m5_CallCast_Func");
    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_AllySupport",0),c_abilEffectStageCast,false);
    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_PrimalSupport",0),c_abilEffectStageCast,false);
    t=TriggerCreate("gt_m5_CallMouse_Func");
    TriggerAddEventMouseClicked(t,1,c_mouseButtonLeft,true);
    t=TriggerCreate("gt_m5_CallCancel_Func");
    TriggerAddEventMouseClicked(t,1,c_mouseButtonRight,true);
    t=TriggerCreate("gt_m5_CallTimer_Func");
    TriggerAddEventTimePeriodic(t,0.5,c_timeGame);
}

void gf_m5_CallLabel (int p, text name) {
    int left=CeilingI(gv_m5_callAt[p]-GameGetMissionTime());
    if (left>0) {
        DialogControlSetPropertyAsText(gv_m5_callLblP[p],c_triggerControlPropertyText,PlayerGroupAll(),
            TextReplaceWord(StringExternal("rm5/CallWait"),StringToText("%s"),IntToText(left),c_stringReplaceAll,c_stringCase));
        DialogControlSetPropertyAsBool(gv_m5_callBtnP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),true);
    }
    else {
        DialogControlSetPropertyAsText(gv_m5_callLblP[p],c_triggerControlPropertyText,PlayerGroupAll(),name);
        DialogControlSetPropertyAsBool(gv_m5_callBtnP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),false);
    }
}

bool gt_m5_CallTimer_Func (bool testConds,bool runActions) {
    if (!runActions || !gv_m5_callUp) { return true; }
    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);
    gf_m5_CallLabel(8,StringExternal("rm5/CallKeyP"));
    gf_m5_CallLabel(9,StringExternal("rm5/CallKeyZ"));
    return true;
}

void gf_m5_CallTick () {
}

'''.replace('"ICON_P"', '"' + ICON_P + '"').replace('"ICON_Z"', '"' + ICON_Z + '"')

SET = {'rm5/CallWait': '%s초 /// %ss'}
ADD = [
    'rm5/CallWaitMsg=%s초 뒤에 부를 수 있습니다. /// Available in %s seconds.',
    'rm5/CallKeyP=정화자 Ctrl+V /// Purifier Ctrl+V',
    'rm5/CallKeyZ=원시저그 Ctrl+B /// Primal Ctrl+B',
]
ADJ = 'rm5/AdjSup=1분 뒤부터 화면 위 [정화자 지원]·[원시저그 지원] 버튼(Ctrl+V·Ctrl+B)을 누르고 지점을 찍으면 그 동맹이 그곳으로 병력을 보냅니다. 각각 재사용 대기 30초, 비용은 그 동맹의 자원입니다. /// In one minute, press [Purifier Support] or [Primal Zerg Support] at the top of the screen (Ctrl+V / Ctrl+B) and pick a spot: that ally sends forces there. 30-second cooldown each; paid with that ally\'s resources.'


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        s = M5 + 'mapscript.galaxy'
        t = files[s].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = t.replace('\r\n', '\n')
        a = t.index('void gf_m5_CallRefund (string abil, string msg) {\n')
        b = t.index('bool gt_m5_Tick_Func (bool testConds,bool runActions) {\n')
        old = t[a:b]
        assert 'c_triggerControlTypeCommandPanel' in old and 'gf_m5_CallTick ()' in old
        t = t[:a] + CODE + t[b:]
        assert 'gv_m5_callPanel' not in t[a:a + len(CODE)]
        files[s] = t.replace('\n', nl).encode('utf-8')
        ab = files[M5 + GD + 'abildata.xml'].decode('utf-8')
        for link in ('RM5_CD8', 'RM5_CD9'):
            x = f'<Cooldown Link="{link}" Location="Unit" TimeStart="55" TimeUse="30" />'
            assert ab.count(x) == 1, x
            ab = ab.replace(x, f'<Cooldown Link="{link}" Location="Unit" TimeStart="0" TimeUse="0" />')
        files[M5 + GD + 'abildata.xml'] = ab.encode('utf-8')
        ko = files[M5 + KO].decode('utf-8-sig')
        knl = '\r\n' if '\r\n' in ko else '\n'
        lines = ko.split(knl)
        for key, val in list(SET.items()) + [('rm5/AdjSup', ADJ.split('=', 1)[1])]:
            hit = [i for i, l in enumerate(lines) if l.startswith(key + '=')]
            assert len(hit) == 1, key
            lines[hit[0]] = f'{key}={val}'
        files[M5 + KO] = (knl.join(lines).rstrip('\r\n') + knl + knl.join(ADD) + knl).encode('utf-8')
        V35.gate('kokr', files[M5 + KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M5}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[M5 + KO])
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if not n.startswith(M5) and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
