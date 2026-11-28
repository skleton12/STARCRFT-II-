#!/usr/bin/env python3
"""0.12.14 -> 0.13.1: 비밀 임무 '장막 너머로'(THorner05S, 카스타나) 기본판 (사용자 2026-11-28
"다음 미션 비밀미션인 카스타나", "동맹은 없는 대신 칼달리스와 원시 점화자 1기 3/3을 지원 받음 내유닛은 코랄의 후예 5기
의무관 2기로 내가 직접 조종함 멀티샷 업그레이드 되있는걸로 대신 적들 3/3 업글 1.5배 유닛들 더 많음 혼종 제외",
"칼달리스는 그 재수복업그레이드 있게 해줘 자가수복하는거 같은데 부활 말고").

원본: maps/original_wol/thorner05s (사용자 드라이브의 블리자드 캠페인 추출본 36개). 지형·오브젝트·트리거 그대로.
원작 플레이어: 1 레이너 분대, 2 자치령, 3 헤라클레스, 4 혼종, 5·6 실험체, 7 중립, 8 아군 자동 포탑, 9 중립 공격,
10 과학자, 11 브루탈리스크, 12 적 자동 포탑, 13 자치령 연구소. 원작이 8·9번을 써서 동맹 플레이어는 넣지 않는다(사용자).
- 레이너 분대: 해병 5 → 코랄의 후예(RMK_MarineMengsk) 5, 의무관 2 → 용병 의무관(MercMedic) 2 (인트로·건너뛰기 모두).
  중간 증원(헤라클레스 선택): 해병 → 코랄의 후예, 불곰 → 망치 경호대, 화염방사병 → 악마의 개, 의무관 → 용병 의무관.
- 멀티샷(RM6_Multishot)·코랄의 후예 전투 방패는 처음부터 완료. 히페리온 자극제 구매 = 자극제 1단계(다른 임무와 같음).
- 레이너가 내리면 그 옆에 칼달리스(FenixKaldalisZealot)·원시 점화자(DehakaRoachLevel3) 1기씩, 플레이어 1 조종, 부활 없음.
  둘 다 3/3: 프로토스 지상 무기·장갑·보호막 3단계, 원시 공격·갑피 3단계(플레이어 1). 칼달리스 회전 베기(Cleave) 지급.
  칼달리스 '재구축(자가 수복)': 피해 없이 5초 뒤 초당 생명력 5 재생(시험값, 부활 아님 — 사용자).
- 적 3/3: 자치령(2·13)·실험체(5·6)·브루탈리스크(11)·적 자동 포탑(12)에 테란 보병·차량·함선, 저그 근접·원거리·갑피·비행,
  프로토스 지상 무기·장갑·보호막 1~3단계 전부(혼종 4번 제외).
- 적 유닛 1.5배: 3초마다 자치령(2·13) 전투 유닛 중 처음 보는 것(배치·스크립트 생성·하차 모두)마다 0.5씩 쌓아 1이 되면 옆에
  같은 유닛 1기(시험값). 혼종·영웅·건물·일꾼·숨김·수송 중·무적 제외, 실험체는 우리 안에 있어 제외. 지나갈 수 있고 레이너와 길이
  이어진 자리만.
- 업적 끔. 다른 11개 언어는 kokr 영어 부분.
데이터는 코랄 맵(THorner04)의 현재 판에서 tools/catalog_closure.py(rm)로 떠 온다. Game not run.

Usage: python3 tools/build_v0131.py <0.12.14 zip> <thorner05s folder> <new output zip>
"""
import argparse, copy, re, shutil, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import build_v0101 as B

OLD, NEW = b'version=0.12.14', b'version=0.13.1'
M = 'THorner05S.SC2Map'
SRC = 'THorner04.SC2Map'
LOCALES = B.LOCALES
S = ROOT / 'source'
BASE = B.BASE
ROOTS = 'RMK_MarineMengsk,MercMedic,RM6_Multishot,FenixKaldalisZealot,DehakaRoachLevel3'
SKIP = 'skip=^(RML|RMPL|RMZL|RM12|RM5_|RM7_|RM8_|RM9_|RMA_|RM4_HideOriginal)'
UPS = ([f'ProtossGround{k}Level{n}' for k in ('Weapons', 'Armors') for n in (1, 2, 3)] + [f'ProtossShieldsLevel{n}' for n in (1, 2, 3)]
       + [f'DehakaPrimal{k}Level{n}' for k in ('Weapons', 'Armor') for n in (1, 2, 3)]
       + ['TerranInfantryWeapons', 'TerranInfantryArmors']
       + [f'TerranInfantry{k}Level{n}' for k in ('Weapons', 'Armors', 'WeaponsUltraCapacitors', 'ArmorsVanadiumPlating') for n in (1, 2, 3)])
