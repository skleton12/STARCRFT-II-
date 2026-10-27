#!/usr/bin/env python3
"""0.5.5 -> 0.5.6: 레드스톤 임무 목표 창에 '또는: 저그 기지 모두 파괴'를 보인다 (사용자 2026-10-27 "ㅇㅇ").

- 원작 광물 목표를 만드는 순간 바로 아래에 주 목표 하나를 더 만든다.
- 0.5.5 저그 전멸 승리 때 그 목표를 완료로 바꾼다.

동맹 일꾼 제거·협동전식 지원 호출 (사용자 2026-10-27 "일꾼 빼줘", "시작 1분 뒤부터 30초마다",
"협동전처럼 위에 동맹 지원 30초 해서 지점을 정하는 건"):
- 레드스톤 동맹 탐사정·원시 일벌레를 내려보내지 않고 무료 보충도 끈다. 그래서 동맹 기지·채굴(50% 지원)은 없다.
- 자동 30초 지원(0.5.3) 대신 화면 위 [동맹 지원] 버튼: 누르고 보이는·지나갈 수 있는 지점을 왼쪽 클릭하면 두 동맹이
  그곳으로 병력 묶음을 보낸다 (정화자 차원 소환, 원시저그 낙하 주머니). 오른쪽 클릭 취소. 첫 사용 시작 1분 뒤, 재사용 대기 30초 (시험값).
  묶음 구성·동맹 자원 지불·인구 100은 0.5.3과 같다. 한 동맹만 돈이 되면 그 동맹만 온다. 둘 다 안 되면 대기 시간을 쓰지 않는다.
- 동맹 돈은 2초마다 들어오는 수입으로만 모인다.
- 부관 안내를 바꾼다: 일꾼·기지 안내 대신 버튼 안내, 용암 안내에서 동맹 기지 문장 삭제.

Usage: python3 tools/build_v056.py <0.5.5 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.5.5', b'version=0.5.6'
M5 = 'TTosh01.SC2Map/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'

CALL = r"""// 0.5.6: co-op style Ally Support call-down (user 2026-10-27 "협동전처럼 위에 동맹 지원 30초, 지점을 정하는"):
// a button at the top of the screen; click it, then left-click a visible, walkable spot. Both allies send their group
// there (Purifiers warp in, Primal Zerg drop pods), paid with ally money, army cap 100. 30 s cooldown, first use 1 min in.
int gv_m5_callDlg;
int gv_m5_callBtn;
bool gv_m5_callAim;
bool gv_m5_callUp;
fixed gv_m5_callReady;
trigger gv_m5_callTrig8;
trigger gv_m5_callTrig9;

bool gf_m5_CallPay (int p) {
    int i;
    int m=0;
    int g=0;
    fixed food=0.0;
    gf_m5_SupFill(p);
    for (i=0;i<gv_m5_supN[p];i+=1) {
        m+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostMinerals);
        g+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostVespene);
        food+=gf_m5_UnitFood(gv_m5_supKind[p][i]);
    }
    if (gf_m5_Food(p)+food>100.0 || PlayerGetPropertyInt(p,c_playerPropMinerals)<m || PlayerGetPropertyInt(p,c_playerPropVespene)<g) { return false; }
    PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,m);
    PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);
    return true;
}

void gf_m5_CallSpots (int p, point c) {
    point s;
    int i;
    int n=gv_m5_supN[p];
    for (i=0;i<n;i+=1) {
        s=PointWithOffsetPolar(c,2.0,IntToFixed(i*360/n));
        if (!PointPathingPassable(s)) { s=c; }
        gv_m5_supAt[p][i]=s;
    }
}

bool gt_m5_CallGo_Func (bool testConds,bool runActions) {
    int p=8;
    int n;
    int i;
    string[12] kind;
    point[12] at;
    actor[12] fx;
    if (!runActions) { return true; }
    if (TriggerGetCurrent()==gv_m5_callTrig9) { p=9; }
    n=gv_m5_supN[p];
    for (i=0;i<n;i+=1) {
        kind[i]=gv_m5_supKind[p][i];
        at[i]=gv_m5_supAt[p][i];
        if (p==8) {
            fx[i]=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at[i]);
            ActorSend(fx[i],"AnimPlay Warp Birth NonLooping");
        }
        else if (ModI(i,2)==0) {
            fx[i]=libNtve_gf_CreateModelAtPoint("ZergDropPod",at[i]);
            ActorSend(fx[i],"AnimPlay Drop Birth NonLooping");
        }
    }
    if (p==8) { Wait(0.5,c_timeGame); } else { Wait(1.5,c_timeGame); }
    for (i=0;i<n;i+=1) {
        if (!gv_gameOver) { UnitCreate(1,kind[i],0,p,at[i],270.0); }
    }
    Wait(8.0,c_timeGame);
    for (i=0;i<n;i+=1) {
        if (fx[i]!=null) { ActorSend(fx[i],"Destroy"); }
    }
    return true;
}

