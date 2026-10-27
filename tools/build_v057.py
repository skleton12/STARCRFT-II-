#!/usr/bin/env python3
"""0.5.6 -> 0.5.7: 레드스톤 [동맹 지원]을 협동전 상단 능력 패널(Top Bar) 방식으로 (사용자 2026-10-27).

사용자: "이게 아님. 협동전처럼 위에 그런 거 있어야 함" + GPT 설명(사령관 상단 능력 패널: 선택 없이 쓰는 능력 버튼,
아이콘·단축키·설명·재사용 대기 표시, 위치 지정형이면 지도에서 지점 선택).

원작 협동전 구조를 그대로 따른다 (starcoop LibCOMI/LibCOUI 확인):
- 보이지 않는 '전역 시전 유닛'(협동전 CoopGlobalCaster와 같은 역할, 무적·그리지 않음·대상 불가)에 능력을 달고
  선택 불가로 둔다. 화면 위 대화 상자에 명령 패널(CommandPanel)을 만들어 그 유닛 묶음을 연결한다
  (협동전 libCOUI_gf_CU_GPSetUnit과 같은 방식). 그래서 버튼 아이콘·툴팁·단축키·재사용 대기 표시·
  지점 지정 커서는 게임이 원래 능력처럼 그린다.
- 능력 RM5_AllySupport: 지점 지정(CAbilEffectTarget), 재사용 대기 30초, 첫 사용 시작 약 1분 뒤 (시험값).
  아이콘: 원작 아둔의 창 '차원 증원' (btn-ability-spearofadun-warpinreinforcements.dds, Liberty 데이터).
- 시전되면 스크립트가 0.5.6과 같은 묶음을 보낸다 (정화자 차원 소환, 원시저그 낙하 주머니, 동맹 자원·인구 100).
  보이지 않는 곳·못 가는 땅이거나 두 동맹 모두 돈·인구가 모자라면 재사용 대기를 되돌리고 안내한다.
- 0.5.6의 일반 대화 상자 버튼·마우스 클릭 처리는 지운다.
- 패배 판정은 PreventDefeat 유닛만 세므로 시전 유닛은 PreventDefeat를 끈다.

Usage: python3 tools/build_v057.py <0.5.6 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v041 import merge

OLD, NEW = b'version=0.5.6', b'version=0.5.7'
M5 = 'TTosh01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ICON = r'Assets\Textures\btn-ability-spearofadun-warpinreinforcements.dds'
HOTKEY = 'V'

DATA = {
    'unitdata.xml': f'''<Catalog>
  <CUnit id="RM5_AllyCaster">
    <Name value="Unit/Name/RM5_AllyCaster"/>
    <Race value="Terr"/>
    <FlagArray index="PreventDefeat" value="0"/>
    <FlagArray index="Invulnerable" value="1"/>
    <FlagArray index="NoPortraitTalk" value="1"/>
    <FlagArray index="Turnable" value="0"/>
    <LifeStart value="10000"/>
    <LifeMax value="10000"/>
    <FlagArray index="NoDraw" value="1"/>
    <FlagArray index="Untargetable" value="1"/>
    <FlagArray index="Uncursorable" value="1"/>
    <FlagArray index="Unradarable" value="1"/>
    <FlagArray index="TownAlert" value="0"/>
    <Sight value="0"/>
    <AbilArray Link="RM5_AllySupport"/>
    <CardLayouts index="0">
      <LayoutButtons Face="RM5_AllySupport" Type="AbilCmd" AbilCmd="RM5_AllySupport,Execute" Row="0" Column="0"/>
    </CardLayouts>
  </CUnit>
</Catalog>''',
    'actordata.xml': '''<Catalog>
  <CActorUnit id="RM5_AllyCaster" parent="GenericUnitStandard" unitName="RM5_AllyCaster">
    <Model value="Invisible"/>
  </CActorUnit>
</Catalog>''',
    'effectdata.xml': '''<Catalog>
  <CEffectSet id="RM5_AllySupportSet"/>
  <CEffectEnumArea id="RM5_AllySupportSearch">
    <AreaArray Radius="3"/>
  </CEffectEnumArea>
</Catalog>''',
    'abildata.xml': '''<Catalog>
  <CAbilEffectTarget id="RM5_AllySupport">
    <Flags index="Transient" value="1"/>
    <Effect value="RM5_AllySupportSet"/>
    <Cost>
      <Cooldown Location="Unit" TimeStart="55" TimeUse="30"/>
    </Cost>
    <Range value="500"/>
    <Arc value="360"/>
    <CursorEffect value="RM5_AllySupportSearch"/>
    <CmdButtonArray index="Execute" DefaultButtonFace="RM5_AllySupport"/>
  </CAbilEffectTarget>
</Catalog>''',
    'buttondata.xml': f'''<Catalog>
  <CButton id="RM5_AllySupport">
    <Icon value="{ICON}"/>
    <Name value="Button/Name/RM5_AllySupport"/>
    <Tooltip value="Button/Tooltip/RM5_AllySupport"/>
  </CButton>
</Catalog>''',
}

STRINGS = [
    'Unit/Name/RM5_AllyCaster=동맹 지원 /// Ally Support',
    'Button/Name/RM5_AllySupport=동맹 지원 /// Ally Support',
    'Button/Tooltip/RM5_AllySupport=정화자와 원시저그가 지정한 지점으로 병력을 보냅니다.<n/>정화자: 파수병 2, 피닉스 사도 1, 동력기 1(2기 미만일 때), 해금 유닛 1 (차원 소환)<n/>원시저그: 원시 저글링 4, 바퀴 1, 히드라 1, 해금 유닛 (낙하 주머니)<n/>비용은 각 동맹의 자원입니다. 보이는 곳, 걸어갈 수 있는 땅에만 부를 수 있습니다. '
    '/// The Purifiers and Primal Zerg send forces to the target point.<n/>Purifiers: 2 Sentinels, 1 Adept, 1 Energizer (if fewer than 2), 1 unlocked unit (warp-in)<n/>Primal Zerg: 4 Primal Zerglings, 1 Roach, 1 Hydralisk, unlocked units (drop pods)<n/>Paid with each ally\'s resources. Only to a visible, walkable spot.',
]
ADJ = 'rm5/AdjSup=1분 뒤부터 화면 위 [동맹 지원] 능력으로 지점을 정하면 정화자와 원시저그가 그곳으로 병력을 보냅니다. 재사용 대기 30초, 비용은 동맹 자원입니다. /// In one minute, use [Ally Support] at the top of the screen and pick a spot: the Purifiers and Primal Zerg send forces there. 30-second cooldown; costs come from ally resources.'

CALL = r"""// 0.5.7: co-op Top Bar Ally Support (user 2026-10-27 "협동전처럼 위에 그런 거"). Same structure as co-op
// (starcoop libCOUI_gf_CU_GPSetUnit): an invisible, unselectable global caster unit holds the point-target ability and
// a command panel at the top of the screen shows it, so the game draws icon, tooltip, hotkey, cooldown and cursor.
// On cast both allies send their group to the point (Purifiers warp in, Primal Zerg drop pods), ally money, cap 100.
unit gv_m5_caster;
unitgroup gv_m5_casterGroup;
int gv_m5_callDlg;
int gv_m5_callPanel;
bool gv_m5_callUp;
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