STR = {
    'Button/Name/RM13_KaldalisRegen': '재구축 /// Reconstruction',
    'Button/Tooltip/RM13_KaldalisRegen': '피해를 받지 않고 5초가 지나면 초당 생명력을 5씩 회복합니다. /// After 5 seconds without taking damage, regenerates 5 life per second.',
    'Param/Value/C0D11339': '<s val="THorner05sAllButtons">요청: 코랄의 후예 8명</s> /// <s val="THorner05sAllButtons">Request: 8 Sons of Korhal</s>',
    'Param/Value/B3607D5C': '<s val="THorner05sAllButtons">요청: 망치 경호대 3명</s> /// <s val="THorner05sAllButtons">Request: 3 Hammer Securities</s>',
    'Param/Value/2D902983': '<s val="THorner05sAllButtons">요청: 악마의 개 4명</s> /// <s val="THorner05sAllButtons">Request: 4 Devil Dogs</s>',
    'Param/Value/BB0EF13C': '<s val="THorner05sAllButtons">요청: 코랄의 후예 3명,<n/>용병 의무관 3명</s> /// <s val="THorner05sAllButtons">Request: 3 Sons of Korhal,<n/>3 Mercenary Medics</s>',
    'Param/Value/RM13_Heroes': '칼달리스와 원시 점화자가 합류했습니다. /// Kaldalis and a Primal Igniter have joined you.',
}

