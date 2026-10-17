#!/usr/bin/env python3
"""Build CCM 0.3.24 from 0.3.23 (3번 미션).

사용자 결정 (2026-10-17):
  - 동맹 기지 건설 취소. 남서쪽 정화 광선 진입 연출도 없앤다.
  - 시작할 때 동맹의 탐사정·원시 일벌레를 레이너 기지에 내려보낸다. 플레이어가 그 일꾼을 움직이고 건물을 짓는다.
    (이동·건설만. 동맹 병력은 플레이어가 조종하지 않는다.)
  - 정화자는 수정탑, 원시저그는 원시 감시자에서 동맹 자원으로 병력을 만든다. 인구수는 동맹마다 100.
  - 무료 90초 반복 지원은 끈다.
구현 (수치·위치는 모두 시험값):
  - 시작 5초 뒤 안내. 탐사정 1기는 (93,44)에 소환되고, 원시 일벌레 4기는 (100,44) 근처에 협동전 투하 포드로 떨어진다.
  - 정화자·원시저그는 플레이어에게 '조종·자원 사용'을 공유한다. 동맹 병력은 만들 때 선택할 수 없게 해서 플레이어 조종에서 뺀다.
  - 탐사정은 수정탑만 지을 수 있다(다른 프로토스 건물 금지).
    원시 일벌레는 협동전과 같은 변태 건설 DehakaDroneMorph(원시 감시자, 60초, 일벌레 소모)를 쓴다.
  - 동맹 자원: 정화자 광물 200, 원시저그 광물 500으로 시작한다. 2초마다 광물 25·가스 8씩 들어온다 (분당 750·240).
  - 생산: 완성된 거점 하나가 8초마다 1기씩 만든다. 비용은 유닛 데이터 값이고, 자원이 모자라면 기다린다.
    정화자: 파수병·파수병·피닉스 사도 순서이고, 동력기는 2기까지 넣는다.
    원시저그: 저글링·저글링·바퀴·히드라·저글링·라바사우르스 순서다.
    동맹 병력 인구가 100이면 생산을 멈춘다.
  - 전투 (7-0 자동 전투): 핑(30초) 우선 → 레이너 기지 방어 → 위협이 없을 때
    정화자 10기 이상, 원시저그 인구 16 이상이면 가장 가까운 적 건물을 공격한다.
  - 엔진 AI·채취·스크립트 건설은 호출하지 않는다.
  - 자원 복구: 동맹용으로 추가한 광물·가스를 지운다. 남서쪽 원본 광물 8개는 일반 광물로 되돌리고, 0.3.7에서 지운 적 추출장(Id 54)도 되살린다.
    레이너 본진 풍부 자원 +20%는 그대로 둔다.
  - 보급 벙커 오류 구 (사용자 스크린샷): 템플릿이 찾는 건설 중 모델(BuildModel ##unitName##)과
    공사장 액터 RM3_SupplyBunkerBuild가 없었다. 둘 다 연결한다. 협동전 원본에 맞춰 모델 크기 1.0, 건설 모습 0.45,
    부관 초상화, 빈 벙커 파괴 모델로 바꾼다.
  - 협동전 연출 액터 누락 보완: GlazeSentinelRepair(파수병 재구축, 2·3번), AdeptProtossSpiritDeathModel(피닉스 사도 사망, 3번).

Usage: python3 tools/build_v0324.py <0.3.23 zip> <원본 TRaynor03 objects 파일> <new output zip>
  (원본 objects는 maps/original_wol/TRaynor03.SC2Map 안의 objects를 mpyq로 꺼낸 것)
"""
import argparse
import copy
import re
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v035 as V35  # noqa: E402  (other_locale, gate, OTHER_LOCALES)

OLD, NEW = b'version=0.3.23', b'version=0.3.24'
M3 = 'TRaynor03.SC2Map/'
KO = M3 + 'kokr.sc2data/localizeddata/gamestrings.txt'

ADDED_RES = {'30008', '30010', '30011', '30012', '30013', '30014', '30015', '30016', '30017', '30018'}
SW_MINERALS = {'126', '128', '129', '132', '135', '136', '137', '149'}

