#!/usr/bin/env python3
"""0.6.59 -> 0.6.60: 동맹 캠페인 업그레이드 1단계 시험 (4·5·6번, 사용자 2026-11-21).

사용자: "4번째 맵부터 적용되게 해봐 실험으로 1단계만". 결정: 건물이 공격받아도 체력 1에서 멈춤, 데하카의 굴 외형,
1단계 300/300·70초, 사령부에서 광물 반대편 빈자리. 모드에서 재설계한 미션 내 연구(원작에 없음).
- 임무 시작 2초 뒤(못 놓으면 5분까지 1초마다 다시 시도) 레이너(1) 사령부에서 광물 반대쪽 8~16칸, 광물·가스 5칸 안은 피해서 '정화자 대의회'(협동전 피닉스 외형)와 '데하카의 굴'(협동전 외형)이
  하나씩 생긴다. 레이너 소유, 체력 1000, 죽을 피해를 0으로 바꾸는 숨은 행동 RM7_NoDie(코덱스 검토: PreventDestroy만으로는 죽음), SCV 수리 가능(기계 속성).
- 각 건물에 '1단계' 연구 1개 (레이너 돈 300/300, 70초, 시험값, 한 번만, 단축키 Q).
- 연구가 끝나면 스크립트가 그 동맹에게 업그레이드를 준다 (이미 있는 유닛·나중에 오는 유닛 모두, 정보 창에 아이콘):
  정화자(8) — 군단병 돌진(자날 Charge), 거신 열 창 사거리 +3, 동력기 시간 광선 지속 10→20초,
             보전기 보호장 지속 2배(협동전 FenixSentryGuardianZoneCP +30), 정찰기 사거리(협동전 FenixScoutWeaponRange).
  원시저그(9) — 저글링 이속 +60%(3.5→5.6, 대사 촉진), 바퀴 경장갑 +8(요오드화 담즙), 히드라 사거리 +1(홈 파인 가시),
             라바사우르스 사거리 +1·이속 +0.75(협동전 DehakaRavasaurRange), 울트라·티라노조르 근접 피해의 40% 흡혈(조직 동화).
  사도는 분신이 이미 있어 1단계 변화 없음.
게임 미실행.

Usage: python3 tools/build_v0660.py <0.6.59 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import add_xml, set_lines, LOCS, KO, GD

OLD, NEW = b'version=0.6.59', b'version=0.6.60'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
COST, TIME = '300', '70'
COOP = ROOT / 'source/starcoop/starcoop.sc2mod' / GD
ICON_P = 'Assets\\Textures\\btn-ability-protoss-charge-color.dds'
ICON_Z = 'Assets\\Textures\\btn-upgrade-zerg-metabolicboost.dds'

BLDG = '''<CUnit id="{id}"><Name value="Unit/Name/{id}" /><Race value="Terr" /><Mob value="Campaign" />
<FlagArray index="Turnable" value="0" /><FlagArray index="PreventDestroy" value="1" /><FlagArray index="UseLineOfSight" value="1" />
<FlagArray index="NoPortraitTalk" value="1" /><FlagArray index="ArmySelect" value="0" /><PlaneArray index="Ground" value="1" />
<Collide index="Burrow" value="1" /><Collide index="Ground" value="1" /><Collide index="Structure" value="1" />
<Collide index="RoachBurrow" value="1" /><Collide index="ForceField" value="1" /><Collide index="Small" value="1" />
<Attributes index="Armored" value="1" /><Attributes index="Mechanical" value="1" /><Attributes index="Structure" value="1" />
<LifeStart value="1000" /><LifeMax value="1000" /><LifeArmor value="1" /><Sight value="9" /><RepairTime value="30" />
<CostResource index="Minerals" value="150" /><AttackTargetPriority value="11" />
<AbilArray Link="que5" /><AbilArray Link="{abil}" /><BehaviorArray Link="RM7_NoDie" />
<CardLayouts><LayoutButtons Face="{up}" Type="AbilCmd" AbilCmd="{abil},Research1" Row="0" Column="0" />
<LayoutButtons Face="Cancel" Type="AbilCmd" AbilCmd="que5,CancelLast" Row="2" Column="4" /></CardLayouts>
<Footprint value="{fp}Contour" /><PlacementFootprint value="{fp}" /><Radius value="{r}" /><SeparationRadius value="{r}" />
<EditorCategories value="ObjectType:Structure,ObjectFamily:Campaign" /><SubgroupPriority value="10" /></CUnit>'''
ACTOR = ('<CActorUnit id="{id}" parent="GenericUnitStandard" unitName="{id}"><Model value="{model}" />'
         '<PlacementModel value="{model}" /><UnitIcon value="{icon}" /><Aliases value="{alias}" /></CActorUnit>')
RESEARCH = ('<CAbilResearch id="{abil}"><InfoArray index="Research1" Time="{t}" Upgrade="{up}">'
            '<Resource index="Minerals" value="{c}" /><Resource index="Vespene" value="{c}" />'
            '<Button DefaultButtonFace="{up}" State="Available" Requirements="{up}Learn" /></InfoArray></CAbilResearch>')
REQ = '<CRequirement id="{up}Learn"><NodeArray index="Show" Link="{up}NotQueued" /></CRequirement>'
NODES = ('<CRequirementCountUpgrade id="{up}Queued"><Count Link="{up}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
         '<CRequirementNot id="{up}NotQueued"><OperandArray index="0" value="{up}Queued" /></CRequirementNot>')

UPGRADES = f'''<CUpgrade id="RM7_PurifierT1"><Race value="Terr" /><Alert value="ResearchComplete" /><MaxLevel value="1" /><Icon value="{ICON_P}" /></CUpgrade>
<CUpgrade id="RM7_PrimalT1"><Race value="Terr" /><Alert value="ResearchComplete" /><MaxLevel value="1" /><Icon value="{ICON_Z}" /></CUpgrade>
<CUpgrade id="RM7_PurifierT1Fx"><Race value="Prot" /><MaxLevel value="1" /><Icon value="{ICON_P}" />
<AffectedUnitArray value="ZealotPurifier" /><AffectedUnitArray value="ColossusPurifier" /><AffectedUnitArray value="RM21_Energizer" />
<AffectedUnitArray value="SentryFenix" /><AffectedUnitArray value="Scout" />
<EffectArray Reference="Weapon,ColossusPurifierThermalLances,Range" Value="3" />
<EffectArray Reference="Weapon,ColossusPurifierThermalLances,MinScanRange" Value="3" />
<EffectArray Reference="Behavior,RM21_VoidSentryChronoBeam,Duration" Value="10" />
<EffectArray Reference="Effect,FenixSentryGuardianZoneCP,PeriodCount" Value="30" /></CUpgrade>
<CUpgrade id="RM7_PrimalT1Fx"><Race value="Zerg" /><MaxLevel value="1" /><Icon value="{ICON_Z}" />
<AffectedUnitArray value="DehakaZerglingLevel2" /><AffectedUnitArray value="DehakaRoachLevel2" />
<AffectedUnitArray value="DehakaHydraliskLevel2" /><AffectedUnitArray value="DehakaUltraliskLevel2" /><AffectedUnitArray value="DehakaUltraliskLevel3" />
<EffectArray Reference="Unit,DehakaZerglingLevel2,Speed" Value="2.1" />
<EffectArray Reference="Effect,DehakaRoachLevel2Damage,AttributeBonus[Light]" Value="8" />
<EffectArray Reference="Effect,DehakaRoachLevel2Melee,AttributeBonus[Light]" Value="8" />
<EffectArray Reference="Weapon,DehakaHydraliskLevel2NeedleSpines,Range" Value="1" />
<EffectArray Reference="Weapon,DehakaHydraliskLevel2NeedleSpines,MinScanRange" Value="1" /></CUpgrade>'''
NODIE = ('<CBehaviorBuff id="RM7_NoDie"><BehaviorFlags index="Permanent" value="1" /><InfoFlags index="Hidden" value="1" />'
         '<DamageResponse Fatal="1" ModifyFraction="0"><Chance value="1" /></DamageResponse></CBehaviorBuff>')
LEECH = ('<CBehaviorBuff id="RM7_UltraLeech"><BehaviorFlags index="Permanent" value="1" /><InfoFlags index="Hidden" value="1" />'
         '<Modification><VitalDamageLeechArray index="Life"><KindArray index="Melee" value="0.4" /></VitalDamageLeechArray></Modification></CBehaviorBuff>')
BUTTONS = ''.join(f'<CButton id="{i}"><Icon value="{ic}" /><Name value="Button/Name/{i}" /><Tooltip value="Button/Tooltip/{i}" /></CButton>'
                  for i, ic in (('RM7_PurifierT1', ICON_P), ('RM7_PrimalT1', ICON_Z)))

STRINGS = {
    'Unit/Name/RM7_Conclave': '정화자 대의회 /// Purifier Conclave',
    'Unit/Name/RM7_DehakaDen': '데하카의 굴 /// Dehaka\'s Den',
    'Upgrade/Name/RM7_PurifierT1': '정화자 강화 1단계 /// Purifier Enhancements Tier 1',
    'Upgrade/Name/RM7_PrimalT1': '원시저그 변이 1단계 /// Primal Mutations Tier 1',
    'Upgrade/Name/RM7_PurifierT1Fx': '정화자 강화 1단계 /// Purifier Enhancements Tier 1',
    'Upgrade/Name/RM7_PrimalT1Fx': '원시저그 변이 1단계 /// Primal Mutations Tier 1',
    'Button/Name/RM7_PurifierT1': '정화자 강화 1단계 연구 /// Research Purifier Enhancements Tier 1',
    'Button/Tooltip/RM7_PurifierT1': ('정화자 동맹 병력이 강해집니다: 군단병 돌진, 거신 열 창 사거리 +3, 동력기 시간 광선 지속시간 2배, '
                                      '보전기 보호장 지속시간 2배, 정찰기 사거리 증가. 이미 있는 병력과 앞으로 오는 병력 모두 적용됩니다. '
                                      '/// Purifier allies grow stronger: Legionnaire Charge, Colossus thermal lance range +3, Energizer Chrono Beam '
                                      'duration x2, Conservator guardian zone duration x2, Scout range up. Applies to current and future units.'),
    'Button/Name/RM7_PrimalT1': '원시저그 변이 1단계 연구 /// Research Primal Mutations Tier 1',
    'Button/Tooltip/RM7_PrimalT1': ('원시저그 동맹 병력이 진화합니다: 저글링 대사 촉진(이동 속도 +60%), 바퀴 요오드화 담즙(경장갑 +8), '
                                    '히드라 홈 파인 가시(사거리 +1), 라바사우르스 사거리 +1·이동 속도 증가, 울트라리스크·티라노조르 조직 동화'
                                    '(근접 피해의 40% 회복). 이미 있는 병력과 앞으로 오는 병력 모두 적용됩니다. '
                                    '/// Primal Zerg allies evolve: Zergling Metabolic Boost (+60% speed), Roach Hydriodic Bile (+8 vs Light), '
                                    'Hydralisk Grooved Spines (+1 range), Ravasaur range +1 and speed up, Ultralisk/Tyrannozor Tissue Assimilation '
                                    '(heal 40% of melee damage). Applies to current and future units.'),
}
HOTKEYS = {'Button/Hotkey/RM7_PurifierT1': 'Q', 'Button/Hotkey/RM7_PrimalT1': 'Q'}

ALLOW_ANCHOR = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",0),true);\n'
SCRIPT = '''
// 0.6.60 (user 2026-11-21): ally campaign upgrades, tier 1 trial. Purifier Conclave + Dehaka's Den next to Raynor's
// Command Center (away from the minerals); researching tier 1 there gives the allies (8 Purifier, 9 Primal) their upgrades.
trigger gt_rm7Tick;
bool gv_rm7Placed;
bool gv_rm7DoneP;
bool gv_rm7DoneZ;
bool gf_rm7NearMineral (point q) {
    unitgroup g = UnitGroup(null, 0, RegionCircle(q, 5.0), UnitFilter(0, 0, 0, 0), 0);
    int i;
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {
        if (StringFind(UnitGetType(UnitGroupUnit(g, i)), "Mineral", c_stringNoCase) != c_stringNotFound) { return true; }
        if (StringFind(UnitGetType(UnitGroupUnit(g, i)), "Geyser", c_stringNoCase) != c_stringNotFound) { return true; }
    }
    return false;
}
point gf_rm7Spot (string kind, point c, fixed ang, fixed side) {
    point q;
    fixed d;
    int k;
    for (d = 8.0; d <= 16.0; d += 2.0) {
        for (k = 0; k < 4; k += 1) {
            q = UnitTypePlacementFromPoint(kind, 1, PointWithOffsetPolar(c, d, ang + side * IntToFixed(20 + 20 * k)), 2.0);
            if (q != null && !gf_rm7NearMineral(q)) { return q; }
        }
    }
    return null;
}
bool gf_rm7Make (string kind, point c, fixed ang, fixed side) {
    point s;
    if (UnitGroupCount(UnitGroup(kind, 1, null, UnitFilter(0, 0, 0, 0), 0), c_unitCountAll) > 0) { return true; }
    s = gf_rm7Spot(kind, c, ang, side);
    if (s == null) { s = gf_rm7Spot(kind, c, ang, -side); }
    if (s == null) { return false; }
    UnitCreate(1, kind, 0, 1, s, 270.0);
    return UnitLastCreated() != null;
}
bool gf_rm7Place () {
    unitgroup halls;
    unitgroup mins;
    unit cc;
    point c;
    point m;
    fixed ang = 0.0;
    int i;
    int n = 0;
    fixed mx = 0.0;
    fixed my = 0.0;
    bool a;
    bool b;
    halls = UnitGroup("CommandCenter", 1, null, UnitFilter(0, 0, 0, 0), 0);
    UnitGroupAddUnitGroup(halls, UnitGroup("OrbitalCommand", 1, null, UnitFilter(0, 0, 0, 0), 0));
    UnitGroupAddUnitGroup(halls, UnitGroup("PlanetaryFortress", 1, null, UnitFilter(0, 0, 0, 0), 0));
    cc = UnitGroupUnit(halls, 1);
    if (cc != null) { c = UnitGetPosition(cc); } else { c = PlayerStartLocation(1); }
    mins = UnitGroup(null, 0, RegionCircle(c, 12.0), UnitFilter(0, 0, 0, 0), 0);
    for (i = UnitGroupCount(mins, c_unitCountAll); i > 0; i -= 1) {
        if (StringFind(UnitGetType(UnitGroupUnit(mins, i)), "Mineral", c_stringNoCase) != c_stringNotFound) {
            mx += PointGetX(UnitGetPosition(UnitGroupUnit(mins, i)));
            my += PointGetY(UnitGetPosition(UnitGroupUnit(mins, i)));
            n += 1;
        }
    }
    if (n > 0) {
        m = Point(mx / IntToFixed(n), my / IntToFixed(n));
        ang = AngleBetweenPoints(m, c);
    }
    a = gf_rm7Make("RM7_Conclave", c, ang, 1.0);
    b = gf_rm7Make("RM7_DehakaDen", c, ang, -1.0);
    return a && b;
}
void gf_rm7Grant (int p, string up) {
    if (TechTreeUpgradeCount(p, up, c_techCountCompleteOnly) == 0) { TechTreeUpgradeAddLevel(p, up, 1); }
}
bool gt_rm7Tick_Func (bool testConds, bool runActions) {
    unitgroup g;
    unit u;
    int i;
    if (!runActions) { return true; }
    // Retry each second until both buildings exist (up to 5 minutes).
    if (!gv_rm7Placed && GameGetMissionTime() >= 2.0 && GameGetMissionTime() < 300.0) { gv_rm7Placed = gf_rm7Place(); }
    if (!gv_rm7DoneP && TechTreeUpgradeCount(1, "RM7_PurifierT1", c_techCountCompleteOnly) > 0) {
        gv_rm7DoneP = true;
        gf_rm7Grant(8, "RM7_PurifierT1Fx");
        gf_rm7Grant(8, "Charge");
        gf_rm7Grant(8, "FenixScoutWeaponRange");
    }
    if (!gv_rm7DoneZ && TechTreeUpgradeCount(1, "RM7_PrimalT1", c_techCountCompleteOnly) > 0) {
        gv_rm7DoneZ = true;
        gf_rm7Grant(9, "RM7_PrimalT1Fx");
        gf_rm7Grant(9, "DehakaRavasaurRange");
    }
    if (gv_rm7DoneZ) {
        g = UnitGroup("DehakaUltraliskLevel2", 9, null, UnitFilter(0, 0, 0, 0), 0);
        UnitGroupAddUnitGroup(g, UnitGroup("DehakaUltraliskLevel3", 9, null, UnitFilter(0, 0, 0, 0), 0));
        for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {
            u = UnitGroupUnit(g, i);
            if (!UnitHasBehavior2(u, "RM7_UltraLeech")) { UnitBehaviorAdd(u, "RM7_UltraLeech", u, 1); }
        }
    }
    return true;
}
void gf_rm7Start () {
    gt_rm7Tick = TriggerCreate("gt_rm7Tick_Func");
    TriggerAddEventTimePeriodic(gt_rm7Tick, 1.0, c_timeGame);
}
'''
ALLOW = ('    // 0.6.60: ally campaign upgrades tier 1 (Purifier Conclave / Dehaka\'s Den).\n'
         '    TechTreeAbilityAllow(1,AbilityCommand("RM7_ConclaveResearch",0),true);\n'
         '    TechTreeAbilityAllow(1,AbilityCommand("RM7_DenResearch",0),true);\n'
         '    TechTreeUpgradeAllow(1,"RM7_PurifierT1",true);\n'
         '    TechTreeUpgradeAllow(1,"RM7_PrimalT1",true);\n'
         '    gf_rm7Start();\n')


def coop_record(fn, rid):
    for e in E.parse(COOP / fn).getroot():
        if e.get('id') == rid:
            e = copy.deepcopy(e); e.tail = None
            return E.tostring(e, encoding='unicode')
    raise KeyError(rid)


def edit_map(d):
    g = d / GD
    for f, rid in (('modeldata.xml', 'FenixAltarOfPsiStorms'), ('modeldata.xml', 'Dehaka_Nest_COOP')):
        assert f'id="{rid}"' not in (g / f).read_text('utf-8'), rid
        add_xml(g / f, coop_record(f, rid))
    add_xml(g / 'unitdata.xml',
            BLDG.format(id='RM7_Conclave', abil='RM7_ConclaveResearch', up='RM7_PurifierT1', fp='Footprint4x4', r='1.75') +
            BLDG.format(id='RM7_DehakaDen', abil='RM7_DenResearch', up='RM7_PrimalT1', fp='Footprint3x3', r='1.25'))
    add_xml(g / 'actordata.xml',
            ACTOR.format(id='RM7_Conclave', model='FenixAltarOfPsiStorms', icon='Assets\\Textures\\btn-unit-protoss-fenix-purifier-conclave.dds', alias='_UnitHuge') +
            ACTOR.format(id='RM7_DehakaDen', model='Dehaka_Nest_COOP', icon='Assets\\Textures\\btn-building-dehaka-dehakanest.dds', alias='_UnitMedium'))
    add_xml(g / 'abildata.xml', RESEARCH.format(abil='RM7_ConclaveResearch', up='RM7_PurifierT1', t=TIME, c=COST) +
            RESEARCH.format(abil='RM7_DenResearch', up='RM7_PrimalT1', t=TIME, c=COST))
    add_xml(g / 'upgradedata.xml', UPGRADES)
    add_xml(g / 'behaviordata.xml', LEECH + NODIE)
    add_xml(g / 'buttondata.xml', BUTTONS)
    add_xml(g / 'requirementdata.xml', REQ.format(up='RM7_PurifierT1') + REQ.format(up='RM7_PrimalT1'))
    add_xml(g / 'requirementnodedata.xml', NODES.format(up='RM7_PurifierT1') + NODES.format(up='RM7_PrimalT1'))
    p = d / 'mapscript.galaxy'
    raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    assert t.count(ALLOW_ANCHOR) == 1 and 'gt_rm7Tick' not in t, d.name
    t = t.replace(ALLOW_ANCHOR, ALLOW_ANCHOR + ALLOW)
    inc = list(re.finditer(r'^include "[^"]+"\n', t, re.M))
    t = t[:inc[-1].end()] + SCRIPT + t[inc[-1].end():]
    p.write_bytes(t.replace('\n', nl).encode('utf-8'))


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            d = root / f'{m}.SC2Map'
            edit_map(d)
            ko = set_lines((d / KO).read_bytes(), STRINGS)
            (d / KO).write_bytes(ko)
            V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
            for loc in LOCS:
                h = d / f'{loc}.sc2data/localizeddata/gamehotkeys.txt'
                h.write_bytes(set_lines(h.read_bytes(), HOTKEYS))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in MAPS) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