void gf_m5_CallRefund (string msg) {
    UnitAbilityReset(gv_m5_caster,AbilityCommand("RM5_AllySupport",0),c_spendLocationAll);
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaError,StringExternal(msg));
}

bool gt_m5_CallCast_Func (bool testConds,bool runActions) {
    point c;
    bool sent=false;
    if (!runActions || gv_gameOver) { return true; }
    c=EventUnitTargetPoint();
    if (EventUnitTargetUnit()!=null) { c=UnitGetPosition(EventUnitTargetUnit()); }
    if (c==null || !VisIsVisibleForPlayer(1,c) || !PointPathingPassable(c)) {
        gf_m5_CallRefund("rm5/CallBad");
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
    if (!sent) { gf_m5_CallRefund("rm5/CallNoMoney"); }
    return true;
}

void gf_m5_CallUI () {
    trigger t;
    if (gv_m5_callUp) { return; }
    gv_m5_callUp=true;
    gv_m5_callTrig8=TriggerCreate("gt_m5_CallGo_Func");
    gv_m5_callTrig9=TriggerCreate("gt_m5_CallGo_Func");
    UnitCreate(1,"RM5_AllyCaster",c_unitCreateIgnorePlacement,1,Point(0.5,0.5),270.0);
    gv_m5_caster=UnitLastCreated();
    UnitSetState(gv_m5_caster,c_unitStateSelectable,false);
    gv_m5_casterGroup=UnitGroupEmpty();
    UnitGroupAdd(gv_m5_casterGroup,gv_m5_caster);
    DialogCreate(96,96,c_anchorTop,0,64,false);
    gv_m5_callDlg=DialogLastCreated();
    DialogSetImageVisible(gv_m5_callDlg,false);
    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeCommandPanel);
    gv_m5_callPanel=DialogControlLastCreated();
    DialogControlSetSize(gv_m5_callPanel,PlayerGroupAll(),80,80);
    DialogControlSetPosition(gv_m5_callPanel,PlayerGroupAll(),c_anchorTopLeft,8,8);
    libNtve_gf_SetDialogItemUnitGroup(gv_m5_callPanel,gv_m5_casterGroup,PlayerGroupSingle(1));
    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),true);
    t=TriggerCreate("gt_m5_CallCast_Func");
    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_AllySupport",0),c_abilEffectStageCast,false);
}