ARRIVE = '''bool gt_m3_Arrive_Func (bool testConds,bool runActions) {
    actor fx;
    actor pod;
    int i;
    if (!runActions) { return true; }
    // No ally bases (user 2026-10-17): ally workers land in Raynor's base and the player builds with them. Trial spots.
    Wait(5.0,c_timeGame);
    if (gv_gameOver) { return true; }
    UIDisplayMessage(PlayerGroupAll(),c_messageAreaSubtitle,StringExternal("rm3/Arrival"));
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSetTo,200);
    PlayerModifyPropertyInt(10,c_playerPropVespene,c_playerPropOperSetTo,0);
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSetTo,500);
    PlayerModifyPropertyInt(11,c_playerPropVespene,c_playerPropOperSetTo,0);
    fx=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",Point(93.0,44.0));
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
    UIDisplayMessage(PlayerGroupAll(),c_messageAreaSubtitle,StringExternal("rm3/Ready"));
    return true;
}

'''

FIND = '''void gf_m3_FindThreat () {
    unitgroup raynor;
    // Both allies defend Raynor's base; with no threat and enough army they attack the nearest enemy structure.
    raynor=gf_m3_Enemies(Point(92.0,38.0),24.0);
    UnitGroupAddUnitGroup(raynor,gf_m3_Enemies(Point(65.0,47.0),12.0));
    UnitGroupAddUnitGroup(raynor,gf_m3_Enemies(Point(101.0,47.0),10.0));
    gv_m3_rally10=Point(84.0,48.0);
    gv_m3_rally11=Point(80.0,46.0);
    gv_m3_has10=true;
    gv_m3_has11=true;
    if (UnitGroupCount(raynor,c_unitCountAlive)>0) {
        gv_m3_threat10=UnitGetPosition(UnitGroupClosestToPoint(raynor,Point(92.0,38.0)));
        gv_m3_threat11=gv_m3_threat10;
    }
    else {
        if (UnitGroupCount(gf_m3_Army(10),c_unitCountAlive)>=10 && gf_m3_EnemyBase(Point(92.0,38.0))) { gv_m3_threat10=gv_m3_enemyBase; }
        else { gv_m3_has10=false; }
        if (gf_m3_Food(11)>=16.0 && gf_m3_EnemyBase(Point(92.0,38.0))) { gv_m3_threat11=gv_m3_enemyBase; }
        else { gv_m3_has11=false; }
    }
    gv_m3_hasThreat=(gv_m3_has10 || gv_m3_has11);
}

fixed gf_m3_Food (int p) {
    unitgroup g;
    int i;
    fixed total;
    g=gf_m3_Army(p);
    total=0.0;
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) { total+=gf_m3_UnitFood(UnitGetType(UnitGroupUnit(g,i))); }
    return total;
}

fixed gf_m3_UnitFood (string kind) {
    // Data Food values: Primal Zergling 1, every other ally army unit 2.
    if (kind=="DehakaZerglingLevel2") { return 1.0; }
    return 2.0;
}

bool gf_m3_Buy (int p,string kind) {
    int m;
    int g;
    // Allies pay the unit's data cost from their own resources; ally army supply cap 100 (user 2026-10-17).
    m=UnitTypeGetCost(kind,c_unitCostMinerals);
    g=UnitTypeGetCost(kind,c_unitCostVespene);
    if (gf_m3_Food(p)+gf_m3_UnitFood(kind)>100.0) { return false; }
    if (PlayerGetPropertyInt(p,c_playerPropMinerals)<m || PlayerGetPropertyInt(p,c_playerPropVespene)<g) { return false; }
    PlayerModifyPropertyInt(p,c_playerPropMinerals,c_playerPropOperSubtract,m);
    PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);
    return true;
}

fixed gv_m3_nextMake10;
fixed gv_m3_nextMake11;
int gv_m3_turn10;
int gv_m3_turn11;

void gf_m3_Produce () {
    unitgroup posts;
    unit post;
    string kind;
    int n;
    point at;
    actor fx;
    // Income (trial): 25 minerals / 8 gas per 2 s tick for each ally.
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperAdd,25);
    PlayerModifyPropertyInt(10,c_playerPropVespene,c_playerPropOperAdd,8);
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperAdd,25);
    PlayerModifyPropertyInt(11,c_playerPropVespene,c_playerPropOperAdd,8);
    // Ally armies stay AI-only: they are made unselectable, so the shared control only reaches the workers and posts.
    // Purifiers warp in at their pylons: Sentinel, Sentinel, Fenix Adept; up to 2 Energizers. 8 s per pylon (trial).
    posts=UnitGroup("Pylon",10,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    n=UnitGroupCount(posts,c_unitCountAlive);
    if (n>0 && GameGetMissionTime()>=gv_m3_nextMake10) {
        if (ModI(gv_m3_turn10,6)==5 && UnitGroupCount(UnitGroup("RM21_Energizer",10,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)<2) { kind="RM21_Energizer"; }
        else if (ModI(gv_m3_turn10,3)==2) { kind="AdeptFenix"; }
        else { kind="ZealotPurifier"; }
        if (gf_m3_Buy(10,kind)) {
            post=UnitGroupUnit(posts,ModI(gv_m3_turn10,n)+1);
            at=PointWithOffsetPolar(UnitGetPosition(post),2.5,IntToFixed(ModI(gv_m3_turn10*67,360)));
            fx=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at);
            ActorSend(fx,"AnimPlay Warp Birth NonLooping");
            UnitCreate(1,kind,0,10,at,270.0);
            UnitSetState(UnitLastCreated(),c_unitStateSelectable,false);
            gv_m3_turn10+=1;
            gv_m3_nextMake10=GameGetMissionTime()+8.0/IntToFixed(n);
        }
    }
    // Primal Zerg spawn at their wardens: ling, ling, roach, hydra, ling, ravasaur. 8 s per warden (trial).
    posts=UnitGroup("DehakaBarracks",11,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    n=UnitGroupCount(posts,c_unitCountAlive);
    if (n>0 && GameGetMissionTime()>=gv_m3_nextMake11) {
        if (ModI(gv_m3_turn11,6)==2) { kind="DehakaRoachLevel2"; }
        else if (ModI(gv_m3_turn11,6)==3) { kind="DehakaHydraliskLevel2"; }
        else if (ModI(gv_m3_turn11,6)==5) { kind="DehakaRavasaur"; }
        else { kind="DehakaZerglingLevel2"; }
        if (gf_m3_Buy(11,kind)) {
            post=UnitGroupUnit(posts,ModI(gv_m3_turn11,n)+1);
            UnitCreate(1,kind,0,11,PointWithOffsetPolar(UnitGetPosition(post),2.5,270.0),270.0);
            UnitSetState(UnitLastCreated(),c_unitStateSelectable,false);
            gv_m3_turn11+=1;
            gv_m3_nextMake11=GameGetMissionTime()+8.0/IntToFixed(n);
        }
    }
}

'''

