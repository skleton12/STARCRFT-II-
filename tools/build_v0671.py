#!/usr/bin/env python3
"""0.6.70 -> 0.6.71 (user 2026-11-22 "왜 스파르타 중대 업글이 없으며", 선택 "원작 + 협동전 2페이지").

Maps 4-7 (TTychus01, TTosh01, THanson01, TTosh02):
- Goliath research in the Factory Tech Lab (rule: armory tech not bought is researched in the mission):
    1페이지 다중 고정 무기 체계(MultilockTargetingSystems), 아레스급 조준 시스템(AresClassWeaponsSystem) - the original
    upgrades already list SpartanCompany. Bought at the Hyperion -> button hidden (QueuedOrBetter).
    협동전 페이지 잠금 미사일(RM7_Lockdown, 모드에서 재설계: 노바 협동전 NovaUnitLockdown): Spartan Company anti-air missiles
    stun mechanical non-heroic units 3 s, the same target again only after 10 s (trial).
  All 100/100, 60 s (trial). Shown only once the Goliath is unlocked (RMA_GoliathUnlocked, set from FactoryTrain Goliath).
  The original campaign Ares button (FactoryTechLabResearch Research4) is disallowed (no double).
- Maps 4-6: Raynor's factory trains Spartan Company / Siege Breakers like mission 7 (merc rule, nonlinear order);
  placed/handed-over Goliaths and Siege Tanks become mercenaries (safety net). Mission 7's inline swap moves into the same function.
Game not run.

Usage: python3 tools/build_v0671.py <0.6.70 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD, LOCS

OLD, NEW = b'version=0.6.70', b'version=0.6.71'
MAPS = {'TTychus01': 'm4', 'TTosh01': 'm5', 'THanson01': 'm6', 'TTosh02': 'm7'}
NOTE = (' 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다.', ' Researched in the mission when not bought at the Hyperion Armory.')
COST = '<Resource index="Minerals" value="100" /><Resource index="Vespene" value="100" />'
# (button, upgrade, research index, card, row, col, hotkey, icon, name ko/en, tooltip ko/en)
ITEMS = [
    ('RMA_Multilock', 'MultilockTargetingSystems', 5, '0', 1, 0, 'M', 'Assets\\Textures\\btn-techupgrade-terran-multilocktargetingsystem.dds',
     ('다중 고정 무기 체계', 'Multi-Lock Weapons System'),
     ('골리앗(스파르타 중대)이 공중과 지상 유닛을 동시에 공격합니다.' + NOTE[0], 'Goliaths (Spartan Company) can fire at air and ground units simultaneously.' + NOTE[1])),
    ('RMA_Ares', 'AresClassWeaponsSystem', 6, '0', 1, 1, 'A', 'Assets\\Textures\\btn-techupgrade-terran-charonboosters.dds',
     ('아레스급 조준 시스템', 'Ares-Class Targeting System'),
     ('골리앗(스파르타 중대)의 미사일 사거리가 3, 기관포 사거리가 1 증가합니다.' + NOTE[0], 'Goliaths (Spartan Company) gain +3 missile range and +1 cannon range.' + NOTE[1])),
    ('RMC_Lockdown', 'RM7_Lockdown', 7, 'RMC2', 0, 0, 'L', 'Assets\\Textures\\btn-upgrade-terran-nova-hellfiremissiles.dds',
     ('잠금 미사일', 'Lockdown Missiles'),
     ('스파르타 중대의 대공 미사일에 맞은 기계 유닛이 3초 동안 기절하고 탐지가 꺼집니다. 같은 대상은 10초 뒤에 다시 걸립니다. 영웅에게는 걸리지 않습니다. (협동전 노바 연구를 개조)',
      'Mechanical units hit by Spartan Company anti-air missiles are stunned and lose detection for 3 seconds. The same target can be locked again after 10 seconds. Heroic units are immune. (Modified co-op Nova research)')),
]


def xml_parts():
    btn = abil = card0 = card1 = req = node = up = ''
    strs = {}
    for bid, upg, n, card, r, c, hk, icon, (nk, ne), (tk, te) in ITEMS:
        btn += (f'<CButton id="{bid}"><Icon value="{icon}" /><Name value="Button/Name/{bid}" /><Tooltip value="Button/Tooltip/{bid}" />'
                f'<Hotkey value="Button/Hotkey/{bid}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>')
        abil += (f'<InfoArray index="Research{n}" Time="60" Upgrade="{upg}">{COST}<Button DefaultButtonFace="{bid}" State="Available" '
                 f'Requirements="{bid}Learn" /></InfoArray>')
        lb = f'<LayoutButtons Face="{bid}" Type="AbilCmd" AbilCmd="FactoryTechLabResearch,Research{n}" Row="{r}" Column="{c}" />'
        if card == '0': card0 += lb
        else: card1 += lb
        req += f'<CRequirement id="{bid}Learn"><NodeArray index="Show" Link="{bid}Show" /></CRequirement>'
        node += (f'<CRequirementCountUpgrade id="{bid}Queued"><Count Link="{upg}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
                 f'<CRequirementNot id="{bid}NotQueued"><OperandArray index="0" value="{bid}Queued" /></CRequirementNot>'
                 f'<CRequirementAnd id="{bid}Show"><OperandArray value="{bid}NotQueued" /><OperandArray value="RMA_GoliathGate" /></CRequirementAnd>')
        strs[f'Button/Name/{bid}'] = f'{nk} 연구 /// Research {ne}'
        strs[f'Button/Tooltip/{bid}'] = f'{tk} /// {te}'
    node += '<CRequirementCountUpgrade id="RMA_GoliathGate"><Count Link="RMA_GoliathUnlocked" State="CompleteOnly" /></CRequirementCountUpgrade>'
    req += '<CRequirement id="RM7_LockdownUse"><NodeArray index="Use" Link="RM7_LockdownDone" /></CRequirement>'
    node += '<CRequirementCountUpgrade id="RM7_LockdownDone"><Count Link="RM7_Lockdown" State="CompleteOnly" /></CRequirementCountUpgrade>'
    btn += ('<CButton id="RMC_FactoryCoopMenu"><Icon value="Assets\\Textures\\btn-upgrade-terran-nova-hellfiremissiles.dds" />'
            '<Name value="Button/Name/RMC_FactoryCoopMenu" /><Tooltip value="Button/Tooltip/RMC_FactoryCoopMenu" />'
            '<Hotkey value="Button/Hotkey/RMC_FactoryCoopMenu" /></CButton>')
    strs['Button/Name/RMC_FactoryCoopMenu'] = '협동전 연구 /// Co-op Research'
    strs['Button/Tooltip/RMC_FactoryCoopMenu'] = '협동전 사령관에게서 가져와 개조한 차량 연구를 엽니다. /// Opens vehicle research adapted from co-op commanders.'
    up = ('<CUpgrade id="RMA_GoliathUnlocked"><Race value="Terr" /></CUpgrade>'
          '<CUpgrade id="RM7_Lockdown"><Race value="Terr" /><Icon value="Assets\\Textures\\btn-upgrade-terran-nova-hellfiremissiles.dds" />'
          '<MaxLevel value="1" /><EditorCategories value="Race:Terran,UpgradeType:Talents" /><Name value="Upgrade/Name/RM7_Lockdown" /></CUpgrade>')
    strs['Upgrade/Name/RM7_Lockdown'] = '잠금 미사일 /// Lockdown Missiles'
    beh = ('<CBehaviorBuff id="RM7_LockdownStun"><Alignment value="Negative" /><InfoIcon value="Assets\\Textures\\btn-upgrade-swann-defensivematrix.dds" />'
           '<Name value="Behavior/Name/RM7_LockdownStun" /><Tooltip value="Behavior/Tooltip/RM7_LockdownStun" /><Duration value="3" />'
           '<Modification><ModifyFlags index="DisableAbils" value="1" /><ModifyFlags index="Reveal" value="1" /><ModifyFlags index="Detected" value="1" />'
           '<StateFlags index="Stun" value="1" /><StateFlags index="SuppressDetection" value="1" /></Modification></CBehaviorBuff>'
           '<CBehaviorBuff id="RM7_LockdownImmune"><InfoFlags index="Hidden" value="1" /><Duration value="10" /></CBehaviorBuff>')
    strs['Behavior/Name/RM7_LockdownStun'] = '잠금 /// Lockdown'
    strs['Behavior/Tooltip/RM7_LockdownStun'] = '이 유닛은 기절했고 탐지할 수 없습니다. /// This unit is stunned and unable to detect.'
    val = ('<CValidatorPlayerRequirement id="RM7_HaveLockdown"><Value value="RM7_LockdownUse" /><Find value="1" /><WhichPlayer Value="Caster" /></CValidatorPlayerRequirement>'
           '<CValidatorUnitFilters id="RM7_LockdownTarget"><Filters value="Mechanical;Structure,Heroic,Dead,Invulnerable" /></CValidatorUnitFilters>'
           '<CValidatorUnitCompareBehaviorCount id="RM7_NotLockImmune"><Behavior value="RM7_LockdownImmune" /><Compare value="LT" /><Value value="1" /></CValidatorUnitCompareBehaviorCount>')
    eff = ('<CEffectLaunchMissile id="SpartanCompanyALM"><ImpactEffect value="RM7_SpartanAImpact" /></CEffectLaunchMissile>'
           '<CEffectSet id="RM7_SpartanAImpact"><EffectArray value="SpartanCompanyAU" /><EffectArray value="RM7_LockdownSet" /></CEffectSet>'
           '<CEffectSet id="RM7_LockdownSet"><ValidatorArray value="RM7_HaveLockdown" /><ValidatorArray value="RM7_LockdownTarget" />'
           '<ValidatorArray value="RM7_NotLockImmune" /><EffectArray value="RM7_LockdownAB" /><EffectArray value="RM7_LockdownImmuneAB" /></CEffectSet>'
           '<CEffectApplyBehavior id="RM7_LockdownAB"><Behavior value="RM7_LockdownStun" /></CEffectApplyBehavior>'
           '<CEffectApplyBehavior id="RM7_LockdownImmuneAB"><Behavior value="RM7_LockdownImmune" /></CEffectApplyBehavior>')
    # Codex review: the Factory Tech Reactor has its own command card; both get the same buttons. The co-op menu needs the Goliath too.
    unit = ''.join(f'<CUnit id="{u}"><CardLayouts index="0">{card0}'
            '<LayoutButtons Face="RMC_FactoryCoopMenu" Type="Submenu" SubmenuCardId="RMC2" Requirements="RMC_FactoryCoopMenuShow" Row="2" Column="3" /></CardLayouts>'
            f'<CardLayouts CardId="RMC2">{card1}<LayoutButtons Face="Cancel" Type="CancelSubmenu" Row="2" Column="4" /></CardLayouts></CUnit>'
            for u in ('FactoryTechLab', 'FactoryTechReactor'))
    req += '<CRequirement id="RMC_FactoryCoopMenuShow"><NodeArray index="Show" Link="RMA_GoliathGate" /></CRequirement>'
    data = {'buttondata.xml': btn, 'abildata.xml': f'<CAbilResearch id="FactoryTechLabResearch">{abil}</CAbilResearch>',
            'unitdata.xml': unit, 'requirementdata.xml': req, 'requirementnodedata.xml': node, 'upgradedata.xml': up,
            'behaviordata.xml': beh, 'validatordata.xml': val, 'effectdata.xml': eff}
    hk = {bid: hk for bid, _, _, _, _, _, hk, *_ in ITEMS}
    hk['RMC_FactoryCoopMenu'] = 'X'
    return data, strs, hk


FN = '''// 0.6.71 (user 2026-11-22): Raynor's factory trains Spartan Company / Siege Breakers (merc rule, player 1 only data) and
// researches the Goliath armory tech not bought at the Hyperion + co-op Lockdown Missiles (Factory Tech Lab).
void gf_rmFactory () {
    CatalogFieldValueSet(c_gameCatalogAbil,"FactoryTrain","InfoArray[Train7].Unit[0]",1,"SpartanCompany");
    CatalogFieldValueSet(c_gameCatalogAbil,"FactoryTrain","InfoArray[Train2].Unit[0]",1,"SiegeBreaker");
    CatalogFieldValueSet(c_gameCatalogButton,"Goliath","Icon",1,"Assets\\\\Textures\\\\btn-unit-terran-goliathmercenary.dds");
    CatalogFieldValueSet(c_gameCatalogButton,"Goliath","Name",1,"Button/Name/RM_SpartanCompany");
    CatalogFieldValueSet(c_gameCatalogButton,"Goliath","Tooltip",1,"Button/Tooltip/RM_SpartanCompany");
    CatalogFieldValueSet(c_gameCatalogButton,"SiegeTank","Icon",1,"Assets\\\\Textures\\\\btn-unit-terran-siegetankmercenary-tank.dds");
    CatalogFieldValueSet(c_gameCatalogButton,"SiegeTank","Name",1,"Button/Name/RM_SiegeBreaker");
    CatalogFieldValueSet(c_gameCatalogButton,"SiegeTank","Tooltip",1,"Button/Tooltip/RM_SiegeBreaker");
    TechTreeUnitAllow(1,"SpartanCompany",TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",6)));
    TechTreeUnitAllow(1,"SiegeBreaker",TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",1)));
    TechTreeUpgradeAllow(1,"RMA_GoliathUnlocked",true);
    if (TechTreeUpgradeCount(1,"RMA_GoliathUnlocked",c_techCountQueuedOrBetter)==0 && TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",6))) {
        TechTreeUpgradeAddLevel(1,"RMA_GoliathUnlocked",1);
    }
    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",3),false);
    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",4),true);
    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",5),true);
    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",6),true);
    TechTreeUpgradeAllow(1,"MultilockTargetingSystems",true);
    TechTreeUpgradeAllow(1,"AresClassWeaponsSystem",true);
    TechTreeUpgradeAllow(1,"RM7_Lockdown",true);
}

'''
SWAP = ('else if (t=="Goliath") { libNtve_gf_ReplaceUnit(u,"SpartanCompany",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }',
        'else if (t=="SiegeTank") { libNtve_gf_ReplaceUnit(u,"SiegeBreaker",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }')
M7_INLINE_START = '    // 0.6.70: Raynor\'s factory trains Spartan Company / Siege Breakers (player 1 only data).\n'


def script(m, tag, raw):
    t = raw.decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
    if m == 'TTosh02':
        a = t.index(M7_INLINE_START); b = t.index('    CatalogFieldValueSet(c_gameCatalogButton,"Reaper","Icon",1', a)
        t = t[:a] + t[b:]
        a = t.index('    TechTreeUnitAllow(1,"SpartanCompany",'); b = t.index('\n', t.index('    TechTreeUnitAllow(1,"SiegeBreaker",', a)) + 1
        t = t[:a] + t[b:]
    else:
        for fn in (f'void gf_{tag}_Reapers (', f'bool gt_{tag}_TrainMerc_Func ('):
            if fn not in t: continue
            a = t.index(fn); end = t.index('\n}\n', a)
            for anchor in ('else if (t=="Reaper") {', 'else if (t=="Firebat") {'):
                i = t.find(anchor, a, end)
                if i >= 0: break
            if i < 0:
                assert fn.startswith('void'), (m, fn)   # mission 5 Reapers() swaps reapers only; the train safety net covers it
                continue
            ls = t.rindex('\n', 0, i) + 1; le = t.index('\n', i) + 1
            ind = t[ls:i]
            t = t[:le] + ''.join(f'{ind}{s}\n' for s in SWAP) + t[le:]
    assert t.count('void InitGlobals () {') == 1 and t.count('    gf_rm7Start();\n') == 1
    t = t.replace('    gf_rm7Start();\n', '    gf_rm7Start();\n    gf_rmFactory();\n')
    k = t.rindex('\nvoid ', 0, t.index('    gf_rmFactory();\n')) + 1   # before the function that calls it
    t = t[:k] + FN + t[k:]
    return t.replace('\n', nl).encode('utf-8')


def append(raw, xml, ids):
    t = raw.decode('utf-8')
    for i in ids:
        assert f'id="{i}"' not in t or i in ('FactoryTechLab', 'FactoryTechReactor', 'FactoryTechLabResearch', 'SpartanCompanyALM'), i
    k = t.rindex('</Catalog>')
    return (t[:k] + xml + t[k:]).encode('utf-8')


def build(src, out):
    import re
    if out.exists(): raise ValueError('Output must be new')
    data, strs, hk = xml_parts()
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m, tag in MAPS.items():
            for f, xml in data.items():
                p = f'{m}.SC2Map/{GD}{f}'
                files[p] = append(files[p], xml, re.findall(r'id="([^"]+)"', xml)); changed.add(p)
            p = f'{m}.SC2Map/mapscript.galaxy'
            files[p] = script(m, tag, files[p]); changed.add(p)
            k = f'{m}.SC2Map/{KO}'
            add = dict(strs)
            if m != 'TTosh02':
                add.update({kk: vv for kk, vv in {
                    'Button/Name/RM_SpartanCompany': '스파르타 중대 /// Spartan Company',
                    'Button/Tooltip/RM_SpartanCompany': '용병 골리앗입니다. 지상과 공중을 모두 공격합니다. /// Mercenary Goliath. Attacks ground and air units.',
                    'Button/Name/RM_SiegeBreaker': '공성 파괴단 /// Siege Breakers',
                    'Button/Tooltip/RM_SiegeBreaker': '용병 공성 전차입니다. 공성 모드로 먼 거리의 지상 유닛을 공격합니다. /// Mercenary Siege Tank. Siege Mode attacks distant ground units.'}.items()})
            ko = set_lines(files[k], add); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
            for loc in LOCS:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'
                files[q] = set_lines(files[q], {f'Button/Hotkey/{b}': h for b, h in hk.items()}); changed.add(q)
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
