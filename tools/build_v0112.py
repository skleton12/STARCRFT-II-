#!/usr/bin/env python3
"""0.11.1 -> 0.11.2: 발할라(THorner03) 레이스 -> 아스테리아 망령(HHWraith)·업그레이드 (사용자 2026-11-25 "바꿔 그리고 업그레이드도").

규칙(3장): 레이너의 레이스는 한과 호너 협동전 아스테리아 망령(HHWraith)으로 바꾼다.
- tools/port_units.py로 협동전 HHWraith·연구 2개(방아쇠 해제 HHWraithFury: 공격마다 공속 +10%, 최대 +100% / 미등록 은폐 체계
  HHWraithPermaCloak: 영구 은폐)를 이식. 호너 사령관 전용(함대 도약·호너 통계·OOC 재생·사랑의 힘 HHSOBuff)은 따라가지 않고 버튼에서 뺀다.
- 우주공항 레이스 칸(StarportTrain Train8)을 플레이어 1만 HHWraith로(버튼 이름·설명도). 이미 있는 플레이어 1 레이스
  (호위 단계에 넘어오는 4기 포함)와 생산돼 나온 레이스는 HHWraith로 바꾼다(용병 바꿈과 같은 곳).
  비용·인구는 자날 레이스와 같은 150/100·2로 둔다(시험값, 협동전 원본 400/200·4).
- 우주공항 기술실 첫 화면 (1,0) 방아쇠 해제(S)·(1,1) 미등록 은폐 체계(C): 협동전 비용 100/100·90초, 한 번만. 모드에서 재설계한
  미션 내 연구(협동전 연구는 원래 사령관 레벨 해금). 원작 레이스 은폐 연구(Research5)는 레이스가 없으니 숨김.
- 함선 공격·방어 1~3단계(울트라 축전기·바나듐 장갑판 포함)가 HHWraith에도 붙게 협동전 한과 호너 값대로 줄을 더함.
- 원본 스크립트의 레이너 레이스 확인 3곳("Wraith")을 "HHWraith"로.
Game not run.
Usage: python3 tools/build_v0112.py <0.11.1 zip> <new output zip>"""
import copy, re, shutil, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import build_v035 as V35
import build_v0101 as V1
from build_v051 import sub1

OLD, NEW = b'version=0.11.1', b'version=0.11.2'
M = 'THorner03.SC2Map'
DROP = '--drop=Horner|FleetwideJump|TheHornersStatUpdate|Vorazun|HHArmyOOCRegen|HHSOBuff|HHMSOHealth'
SEEDS = ['HHWraith', 'HHWraithFury', 'HHWraithPermaCloak', 'ResearchHHWraithFury', 'ResearchHHWraithPermaCloak']
FURY = '방아쇠 해제 /// Trigger Override'
CLOAK = '미등록 은폐 체계 /// Unregistered Cloaking System'
STR = {
    'Unit/Name/HHWraith': '아스테리아 망령 /// Asteria Wraith',
    'ArmyCategory/Name/HHWraith': '망령 /// Wraith',
    'Button/Name/HHWraith': '아스테리아 망령 /// Asteria Wraith',
    'Button/Tooltip/HHWraith': '기동성이 뛰어난 비행 유닛입니다. 정밀 타격에 뛰어나며 은폐할 수 있습니다. /// Highly mobile flying unit. Excellent at surgical strikes. Can cloak.',
    'Weapon/Name/HHWraith': '폭발 레이저 /// Burst Lasers',
    'Button/Name/HHWraithFury': FURY,
    'Button/Tooltip/HHWraithFury': '<c val="FFFF8A">아스테리아 망령</c>이 공격할 때마다 공격 속도가 10%씩 증가합니다(최대 100%).<n/><n/><c val="#ColorAttackInfo">지속 효과</c> /// <c val="FFFF8A">Wraith</c> attack speed increases by 10% with each attack, up to a maximum of 100%.<n/><n/><c val="#ColorAttackInfo">Passive ability.</c>',
    'Button/Name/HHWraithPermaCloak': CLOAK,
    'Button/Tooltip/HHWraithPermaCloak': '아스테리아 망령이 영구히 은폐합니다. /// Wraiths are permanently cloaked.',
    'Button/Name/ResearchHHWraithFury': '방아쇠 해제 연구 /// Research Trigger Override',
    'Button/Tooltip/ResearchHHWraithFury': '<c val="FFFF8A">아스테리아 망령</c>이 공격할 때마다 공격 속도가 10%씩 증가합니다(최대 100%). /// <c val="FFFF8A">Wraith</c> attack speed increases by 10% with each attack, up to a maximum of 100%.',
    'Button/Name/ResearchHHWraithPermaCloak': '미등록 은폐 체계 연구 /// Research Unregistered Cloaking System',
    'Button/Tooltip/ResearchHHWraithPermaCloak': '<c val="ffff8a">아스테리아 망령</c>이 에너지 없이 영구히 은폐합니다. /// Allows <c val="ffff8a">Wraiths</c> to remain permanently cloaked.',
    'Upgrade/Name/HHWraithFury': FURY,
    'Upgrade/Name/HHWraithPermaCloak': CLOAK,
    'RequirementNode/Tooltip/CountUpgradeHHWraithFuryCompleteOnly1586759016': '우주공항 기술실에서 방아쇠 해제 연구 필요 /// Research Trigger Override at the Starport Tech Lab.',
}
for n in range(1, 11):
    STR[f'Behavior/Name/HHWraithFury{n}'] = FURY
    STR[f'Behavior/Tooltip/HHWraithFury{n}'] = f'공격 속도 {n * 10}% 증가 /// Attack Speed increased by {n * 10}%'