TICK = '''bool gt_m3_Tick_Func (bool testConds,bool runActions) {
    if (!runActions || gv_gameOver || gv_inCinematic) { return true; }
    gf_m3_Skin(10);
    gf_m3_Skin(11);
    if (!gv_m3_ready) { return true; }
    gf_m3_Produce();
    gf_m3_FindThreat();
    gf_m3_Attack(10);
    gf_m3_Attack(11);
    gv_m3_threatTick=ModI(gv_m3_threatTick+1,2);
    return true;
}

'''

STRINGS = {
    'rm3/Arrival': '정화자·원시저그: 탐사정과 원시 일벌레를 레이너 기지에 보냅니다. /// Purifiers and Primal Zerg: Sending a Probe and Primal Drones to Raynor\'s base.',
    'rm3/Ready': '동맹 일꾼을 직접 움직여 수정탑과 원시 감시자를 지으십시오. 동맹이 그곳에서 자기 자원으로 병력을 만듭니다. /// Move the allied workers to build Pylons and Primal Wardens. The allies will train forces there with their own resources.',
}

INIT_OLD = """    TechTreeUnitAllow(10,"Probe",true);
    TechTreeUnitAllow(10,"Nexus",true);
    TechTreeUnitAllow(10,"Pylon",true);
    TechTreeUnitAllow(10,"Assimilator",true);
    TechTreeUnitAllow(10,"Gateway",true);
    TechTreeUnitAllow(10,"CyberneticsCore",true);
    TechTreeUnitAllow(10,"Zealot",true);
    TechTreeUnitAllow(10,"Stalker",true);
"""
INIT_NEW = """    // The player moves/builds with the ally workers (control + spending shared). Ally armies are unselectable.
    libNtve_gf_SetAlliance(10,1,libNtve_ge_AllianceSetting_AllyWithSharedVisionControlAndSpending);
    libNtve_gf_SetAlliance(11,1,libNtve_ge_AllianceSetting_AllyWithSharedVisionControlAndSpending);
    // The Purifier Probe builds Pylons only.
    TechTreeUnitAllow(10,"Pylon",true);
    TechTreeUnitAllow(10,"Nexus",false);
    TechTreeUnitAllow(10,"Assimilator",false);
    TechTreeUnitAllow(10,"Gateway",false);
    TechTreeUnitAllow(10,"Forge",false);
    TechTreeUnitAllow(10,"FleetBeacon",false);
    TechTreeUnitAllow(10,"TwilightCouncil",false);
    TechTreeUnitAllow(10,"PhotonCannon",false);
    TechTreeUnitAllow(10,"Stargate",false);
    TechTreeUnitAllow(10,"TemplarArchive",false);
    TechTreeUnitAllow(10,"DarkShrine",false);
    TechTreeUnitAllow(10,"RoboticsBay",false);
    TechTreeUnitAllow(10,"RoboticsFacility",false);
    TechTreeUnitAllow(10,"CyberneticsCore",false);
"""

