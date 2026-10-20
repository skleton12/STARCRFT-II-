#!/usr/bin/env python3
"""Build CCM 0.4.42 from 0.4.41: 레이너 해금 → 동맹 유닛 해금 (4번 + 공통 스크립트).

사용자 확정 표 (2026-10-19, 2026-10-20 수정; GPT 조사 docs/research/purifier_and_primal_unit_reference.md 반영):
  레이너 해금(원작 생산 명령 허용)  | 정화자 (차원 관문 새 칸)        | 원시저그
  화염차 FactoryTrain 5            | 선동자 StalkerPurifier           | 라바사우르스 (저글링 2기 원시 전투)
  다이아몬드백 FactoryTrain 7      | 불멸자 Immortal (정화자 외형)    | 원시 점화자 (바퀴 2기)
  공성 전차 FactoryTrain 1         | 거신 ColossusPurifier            | 원시 숙주 DehakaSwarmHost (감시자 알)
  골리앗 FactoryTrain 6            | 분열기 Disruptor (정화자 외형)   | 원시 울트라리스크 (감시자 알)
  바이킹 StarportTrain 4           | 신기루 PhoenixPurifier           | 원시 뮤탈리스크 (히드라 2기)
  밴시·망령 StarportTrain 1·7      | 정찰기 Scout                     | 원시 수호군주 (바퀴 2기)
  과학선·밤까마귀 StarportTrain 6·2| 보전기 SentryFenix               | 관통촉수 (히드라 2기)
  토르 FactoryTrain 4              | 폭풍함 TempestPurifier (정화자면 넣음, 사용자) | 티라노조르 (울트라 2기)
  전투순양함 StarportTrain 3       | 우주모함 Carrier (정화자 외형)   | 땅무지 숙주 (원시 숙주 2기)
  피닉스 영웅 전투복(용기병·중재자)은 제외 (사용자).
모드 변경: 원시 전투(합체)와 숙주·울트라 알의 원작 건물 요구조건(무리 우두머리 건물)을 뺀다. 데하카 유전자 돌연변이(사령관 15레벨)는 끈다.
차원 관문 새 칸은 8번(정화자)에게만 열고 다른 플레이어는 막는다. 생산 비율·대기 시간은 시험값.

Usage: python3 tools/build_v0442.py <0.4.41 zip> <new output zip>
"""
import argparse, copy, re, subprocess, sys, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD, NEW = b'version=0.4.41', b'version=0.4.42'
M4 = 'TTychus01.SC2Map'
SEEDS = ['StalkerPurifier', 'ColossusPurifier', 'Disruptor', 'PhoenixPurifier', 'Scout', 'SentryFenix', 'TempestPurifier',
         'DehakaTrainEggSwarmHost', 'DehakaTrainEggUltralisk', 'DehakaSwarmHost', 'DehakaUltraliskLevel2', 'DehakaRoachLevel3',
         'ImpalerDehaka', 'DehakaMutaliskLevel3', 'DehakaGuardian', 'DehakaPrimalSwarmHost', 'DehakaUltraliskLevel3',
         'PrimalZerglingRavasaurMerge', 'PrimalRoachLevel2Merge', 'PrimalHydraliskImpalerMerge', 'PrimalHydraliskToMutalisk',
         'PrimalRoachGuardianMerge', 'PrimalSwarmHostMerge', 'PrimalUltraliskLevel2Merge']
DROP = ('FenixMojo|FenixWarbringer|FenixCommander|FenixChampion|FenixPurificationNova|^SOA|Vorazun|DehakaMurvar|DehakaGlevig|'
        'DehakaDakrun|ReviveEgg|RespawnOnDeath|MorphToFenix|Champion')
MERGES = ['PrimalZerglingRavasaurMerge', 'PrimalRoachLevel2Merge', 'PrimalHydraliskImpalerMerge', 'PrimalHydraliskToMutalisk',
          'PrimalRoachGuardianMerge', 'PrimalSwarmHostMerge', 'PrimalUltraliskLevel2Merge']