void gf_m5_CallTick () {
    if (!gv_m5_callUp) { return; }
    DialogSetVisible(gv_m5_callDlg,PlayerGroupSingle(1),!gv_inCinematic && !gv_gameOver);
}

"""


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        s = M5 + 'mapscript.galaxy'
        t = files[s].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = t.replace('\r\n', '\n')
        a = t.index('// 0.5.6: co-op style Ally Support call-down')
        b = t.index('bool gt_m5_Tick_Func (bool testConds,bool runActions) {\n')
        assert a < b and 'gf_m5_CallTick ()' in t[a:b]
        t = t[:a] + CALL + t[b:]
        assert t.count('gf_m5_CallUI();') == 1 and t.count('gf_m5_CallTick();') == 1
        assert 'TriggerAddEventMouseClicked' not in t[a:a + len(CALL)]
        files[s] = t.replace('\n', nl).encode('utf-8')
        for name, xml in DATA.items():
            key = M5 + GD + name
            assert 'RM5_Ally' not in files[key].decode('utf-8')
            files[key] = merge(files[key], xml.encode('utf-8'))
        ko = files[M5 + KO].decode('utf-8-sig')
        knl = '\r\n' if '\r\n' in ko else '\n'
        lines = ko.split(knl)
        hit = [i for i, l in enumerate(lines) if l.startswith('rm5/AdjSup=')]
        assert len(hit) == 1
        lines[hit[0]] = ADJ
        ko = knl.join(lines)
        files[M5 + KO] = (ko.rstrip('\r\n') + knl + knl.join(STRINGS) + knl).encode('utf-8')
        V35.gate('kokr', files[M5 + KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M5}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[M5 + KO])
        for loc in ['kokr'] + V35.OTHER_LOCALES:
            hp = f'{M5}{loc}.sc2data/localizeddata/gamehotkeys.txt'
            d = files[hp]
            h = d.decode('utf-8-sig')
            hn = '\r\n' if '\r\n' in h else '\n'
            files[hp] = (h.rstrip('\r\n') + hn + f'Button/Hotkey/RM5_AllySupport={HOTKEY}' + hn).encode(
                'utf-8-sig' if d.startswith(b'\xef\xbb\xbf') else 'utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        import xml.etree.ElementTree as ET
        for n, d in files.items():
            if n.startswith(M5) and n.endswith('.xml'): ET.fromstring(d)
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