# co-op DehakaDroneMorph (starcoop), Primal Warden only.
DRONE_MORPH = ('<CAbilBuild id="DehakaDroneMorph"><EditorCategories value="AbilityorEffectType:MorphsandBurrows" />'
               '<FlagArray index="PeonHide" value="1" /><FlagArray index="PeonKillFinish" value="1" />'
               '<FlagArray index="RangeIncludesBuilding" value="0" />'
               '<InfoArray index="Build1" Unit="DehakaBarracks" Time="60"><Button DefaultButtonFace="DehakaBarracks" /></InfoArray>'
               '</CAbilBuild>')
DRONE_BUTTON = '<LayoutButtons Face="DehakaBarracks" Type="AbilCmd" AbilCmd="DehakaDroneMorph,Build1" Row="2" Column="0" />'
# void.sc2campaign / void.sc2mod originals.
GLAZE = ('<CActorModelMaterial id="GlazeSentinelRepair" parent="GlazeParent"><ModelFlags index="AutomateGlobalLoops" value="1" />'
         '<On Terms="Behavior.ZealotPurifierReviveSupressed.On" Send="Create" />'
         '<On Terms="ActorCreation" Send="TimerSet 0.125000 DelayApply" />'
         '<On Terms="TimerExpired; TimerName DelayApply" Send="ModelMaterialApplyTo ::Main" />'
         '<On Terms="Behavior.ZealotPurifierReviveSupressed.Off" Send="ModelMaterialRemoveFrom ::Main" />'
         '<On Terms="Behavior.ZealotPurifierReviveSupressed.Off" Send="Destroy" /></CActorModelMaterial>')
ADEPT_DEATH = ('<CActorModel id="AdeptProtossSpiritDeathModel" parent="ModelAnimationStyleOneShot"><Host Subject="_Unit" />'
               '<InheritType value="OneShot" /><Inherits index="Visibility" value="1" /></CActorModel>')
# Supply Bunker: construction scaffold actor (template 'Create ##unitName##Build') and the empty-death model.
BUNKER_ACTOR = '<CActorModel id="RM3_SupplyBunkerBuild" parent="TerranBuildingBuild" />'
BUNKER_EMPTY = (r'<CModel id="RM3_SupplyBunkerDeathEmpty" parent="BuildingDeath"><Model value="Assets\COOP\Mengsk\Buildings'
                r'\SupplyBunker_Mengsk_COOP_DeathEmpty\SupplyBunker_Mengsk_COOP_DeathEmpty.m3" /></CModel>')


def cut(text, start, end):
    a = text.index(start)
    b = text.index(end, a)
    return a, b


def script(data):
    text = data.decode('utf-8')
    a, b = cut(text, 'bool gt_m3_Arrive_Func (bool testConds,bool runActions) {', 'void gf_m3_Skin (int p) {')
    text = text[:a] + ARRIVE + text[b:]
    a, b = cut(text, 'void gf_m3_FindThreat () {', 'void gf_m3_GuardWarp () {')
    text = text[:a] + FIND + text[b:]
    a, b = cut(text, 'bool gt_m3_Tick_Func (bool testConds,bool runActions) {', 'void gf_m3_Start () {')
    text = text[:a] + TICK + text[b:]
    # gf_m3_Food is used by FindThreat before its definition: forward declaration.
    anchor = 'bool gf_m3_EnemyBase (point from) {'
    assert text.count(anchor) == 1
    text = text.replace(anchor, 'fixed gf_m3_Food (int p);\nfixed gf_m3_UnitFood (string kind);\n\n' + anchor, 1)
    assert text.count(INIT_OLD) == 1
    text = text.replace(INIT_OLD, INIT_NEW, 1)
    for gone in ('gf_m3_PrimalWorkers();', 'TriggerExecute(gt_m3_warp', 'TriggerExecute(gt_m3_drop', 'AISetStock'):
        assert gone not in text[text.index('bool gt_m3_Tick_Func'):text.index('void gf_m3_Start () {')], gone
    return text.encode('utf-8')