# Purifier warp slots: (WarpGateTrain index, unit, warp cooldown seconds — trial)
WARP = [(7, 'StalkerPurifier', 32), (8, 'Immortal', 55), (9, 'ColossusPurifier', 75), (10, 'Disruptor', 50), (11, 'PhoenixPurifier', 35),
        (12, 'Scout', 40), (13, 'SentryFenix', 32), (14, 'TempestPurifier', 60), (15, 'Carrier', 90)]
SKIN = {'Immortal': 'Immortal_Purifier', 'Carrier': 'Carrier_Purifier', 'Disruptor': 'Disruptor_Purifier'}
LEVEL = r'(?:Raynor|Kerrigan|Artanis|Swann|Zagara|Vorazun|Karax|Abathur|Alarak|Nova|Stukov|Fenix|Dehaka|Horner|Han|Tychus|Zeratul|Stetmann|Mengsk)Level\d\d'


def src(path):
    return (ROOT / 'source' / path).read_text('utf-8')


def element(text, tag_id):
    m = re.search(r'<(C\w+)(?: default="1")? id="' + re.escape(tag_id) + r'"[^>]*?(?:/>|>.*?</\1>)', text, re.S)
    assert m, tag_id
    return m.group(0)


def sub1(t, a, b, flags=0, count=1):
    t2, n = re.subn(a, b, t, flags=flags)
    assert n >= count, a
    return t2