SCRIPT = '''// 0.13.1 (user 2026-11-28): Castanar secret mission - no ally players; Kaldalis + Primal Igniter (3/3) join Raynor,
// Sons of Korhal x5 + mercenary medics x2 with Multishot, enemies 3/3 and 1.5x Dominion units (hybrids excluded).
const fixed gv_rm13Extra = 0.5;  // trial: +50% Dominion combat units
bool gv_rm13Up;
bool gv_rm13Heroes;
fixed[16] gv_rm13Carry;

void gf_rm13Grant (int p, string up) {
    if (TechTreeUpgradeCount(p, up, c_techCountCompleteOnly) < 1) { TechTreeUpgradeAddLevel(p, up, 1); }
}

void gf_rm13Lines (int p, string line) {
    gf_rm13Grant(p, line + "1");
    gf_rm13Grant(p, line + "2");
    gf_rm13Grant(p, line + "3");
}

void gf_rm13EnemyUp (int p) {
    gf_rm13Lines(p, "TerranInfantryWeaponsLevel");
    gf_rm13Lines(p, "TerranInfantryArmorsLevel");
    gf_rm13Lines(p, "TerranVehicleWeaponsLevel");
    gf_rm13Lines(p, "TerranVehicleArmorsLevel");
    gf_rm13Lines(p, "TerranShipWeaponsLevel");
    gf_rm13Lines(p, "TerranShipArmorsLevel");
    gf_rm13Lines(p, "ZergMeleeWeaponsLevel");
    gf_rm13Lines(p, "ZergMissileWeaponsLevel");
    gf_rm13Lines(p, "ZergGroundArmorsLevel");
    gf_rm13Lines(p, "ZergFlyerWeaponsLevel");
    gf_rm13Lines(p, "ZergFlyerArmorsLevel");
    gf_rm13Lines(p, "ProtossGroundWeaponsLevel");
    gf_rm13Lines(p, "ProtossGroundArmorsLevel");
    gf_rm13Lines(p, "ProtossShieldsLevel");
}

void gf_rm13Hero (string k, fixed ang) {
    point c = UnitGetPosition(gv_raynor);
    point p = UnitTypePlacementFromPoint(k, 1, PointWithOffsetPolar(c, 2.5, ang), 6.0);
    if (p == null || !PointPathingPassable(p) || !PointPathingIsConnected(p, c)) { p = c; }
    UnitCreate(1, k, 0, 1, p, 270.0);
}

bool gf_rm13Skip (unit u) {
    string t = UnitGetType(u);
    if (StringContains(t, "Hybrid", c_stringAnywhere, c_stringNoCase)) { return true; }
    if (UnitWeaponCount(u) == 0) { return true; }
    if (UnitTransport(u) != null) { return true; }
    return false;
}

void gf_rm13Clone (unit u, unit h) {
    int p = UnitGetOwner(u);
    point at;
    if (UnitGetCustomValue(u, 9) != 0.0 || gf_rm13Skip(u)) { return; }
    if (gv_rm13Carry[p] + gv_rm13Extra < 1.0) { gv_rm13Carry[p] += gv_rm13Extra; UnitSetCustomValue(u, 9, 1.0); return; }
    at = UnitTypePlacementFromPoint(UnitGetType(u), p, UnitGetPosition(u), 4.0);
    if (at == null || !PointPathingPassable(at) || (h != null && !PointPathingIsConnected(at, UnitGetPosition(h)))) { return; }
    UnitSetCustomValue(u, 9, 1.0);
    gv_rm13Carry[p] += gv_rm13Extra - 1.0;
    UnitCreate(1, UnitGetType(u), 0, p, at, UnitGetFacing(u));
    if (UnitLastCreated() != null) { UnitSetCustomValue(UnitLastCreated(), 9, 1.0); }
}

// placed units: before the triggers capture their groups (Codex review)
void gf_rm13ClonePlaced () {
    int p;
    int i;
    unitgroup g;
    for (p = 2; p <= 13; p += 11) {
        g = UnitGroup(null, p, RegionEntireMap(), UnitFilter(0, 0, (1 << c_targetFilterStructure) | (1 << c_targetFilterWorker) | (1 << c_targetFilterHeroic) | (1 << c_targetFilterMissile),
            (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterHallucination - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);
        for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) { gf_rm13Clone(UnitGroupUnit(g, i), null); }
    }
}

void gf_rm13SpawnHeroes () {
    if (gv_rm13Heroes || gv_raynor == null) { return; }
    gv_rm13Heroes = true;
    gf_rm13Hero("FenixKaldalisZealot", 200.0);
    gf_rm13Hero("DehakaRoachLevel3", 340.0);
    UIDisplayMessage(PlayerGroupAll(), c_messageAreaSubtitle, StringExternal("Param/Value/RM13_Heroes"));
}

bool gt_rm13Tick_Func (bool testConds, bool runActions) {
    int p;
    int i;
    unit u;
    unit h;
    unitgroup g;
    if (!runActions || GameGetMissionTime() < 2.0) { return true; }
    if (!gv_rm13Up) {
        gv_rm13Up = true;
        gf_rm13EnemyUp(2);
        gf_rm13EnemyUp(5);
        gf_rm13EnemyUp(6);
        gf_rm13EnemyUp(11);
        gf_rm13EnemyUp(12);
        gf_rm13EnemyUp(13);
        gf_rm13Grant(1, "RM6_Multishot");
        gf_rm13Grant(1, "RMK_MarineMengskCombatShield");
        if (TechTreeUpgradeCount(1, "MarineStimpack", c_techCountCompleteOnly) > 0) { gf_rm13Grant(1, "RM3_Stim1"); }
        TechTreeAbilityAllow(1, AbilityCommand("RM4_MercStimpack", 0), true);
        gf_rm13Grant(1, "FenixKaldalisCleave");
        gf_rm13Lines(1, "ProtossGroundWeaponsLevel");
        gf_rm13Lines(1, "ProtossGroundArmorsLevel");
        gf_rm13Lines(1, "ProtossShieldsLevel");
        gf_rm13Lines(1, "DehakaPrimalWeaponsLevel");
        gf_rm13Lines(1, "DehakaPrimalArmorLevel");
    }
    h = gv_raynor;
    for (p = 2; p <= 13; p += 11) {
        g = UnitGroup(null, p, RegionEntireMap(), UnitFilter(0, 0, (1 << c_targetFilterStructure) | (1 << c_targetFilterWorker) | (1 << c_targetFilterHeroic) | (1 << c_targetFilterMissile),
            (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterHallucination - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);
        for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {
            u = UnitGroupUnit(g, i);
            gf_rm13Clone(u, h);
        }
    }
    return true;
}

void gf_rm13Init () {
    TriggerAddEventTimePeriodic(TriggerCreate("gt_rm13Tick_Func"), 3.0, c_timeGame);
}

'''


