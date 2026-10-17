#!/usr/bin/env python3
"""Build CCM 0.3.2 from 0.3.1 (fix layer, maps are never saved in Editor).

Fixes reported after 0.3.1 play:
  1. Mission 3 research/build/hire buttons used placeholder infantry-armor icons.
  2. Ported co-op strings (Sons of Korhal, Dehaka, Energizer) showed English in the Korean client.
  3. Mission 3 ally AI stock was never cleared/enabled, so allies did not run their economy as planned.

Usage: python3 tools/build_v032.py <0.3.1 zip> <new output zip>
"""
import argparse
import copy
import re
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.1', b'version=0.3.2'
T = 'Assets\\Textures\\'
# Icons present in Liberty/LibertyStory data, so a WoL-dependent map can always load them.
ICONS = {
    'RM3_Stim1': 'btn-ability-terran-stimpack.dds',
    'RM3_Stim2': 'btn-techupgrade-terran-stimpack.dds',
    'RM3_Stim3': 'btn-ability-terran-stimpack-color.dds',
    'RM3_Shield': 'btn-techupgrade-terran-combatshield-color.dds',
    'RM3_Laser': 'btn-upgrade-terran-hisecautotracking.dds',
    'RM3_SupplyBunker': 'btn-building-terran-supplybunkermengsk.dds',
    'RM3_Armor': 'btn-upgrade-terran-buildingarmor.dds',
    'RM3_BuildSupplyBunker': 'btn-building-terran-supplybunkermengsk.dds',
    'RM3_HireKorhal': 'btn-unit-terran-SoKmarine.dds',  # shipped inside the map's Assets
}

# Player-visible ported strings (key -> Korean). Editor-only names are left alone.
KO = {
    'Abil/Name/RMK_MagrailMunitionsMarineMengsk': '자기 가속 탄약',
    'Abil/Name/RMK_MarineMengskAttackSpeedBoost': '고급 자극제',
    'Behavior/Name/RMK_MarineMengskAttackSpeedBoost': '고급 자극제',
    'Behavior/Name/RMK_MarineMengskCombatShield': '전투 방패',
    'Behavior/Name/RMK_MarineMengskCombatShieldUpgrade': '무사 통과',
    'Behavior/Name/RMK_MengskVeterancyMarineMengsk': '코랄의 후예 계급',
    'Behavior/Tooltip/RMK_MarineMengskAttackSpeedBoost': '고급 자극제의 효과로 이동 속도, 생명력 재생, 공격 속도가 증가합니다.',
    'Behavior/Tooltip/RMK_MarineMengskCombatShield': '받는 피해가 25% 감소하고 범위 피해를 받지 않습니다.',
    'Behavior/Tooltip/RMK_MarineMengskCombatShieldUpgrade': '일시적으로 무적 상태입니다.',
    'Behavior/Tooltip/RMK_MarineMengskCombatShieldUpgradeCooldown': '무사 통과 효과가 발동된 유닛입니다.',
    'Button/Name/RMK_MarineMengsk': '코랄의 후예 훈련',
    'Button/Name/RMK_RoyalGuardMengsk': '자치령 근위대',
    'Button/Tooltip/RMK_MagrailMunitionsMengsk': '대상 유닛에게 <d ref="Effect,RMK_MagrailMunitionsMengskDamage,Amount"/>의 피해를 줍니다.',
    'Button/Tooltip/RMK_MarineLaserTargetingSystemMengsk': '<c val="FFFF80">코랄의 후예</c>의 시야가 2, 무기 사거리가 1 증가합니다.',
    'Button/Tooltip/RMK_MarineMengsk': '근위대 소속의 범용 보병입니다.<n/><n/><c val="#ColorAttackInfo">지상 및 공중 공격 가능</c>',
    'Button/Tooltip/RMK_MarineMengskCombatShield': '<c val="FFFF80">코랄의 후예</c>가 받는 피해가 <d ref="-Behavior,RMK_MarineMengskCombatShield,Modification.DamageTakenUnscaled[Melee]*100"/>% 감소하고 범위 피해를 받지 않습니다.',
    'Button/Tooltip/RMK_MarineMengskCombatShieldUpgrade': '<n/><c val="FFFF80">무기고 업그레이드</c>: 전투 방패 업그레이드를 가진 코랄의 후예가 치명적인 피해를 받으면 생명력의 절반을 즉시 회복하고 5초 동안 무적이 됩니다. 300초마다 발동합니다.',
    'Button/Tooltip/RMK_Mengsk': '생명력과 공격력이 더 높은 정예 해병 레이너입니다.<n/><n/><c val="#ColorAttackInfo">지상 및 공중 공격 가능</c><n/>',
    'Button/Tooltip/RMK_RoyalGuardMengsk': '적을 처치하면 주변 <c val="ffff8a">근위대</c> 유닛이 경험치를 얻습니다. 주변에 근위대가 없으면 맵 전체의 근위대에게 나누어집니다. 경험치로 <c val="ffff8a">계급</c>이 오르면 공격력, 방어력, 최대 생명력이 증가합니다.',
    'RequirementNode/Tooltip/RMK_CountUpgradeMarineMengskCombatShieldCompleteOnly1321814377': '전투 방패 연구 필요',
    'RequirementNode/Tooltip/RMK_Or1040053073GTECountBehaviorMengskVeterancyMarineMengskCompleteOnlyAtUnit2': '계급 1 필요',
    'RequirementNode/Tooltip/RMK_Or1977052814GTECountBehaviorMengskVeterancyMarineMengskCompleteOnlyAtUnit3': '계급 2 필요',
    'RequirementNode/Tooltip/RMK_Or3912144799GTECountBehaviorMengskVeterancyMarineMengskCompleteOnlyAtUnit4': '계급 3 필요',
    'Unit/Name/RMK_MagrailMunitionMissileMengsk': '자기 가속 탄약',
    'Unit/Name/RMK_Mengsk': '짐 레이너',
    'Upgrade/Name/RMK_MarineMengskCombatShield': '전투 방패',
    'Weapon/Name/RMK_MarineMengskGaussRifle': '가우스 소총',
    'Button/Name/RM21_Energizer': '동력기 소환',
    'Unit/Name/RM21_SentryCampaignBase': '동력기',
    'Button/Name/DehakaHydralisk': '원시 히드라리스크 생성',
    'Button/Name/DehakaZergling': '원시 저글링 생성',
    'Card/Name/DehakaHydraliskLevel2Burrowed': '잠복',
    'Card/Name/DehakaRoachLevel2Burrowed': '잠복',
    'Card/Name/DehakaZerglingLevel2Burrowed': '잠복',
    'Weapon/Name/DehakaHydraliskLevel2NeedleSpines': '바늘 가시',
    'Weapon/Name/DehakaRoachLevel2': '산성 타액',
    'Weapon/Name/DehakaZerglingLevel2': '발톱',
}

