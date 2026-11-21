#!/usr/bin/env python3
"""0.6.55 -> 0.6.56: War Pig research - Combat Shield level 2 and B-2 High-Cal LMG (user 2026-11-21).

User: "마린 방패 2단계 업글 추가 스플레쉬 데미지 20%저항", "마린 무기 업그레이드 추가 중장갑 공격력 +2",
"B-2 High-Cal LMG 이걸로 교체 되는걸로 대신 마린 가격이 높아짐", chose "원본 B-2처럼 세게" and "광물 +25",
"코랄의 후예는 미적용". Mod-redesigned in-mission researches (not in the original), maps 3-6, Barracks Tech Lab:

1. RM6_ShieldSplash 'Combat Shield Level 2' (150/150, 90 s, trial): appears in the Combat Shield slot once
   Combat Shield (RM3_Shield) is done, like the Stim 1->2->3 chain. War Pigs take 20% less splash damage
   (hidden permanent behaviour RM6_SplashGuard, DamageResponse limited to Kind Splash; the upgrade lowers its
   ModifyFraction 1 -> 0.8). Spells, melee and normal ranged hits are unchanged.
2. RM6_B2LMG 'B-2 High-Cal LMG' (100/100, 60 s, trial): War Pig weapon damage 8 -> 12 (co-op B-2 value) and
   +2 vs Armored; the weapon name/icon switch to B-2 for player 1 when done. War Pig cost +25 minerals.
   The Multishot second target uses the same damage effect, so it gets the bonus too.
   Map 3: tech lab first page row 1 col 3; maps 4-6: co-op page (RMC1) row 0 col 1. Hotkey B.
Sons of Korhal are not affected. Passive icons on the War Pig card once researched. Game not run.

Usage: python3 tools/build_v0656.py <0.6.55 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import find, xml_edit, add_xml, set_lines, LOCS, KO, GD

OLD, NEW = b'version=0.6.55', b'version=0.6.56'
MAPS = ('TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
SH, B2, BEH = 'RM6_ShieldSplash', 'RM6_B2LMG', 'RM6_SplashGuard'
SH_ICON = 'Assets\\Textures\\btn-techupgrade-terran-combatshield.dds'
B2_ICON = 'Assets\\Textures\\btn-upgrade-terran-weaponrefit.dds'
SPLASH_CUT, B2_DMG, B2_ARMORED, B2_COST = '0.2', '4', '2', '25'
SH_COST, SH_TIME, B2_RCOST, B2_TIME = '150', '90', '100', '60'

ADD = {
    'upgradedata.xml':
        f'<CUpgrade id="{SH}"><Race value="Terr" /><Alert value="ResearchComplete" /><MaxLevel value="1" />'
        f'<Icon value="{SH_ICON}" /><AffectedUnitArray value="WarPig" />'
        f'<EffectArray Operation="Subtract" Reference="Behavior,{BEH},DamageResponse.ModifyFraction" Value="{SPLASH_CUT}" /></CUpgrade>'
        f'<CUpgrade id="{B2}"><Race value="Terr" /><Alert value="ResearchComplete" /><MaxLevel value="1" />'
        f'<Icon value="{B2_ICON}" /><AffectedUnitArray value="WarPig" />'
        f'<EffectArray Reference="Effect,KelmorianMinerDamage,Amount" Value="{B2_DMG}" />'
        f'<EffectArray Reference="Effect,KelmorianMinerDamage,AttributeBonus[Armored]" Value="{B2_ARMORED}" />'
        f'<EffectArray Reference="Unit,WarPig,CostResource[Minerals]" Value="{B2_COST}" /></CUpgrade>',
    'behaviordata.xml':
        f'<CBehaviorBuff id="{BEH}"><InfoFlags index="Hidden" value="1" /><BehaviorFlags index="Permanent" value="1" />'
        f'<DamageResponse ModifyFraction="1"><Kind index="Spell" value="0" /><Kind index="Melee" value="0" />'
        f'<Kind index="Ranged" value="0" /><Kind index="NoProc" value="0" /><Chance value="1" /></DamageResponse></CBehaviorBuff>',
    'buttondata.xml': ''.join(
        f'<CButton id="{i}"><Icon value="{ic}" /><Name value="Button/Name/{i}" /><Tooltip value="Button/Tooltip/{i}" /></CButton>'
        for i, ic in ((SH, SH_ICON), (B2, B2_ICON), ('RMP_' + SH, SH_ICON), ('RMP_' + B2, B2_ICON))),
    'requirementdata.xml':
        f'<CRequirement id="{SH}Learn"><NodeArray index="Use" Link="RM6_ShieldDone" /><NodeArray index="Show" Link="{SH}Show" /></CRequirement>'
        f'<CRequirement id="{B2}Learn"><NodeArray index="Show" Link="{B2}NotQueued" /></CRequirement>'
        f'<CRequirement id="RMP_Have{SH}"><NodeArray index="Show" Link="RMP_Done{SH}" /></CRequirement>'
        f'<CRequirement id="RMP_Have{B2}"><NodeArray index="Show" Link="RMP_Done{B2}" /></CRequirement>',
    'requirementnodedata.xml':
        '<CRequirementCountUpgrade id="RM6_ShieldDone"><Count Link="RM3_Shield" State="CompleteOnly" /></CRequirementCountUpgrade>'
        f'<CRequirementCountUpgrade id="{SH}Queued"><Count Link="{SH}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
        f'<CRequirementNot id="{SH}NotQueued"><OperandArray index="0" value="{SH}Queued" /></CRequirementNot>'
        f'<CRequirementAnd id="{SH}Show"><OperandArray value="RM6_ShieldDone" /><OperandArray value="{SH}NotQueued" /></CRequirementAnd>'
        f'<CRequirementCountUpgrade id="{B2}Queued"><Count Link="{B2}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
        f'<CRequirementNot id="{B2}NotQueued"><OperandArray index="0" value="{B2}Queued" /></CRequirementNot>'
        f'<CRequirementCountUpgrade id="RMP_Done{SH}"><Count Link="{SH}" State="CompleteOnly" /></CRequirementCountUpgrade>'
        f'<CRequirementCountUpgrade id="RMP_Done{B2}"><Count Link="{B2}" State="CompleteOnly" /></CRequirementCountUpgrade>',
}

STRINGS = {
    f'Upgrade/Name/{SH}': '전투 방패 2단계 /// Combat Shield Level 2',
    f'Button/Name/{SH}': '전투 방패 2단계 연구 /// Research Combat Shield Level 2',
    f'Button/Tooltip/{SH}': '전쟁광이 받는 범위 공격 피해가 20% 줄어듭니다. 주문·근접·일반 원거리 피해는 그대로입니다. 전투 방패를 먼저 연구해야 합니다. '
                            '/// War Pigs take 20% less splash damage. Spell, melee and normal ranged damage are unchanged. Requires Combat Shield.',
    f'Button/Name/RMP_{SH}': '전투 방패 2단계 /// Combat Shield Level 2',
    f'Button/Tooltip/RMP_{SH}': '받는 범위 공격 피해 20% 감소. /// Takes 20% less splash damage.',
    f'Upgrade/Name/{B2}': 'B-2 고구경 경기관총 /// B-2 High-Cal LMG',
    f'Button/Name/{B2}': 'B-2 고구경 경기관총 장착 /// Equip B-2 High-Cal LMG',
    f'Button/Tooltip/{B2}': '전쟁광의 무기를 B-2 고구경 경기관총으로 바꿉니다. 공격력 8 → 12, 중장갑 상대 +2. 대신 전쟁광 훈련 비용이 광물 25 늘어납니다. '
                            '/// War Pigs switch to the B-2 High-Cal LMG: damage 8 -> 12, +2 vs Armored. War Pigs cost 25 more minerals to train.',
    f'Button/Name/RMP_{B2}': 'B-2 고구경 경기관총 /// B-2 High-Cal LMG',
    f'Button/Tooltip/RMP_{B2}': '공격력 12, 중장갑 상대 +2. /// Damage 12, +2 vs Armored.',
    f'Weapon/Name/{B2}': 'B-2 고구경 경기관총 /// B-2 High-Cal LMG',
}
HOTKEYS = {f'Button/Hotkey/{SH}': 'C', f'Button/Hotkey/{B2}': 'B'}

ALLOW_ANCHOR = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",0),true);\n'
SCRIPT = f'''
// 0.6.56 (user 2026-11-21): B-2 High-Cal LMG - War Pig weapon name/icon follow the research (player 1 only).
trigger gt_rmB2;
bool gt_rmB2_Func (bool testConds, bool runActions) {{
    if (!runActions) {{ return true; }}
    if (TechTreeUpgradeCount(1, "{B2}", c_techCountCompleteOnly) == 0) {{ return true; }}
    CatalogFieldValueSet(c_gameCatalogWeapon, "KelmorianMinerGaussRifle", "Name", 1, "Weapon/Name/{B2}");
    CatalogFieldValueSet(c_gameCatalogWeapon, "KelmorianMinerGaussRifle", "Icon", 1, "{B2_ICON.replace(chr(92), chr(92) * 2)}");
    TriggerEnable(gt_rmB2, false);
    return true;
}}
'''


def edit_map(m, d):
    g = d / GD
    for fn, xml in ADD.items():
        add_xml(g / fn, xml)
    info = {}

    def abils(root):
        r = find(root, 'CAbilResearch', 'RM3_TechResearch')
        n = max(int(i.get('index')[8:]) for i in r.findall('InfoArray')) + 1
        assert n + 1 <= 30, (m, n)
        for k, up, cost, time in ((n, SH, SH_COST, SH_TIME), (n + 1, B2, B2_RCOST, B2_TIME)):
            r.append(E.fromstring(f'<InfoArray index="Research{k}" Time="{time}" Upgrade="{up}">'
                                  f'<Resource index="Minerals" value="{cost}" /><Resource index="Vespene" value="{cost}" />'
                                  f'<Button DefaultButtonFace="{up}" State="Available" Requirements="{up}Learn" /></InfoArray>'))
        info['n'] = n
    xml_edit(g / 'abildata.xml', abils)
    n = info['n']

    def units(root):
        lab = find(root, 'CUnit', 'BarracksTechLab')
        hit = [(c, b) for c in lab.findall('CardLayouts') for b in c.findall('LayoutButtons') if b.get('Face') == 'RM3_Shield']
        assert len(hit) == 1, m
        card, sb = hit[0]
        card.append(E.fromstring(f'<LayoutButtons Face="{SH}" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research{n}" '
                                 f'Row="{sb.get("Row")}" Column="{sb.get("Column")}" />'))
        if m == 'TRaynor03':
            page, row, col = [c for c in lab.findall('CardLayouts') if c.get('index') == '0'][0], '1', '3'
        else:
            page, row, col = [c for c in lab.findall('CardLayouts') if c.get('CardId') == 'RMC1'][0], '0', '1'
        assert not [b for b in page.findall('LayoutButtons') if (b.get('Row'), b.get('Column')) == (row, col)], m
        page.append(E.fromstring(f'<LayoutButtons Face="{B2}" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research{n + 1}" Row="{row}" Column="{col}" />'))
        wp = find(root, 'CUnit', 'WarPig')
        assert not wp.findall('BehaviorArray'), m
        wp.append(E.fromstring(f'<BehaviorArray Link="{BEH}" />'))
        c0 = [c for c in wp.findall('CardLayouts') if c.get('index') == '0'][0]
        used = {(b.get('Row'), b.get('Column')) for b in c0.findall('LayoutButtons')}
        for up, rc in ((SH, ('1', '2')), (B2, ('1', '3'))):
            assert rc not in used, (m, rc)
            c0.append(E.fromstring(f'<LayoutButtons Face="RMP_{up}" Type="Passive" Requirements="RMP_Have{up}" Row="{rc[0]}" Column="{rc[1]}" />'))
    xml_edit(g / 'unitdata.xml', units)

    p = d / 'mapscript.galaxy'
    raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    assert t.count(ALLOW_ANCHOR) == 1 and 'gt_rmB2' not in t, m
    t = t.replace(ALLOW_ANCHOR, ALLOW_ANCHOR + '    // 0.6.56: Combat Shield Level 2 and B-2 High-Cal LMG (Barracks Tech Lab).\n'
                  f'    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",{n - 1}),true);\n'
                  f'    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",{n}),true);\n'
                  f'    TechTreeUpgradeAllow(1,"{SH}",true);\n'
                  f'    TechTreeUpgradeAllow(1,"{B2}",true);\n'
                  '    gt_rmB2 = TriggerCreate("gt_rmB2_Func");\n'
                  '    TriggerAddEventTimePeriodic(gt_rmB2, 1.0, c_timeGame);\n')
    inc = list(re.finditer(r'^include "[^"]+"\n', t, re.M))
    t = t[:inc[-1].end()] + SCRIPT + t[inc[-1].end():]
    p.write_bytes(t.replace('\n', nl).encode('utf-8'))
    print(m, 'Shield2 Research', n, 'B-2 Research', n + 1)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            d = root / f'{m}.SC2Map'
            edit_map(m, d)
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