HOT = {'Button/Hotkey/ResearchHHWraithFury': 'S', 'Button/Hotkey/ResearchHHWraithPermaCloak': 'C'}

REQ = '''    <CRequirement id="RM11_FuryLearn">
        <NodeArray index="Show" Link="RM11_FuryNotQueued" />
        <NodeArray index="Use" Link="RM11_FuryNotQueued" />
    </CRequirement>
    <CRequirement id="RM11_CloakLearn">
        <NodeArray index="Show" Link="RM11_CloakNotQueued" />
        <NodeArray index="Use" Link="RM11_CloakNotQueued" />
    </CRequirement>
'''
NODES = '''    <CRequirementCountUpgrade id="RM11_FuryQueued">
        <Count Link="HHWraithFury" State="QueuedOrBetter" />
    </CRequirementCountUpgrade>
    <CRequirementNot id="RM11_FuryNotQueued">
        <OperandArray index="0" value="RM11_FuryQueued" />
    </CRequirementNot>
    <CRequirementCountUpgrade id="RM11_CloakQueued">
        <Count Link="HHWraithPermaCloak" State="QueuedOrBetter" />
    </CRequirementCountUpgrade>
    <CRequirementNot id="RM11_CloakNotQueued">
        <OperandArray index="0" value="RM11_CloakQueued" />
    </CRequirementNot>
'''
ABIL = '''    <CAbilResearch id="StarportTechLabResearch">
        <InfoArray index="Research5">
            <Button Requirements="RM4_HideOriginal" />
        </InfoArray>
        <InfoArray index="Research26" Time="90" Upgrade="HHWraithFury">
            <Resource index="Minerals" value="100" />
            <Resource index="Vespene" value="100" />
            <Button DefaultButtonFace="ResearchHHWraithFury" Requirements="RM11_FuryLearn" />
        </InfoArray>
        <InfoArray index="Research28" Time="90" Upgrade="HHWraithPermaCloak">
            <Resource index="Minerals" value="100" />
            <Resource index="Vespene" value="100" />
            <Button DefaultButtonFace="ResearchHHWraithPermaCloak" Requirements="RM11_CloakLearn" />
        </InfoArray>
    </CAbilResearch>
'''
UNIT = '''    <CUnit id="StarportTechLab">
        <CardLayouts index="0">
            <LayoutButtons Face="ResearchHHWraithFury" Type="AbilCmd" AbilCmd="StarportTechLabResearch,Research26" Row="1" Column="0" />
            <LayoutButtons Face="ResearchHHWraithPermaCloak" Type="AbilCmd" AbilCmd="StarportTechLabResearch,Research28" Row="1" Column="1" />
        </CardLayouts>
    </CUnit>
    <CUnit id="StarportTechReactor">
        <CardLayouts index="0">
            <LayoutButtons Face="ResearchHHWraithFury" Type="AbilCmd" AbilCmd="StarportTechLabResearch,Research26" Row="1" Column="0" />
            <LayoutButtons Face="ResearchHHWraithPermaCloak" Type="AbilCmd" AbilCmd="StarportTechLabResearch,Research28" Row="1" Column="1" />
        </CardLayouts>
    </CUnit>
'''
WLINES = '''        <AffectedUnitArray value="HHWraith" />
        <EffectArray Reference="Weapon,HHWraith,Level" Value="1" />
        <EffectArray Reference="Effect,HHWraithU,Amount" Value="2.000000" />
        <EffectArray Operation="Set" Reference="Weapon,HHWraith,Icon" Value="Assets\\Textures\\btn-upgrade-terran-shipweaponslevel{n}.dds" />
'''
ALINES = '''        <AffectedUnitArray value="HHWraith" />
        <EffectArray Reference="Unit,HHWraith,LifeArmorLevel" Value="1" />
        <EffectArray Reference="Unit,HHWraith,LifeArmor" Value="1" />
        <EffectArray Operation="Set" Reference="Actor,HHWraith,LifeArmorIcon" Value="Assets\\Textures\\btn-upgrade-terran-shipplatinglevel{n}.dds" />
'''
SCRIPT_FN = '''// 0.11.2 (user 2026-11-25): Raynor's Wraiths are Asteria Wraiths (co-op Han and Horner HHWraith, rule 3).
void gf_rm11Starport () {
    CatalogFieldValueSet(c_gameCatalogAbil,"StarportTrain","InfoArray[Train8].Unit[0]",1,"HHWraith");
    CatalogFieldValueSet(c_gameCatalogButton,"Wraith","Name",1,"Button/Name/HHWraith");
    CatalogFieldValueSet(c_gameCatalogButton,"Wraith","Tooltip",1,"Button/Tooltip/HHWraith");
    TechTreeUnitAllow(1,"HHWraith",true);
    TechTreeAbilityAllow(1,AbilityCommand("StarportTechLabResearch",4),false);
    TechTreeAbilityAllow(1,AbilityCommand("StarportTechLabResearch",25),true);
    TechTreeAbilityAllow(1,AbilityCommand("StarportTechLabResearch",27),true);
    TechTreeUpgradeAllow(1,"HHWraithFury",true);
    TechTreeUpgradeAllow(1,"HHWraithPermaCloak",true);
}

'''
SWAP = '        else if (t=="SiegeTank") { libNtve_gf_ReplaceUnit(u,"SiegeBreaker",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'
SWAPW = SWAP + '        else if (t=="Wraith") { libNtve_gf_ReplaceUnit(u,"HHWraith",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'
SWAP2 = '    else if (t=="SiegeTank") { libNtve_gf_ReplaceUnit(u,"SiegeBreaker",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'
SWAP2W = SWAP2 + '    else if (t=="Wraith") { libNtve_gf_ReplaceUnit(u,"HHWraith",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'