def ids_of_file(f):
    return set(re.findall(r'\bid="([^"]+)"', f.read_text('utf-8', 'replace'))) if f.exists() else set()


def ids_of(gd):
    out = set()
    for f in gd.glob('*.xml'): out |= set(re.findall(r'\bid="([^"]+)"', f.read_text('utf-8', 'replace')))
    return out


def port(m, src):
    out = subprocess.run([sys.executable, str(HERE / 'catalog_closure.py'), str(src / 'base.sc2data/gamedata'), ROOTS,
                          ','.join(map(str, BASE)), 'rm', SKIP], check=True, capture_output=True, text=True).stdout
    items, ids = {}, set()
    for line in out.splitlines():
        i, files = line.split(' ', 1); ids.add(i)
        for fn in files.split(','): items.setdefault(fn, []).append(i)
    print('records', B.add_records(m / 'base.sc2data/gamedata', src / 'base.sc2data/gamedata', items))
    return ids


def upgrades(m, src):
    gd = m / 'base.sc2data/gamedata'
    def kind(fn):
        out = ids_of_file(gd / fn)
        for d in BASE: out |= ids_of_file(d / fn)
        return out
    have = {'Unit': kind('unitdata.xml'), 'Weapon': kind('weapondata.xml'), 'Effect': kind('effectdata.xml'),
            'Behavior': kind('behaviordata.xml'), 'Abil': kind('abildata.xml')}
    srcrec = B.recs(src / 'base.sc2data/gamedata/upgradedata.xml')
    add = ''
    for u in UPS:
        if u not in srcrec: continue
        r = srcrec[u]
        def keep(mm):
            ref = re.search(r'Reference="([A-Za-z]+),([^,"]+)', mm.group(0))
            if ref is None: return mm.group(0)
            return mm.group(0) if ref.group(2) in have.get(ref.group(1), set()) else ''
        r = re.sub(r'\s*<EffectArray\b[^>]*/>', lambda mm: keep(mm), r)
        r = re.sub(r'\s*<AffectedUnitArray value="([^"]+)"\s*/>', lambda mm: mm.group(0) if mm.group(1) in have['Unit'] else '', r)
        add += '    ' + r.strip() + '\n'
    p = gd / 'upgradedata.xml'
    body = p.read_text('utf-8') if p.exists() else '<?xml version="1.0" encoding="utf-8"?>\n<Catalog>\n</Catalog>\n'
    assert not any(f'id="{u}"' in body for u in UPS)
    i = body.rindex('</Catalog>'); p.write_text(body[:i] + add + body[i:], 'utf-8')


def kaldalis(gd):
    p = gd / 'unitdata.xml'; t = p.read_text('utf-8')
    s = t.index('<CUnit id="FenixKaldalisZealot"'); e = t.index('</CUnit>', s)
    u = t[s:e]
    assert 'LifeRegen' not in u and 'Row="2" Column="2"' not in u
    u = u.replace('<LifeMax value="400" />', '<LifeMax value="400" />\n        <LifeRegenRate value="5" />\n        <LifeRegenDelay value="5" />', 1)
    u = u.replace('Requirements="HaveKaldalisCleave" Row="2" Column="1" />',
                  'Requirements="HaveKaldalisCleave" Row="2" Column="1" />\n            <LayoutButtons Face="RM13_KaldalisRegen" Type="Passive" Row="2" Column="2" />', 1)
    assert 'LifeRegenRate' in u and 'RM13_KaldalisRegen' in u
    p.write_text(t[:s] + u + t[e:], 'utf-8')
    b = gd / 'buttondata.xml'; bt = b.read_text('utf-8'); i = bt.rindex('</Catalog>')
    b.write_text(bt[:i] + '    <CButton id="RM13_KaldalisRegen">\n        <Icon value="Assets\\Textures\\BTN-Ability-Protoss-Reconstruction.dds" />\n'
                 '        <Name value="Button/Name/RM13_KaldalisRegen" />\n        <Tooltip value="Button/Tooltip/RM13_KaldalisRegen" />\n    </CButton>\n' + bt[i:], 'utf-8')