def edit(gd):
    def rw(name, fn):
        p = gd / name
        p.write_text(fn(p.read_text('utf-8')), 'utf-8')

    def add(t, xml):
        i = t.rindex('</Catalog>')
        return t[:i] + xml + t[i:]

    # Turrets: WoL data has no turret catalog entries (FreeRotate etc. come from later mods) → standalone like NydusCanalAttacker.
    tur = ('<CTurret id="FreeRotate"><YawArc value="360" /><YawRate value="720" /><YawIdleRate value="360" /></CTurret>'
           '<CTurret id="Phoenix"><Idle value="ResetIfMoving" /><YawArc value="360" /><YawRate value="539.2968" /></CTurret>'
           '<CTurret id="Colossus"><YawArc value="360" /><YawRate value="360" /></CTurret>')
    rw('turretdata.xml', lambda t: add(sub1(t, r'<CTurret id="PhoenixPurifier" parent="FreeRotate">',
                                            '<CTurret id="PhoenixPurifier"><YawArc value="360" />'), tur))

    def actors(t):
        add_x = ''.join(f'<CActorSound id="{i}_Land" parent="SoundOneShot" />'
                        for i in ('Colossus', 'Mutalisk', 'SwarmHost', 'Infestor', 'Disruptor', 'Tempest') if f'id="{i}_Land"' not in t)
        add_x += element(src('void.sc2mod/base.sc2data/gamedata/actordata.xml'), 'PurificationNovaBirth')
        add_x += element(src('swarm.sc2mod/base.sc2data/gamedata/actordata.xml'), 'DeathRagdollDetonationForce')
        t = re.sub(r'\n[ \t]*<On Terms="[^"]*" Send="Create DehakaMutaliskReviveEggDeath" />', '', t)
        # Ally-only Purifier look for shared unit IDs (same RM3_AllySkin marker as buildings).
        m = re.search(r'<CActorUnit id="Disruptor"[^>]*>', t)
        t = t[:m.end()] + '<On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap Disruptor_Purifier" />' + t[m.end():]
        for u in ('Immortal', 'Carrier'):
            add_x += f'<CActorUnit id="{u}"><On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap {SKIN[u]}" /></CActorUnit>'
        return add(t, add_x)
    rw('actordata.xml', actors)

    def units(t):
        t = re.sub(r'\n[ \t]*<BehaviorArray Link="SpawnLocusts" />', '', t)  # Dehaka hosts spawn through their own ability
        return re.sub(r'\n[ \t]*<LayoutButtons [^>]*Requirements="' + LEVEL + r'"[^>]*/>', '', t)
    rw('unitdata.xml', units)
    rw('requirementdata.xml', lambda t: add(re.sub(r'\n[ \t]*<CRequirement id="' + LEVEL + r'">.*?</CRequirement>', '', t, flags=re.S),
                                            '<CRequirement id="RMZ_Never"><NodeArray index="Use" Link="RMZ_NeverNode" /></CRequirement>'))
    rw('requirementnodedata.xml', lambda t: add(t, '<CRequirementCountUpgrade id="RMZ_NeverNode"><Count Link="RMZ_NeverUpgrade" State="CompleteOnly" /></CRequirementCountUpgrade>'))
    rw('upgradedata.xml', lambda t: add(t, '<CUpgrade id="RMZ_NeverUpgrade" />'))
    # Gene mutations are a Dehaka level-15 talent (level rule): never pass.
    rw('validatordata.xml', lambda t: sub1(t, r'(<CValidatorPlayerRequirement id="DehakaGeneCheck">\s*)<Value value="DehakaLevel15" />',
                                           r'\1<Find value="1" /><Value value="RMZ_Never" />'))

    def abil(t):
        egg = ''.join(
            f'<InfoArray index="Train{n}" Effect="DehakaTrainInitialSet" Rotation="Source"><Charge><CountMax value="10" />'
            '<CountStart value="1" /><CountUse value="1" /><Location value="Unit" /><TimeStart value="16" /><TimeUse value="16" />'
            '<Flags index="EnableChargeTimeQueuing" value="1" /></Charge><Cooldown TimeStart="20" />'
            f'<Button DefaultButtonFace="{face}" Requirements=""><Flags index="ToSelection" value="1" /></Button>'
            f'<Unit value="{unit}" /><Flags index="InheritRally" value="1" /></InfoArray>'
            for n, face, unit in ((4, 'DehakaSwarmHost', 'DehakaTrainEggSwarmHost'), (5, 'DehakaUltralisk', 'DehakaTrainEggUltralisk')))
        m = re.search(r'<CAbilTrain id="DehakaBarracksTrainEgg">.*?</CAbilTrain>', t, re.S)
        assert 'index="Train4"' not in m.group(0)
        t = t[:m.start()] + m.group(0).replace('</CAbilTrain>', egg + '</CAbilTrain>') + t[m.end():]
        for a in ('DehakaTrainEggMorphToSwarmHost', 'DehakaTrainEggMorphToUltralisk'):  # pay once, at the egg (0.4.24 rule)
            m = re.search(r'<CAbilTrain id="' + a + r'">.*?</CAbilTrain>', t, re.S)
            t = t[:m.start()] + re.sub(r'(<Resource index="\w+" value=")\d+(" />)', r'\g<1>0\2', m.group(0)) + t[m.end():]
        for a in MERGES:  # original needs Dehaka pack-leader structures, not in this mod
            m = re.search(r'<CAbilMerge id="' + a + r'">.*?</CAbilMerge>', t, re.S)
            t = t[:m.start()] + re.sub(r'Requirements="[^"]*"', 'Requirements=""', m.group(0)) + t[m.end():]
        warp = ''.join(f'<InfoArray index="Train{n}" Time="5" Unit="{u}"><Charge><Link value="RM4_WarpGate" /><CountMax value="3" />'
                       f'<CountStart value="3" /><CountUse value="1" /><TimeUse value="{cd}" /></Charge><Cooldown Link="WarpGateTrain" TimeUse="0" />'
                       f'<Button DefaultButtonFace="{u}" State="Available" /></InfoArray>' for n, u, cd in WARP)
        return add(t, f'<CAbilWarpTrain id="WarpGateTrain">{warp}</CAbilWarpTrain>')
    rw('abildata.xml', abil)