def ins(path, text):
    t = path.read_text('utf-8'); k = t.rindex('</Catalog>')
    path.write_text(t[:k] + text + t[k:], 'utf-8')


def unitfix(gd):
    p = gd / 'unitdata.xml'; t = p.read_text('utf-8')
    a = t.index('<CUnit id="HHWraith">'); b = t.index('</CUnit>', a)
    blk = t[a:b]
    for bad in ('HHArmyOOCRegen', 'HHMSOHealth', 'TheHornersStatUpdate'):
        blk = '\n'.join(l for l in blk.split('\n') if bad not in l)
    blk = sub1(blk, '<Food value="-4" />', '<Food value="-2" />')
    blk = sub1(blk, '<CostResource index="Minerals" value="400" />', '<CostResource index="Minerals" value="150" />')
    blk = sub1(blk, '<CostResource index="Vespene" value="200" />', '<CostResource index="Vespene" value="100" />')
    assert 'Horner' not in blk and 'HHSO' not in blk
    p.write_text(t[:a] + blk + t[b:], 'utf-8')
    # co-op Mira/Horner transformation signal and the Horner launch attach pattern are not in this map (check_release, Codex)
    p = gd / 'actordata.xml'; t = p.read_text('utf-8')
    t = sub1(t, '        <On Terms="Signal.*.Mira" Send="Create MiraHorner_Transformation_Coop_Wraith" />\n', '')
    t = sub1(t, '        <LaunchAttachQuery Methods="AMPatternHHWraith" />\n', '')
    p.write_text(t, 'utf-8')