def script(t):
    def rep(a, b, n=1):
        nonlocal t
        assert t.count(a) == n, (a[:70], t.count(a)); t = t.replace(a, b)
    rep('    UnitCargoCreate(gv_introDropship, "Marine", 5);', '    UnitCargoCreate(gv_introDropship, "RMK_MarineMengsk", 5);')
    rep('    UnitCargoCreate(gv_introDropship, "Medic", 2);', '    UnitCargoCreate(gv_introDropship, "MercMedic", 2);')
    for pt in (7, 15, 159, 182, 227):
        rep(f'libNtve_gf_CreateUnitsAtPoint2(1, "Marine", 0, gv_p01_USER, PointFromId({pt}));', f'libNtve_gf_CreateUnitsAtPoint2(1, "RMK_MarineMengsk", 0, gv_p01_USER, PointFromId({pt}));')
    for pt in (279, 245):
        rep(f'libNtve_gf_CreateUnitsAtPoint2(1, "Medic", 0, gv_p01_USER, PointFromId({pt}));', f'libNtve_gf_CreateUnitsAtPoint2(1, "MercMedic", 0, gv_p01_USER, PointFromId({pt}));')
    rep('(UnitGetType(EventUnitCargo()) == "Marine") || (UnitGetType(EventUnitCargo()) == "Medic")',
        '(UnitGetType(EventUnitCargo()) == "RMK_MarineMengsk") || (UnitGetType(EventUnitCargo()) == "MercMedic")')
    rep('    if ((UnitGetType(EventUnitCargo()) == "Marine")) {', '    if ((UnitGetType(EventUnitCargo()) == "RMK_MarineMengsk")) {')
    rep('    if ((UnitGetType(EventUnitCargo()) == "Medic")) {', '    if ((UnitGetType(EventUnitCargo()) == "MercMedic")) {')
    rep('libCamp_gf_AddUnitTypeToUnitHelpPanel("Marine", false, gv_p01_USER);', 'libCamp_gf_AddUnitTypeToUnitHelpPanel("RMK_MarineMengsk", false, gv_p01_USER);')
    rep('libCamp_gf_AddUnitTypeToUnitHelpPanel("Medic", false, gv_p01_USER);', 'libCamp_gf_AddUnitTypeToUnitHelpPanel("MercMedic", false, gv_p01_USER);')
    rep('UnitCargoCreate(gv_dropshipComputer05, "Marine", 8);', 'UnitCargoCreate(gv_dropshipComputer05, "RMK_MarineMengsk", 8);')
    rep('UnitCargoCreate(gv_dropshipComputer05, "Marauder", 3);', 'UnitCargoCreate(gv_dropshipComputer05, "HammerSecurity", 3);')
    rep('UnitCargoCreate(gv_dropshipComputer05, "Firebat", 4);', 'UnitCargoCreate(gv_dropshipComputer05, "DevilDog", 4);')
    rep('UnitCargoCreate(gv_dropshipComputer05, "Marine", 3);', 'UnitCargoCreate(gv_dropshipComputer05, "RMK_MarineMengsk", 3);')
    rep('UnitCargoCreate(gv_dropshipComputer05, "Medic", 3);', 'UnitCargoCreate(gv_dropshipComputer05, "MercMedic", 3);')
    a = '//--------------------------------------------------------------------------------------------------\n// Trigger: '
    i = t.index(a); t = t[:i] + SCRIPT + t[i:]
    rep('    UnitSetPropertyFixed(gv_raynor, c_unitPropLifePercent, 100.0);\n    UnitPauseAll(false);',
        '    UnitSetPropertyFixed(gv_raynor, c_unitPropLifePercent, 100.0);\n    gf_rm13SpawnHeroes();\n    UnitPauseAll(false);')
    rep('void InitMap () {\n    InitLibs();\n    InitGlobals();\n    InitTriggers();\n}',
        'void InitMap () {\n    AchievementsDisable(1);\n    InitLibs();\n    gf_rm13ClonePlaced();\n    InitGlobals();\n    InitTriggers();\n    gf_rm13Init();\n}')
    return t


