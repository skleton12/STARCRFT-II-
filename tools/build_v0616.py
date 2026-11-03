#!/usr/bin/env python3
"""0.6.15 -> 0.6.16: 3번 제로 아워(TRaynor03) 동맹 = 4·5·6번 지원 버튼 방식 (사용자 2026-11-03).

사용자 선택: "일꾼·건설을 빼고 지원 버튼만 둬". 3-1의 '3번 미션 예외'(일꾼이 내려와 플레이어가 짓는 방식)를 철회한다.
- 동맹 탐사정·원시 일벌레를 내려보내지 않는다 (일벌레 보충도 끔). 동맹 자원·원시저그 보급·2초 수입은 그대로.
- 화면 위 [정화자 지원]·[원시저그 지원] 아이콘 버튼(Ctrl+V·Ctrl+B) → 다음 지도 왼쪽 클릭 위치에 그 동맹이
  병력 묶음을 차원 소환·낙하 주머니로 보낸다 (오른쪽 클릭 취소). 6번(0.5.18 방식) 그대로이고 커서·시전 유닛은 없다.
  첫 사용은 임무 4분, 재사용 대기 120초, 그 동맹 자원으로 지불하고 동맹 인구 100까지 (모두 6번과 같은 시험값).
- 묶음 (3번 맵에 있는 유닛만): 정화자 군단병 3·피닉스 사도 2·동력기 1(2기 미만일 때),
  원시저그 원시 저글링 6·바퀴 1·히드라 2. 연구실 단계(0~5) 무료 추가분도 3번 맵에 있는 유닛으로 바꿔 쓴다
  (거신·폭풍함·원시 점화자·울트라리스크가 3번 맵 데이터에 없어서). 정화자 1 군단병·2 사도·3 군단병·4 사도·5 군단병 2,
  원시저그 1 저글링 2·2 라바사우르스·3 바퀴·4 히드라·5 라바사우르스.
- 동맹 자동 전투(0.3.21 역할)·핑·업그레이드 연동은 그대로. 동맹이 건물을 못 지으니 생산 거점도 없다.

Usage: python3 tools/build_v0616.py <0.6.15 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO

OLD, NEW = b'version=0.6.15', b'version=0.6.16'
MAP = 'TRaynor03.SC2Map'

MODULE = r'''// 0.6.16 (user 2026-11-03): mission 3 allies work like missions 4-6 — no ally workers or buildings, only the
// top support buttons. Click a button (or Ctrl+V / Ctrl+B), then left-click the map: that ally sends a group there
// (Purifiers warp in, Primal Zerg drop pods). First use at 4:00, 120 s each, ally money, ally army cap 100 (trial).
int[16] gv_m3c_supN;
string[16][24] gv_m3c_supKind;
point[16][24] gv_m3c_supAt;
int[16] gv_m3c_supPaid;
int[16] gv_m3c_tier;
trigger gv_m3c_callTrig10;
trigger gv_m3c_callTrig11;
int gv_m3c_callDlg;
bool gv_m3c_callUp;
fixed[16] gv_m3c_callAt;
int[16] gv_m3c_callBtnP;
int[16] gv_m3c_callLblP;
int gv_m3c_aimP;
fixed gv_m3c_aimTime;

int gf_m3c_Tier (int p) {
    int i;
    int r;
    int n=0;
    int cat=libCamp_ge_StoryResearchCategory_ResearchCategoryProtoss;
    if (p==11) { cat=libCamp_ge_StoryResearchCategory_ResearchCategoryZerg; }
    for (i=libCamp_gv_TSC_RESEARCH_FIRST;i<=libCamp_gv_TSC_RESEARCH_LAST;i+=1) {
        r=libCamp_gv_tS_ResearchID[i];
        if (libCamp_gf_StoryResearchCategory(r)==cat && libCamp_gf_StoryResearchStateCheck(r,libCamp_ge_StoryResearchState_ResearchStatePurchased)) { n+=1; }
    }
    return MinI(n,5);
}

void gf_m3c_SupAdd (int p, string kind) {
    if (gv_m3c_supN[p]>=24) { return; }
    gv_m3c_supKind[p][gv_m3c_supN[p]]=kind;
    gv_m3c_supN[p]+=1;
}

void gf_m3c_SupFill (int p) {
    int k;
    gv_m3c_supN[p]=0;
    if (p==10) {
        for (k=0;k<3;k+=1) { gf_m3c_SupAdd(p,"ZealotPurifier"); }
        gf_m3c_SupAdd(p,"AdeptFenix");
        gf_m3c_SupAdd(p,"AdeptFenix");
        if (UnitGroupCount(UnitGroup("RM21_Energizer",10,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)<2) { gf_m3c_SupAdd(p,"RM21_Energizer"); }
        // Lab tier units (free, trial; only kinds this map has).
        gv_m3c_supPaid[p]=gv_m3c_supN[p];
        if (gv_m3c_tier[p]>=1) { gf_m3c_SupAdd(p,"ZealotPurifier"); }
        if (gv_m3c_tier[p]>=2) { gf_m3c_SupAdd(p,"AdeptFenix"); }
        if (gv_m3c_tier[p]>=3) { gf_m3c_SupAdd(p,"ZealotPurifier"); }
        if (gv_m3c_tier[p]>=4) { gf_m3c_SupAdd(p,"AdeptFenix"); }
        if (gv_m3c_tier[p]>=5) { gf_m3c_SupAdd(p,"ZealotPurifier"); gf_m3c_SupAdd(p,"ZealotPurifier"); }
        return;
    }
    for (k=0;k<6;k+=1) { gf_m3c_SupAdd(p,"DehakaZerglingLevel2"); }
    gf_m3c_SupAdd(p,"DehakaRoachLevel2");
    gf_m3c_SupAdd(p,"DehakaHydraliskLevel2");
    gf_m3c_SupAdd(p,"DehakaHydraliskLevel2");
    gv_m3c_supPaid[p]=gv_m3c_supN[p];
    if (gv_m3c_tier[p]>=1) { gf_m3c_SupAdd(p,"DehakaZerglingLevel2"); gf_m3c_SupAdd(p,"DehakaZerglingLevel2"); }
    if (gv_m3c_tier[p]>=2) { gf_m3c_SupAdd(p,"DehakaRavasaur"); }
    if (gv_m3c_tier[p]>=3) { gf_m3c_SupAdd(p,"DehakaRoachLevel2"); }
    if (gv_m3c_tier[p]>=4) { gf_m3c_SupAdd(p,"DehakaHydraliskLevel2"); }
    if (gv_m3c_tier[p]>=5) { gf_m3c_SupAdd(p,"DehakaRavasaur"); }
}

bool gf_m3c_CallPay (int p) {
    int i;
    int m=0;
    int g=0;
    fixed food=0.0;
    gf_m3c_SupFill(p);
    for (i=0;i<gv_m3c_supN[p];i+=1) {
        // Tier units are free (lab reward) but still count toward the army cap.
        if (i<gv_m3c_supPaid[p]) {
            m+=UnitTypeGetCost(gv_m3c_supKind[p][i],c_unitCostMinerals);
            g+=UnitTypeGetCost(gv_m3c_supKind[p][i],c_unitCostVespene);
        }
        food+=gf_m3_UnitFood(gv_m3c_supKind[p][i]);
    }
    if (gf_m3_Food(p)+food>100.0 || PlayerGetPropertyInt(p,c_playerPropMinerals)<m || PlayerGetPropertyInt(p,c_playerPropVespene)<g) { return false; }
    PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,m);
    PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);
    return true;
}

void gf_m3c_CallSpots (int p, point c) {
    point s;
    int i;
    int n=gv_m3c_supN[p];
    for (i=0;i<n;i+=1) {
        s=PointWithOffsetPolar(c,2.0,IntToFixed(i*360/n));
        if (!PointPathingPassable(s)) { s=c; }
        gv_m3c_supAt[p][i]=s;
    }
}

bool gt_m3c_CallGo_Func (bool testConds,bool runActions) {
    int p=10;
    int n;
    int i;
    string[24] kind;
    point[24] at;
    actor[24] fx;
    if (!runActions) { return true; }
    if (TriggerGetCurrent()==gv_m3c_callTrig11) { p=11; }
    n=gv_m3c_supN[p];
    for (i=0;i<n;i+=1) {
        kind[i]=gv_m3c_supKind[p][i];
        at[i]=gv_m3c_supAt[p][i];
        if (p==10) {
            fx[i]=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at[i]);
            ActorSend(fx[i],"AnimPlay Warp Birth NonLooping");
        }
        else if (ModI(i,2)==0) {
            fx[i]=libNtve_gf_CreateModelAtPoint("ZergDropPod",at[i]);
            ActorSend(fx[i],"AnimPlay Drop Birth NonLooping");
        }
    }
    // Units appear after the warp-in / drop-pod effect.
    if (p==10) { Wait(2.5,c_timeGame); } else { Wait(3.0,c_timeGame); }
    for (i=0;i<n;i+=1) {
        if (!gv_gameOver) { UnitCreate(1,kind[i],0,p,at[i],270.0); }
    }
    Wait(8.0,c_timeGame);
    for (i=0;i<n;i+=1) {
        if (fx[i]!=null) { ActorSend(fx[i],"Destroy"); }
    }
    return true;
}

void gf_m3c_CallErr (text msg) {
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaError,msg);
}

bool gf_m3c_CallAt (int p, point c) {
    if (c==null || !VisIsVisibleForPlayer(1,c) || !PointPathingPassable(c)) {
        gf_m3c_CallErr(StringExternal("rm3c/CallBad"));
        return false;
    }
    if (!gf_m3c_CallPay(p)) {
        gf_m3c_CallErr(StringExternal("rm3c/CallNoMoney"));
        return false;
    }
    gf_m3c_CallSpots(p,c);
    if (p==10) { TriggerExecute(gv_m3c_callTrig10,false,false); }
    else { TriggerExecute(gv_m3c_callTrig11,false,false); }
    gv_m3c_callAt[p]=GameGetMissionTime()+120.0;
    return true;
}

void gf_m3c_Aim (int p) {
    fixed left;
    if (gv_gameOver || gv_inCinematic || !gv_m3c_callUp) { return; }
    left=gv_m3c_callAt[p]-GameGetMissionTime();
    if (left>0.0) {
        gf_m3c_CallErr(TextReplaceWord(StringExternal("rm3c/CallWaitMsg"),StringToText("%s"),IntToText(CeilingI(left)),c_stringReplaceAll,c_stringCase));
        return;
    }
    gv_m3c_aimP=p;
    gv_m3c_aimTime=GameGetMissionTime();
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm3c/CallAim"));
}

bool gt_m3c_CallBtn_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    if (EventDialogControl()==gv_m3c_callBtnP[10]) { gf_m3c_Aim(10); }
    else if (EventDialogControl()==gv_m3c_callBtnP[11]) { gf_m3c_Aim(11); }
    return true;
}

bool gt_m3c_CallKey_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    if (EventKeyPressed()==c_keyV) { gf_m3c_Aim(10); }
    else if (EventKeyPressed()==c_keyB) { gf_m3c_Aim(11); }
    return true;
}

// The next left click on the map after pressing a button is the spot.
bool gt_m3c_CallMouse_Func (bool testConds,bool runActions) {
    int p=gv_m3c_aimP;
    point c;
    if (!runActions || p==0 || GameGetMissionTime()<gv_m3c_aimTime+0.2) { return true; }
    c=Point(EventMouseClickedPosXWorld(),EventMouseClickedPosYWorld());
    Wait(0.25,c_timeGame);
    if (gv_m3c_aimP!=p) { return true; }
    gv_m3c_aimP=0;
    gf_m3c_CallAt(p,c);
    return true;
}

bool gt_m3c_CallCancel_Func (bool testConds,bool runActions) {
    if (!runActions) { return true; }
    gv_m3c_aimP=0;
    return true;
}

void gf_m3c_CallBtn (int p, int x, string icon, string tip) {
    int img;
    DialogControlCreate(gv_m3c_callDlg,c_triggerControlTypeLabel);
    gv_m3c_callLblP[p]=DialogControlLastCreated();
    DialogControlSetSize(gv_m3c_callLblP[p],PlayerGroupAll(),96,24);
    DialogControlSetPosition(gv_m3c_callLblP[p],PlayerGroupAll(),c_anchorTopLeft,x-16,0);
    DialogControlCreate(gv_m3c_callDlg,c_triggerControlTypeButton);
    gv_m3c_callBtnP[p]=DialogControlLastCreated();
    DialogControlSetSize(gv_m3c_callBtnP[p],PlayerGroupAll(),64,64);
    DialogControlSetPosition(gv_m3c_callBtnP[p],PlayerGroupAll(),c_anchorTopLeft,x,26);
    DialogControlSetPropertyAsText(gv_m3c_callBtnP[p],c_triggerControlPropertyTooltip,PlayerGroupAll(),StringExternal(tip));
    DialogControlCreate(gv_m3c_callDlg,c_triggerControlTypeImage);
    img=DialogControlLastCreated();
    DialogControlSetSize(img,PlayerGroupAll(),52,52);
    DialogControlSetPosition(img,PlayerGroupAll(),c_anchorTopLeft,x+6,32);
    DialogControlSetPropertyAsString(img,c_triggerControlPropertyImage,PlayerGroupAll(),icon);
    DialogControlSetPropertyAsInt(img,c_triggerControlPropertyImageType,PlayerGroupAll(),c_triggerImageTypeNormal);
}

void gf_m3c_CallLabel (int p, text name) {
    int left=CeilingI(gv_m3c_callAt[p]-GameGetMissionTime());
    if (left>0) {
        DialogControlSetPropertyAsText(gv_m3c_callLblP[p],c_triggerControlPropertyText,PlayerGroupAll(),
            TextReplaceWord(StringExternal("rm3c/CallWait"),StringToText("%s"),IntToText(left),c_stringReplaceAll,c_stringCase));
    }
    else {
        DialogControlSetPropertyAsText(gv_m3c_callLblP[p],c_triggerControlPropertyText,PlayerGroupAll(),
            name+StringToText(" ")+TextReplaceWord(StringExternal("rm3c/CallTier"),StringToText("%s"),IntToText(gv_m3c_tier[p]),c_stringReplaceAll,c_stringCase));
    }
}

bool gt_m3c_CallTimer_Func (bool testConds,bool runActions) {
    if (!runActions || !gv_m3c_callUp) { return true; }
    DialogSetVisible(gv_m3c_callDlg,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);
    gf_m3c_CallLabel(10,StringExternal("rm3c/CallKeyP"));
    gf_m3c_CallLabel(11,StringExternal("rm3c/CallKeyZ"));
    return true;
}

void gf_m3c_CallUI () {
    trigger t;
    if (gv_m3c_callUp) { return; }
    gv_m3c_callUp=true;
    gv_m3c_callTrig10=TriggerCreate("gt_m3c_CallGo_Func");
    gv_m3c_callTrig11=TriggerCreate("gt_m3c_CallGo_Func");
    gv_m3c_tier[10]=gf_m3c_Tier(10);
    gv_m3c_tier[11]=gf_m3c_Tier(11);
    gv_m3c_callAt[10]=MaxF(240.0,GameGetMissionTime());
    gv_m3c_callAt[11]=gv_m3c_callAt[10];
    DialogCreate(240,96,c_anchorTop,0,4,false);
    gv_m3c_callDlg=DialogLastCreated();
    DialogSetImageVisible(gv_m3c_callDlg,false);
    gf_m3c_CallBtn(10,46,"Assets\\Textures\\btn-ability-spearofadun-warpinreinforcements.dds","Button/Tooltip/RM3C_AllySupport");
    gf_m3c_CallBtn(11,130,"Assets\\Textures\\btn-unit-collection-primal-Zergling.dds","Button/Tooltip/RM3C_PrimalSupport");
    DialogSetVisible(gv_m3c_callDlg,PlayerGroupSingle(1),true);
    t=TriggerCreate("gt_m3c_CallBtn_Func");
    TriggerAddEventDialogControl(t,1,c_invalidDialogControlId,c_triggerControlEventTypeClick);
    t=TriggerCreate("gt_m3c_CallKey_Func");
    TriggerAddEventKeyPressed(t,1,c_keyV,true,c_keyModifierStateExclude,c_keyModifierStateRequire,c_keyModifierStateExclude);
    TriggerAddEventKeyPressed(t,1,c_keyB,true,c_keyModifierStateExclude,c_keyModifierStateRequire,c_keyModifierStateExclude);
    t=TriggerCreate("gt_m3c_CallMouse_Func");
    TriggerAddEventMouseClicked(t,1,c_mouseButtonLeft,true);
    t=TriggerCreate("gt_m3c_CallCancel_Func");
    TriggerAddEventMouseClicked(t,1,c_mouseButtonRight,true);
    t=TriggerCreate("gt_m3c_CallTimer_Func");
    TriggerAddEventTimePeriodic(t,0.5,c_timeGame);
}

'''

ARRIVE_OLD = '''    fx=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",Point(93.0,44.0));
    ActorSend(fx,"AnimPlay Warp Birth NonLooping");
    pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(100.0,44.0));
    ActorSend(pod,"AnimPlay Drop Birth NonLooping");
    Wait(3.0,c_timeGame);
    ActorSend(fx,"Destroy");
    ActorSend(pod,"Destroy");
    if (gv_gameOver) { return true; }
    UnitCreate(1,"Probe",0,10,Point(93.0,44.0),270.0);
    for (i=0;i<4;i+=1) { UnitCreate(1,"DehakaDrone",0,11,Point(99.0+1.0*i,44.0),270.0); }
    gv_m3_ready=true;
'''
ARRIVE_NEW = '''    // 0.6.16: no ally workers (user 2026-11-03); the top support buttons bring the allied forces.
    gv_m3_ready=true;
    gf_m3c_CallUI();
'''
ADJ_OLD = '''StringExternal("rm3/Adj1"),7.0,c_transmissionDurationSet,true);
    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm3/AdjName"),StringExternal("rm3/Adj2"),7.0,c_transmissionDurationSet,true);
'''
ADJ_NEW = '''StringExternal("rm3c/AdjSup"),7.0,c_transmissionDurationSet,true);
'''
SUBTITLE = '    UIDisplayMessage(PlayerGroupAll(),c_messageAreaSubtitle,StringExternal("rm3/Arrival"));\n'
WORKERS = '    gf_m3_Workers();\n'
ANCHOR = 'bool gt_m3_Arrive_Func (bool testConds,bool runActions) {\n'

STRINGS = {
    'rm3c/AdjSup': '4분 뒤부터 화면 위 [정화자 지원]·[원시저그 지원] 버튼(Ctrl+V·Ctrl+B)을 누르고 지점을 찍으면 그 동맹이 그곳으로 병력을 보냅니다. 각각 재사용 대기 120초, 비용은 그 동맹의 자원입니다. /// After 4 minutes, press [Purifier Support] or [Primal Zerg Support] at the top of the screen (Ctrl+V / Ctrl+B) and pick a spot: that ally sends forces there. 120-second cooldown each; paid with that ally\'s resources.',
    'rm3c/CallWait': '%s초 /// %ss',
    'rm3c/CallAim': '지원할 지점을 왼쪽 클릭하세요. 오른쪽 클릭은 취소입니다. /// Left-click where the support should arrive. Right-click cancels.',
    'rm3c/CallBad': '보이는 곳, 지나갈 수 있는 땅에만 부를 수 있습니다. /// Support can only be called to a visible, walkable spot.',
    'rm3c/CallNoMoney': '그 동맹의 자원이나 인구가 모자라 지원이 오지 않았습니다. /// That ally lacks resources or supply; no support was sent.',
    'rm3c/CallWaitMsg': '%s초 뒤에 부를 수 있습니다. /// Available in %s seconds.',
    'rm3c/CallKeyP': '정화자 Ctrl+V /// Purifier Ctrl+V',
    'rm3c/CallKeyZ': '원시저그 Ctrl+B /// Primal Ctrl+B',
    'rm3c/CallTier': '%s단계 /// Tier %s',
    'Button/Tooltip/RM3C_AllySupport': '정화자 지원 (Ctrl+V)<n/>누른 뒤 지도를 왼쪽 클릭하면 그곳으로 정화자 병력을 차원 소환합니다.<n/>군단병 3, 피닉스 사도 2, 동력기 1(2기 미만일 때), 연구실 단계 추가 병력<n/>비용은 정화자 자원입니다. 재사용 대기 120초. /// Purifier Support (Ctrl+V)<n/>Press, then left-click the map to warp in Purifier forces there.<n/>3 Legionnaires, 2 Fenix Adepts, 1 Energizer (if fewer than 2), plus lab tier units<n/>Paid with Purifier resources. 120-second cooldown.',
    'Button/Tooltip/RM3C_PrimalSupport': '원시저그 지원 (Ctrl+B)<n/>누른 뒤 지도를 왼쪽 클릭하면 그곳에 원시저그 병력을 낙하 주머니로 투하합니다.<n/>원시 저글링 6, 바퀴 1, 히드라 2, 연구실 단계 추가 병력<n/>비용은 원시저그 자원입니다. 재사용 대기 120초. /// Primal Zerg Support (Ctrl+B)<n/>Press, then left-click the map to drop Primal Zerg forces there.<n/>6 Primal Zerglings, 1 Roach, 2 Hydralisks, plus lab tier units<n/>Paid with Primal Zerg resources. 120-second cooldown.',
}


def once(t, old, new):
    assert t.count(old) == 1, old[:70]
    return t.replace(old, new)


def edit(t):
    t = once(t, ANCHOR, MODULE + ANCHOR)
    t = once(t, ARRIVE_OLD, ARRIVE_NEW)
    t = once(t, ADJ_OLD, ADJ_NEW)
    t = once(t, SUBTITLE, '')
    t = once(t, WORKERS, '    // 0.6.16: no ally workers to top up.\n')
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        d = root / MAP
        p = d / 'mapscript.galaxy'
        raw = p.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in raw else '\n'
        p.write_bytes(edit(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'))
        ko = set_lines((d / KO).read_bytes(), STRINGS)
        (d / KO).write_bytes(ko)
        V35.gate('kokr', ko)
        for loc in V35.OTHER_LOCALES:
            (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not n.startswith(MAP + '/') and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