# ---------------------------------------------------------------- script
SCRIPT_GLOBALS_OLD = 'string[4] gv_m4_eggUnit;\n'
SCRIPT_GLOBALS_NEW = 'string[6] gv_m4_eggUnit;\n'
UNL = '''
// Raynor unlock -> ally unlock (user table 2026-10-20). k = 0..8, see tools/build_v0442.py.
bool gf_m4_Unl (int k) {
    if (k==0) { return TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",5)); }
    if (k==1) { return TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",7)); }
    if (k==2) { return TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",1)); }
    if (k==3) { return TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",6)); }
    if (k==4) { return TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",4)); }
    if (k==5) { return TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",1)) || TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",7)); }
    if (k==6) { return TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",6)) || TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",2)); }
    if (k==7) { return TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",4)); }
    if (k==8) { return TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",3)); }
    return false;
}

bool gf_m4_IsArmyType (unit u) {
    string t;
    // Ally army = non-structure units that use supply, minus workers and eggs (interceptors, locusts, creepers use none).
    t=UnitGetType(u);
    if (t=="Probe" || t=="DehakaDrone" || StringContains(t,"DehakaTrainEgg",c_stringBegin,c_stringCase)) { return false; }
    if (!UnitFilterMatch(u,UnitGetOwner(u),UnitFilter(0,0,(1 << c_targetFilterStructure),0))) { return false; }
    return UnitTypeGetProperty(t,c_unitPropSuppliesUsed)>0.0;
}

void gf_m4_Unlocks () {
    int k;
    int p;
    string[9] merge;
    // Purifier warp slots WarpGateTrain 6..14 (Train7..15): player 8 only, when Raynor has the matching unlock.
    for (k=0;k<=8;k+=1) {
        for (p=2;p<=7;p+=1) { TechTreeAbilityAllow(p,AbilityCommand("WarpGateTrain",6+k),false); }
        TechTreeAbilityAllow(1,AbilityCommand("WarpGateTrain",6+k),false);
        TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",6+k),gf_m4_Unl(k));
    }
    TechTreeUnitAllow(8,"StalkerPurifier",true);
    TechTreeUnitAllow(8,"Immortal",true);
    TechTreeUnitAllow(8,"ColossusPurifier",true);
    TechTreeUnitAllow(8,"Disruptor",true);
    TechTreeUnitAllow(8,"PhoenixPurifier",true);
    TechTreeUnitAllow(8,"Scout",true);
    TechTreeUnitAllow(8,"SentryFenix",true);
    TechTreeUnitAllow(8,"TempestPurifier",true);
    TechTreeUnitAllow(8,"Carrier",true);
    // Primal Warden eggs: host (Train4) with Siege Tank, ultralisk (Train5) with Goliath.
    TechTreeAbilityAllow(9,AbilityCommand("DehakaBarracksTrainEgg",3),gf_m4_Unl(2));
    TechTreeAbilityAllow(9,AbilityCommand("DehakaBarracksTrainEgg",4),gf_m4_Unl(3));
    for (k=0;k<=8;k+=1) { merge[k]=""; }
    merge[0]="PrimalZerglingRavasaurMerge";
    merge[1]="PrimalRoachLevel2Merge";
    merge[4]="PrimalHydraliskToMutalisk";
    merge[5]="PrimalRoachGuardianMerge";
    merge[6]="PrimalHydraliskImpalerMerge";
    merge[7]="PrimalUltraliskLevel2Merge";
    merge[8]="PrimalSwarmHostMerge";
    for (k=0;k<=8;k+=1) {
        if (merge[k]!="") {
            TechTreeAbilityAllow(9,AbilityCommand(merge[k],0),gf_m4_Unl(k));
            TechTreeAbilityAllow(9,AbilityCommand(merge[k],1),gf_m4_Unl(k));
        }
    }
}

void gf_m4_MergeOne (string src, string abil) {
    unitgroup g;
    unit a;
    unit b;
    unit u;
    int i;
    // Primal combat (original merge ability): only idle units, keep at least 2 of the source kind (trial).
    g=UnitGroup(src,9,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);
    if (UnitGroupCount(g,c_unitCountAlive)<4) { return; }
    a=null;
    b=null;
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (UnitOrderCount(u)==0) {
            if (a==null) { a=u; }
            else if (b==null && DistanceBetweenPoints(UnitGetPosition(a),UnitGetPosition(u))<8.0) { b=u; }
        }
    }
    if (a!=null && b!=null) { UnitIssueOrder(a,OrderTargetingUnit(AbilityCommand(abil,1),b),c_orderQueueReplace); }
}

void gf_m4_Merges () {
    if (gf_m4_Unl(0)) { gf_m4_MergeOne("DehakaZerglingLevel2","PrimalZerglingRavasaurMerge"); }
    if (gf_m4_Unl(1) && (!gf_m4_Unl(5) || ModI(gv_m4_turn9,2)==0)) { gf_m4_MergeOne("DehakaRoachLevel2","PrimalRoachLevel2Merge"); }
    else if (gf_m4_Unl(5)) { gf_m4_MergeOne("DehakaRoachLevel2","PrimalRoachGuardianMerge"); }
    if (gf_m4_Unl(4) && (!gf_m4_Unl(6) || ModI(gv_m4_turn9,2)==0)) { gf_m4_MergeOne("DehakaHydraliskLevel2","PrimalHydraliskToMutalisk"); }
    else if (gf_m4_Unl(6)) { gf_m4_MergeOne("DehakaHydraliskLevel2","PrimalHydraliskImpalerMerge"); }
    if (gf_m4_Unl(7)) { gf_m4_MergeOne("DehakaUltraliskLevel2","PrimalUltraliskLevel2Merge"); }
    if (gf_m4_Unl(8)) { gf_m4_MergeOne("DehakaSwarmHost","PrimalSwarmHostMerge"); }
}
'''
FOOD_OLD = '''fixed gf_m4_UnitFood (string kind) {
    // Data Food values: Primal Zergling 1, every other ally army unit 2.
    if (kind=="DehakaZerglingLevel2") { return 1.0; }
    return 2.0;
}
'''
FOOD_NEW = '''fixed gf_m4_UnitFood (string kind) {
    // Supply from the unit data (0.4.42: new ally kinds use 2-8).
    return UnitTypeGetProperty(kind,c_unitPropSuppliesUsed);
}
'''
ARMY_OLD = 'if (UnitIsAlive(u) && (t=="ZealotPurifier" || t=="AdeptFenix" || t=="RM21_Energizer" || t=="DehakaZerglingLevel2" || t=="DehakaRavasaur" || t=="DehakaHydraliskLevel2" || t=="DehakaRoachLevel2")) { UnitGroupAdd(army,u); }'
ARMY_NEW = 'if (UnitIsAlive(u) && gf_m4_IsArmyType(u)) { UnitGroupAdd(army,u); }'
HATCH_OLD = '''        c=ModI(gv_m4_turn9,4)-1;
        if (c<0) { c=0; }
'''
HATCH_NEW = '''        // Base order zergling, zergling, roach, hydralisk; unlocked host/ultralisk join the rotation (trial).
        c=ModI(gv_m4_turn9,4+gv_m4_eggExtra)-1;
        if (c<0) { c=0; }
        if (c>=3) { c=gv_m4_eggSlot[c-3]; }
'''
EGGCOUNT_OLD = 'UnitGroupCount(UnitGroup("DehakaTrainEggHydralisk",9,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)>=2*n'
EGGCOUNT_NEW = ('UnitGroupCount(UnitGroup("DehakaTrainEggHydralisk",9,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)'
                '+UnitGroupCount(UnitGroup("DehakaTrainEggSwarmHost",9,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)'
                '+UnitGroupCount(UnitGroup("DehakaTrainEggUltralisk",9,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)>=2*n')