def assets(m, src):
    # mod model files (Sons of Korhal WoM model, legionnaire/Kaldalis model, textures); not Goliath/Incinerator
    n = 0
    for f in (src / 'Assets').rglob('*'):
        if not f.is_file() or re.search(r'goliath|incinerator', str(f), re.I): continue
        d = m / f.relative_to(src); d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(f, d); n += 1
    print('assets', n)


def fixups(gd, src):
    u = gd / 'unitdata.xml'; ut = u.read_text('utf-8')
    s = ut.index('<CUnit id="RMK_MarineMengsk">'); e = ut.index('</CUnit>', s)
    blk = ut[s:e]; assert blk.count('<CargoSize value="2" />') == 1
    ut = ut[:s] + blk.replace('<CargoSize value="2" />', '<CargoSize value="1" />') + ut[e:]
    ut2 = re.sub(r'\s*<LayoutButtons Face="DehakaGlevigHaveRoachFireBreath"[^>]*/>', '', ut)
    assert ut2 != ut; u.write_text(ut2, 'utf-8')
    f = gd / 'effectdata.xml'; ft = f.read_text('utf-8')
    ft2 = ft.replace('\n        <EffectArray value="CommanderPrestigeFenixAvengerRefundZealot" />', '')
    assert ft2 != ft; f.write_text(ft2, 'utf-8')
    ab = gd / 'abildata.xml'; abt = ab.read_text('utf-8')
    abt2 = abt.replace('\n        <Effect value="KerriganReviveHeal" />', ''); assert abt2 != abt; ab.write_text(abt2, 'utf-8')
    ft = f.read_text('utf-8'); ft2 = re.sub(r'\s*<CEffectSet id="KerriganReviveHeal">.*?</CEffectSet>', '', ft, flags=re.S)
    assert ft2 != ft; f.write_text(ft2, 'utf-8')
    a = gd / 'actordata.xml'; t = a.read_text('utf-8')
    t2 = re.sub(r'\s*<On [^>]*Send="Create (?:Infestor_Land|GlazeSentinelRepair)"\s*/>', '', t)
    assert t2 != t; a.write_text(t2, 'utf-8')
    B.add_records(gd, src / 'base.sc2data/gamedata', {'moverdata.xml': ['WarHoundWeapon']})
    assert 'id="WarHoundWeapon"' in (gd / 'moverdata.xml').read_text('utf-8')


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        root = Path(tmp)
        prev.extractall(root)
        m, src = root / M, root / SRC
        assert not m.exists()
        shutil.copytree(folder, m)
        gd = m / 'base.sc2data/gamedata'
        ids = port(m, src)
        upgrades(m, src)
        kaldalis(gd)
        assets(m, src)
        fixups(gd, src)
        sp = m / 'mapscript.galaxy'; raw = sp.read_bytes().decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
        assert 'AchievementsDisable' not in raw
        sp.write_bytes(script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'))
        ks = (src / 'kokr.sc2data/localizeddata/gamestrings.txt').read_bytes().decode('utf-8-sig')
        kh = (src / 'kokr.sc2data/localizeddata/gamehotkeys.txt').read_bytes().decode('utf-8-sig')
        ko = m / 'kokr.sc2data/localizeddata/gamestrings.txt'
        B.add_lines(ko, B.strip_lines(ks, ids))
        kt = ko.read_bytes().decode('utf-8-sig'); nl = '\r\n' if '\r\n' in kt else '\n'
        lines = [l for l in kt.splitlines() if l.split('=', 1)[0] not in STR] + [f'{k}={v}' for k, v in STR.items()]
        ko.write_bytes((nl.join(lines) + nl).encode('utf-8'))
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            q = m / f'{loc}.sc2data/localizeddata/gamestrings.txt'; q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(V35.other_locale(ko.read_bytes()))
        hot = {**B.strip_lines(kh, ids), 'Button/Hotkey/RM13_KaldalisRegen': 'R'}
        for loc in LOCALES:
            B.add_lines(m / f'{loc}.sc2data/localizeddata/gamehotkeys.txt', hot)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in m.rglob('*.xml'): E.parse(f)
        names = prev.namelist()
        extra = sorted(str(p.relative_to(root)).replace('\\', '/') for p in m.rglob('*') if p.is_file())
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra:
                    zi = zipfile.ZipInfo(f, (2026, 11, 28, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    out.writestr(zi, (root / f).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(extra), 'new files')


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('folder', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.folder, a.output)