def ship_upgrades(gd):
    p = gd / 'upgradedata.xml'; t = p.read_text('utf-8')
    add = ''
    for n in (1, 2, 3):
        uc = WLINES + '        <EffectArray Reference="Weapon,HHWraith,RateMultiplier" Value="0.05" />\n'
        vp = ALINES + ('        <EffectArray Operation="Multiply" Reference="Unit,HHWraith,LifeMax" Value="1.05" />\n'
                       '        <EffectArray Operation="Multiply" Reference="Unit,HHWraith,LifeStart" Value="1.05" />\n')
        for kind, lines in (('Weapons', WLINES), ('WeaponsUltraCapacitors', uc), ('Armors', ALINES), ('ArmorsVanadiumPlating', vp)):
            uid = f'TerranShip{kind}Level{n}'
            assert f'id="{uid}"' not in t, uid
            add += f'    <CUpgrade id="{uid}">\n' + lines.replace('{n}', str(n)) + '    </CUpgrade>\n'
    k = t.rindex('</Catalog>'); p.write_text(t[:k] + add + t[k:], 'utf-8')


def script(raw):
    nl = '\r\n' if '\r\n' in raw else '\n'; t = raw.replace('\r\n', '\n')
    for a, b in ((SWAP, SWAPW), (SWAP2, SWAP2W)):
        hits = [m.start() for m in re.finditer('^' + re.escape(a), t, re.M)]
        assert len(hits) == 1, (a, hits)
        t = t[:hits[0]] + b + t[hits[0] + len(a):]
    t = sub1(t, 'void gf_m11_Init () {', SCRIPT_FN + 'void gf_m11_Init () {')
    t = sub1(t, '    gf_rmFactory();\n', '    gf_rmFactory();\n    gf_rm11Starport();\n')
    t = sub1(t, 'UnitGroup("Wraith", c_playerAny, RegionEntireMap()', 'UnitGroup("HHWraith", c_playerAny, RegionEntireMap()')
    t = sub1(t, 'UnitGroup("Wraith", gv_p01_USER, RegionPlayableMap()', 'UnitGroup("HHWraith", gv_p01_USER, RegionPlayableMap()')
    t = sub1(t, 'UnitGroup("Wraith", gv_p01_USER, RegionEntireMap()', 'UnitGroup("HHWraith", gv_p01_USER, RegionEntireMap()')
    return t.replace('\n', nl)


def build(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z, tempfile.TemporaryDirectory() as tmp:
        assert OLD in z.read('metadata.txt').splitlines()
        root = Path(tmp)
        for n in z.namelist():
            if n.startswith(M + '/'): z.extract(n, root)
        m = root / M; gd = m / 'base.sc2data/gamedata'
        before = {str(p.relative_to(root)).replace('\\', '/'): p.read_bytes() for p in m.rglob('*') if p.is_file()}
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(m), '--liberty-base', '--skip-existing', DROP, *SEEDS],
                       check=True, stdout=subprocess.DEVNULL)
        (m / 'ported_shared_refs.txt').unlink(missing_ok=True)
        unitfix(gd)
        ins(gd / 'requirementdata.xml', REQ)
        ins(gd / 'requirementnodedata.xml', NODES)
        for f, needle in (('abildata.xml', 'id="StarportTechLabResearch"'), ('unitdata.xml', '<CUnit id="StarportTechLab"'), ('unitdata.xml', '<CUnit id="StarportTechReactor"')):
            assert needle not in (gd / f).read_text('utf-8'), f
        ins(gd / 'abildata.xml', ABIL)
        ins(gd / 'unitdata.xml', UNIT)
        ship_upgrades(gd)
        sp = m / 'mapscript.galaxy'; sp.write_bytes(script(sp.read_bytes().decode('utf-8')).encode('utf-8'))
        ko = m / 'kokr.sc2data/localizeddata/gamestrings.txt'
        V1.add_lines(ko, STR)
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (m / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        for loc in V1.LOCALES:
            V1.add_lines(m / f'{loc}.sc2data/localizeddata/gamehotkeys.txt', HOT)
        for f in gd.glob('*.xml'): E.parse(f)
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        for p in m.rglob('*'):
            if not p.is_file(): continue
            k = str(p.relative_to(root)).replace('\\', '/')
            if before.get(k) != p.read_bytes(): rep[k] = p.read_bytes()
        new = sorted(k for k in rep if k not in z.namelist())
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)))
                for k in new:
                    zi = zipfile.ZipInfo(k, (2026, 11, 25, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    w.writestr(zi, rep[k], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out, len(rep), 'changed,', len(new), 'new')


if __name__ == '__main__': build(*sys.argv[1:])