HATCHFOOD_OLD = 'if (gf_m4_Food(9)+2.0>100.0 || PlayerGetPropertyInt(9,c_playerPropMinerals)<m'
HATCHFOOD_NEW = 'if (gf_m4_Food(9)+6.0>100.0 || PlayerGetPropertyInt(9,c_playerPropMinerals)<m'
WARP_OLD = '''        k=ModI(gv_m4_turn8,4);
        if (k==3 && UnitGroupCount(UnitGroup("RM21_Energizer",8,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)>=2) { k=0; }
        if (k==3) { cmd=5; } else if (k==2) { cmd=1; } else { cmd=0; }
'''
WARP_NEW = '''        // Base: Sentinel, Sentinel, Fenix Adept, Energizer (<2). Unlocked Purifier units join the rotation (0.4.42, trial).
        k=ModI(gv_m4_turn8,4+gv_m4_warpExtra);
        if (k==3 && UnitGroupCount(UnitGroup("RM21_Energizer",8,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)>=2) { k=0; }
        if (k>=4) { cmd=gv_m4_warpSlot[k-4]; } else if (k==3) { cmd=5; } else if (k==2) { cmd=1; } else { cmd=0; }
'''
EXTRA_GLOBALS = 'int gv_m4_warpExtra;\nint[9] gv_m4_warpSlot;\nint gv_m4_eggExtra;\nint[2] gv_m4_eggSlot;\n'
PRODUCE_OLD = '    gf_m4_Warp();\n    gf_m4_Hatch();\n'
PRODUCE_NEW = '''    // Unlocked extras for this tick's rotation.
    gv_m4_warpExtra=0;
    for (k=0;k<=8;k+=1) {
        if (gf_m4_Unl(k)) { gv_m4_warpSlot[gv_m4_warpExtra]=6+k; gv_m4_warpExtra+=1; }
    }
    gv_m4_eggExtra=0;
    if (gf_m4_Unl(2)) { gv_m4_eggSlot[gv_m4_eggExtra]=3; gv_m4_eggExtra+=1; }
    if (gf_m4_Unl(3)) { gv_m4_eggSlot[gv_m4_eggExtra]=4; gv_m4_eggExtra+=1; }
    gf_m4_Warp();
    gf_m4_Hatch();
    gf_m4_Merges();
'''
EGGINIT_OLD = '    gv_m4_eggUnit[2]="DehakaTrainEggHydralisk";\n'
EGGINIT_NEW = EGGINIT_OLD + '    gv_m4_eggUnit[3]="DehakaTrainEggSwarmHost";\n    gv_m4_eggUnit[4]="DehakaTrainEggUltralisk";\n'
TICK_OLD = '    gf_m4_Gates();\n'
TICK_NEW = '    gf_m4_Gates();\n    gf_m4_Unlocks();\n'
SKIN_OLD = '        if (!UnitHasBehavior2(u,"RM3_AllySkin")) { UnitBehaviorAdd(u,"RM3_AllySkin",u,1); }\n'
SKIN_NEW = SKIN_OLD + '        if (gf_m4_IsArmyType(u)) { libNtve_gf_MakeUnitUncommandable(u,true); }  // new ally kinds (0.4.42)\n'