bool gt_m5_CallClick_Func (bool testConds,bool runActions) {
    if (!runActions || gv_gameOver || EventDialogControl()!=gv_m5_callBtn) { return true; }
    if (GameGetMissionTime()<gv_m5_callReady) { return true; }
    gv_m5_callAim=true;
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/CallAim"));
    return true;
}

bool gt_m5_CallCancel_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    gv_m5_callAim=false;
    return true;
}

bool gt_m5_CallPoint_Func (bool testConds,bool runActions) {
    point c;
    bool sent=false;
    if (!runActions || !gv_m5_callAim || gv_gameOver) { return true; }
    gv_m5_callAim=false;
    c=Point(EventMouseClickedPosXWorld(),EventMouseClickedPosYWorld());
    if (!VisIsVisibleForPlayer(1,c) || !PointPathingPassable(c)) {
        UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaError,StringExternal("rm5/CallBad"));
        return true;
    }
    if (gf_m5_CallPay(8)) {
        gf_m5_CallSpots(8,c);
        gv_m5_supTurn+=1;
        TriggerExecute(gv_m5_callTrig8,false,false);
        sent=true;
    }
    if (gf_m5_CallPay(9)) {
        gf_m5_CallSpots(9,c);
        TriggerExecute(gv_m5_callTrig9,false,false);
        sent=true;
    }
    if (!sent) {
        UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaError,StringExternal("rm5/CallNoMoney"));
        return true;
    }
    gv_m5_callReady=GameGetMissionTime()+30.0;
    return true;
}

void gf_m5_CallUI () {
    trigger t;
    if (gv_m5_callUp) { return; }
    gv_m5_callUp=true;
    gv_m5_callTrig8=TriggerCreate("gt_m5_CallGo_Func");
    gv_m5_callTrig9=TriggerCreate("gt_m5_CallGo_Func");
    DialogCreate(260,64,c_anchorTop,0,70,false);
    gv_m5_callDlg=DialogLastCreated();
    DialogSetImageVisible(gv_m5_callDlg,false);
    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeButton);
    gv_m5_callBtn=DialogControlLastCreated();
    DialogControlSetSize(gv_m5_callBtn,PlayerGroupAll(),240,50);
    DialogControlSetPosition(gv_m5_callBtn,PlayerGroupAll(),c_anchorCenter,0,0);
    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),true);
    t=TriggerCreate("gt_m5_CallClick_Func");
    TriggerAddEventDialogControl(t,1,gv_m5_callBtn,c_triggerControlEventTypeClick);
    t=TriggerCreate("gt_m5_CallPoint_Func");
    TriggerAddEventMouseClicked(t,1,c_mouseButtonLeft,true);
    t=TriggerCreate("gt_m5_CallCancel_Func");
    TriggerAddEventMouseClicked(t,1,c_mouseButtonRight,true);
}

void gf_m5_CallTick () {
    int left;
    if (!gv_m5_callUp) { return; }
    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);
    left=CeilingI(gv_m5_callReady-GameGetMissionTime());
    if (left>0) {
        DialogControlSetEnabled(gv_m5_callBtn,PlayerGroupAll(),false);
        DialogControlSetPropertyAsText(gv_m5_callBtn,c_triggerControlPropertyText,PlayerGroupAll(),
            TextReplaceWord(StringExternal("rm5/CallWait"),StringToText("%s"),IntToText(left),c_stringReplaceAll,c_stringCase));
    }
    else {
        DialogControlSetEnabled(gv_m5_callBtn,PlayerGroupAll(),true);
        DialogControlSetPropertyAsText(gv_m5_callBtn,c_triggerControlPropertyText,PlayerGroupAll(),StringExternal("rm5/CallReady"));
    }
}