def objects(orig_path):
    orig = {e.get('Id'): e for e in E.parse(orig_path).getroot()}

    def f(data):
        root = E.fromstring(data)
        gone = [el for el in root if el.get('Id') in ADDED_RES]
        assert len(gone) == len(ADDED_RES), sorted(el.get('Id') for el in gone)
        for el in gone: root.remove(el)
        for i, el in enumerate(list(root)):
            if el.get('Id') in SW_MINERALS:
                assert el.get('UnitType') == 'RichMineralField'
                root.remove(el)
                root.insert(i, copy.deepcopy(orig[el.get('Id')]))
        assert not any(el.get('Id') == '54' for el in root) and orig['54'].get('UnitType') == 'Extractor'
        root.append(copy.deepcopy(orig['54']))
        return E.tostring(root, encoding='utf-8', xml_declaration=True)
    return f


def append(xml, absent):
    def f(data):
        text = data.decode('utf-8')
        for x in absent: assert f'id="{x}"' not in text, x
        out = text.replace('</Catalog>', xml + '</Catalog>', 1).encode('utf-8')
        E.fromstring(out)
        return out
    return f


def units(data):
    root = E.fromstring(data)
    d = [e for e in root if e.tag == 'CUnit' and e.get('id') == 'DehakaDrone']
    assert len(d) == 1
    E.SubElement(d[0], 'AbilArray', Link='DehakaDroneMorph')
    card = d[0].find('CardLayouts')
    card.append(E.fromstring(DRONE_BUTTON))
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def actors(data):
    root = E.fromstring(append(GLAZE + ADEPT_DEATH + BUNKER_ACTOR, ['GlazeSentinelRepair', 'AdeptProtossSpiritDeathModel', 'RM3_SupplyBunkerBuild'])(data))
    b = [e for e in root if e.tag == 'CActorUnit' and e.get('id') == 'RM3_SupplyBunker']
    assert len(b) == 1 and b[0].find('BuildModel') is None
    E.SubElement(b[0], 'BuildModel', value='RM3_SupplyBunkerModel')
    for dc in b[0].findall('DeathCustoms'):
        if dc.get('Name') == 'Empty': dc.set('ModelLink', 'RM3_SupplyBunkerDeathEmpty')
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def models(data):
    root = E.fromstring(append(BUNKER_EMPTY, ['RM3_SupplyBunkerDeathEmpty'])(data))
    ids = {e.get('id'): e for e in root if e.tag == 'CModel'}
    m = ids['RM3_SupplyBunkerModel']  # co-op BunkerDepotMengsk: no scale (1.0)
    for tag in ('ScaleMax', 'ScaleMin'):
        for s in m.findall(tag): m.remove(s)
    for tag in ('ScaleMax', 'ScaleMin'):  # co-op BunkerDepotMengskBuild 0.45
        ids['RM3_SupplyBunkerBuild'].find(tag).set('value', '0.450000,0.450000,0.450000')
    ids['RM3_SupplyBunkerPortrait'].set('parent', 'AdjutantPortrait')  # co-op BunkerDepotMengskPortrait
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def kokr(data):
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    out = []
    for line in text.splitlines():
        k = line.split('=', 1)[0]
        if k in STRINGS: line = f'{k}={STRINGS[k]}'
        out.append(line)
    res = (nl.join(out) + nl).encode('utf-8')
    for k in STRINGS: assert f'{k}={STRINGS[k]}'.encode('utf-8') in res, k
    V35.gate('kokr', res)
    return res


def build(source, orig_objects, output):
    if output.exists(): raise ValueError('Output must be new')
    gd3 = M3 + 'base.sc2data/gamedata/'
    gd2 = 'TRaynor02.SC2Map/base.sc2data/gamedata/'
    fix = {M3 + 'mapscript.galaxy': script, M3 + 'objects': objects(orig_objects), KO: kokr,
           gd3 + 'abildata.xml': append(DRONE_MORPH, ['DehakaDroneMorph']), gd3 + 'unitdata.xml': units,
           gd3 + 'actordata.xml': actors, gd3 + 'modeldata.xml': models,
           gd2 + 'actordata.xml': append(GLAZE, ['GlazeSentinelRepair']),
           'metadata.txt': lambda d: d.replace(OLD, NEW)}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for name, fn in fix.items(): files[name] = fn(files[name])
        changed = set(fix)
        for loc in V35.OTHER_LOCALES:
            n = f'{M3}{loc}.sc2data/localizeddata/gamestrings.txt'
            files[n] = V35.other_locale(files[KO]); changed.add(n)
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
    p.add_argument('source', type=Path)
    p.add_argument('orig_objects', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.orig_objects, a.output)