STOCK_OLD = '    AISetStockUnitNext(10,12,"Probe",false);\n'
STOCK_FARMS = '    AISetStockFarms(11,"Overlord",true);\n'


def strings(data):
    text = data.decode('utf-8-sig')
    hits = 0
    for key, value in KO.items():
        pat = re.compile(r'^' + re.escape(key) + r'=[^\r\n]*', re.M)
        text, n = pat.subn(lambda _: key + '=' + value, text)
        hits += n
    return text.encode('utf-8'), hits


def buttons(data):
    text = data.decode('utf-8')
    for ident, icon in ICONS.items():
        pat = re.compile(r'(<CButton id="' + ident + r'"><Icon value=")[^"]*(")')
        text, n = pat.subn(lambda m: m[1] + T + icon + m[2], text)
        assert n == 1, ident
    return text.encode('utf-8')


def upgrades(data):
    text = data.decode('utf-8')
    for ident, icon in ICONS.items():
        if ident in ('RM3_BuildSupplyBunker', 'RM3_HireKorhal'): continue
        head = '<CUpgrade id="' + ident + '">'
        assert text.count(head) == 1, ident
        text = text.replace(head, head + '<Icon value="' + T + icon + '" />', 1)
    return text.encode('utf-8')


def script(data):
    text = data.decode('utf-8')
    assert text.count(STOCK_OLD) == 1 and text.count(STOCK_FARMS) == 1 and 'AIEnableStock' not in text
    text = text.replace(STOCK_OLD, '    AIClearStock(10);\n    AIClearStock(11);\n' + STOCK_OLD, 1)
    text = text.replace(STOCK_FARMS, STOCK_FARMS + '    AIEnableStock(10);\n    AIEnableStock(11);\n', 1)
    return text.encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    changed = {}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None
        assert OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    name, data = info.filename, prev.read(info.filename)
                    low = name.lower()
                    new = data
                    if name == 'metadata.txt':
                        new = data.replace(OLD, NEW)
                    elif low.endswith('kokr.sc2data/localizeddata/gamestrings.txt'):
                        new, hits = strings(data)
                        print(name, 'strings', hits)
                    elif name == 'TRaynor03.SC2Map/base.sc2data/gamedata/buttondata.xml':
                        new = buttons(data)
                    elif name == 'TRaynor03.SC2Map/base.sc2data/gamedata/upgradedata.xml':
                        new = upgrades(data)
                    elif name == 'TRaynor03.SC2Map/mapscript.galaxy':
                        new = script(data)
                    if new != data: changed[name] = new
                    out.writestr(copy.copy(info), new)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                assert out.namelist() == prev.namelist()
                for name in prev.namelist():
                    if name not in changed: assert out.read(name) == prev.read(name), name
        except BaseException:
            output.unlink(missing_ok=True); raise
    print('changed:', *sorted(changed), sep='\n  ')
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