"""

SCRIPT = [
    ('bool gt_m5_ZergWipe_Func (bool testConds, bool runActions) {\n',
     'int gv_m5_objWipe;\nbool gv_m5_objWipeOn;\n\nbool gt_m5_ZergWipe_Func (bool testConds, bool runActions) {\n'),
    ('    TriggerEnable(gt_VictoryCollectedQuota, false);\n    gv_gameOver = true;\n',
     '    TriggerEnable(gt_VictoryCollectedQuota, false);\n'
     '    if (gv_m5_objWipeOn) { ObjectiveSetState(gv_m5_objWipe, c_objectiveStateCompleted); }\n'
     '    gv_gameOver = true;\n'),
    ('    gv_objectiveCollect = ObjectiveLastCreated();\n',
     '    gv_objectiveCollect = ObjectiveLastCreated();\n'
     '    // 0.5.5: the second way to win (user 2026-10-27).\n'
     '    ObjectiveCreate(StringExternal("rm5/ObjWipe"), StringExternal("rm5/ObjWipeDesc"), c_objectiveStateActive, true);\n'
     '    gv_m5_objWipe = ObjectiveLastCreated();\n'
     '    gv_m5_objWipeOn = true;\n'),
    # no ally workers; support from 1 minute after the start, next to Raynor's base
    ('    gf_m5_Workers();\n', ''),
    ('    fx=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",Point(45.0,81.0));\n'
     '    ActorSend(fx,"AnimPlay Warp Birth NonLooping");\n'
     '    pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(47.0,80.0));\n'
     '    ActorSend(pod,"AnimPlay Drop Birth NonLooping");\n'
     '    Wait(3.0,c_timeGame);\n'
     '    ActorSend(fx,"Destroy");\n'
     '    ActorSend(pod,"Destroy");\n'
     '    if (gv_gameOver) { return true; }\n'
     '    UnitCreate(1,"Probe",0,8,Point(45.0,81.0),270.0);\n'
     '    for (i=0;i<1;i+=1) { UnitCreate(1,"DehakaDrone",0,9,Point(46.0+1.0*i,80.0),270.0); }\n',
     '    // 0.5.6: no ally workers on Redstone (user 2026-10-27); the Ally Support button opens 1 minute after the start.\n'
     '    gv_m5_callReady=GameGetMissionTime()+55.0;\n'
     '    gf_m5_CallUI();\n'),
    ('    gf_m5_Produce();\n    gf_m5_Support();\n', '    gf_m5_Produce();\n    gf_m5_CallTick();\n'),
    ('bool gt_m5_Tick_Func (bool testConds,bool runActions) {\n', CALL + 'bool gt_m5_Tick_Func (bool testConds,bool runActions) {\n'),
    ('StringExternal("rm4/Adj1"),7.0,c_transmissionDurationSet,true);\n'
     '    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm4/AdjName"),StringExternal("rm4/Adj2"),7.0,c_transmissionDurationSet,true);\n',
     'StringExternal("rm5/AdjSup"),7.0,c_transmissionDurationSet,true);\n'),
]
STRINGS = [
    'rm5/ObjWipe=또는: 저그 기지 모두 파괴 /// Or: Destroy All Zerg Bases',
    'rm5/ObjWipeDesc=맵에 있는 저그 건물을 모두 파괴해도 임무를 완수합니다. /// Destroying every zerg structure on the map also completes the mission.',
    'rm5/AdjSup=1분 뒤부터 화면 위 [동맹 지원] 버튼을 누르고 지점을 클릭하면 정화자와 원시저그가 그곳으로 병력을 보냅니다. 재사용 대기 30초, 비용은 동맹 자원입니다. /// In one minute, press [Ally Support] at the top of the screen and click a spot: the Purifiers and Primal Zerg send forces there. 30-second cooldown; costs come from ally resources.',
    'rm5/CallReady=동맹 지원 /// Ally Support',
    'rm5/CallWait=동맹 지원 (%s초) /// Ally Support (%ss)',
    'rm5/CallAim=지원할 지점을 왼쪽 클릭하세요. 오른쪽 클릭은 취소입니다. /// Left-click where the support should arrive. Right-click cancels.',
    'rm5/CallBad=보이는 곳, 지나갈 수 있는 땅에만 부를 수 있습니다. /// Support can only be called to a visible, walkable spot.',
    'rm5/CallNoMoney=동맹 자원이나 인구가 모자라 지원이 오지 않았습니다. /// The allies lack resources or supply; no support was sent.',
]
ADJ3 = 'rm5/Adj3=용암이 차오르기 전에 동맹 병력은 높은 곳으로 피합니다. /// Allied forces move to high ground before the lava rises.'


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        s = M5 + 'mapscript.galaxy'
        t = files[s].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = t.replace('\r\n', '\n')
        for a, b in SCRIPT:
            assert t.count(a) == 1, a
            t = t.replace(a, b)
        files[s] = t.replace('\n', nl).encode('utf-8')
        ko = files[M5 + KO].decode('utf-8-sig')
        knl = '\r\n' if '\r\n' in ko else '\n'
        assert 'rm5/ObjWipe=' not in ko
        lines = ko.split(knl)
        hit = [i for i, l in enumerate(lines) if l.startswith('rm5/Adj3=')]
        assert len(hit) == 1
        lines[hit[0]] = ADJ3
        ko = knl.join(lines)
        files[M5 + KO] = (ko.rstrip('\r\n') + knl + knl.join(STRINGS) + knl).encode('utf-8')
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