def script(t, support=False):
    def r(a, b):
        nonlocal t
        assert t.count(a) == 1, a[:80]
        t = t.replace(a, b)
    r(SCRIPT_GLOBALS_OLD, SCRIPT_GLOBALS_NEW + EXTRA_GLOBALS)
    r(FOOD_OLD, FOOD_NEW)
    r('unitgroup gf_m4_Army (int p) {', UNL.strip('\n').split('bool gf_m4_IsArmyType')[0] + 'bool gf_m4_IsArmyType' +
      UNL.split('bool gf_m4_IsArmyType')[1].split('void gf_m4_Unlocks')[0] + 'unitgroup gf_m4_Army (int p) {')
    r(ARMY_OLD, ARMY_NEW)
    r(HATCH_OLD, HATCH_NEW)
    r(EGGCOUNT_OLD, EGGCOUNT_NEW)
    r(HATCHFOOD_OLD, HATCHFOOD_NEW)
    r(WARP_OLD, WARP_NEW)
    r('void gf_m4_Produce () {', 'void gf_m4_Unlocks' + UNL.split('void gf_m4_Unlocks')[1] + '\nvoid gf_m4_Produce () {')
    r(PRODUCE_OLD, PRODUCE_NEW)
    r(EGGINIT_OLD, EGGINIT_NEW)
    r(TICK_OLD, TICK_NEW)
    r(SKIN_OLD, SKIN_NEW)
    return t


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(root / M4), '--liberty-base', '--skip-existing',
                        f'--drop={DROP}', *SEEDS], check=True, stdout=subprocess.DEVNULL)
        (root / M4 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        edit(root / M4 / 'base.sc2data/gamedata')
        sp = root / M4 / 'mapscript.galaxy'
        sp.write_text(script(sp.read_text('utf-8')), 'utf-8')
        ko = root / M4 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        ko.write_bytes(strings(ko.read_bytes()))
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (root / M4 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra: out.writestr(f, (root / f).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if not n.startswith(M4 + '/') and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, 'new files:', len(extra))


# Ported strings whose English half is missing from the source mirror (void campaign) -> English added here.
EN_FIX = {'Abil/Name/LightningBomb': 'Disintegration', 'Abil/Name/RoboticsFacilityWarpTrain': 'Robotics Facility Warp Train', 'Abil/Name/StargateWarpTrain': 'Stargate Warp Train', 'Abil/Name/VoidDarkTemplarStunningBlow': 'Void Dark Templar Stunning Blow', 'Behavior/Name/Aiur05EMPWaveStun': 'Aiur 05 EMP Wave Stun', 'Behavior/Name/GreaterBeastStun': 'Greater Beast Stun', 'Behavior/Name/LightningBomb': 'Disintegration', 'Behavior/Name/ScoutSpeedBoost': 'Scout Speed Boost', 'Behavior/Name/VoidDarkTemplarStunningBlow': 'Stunning Blow', 'Button/Name/Scout': 'Warp in Scout', 'Button/Name/StalkerPurifier': 'Warp in Instigator', 'Button/Name/VoidPhoenixDoubleGraviton': 'Void Phoenix Double Graviton', 'Button/Tooltip/StalkerPurifier': 'Purifier<n/>Ranged support walker. Can Blink several times in a row.<n/><n/><c val="ffff8a">Can attack ground and air units</c>', 'Effect/Name/Aiur05EMPWaveStun': 'Aiur 05 EMP Wave Stun', 'Effect/Name/GravitonBeamVoidCampaign': 'Graviton Beam (Persistent)', 'Effect/Name/GravitonBeamVoidCampaignBehavior': 'Graviton Beam (Apply Behavior)', 'Effect/Name/GravitonBeamVoidCampaignHeightBehavior': 'Graviton Beam (Height Behavior)', 'Effect/Name/GravitonBeamVoidCampaignInitialSet': 'Graviton Beam (Initial Set)', 'Effect/Name/GravitonBeamVoidCampaignPeriodicSet': 'Graviton Beam (Periodic Set)', 'Effect/Name/PurificationNovaNotificationDamage': 'Purification Nova', 'Effect/Name/PurificationNovaNotificationSearch': 'Purification Nova', 'Effect/Name/PurificationNovaTargettedCasterAB': 'Purification Nova Targeted Caster AB', 'Effect/Name/PurificationNovaTargettedInitialSet': 'Purification Nova Targeted Initial Set', 'Effect/Name/PurificationNovaTargettedIssueOrder': 'Purification Nova Targeted Issue Order', 'Effect/Name/PurificationNovaTargettedSearchSet': 'Purification Nova Targeted Search Set', 'Effect/Name/PurificationNovaTargettedSpawnAB': 'Purification Nova Targeted Spawn AB', 'Effect/Name/PurificationNovaTargettedSpawnSet': 'Purification Nova Targeted Spawn Set', 'Effect/Name/ScoutSpeedBoost': 'Scout Speed Boost', 'Unit/Name/TempestPurifierWeapon': 'Tempest Purifier Weapon', 'Unit/Name/TempestPurifierWeaponGround': 'Tempest Purifier Weapon Ground', 'Upgrade/Name/VoidColossusFireBeam': 'Void Colossus Fire Beam', 'Upgrade/Name/VoidPhoenixGravitonCampaignVersion': 'Void Phoenix Graviton (Campaign)', 'Upgrade/Name/VoidPhoenixPhasingArmor': 'Void Phoenix Phasing Armor', 'Weapon/Name/DisruptorWeapon': 'Disruptor Weapon'}
KO_FIX = {'Abil/Name/PrimalHydraliskToMutalisk': '원시 전투: 원시 뮤탈리스크 /// Primal Combat: Primal Mutalisk', 'Behavior/Name/DisruptorPermanentCloak': '분열기 영구 은폐 /// Disruptor Permanent Cloak', 'Behavior/Name/GravitonBeamHeightVoidCampaign': '반중력 높이 /// Anti Gravity Height', 'Behavior/Name/HyperjumpTeleport': '초공간 도약 /// Hyperjump Teleport', 'Behavior/Name/HyperjumpTeleportIn': '초공간 도약 진입 /// Hyperjump Teleport In', 'Behavior/Name/HyperjumpTeleportOut': '초공간 도약 이탈 /// Hyperjump Teleport Out', 'Behavior/Name/ImpalerGenerateCreep': '관통촉수 점막 생성 /// Impaler Generate Creep', 'Behavior/Name/MothershipRecalling': '모선 귀환 중 /// Mothership Recalling', 'Behavior/Name/PurificationNovaCooldownVisual': '정화 폭발 재사용 대기 /// Purification Nova Cooldown Visual', 'Behavior/Name/PurificationNovaTargettedCaster': '정화 폭발 대상 지정 시전자 /// Purification Nova Targeted Caster', 'Behavior/Name/PurificationNovaTargettedTarget': '정화 폭발 대상 /// Purification Nova Targeted Target', 'Behavior/Name/PurificationNovaUpgradedTargettedTarget': '강화 정화 폭발 대상 /// Purification Nova Upgraded Targeted Target', 'Behavior/Name/VoidPhoenixPhasingArmor': '위상 장갑 /// Phasing Armor', 'Behavior/Tooltip/VoidPhoenixPhasingArmor': '이 유닛은 피해를 받지 않습니다. /// This unit is immune to damage.', 'Turret/Name/PhoenixPurifier': '신기루 포탑 /// Mirage Turret', 'Upgrade/Name/FenixScoutWeaponRange': '정찰기 무기 사거리 /// Scout Weapon Range', 'Upgrade/Name/PrimalHydraliskToMutalisk': '원시 전투: 원시 뮤탈리스크 /// Primal Combat: Primal Mutalisk'}  # display strings that came English-only -> 'Korean /// English'


def strings(d):
    t = d.decode('utf-8')
    nl = '\r\n' if '\r\n' in t else '\n'
    lines = t.split(nl)
    for i, l in enumerate(lines):
        k, _, v = l.partition('=')
        if k in KO_FIX: lines[i] = f'{k}={KO_FIX[k]}'
        elif k in EN_FIX and '///' not in v: lines[i] = f'{k}={v} /// {EN_FIX[k]}'
    return nl.join(lines).encode('utf-8')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
