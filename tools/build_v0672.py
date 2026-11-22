#!/usr/bin/env python3
"""0.6.71 -> 0.6.72: 고용소 방벽 중대 (사용자 2026-11-22 "왜 용병도 스파르타이지" -> 선택 "WoM에서 빌리기").

협동전 멩스크에 골리앗이 없어(MengskGoliath는 군심 적 유닛, 모델은 스파르타 중대와 같은 용병 골리앗) Wings of Mengsk
(WoM-1.3_Armory.zip, WoMRoyalGuards.SC2Mod)의 'Bulwark Company' 모델만 빌린다 - 코랄의 후예·프로메테우스와 같은 방식.
넣는 파일 (4~7번 맵마다): Goliath_Mengsk_Coop.m3, goliath_mengsk_diffuse(2).dds, 아이콘·와이어프레임 (모드 전용 파일만).
모델이 참조하는 나머지 텍스처(SiegeTank_Mengsk_COOP_* 등)는 블리자드 게임 파일이라 넣지 않는다.

- 유닛 RM7_Bulwark 방벽 중대: 스파르타 중대 데이터를 바탕으로 0.4.68 규칙대로 처음부터 정예(진급 능력 포함), 경험치 없음 (시험값).
  생명력 550·장갑 4·인구 5·시야 13, 두 무기 동시 사격(다중 고정 기본), 사거리 8 (스파르타 6, 아레스급 연구는 그대로 더해짐).
  피해 +50%·영웅 속성 (RM7_BulwarkElite). 대공 미사일 6발(스파르타 2발), 지상 기관포 반경 1.25 범위 피해(본 피해의 절반),
  대공 미사일 잠금(기계 3초 기절, 같은 대상 10초 뒤 다시 - 0.6.71 잠금 미사일 연구와 같은 효과를 기본으로).
  코어 시스템 과부하(능력, C... 아님 O): 10초 공격·이동 속도 2배, 끝나면 10초 피해 -50%, 재사용 30초.
  공격·이동 연출·소리·초상화·사망은 스파르타 중대 것 (피해 효과를 같이 써서 차량 공격·방어 업그레이드가 그대로 적용).
- 고용: 원작 스파르타 중대 칸(SummonMercenaries Train3, 0행 3열, 단축키 C)에 2기. 가격·충전·대기는 원작 그 칸 그대로
  (칸 가스 25 + 유닛 150/50 x2 = 광물 300·가스 125, 2회, 360초). 골리앗이 해금된 뒤부터(RMA_GoliathUnlocked, 버튼 요구조건).
Game not run.

Usage: python3 tools/build_v0672.py <0.6.71 zip> <WoM-1.3_Armory.zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD, LOCS

OLD, NEW = b'version=0.6.71', b'version=0.6.72'
MAPS = ('TTychus01', 'TTosh01', 'THanson01', 'TTosh02')
WOM = 'WoM-1.3_Armory/帝国之翼军械库版v1.5/WoMRoyalGuards.SC2Mod/'
ASSETS = ['Assets/Units/Terran/Goliath/Goliath_Mengsk_Coop.m3', 'Assets/Textures/goliath_mengsk_diffuse.dds',
          'Assets/Textures/goliath_mengsk_diffuse2.dds', 'Assets/Textures/btn-unit-terran-goliath-mengsk-coop.dds',
          'Assets/Textures/wireframe-terran-goliath-mengsk-coop.dds']
U = 'RM7_Bulwark'
ICON = 'Assets\\Textures\\btn-unit-terran-goliath-mengsk-coop.dds'
WIRE = 'Assets\\Textures\\wireframe-terran-goliath-mengsk-coop.dds'
LIFE, ARMOR, FOOD, SIGHT, RANGE = '550', '4', '-5', '13', '8'

MODEL = (f'<CModel id="{U}" parent="Unit" Race="Terran"><Model value="Assets\\Units\\Terran\\Goliath\\Goliath_Mengsk_Coop.m3" />'
         '<AttachProps Id="Ref_TurretZ"><Keys index="Turret" value="0" /></AttachProps>'
         '<AttachProps Id="Ref_Weapon"><Keys index="SetA" value="0" /></AttachProps>'
         '<AttachProps Id="Ref_Weapon 01"><Keys index="SetA" value="0" /></AttachProps>'
         '<AttachProps Id="Ref_Weapon 02"><Keys index="SetB" value="0" /></AttachProps>'
         '<AttachProps Id="Ref_Weapon 03"><Keys index="SetB" value="2" /></AttachProps>'
         '<AttachProps Id="Ref_Weapon 05"><Keys index="SetB" value="1" /></AttachProps>'
         '<AttachProps Id="Ref_Weapon 06"><Keys index="SetB" value="4" /></AttachProps>'
         '<AttachProps Id="Ref_Weapon 07"><Keys index="SetB" value="5" /></AttachProps>'
         '<AttachProps Id="Ref_Center" RadiusShield="0.650000"><Keys index="Shield" value="0" /></AttachProps>'
         '<Occlusion value="Show" /><PlanetPanelCamera value="Star2CameraHigh12" /><Radius value="0.650000" />'
         '<ScaleMax value="0.650000,0.650000,0.650000" /><ScaleMin value="0.650000,0.650000,0.650000" />'
         '<SelectionRadius value="0.999700" /><ShadowRadius value="0.999700" /><TechPurchaseCamera value="Star2CameraHigh12" />'
         '<UnitGlossaryCamera value="Star2CameraHigh12" /></CModel>')

UNIT = (f'<CUnit id="{U}"><SelectAlias value="Goliath" /><DeathRevealRadius value="3" /><ReviveType value="" /><Race value="Terr" />'
        '<Mob value="Campaign" /><FlagArray index="UseLineOfSight" value="1" /><FlagArray index="ArmySelect" value="1" />'
        '<PlaneArray index="Ground" value="1" /><Collide index="Ground" value="1" /><Collide index="Small" value="1" />'
        '<Attributes index="Armored" value="1" /><Attributes index="Mechanical" value="1" />'
        f'<LifeStart value="{LIFE}" /><LifeMax value="{LIFE}" /><LifeArmor value="{ARMOR}" />'
        '<LifeArmorName value="Unit/LifeArmorName/TerranVehiclePlating" /><Speed value="2.6875" /><Acceleration value="1000" />'
        '<LateralAcceleration value="115.1875" /><StationaryTurningRate value="999.8437" /><TurningRate value="999.8437" />'
        f'<Sight value="{SIGHT}" /><Food value="{FOOD}" /><CostCategory value="Army" />'
        '<CostResource index="Minerals" value="150" /><CostResource index="Vespene" value="50" />'
        '<RepairTime value="33.3332" /><AttackTargetPriority value="20" /><RankDisplay value="Never" />'
        '<AbilArray Link="stop" /><AbilArray Link="attack" /><AbilArray Link="move" /><AbilArray Link="RM7_BulwarkOverload" />'
        '<BehaviorArray Link="RM7_BulwarkElite" /><BehaviorArray Link="ScavengingSystemsMechDeath" />'
        f'<WeaponArray Link="RM7_BulwarkG" Turret="SpartanCompany" /><WeaponArray Link="RM7_BulwarkA" Turret="FreeRotate" />'
        '<CardLayouts><LayoutButtons Face="Move" Type="AbilCmd" AbilCmd="move,Move" Row="0" Column="0" />'
        '<LayoutButtons Face="Stop" Type="AbilCmd" AbilCmd="stop,Stop" Row="0" Column="1" />'
        '<LayoutButtons Face="MoveHoldPosition" Type="AbilCmd" AbilCmd="move,HoldPos" Row="0" Column="2" />'
        '<LayoutButtons Face="MovePatrol" Type="AbilCmd" AbilCmd="move,Patrol" Row="0" Column="3" />'
        '<LayoutButtons Face="Attack" Type="AbilCmd" AbilCmd="attack,Execute" Row="0" Column="4" />'
        '<LayoutButtons Face="RMK_MarineMengskVeterancy" Type="Passive" Row="1" Column="0" />'
        '<LayoutButtons Face="RM7_BulwarkOverload" Type="AbilCmd" AbilCmd="RM7_BulwarkOverload,Execute" Row="2" Column="0" />'
        '<LayoutButtons Face="RM7_BulwarkLock" Type="Passive" Row="2" Column="1" />'
        '<LayoutButtons Face="RM7_BulwarkSplashFace" Type="Passive" Row="2" Column="2" /></CardLayouts>'
        '<Radius value="0.6875" /><SeparationRadius value="0.65" /><CargoSize value="4" /><SubgroupPriority value="1" />'
        '<MinimapRadius value="0.65" /><EditorCategories value="ObjectType:Unit,ObjectFamily:Campaign" />'
        '<GlossaryCategory value="Unit/Category/TerranUnits" /><TacticalAI value="Goliath" /><AIEvaluateAlias value="Goliath" /></CUnit>')

WEAP = (f'<CWeaponLegacy id="RM7_BulwarkG"><EditorCategories value="Race:Terran" />'
        '<Icon value="Assets\\Textures\\btn-upgrade-terran-vehicleweaponslevel0.dds" />'
        '<TargetFilters value="Ground,Visible;Missile,Stasis,Dead,Hidden,Invulnerable" />'
        f'<Range value="{RANGE}" /><Arc value="29.9926" /><Period value="1.5" /><DisplayEffect value="SpartanCompanyG" />'
        '<Effect value="RM7_BulwarkGSet" /><Options index="LinkedCooldown" value="0" /><Options index="OnlyFireWhileInAttackOrder" value="0" /><Options index="OnlyFireAtAttackOrderTarget" value="0" /></CWeaponLegacy>'
        f'<CWeaponLegacy id="RM7_BulwarkA"><EditorCategories value="Race:Terran" />'
        '<Icon value="Assets\\Textures\\btn-upgrade-terran-vehicleweaponslevel0.dds" />'
        '<TargetFilters value="Air,Visible;Missile,Stasis,Dead,Hidden,Invulnerable" />'
        f'<Range value="{RANGE}" /><Arc value="29.9926" /><Period value="1.5" /><DisplayEffect value="SpartanCompanyAU" />'
        '<DisplayAttackCount value="6" /><Effect value="RM7_BulwarkAPersist" /><Options index="LinkedCooldown" value="0" /><Options index="OnlyFireWhileInAttackOrder" value="0" /><Options index="OnlyFireAtAttackOrderTarget" value="0" /></CWeaponLegacy>')

EFF = ('<CEffectSet id="RM7_BulwarkGSet"><EditorCategories value="Race:Terran" /><EffectArray value="SpartanCompanyG" />'
       '<EffectArray value="RM7_BulwarkSplash" /></CEffectSet>'
       '<CEffectEnumArea id="RM7_BulwarkSplash"><EditorCategories value="Race:Terran" /><ImpactLocation Value="TargetUnitOrPoint" />'
       '<SearchFilters value="Ground;Player,Ally,Neutral,Missile,Stasis,Dead,Hidden,Invulnerable" />'
       '<ExcludeArray Value="Target" /><AreaArray Radius="1.25" Effect="RM7_BulwarkSplashDmg" /></CEffectEnumArea>'
       '<CEffectDamage id="RM7_BulwarkSplashDmg" parent="DU_WEAP_SPLASH"><EditorCategories value="Race:Terran" />'
       '<Kind value="Splash" /><Amount value="12" /></CEffectDamage>'
       '<CEffectCreatePersistent id="RM7_BulwarkAPersist"><EditorCategories value="Race:Terran" /><PeriodCount value="6" />'
       '<WhichLocation Value="TargetUnit" /><Flags index="Channeled" value="1" /><PeriodicEffectArray value="SpartanCompanyALM" />'
       + ''.join(f'<PeriodicPeriodArray value="{v}" />' for v in ('0', '0.12', '0.12', '0.12', '0.12', '0.12')) +
       '<ValidatorArray value="CasterIsNotHidden" /></CEffectCreatePersistent>'
       '<CEffectApplyBehavior id="RM7_OverloadAB"><EditorCategories value="Race:Terran" /><Behavior value="RM7_Overload" />'
       '<WhichUnit Value="Caster" /></CEffectApplyBehavior>'
       '<CEffectApplyBehavior id="RM7_OverloadWeakAB"><EditorCategories value="Race:Terran" /><Behavior value="RM7_OverloadWeak" />'
       '<WhichUnit Value="Caster" /></CEffectApplyBehavior>')

BEH = ('<CBehaviorBuff id="RM7_BulwarkElite"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" />'
       '<InfoIcon value="Assets\\Textures\\btn-upgrade-terran-vehicleweaponslevel3.dds" /><Modification>'
       '<DamageDealtFraction index="Ranged" value="0.5" /><DamageDealtFraction index="Splash" value="0.5" />'
       '<StateFlags index="UnitAttrOnHeroic" value="1" /></Modification></CBehaviorBuff>'
       '<CBehaviorBuff id="RM7_Overload"><Alignment value="Positive" /><InfoIcon value="Assets\\Textures\\btn-ability-terran-stimpack-color.dds" />'
       '<Name value="Behavior/Name/RM7_Overload" /><Tooltip value="Behavior/Tooltip/RM7_Overload" />'
       '<Duration value="10" /><Modification MoveSpeedMultiplier="2" AttackSpeedMultiplier="2" />'
       '<FinalEffect value="RM7_OverloadWeakAB" /></CBehaviorBuff>'
       '<CBehaviorBuff id="RM7_OverloadWeak"><Alignment value="Negative" /><InfoIcon value="Assets\\Textures\\btn-ability-terran-stimpack-color.dds" />'
       '<Name value="Behavior/Name/RM7_OverloadWeak" /><Tooltip value="Behavior/Tooltip/RM7_OverloadWeak" /><Duration value="10" />'
       '<Modification><DamageDealtFraction index="Ranged" value="-0.5" /><DamageDealtFraction index="Splash" value="-0.5" /></Modification></CBehaviorBuff>')

ABIL = ('<CAbilEffectInstant id="RM7_BulwarkOverload"><EditorCategories value="Race:Terran,AbilityorEffectType:Units" />'
        '<Effect index="0" value="RM7_OverloadAB" /><Flags index="Transient" value="1" />'
        '<Cost><Cooldown Link="RM7_BulwarkOverload" Location="Unit" TimeUse="30" /></Cost>'
        '<CmdButtonArray index="Execute" DefaultButtonFace="RM7_BulwarkOverload" /></CAbilEffectInstant>'
        '')
TRAIN3_OLD = '<InfoArray index="Train3">\n            <Button State="Suppressed" />\n        </InfoArray>'
TRAIN3_NEW = ('<InfoArray index="Train3"><Unit index="0" value="RM7_Bulwark" /><Unit index="1" value="RM7_Bulwark" />'
              '<Button DefaultButtonFace="HireSpartanCompany" State="Available" Requirements="RM7_CanHireBulwark" /></InfoArray>')

ACTOR = (f'<CActorUnit id="{U}" parent="GenericUnitBase" unitName="{U}">'
         '<On Terms="WeaponStart.RM7_BulwarkG.AttackStart" Send="AnimBracketStart Attack Attack" />'
         '<On Terms="WeaponStop.RM7_BulwarkG.AttackStop" Send="AnimBracketStop Attack" />'
         '<On Terms="WeaponStart.RM7_BulwarkA.AttackStart" Send="AnimBracketStart Spell Spell" />'
         '<On Terms="WeaponStop.RM7_BulwarkA.AttackStop" Send="AnimBracketStop Spell" />'
         '<On Terms="Behavior.MercGroundDrop.Create" Send="Create SpartanCompanyDropModel" />'
         '<Macros value="UnloadDropAnim" /><WalkAnimMoveSpeed value="3.6093" /><StandAnimTurnTime value="4" />'
         '<PortraitModel value="GoliathMercenaryPortrait" /><DeathArray index="Normal" ModelLink="SpartanCompanyDeath" SoundLink="Goliath_Explode" />'
         '<BarWidth value="66" /><BarOffset value="95" />'
         f'<UnitIcon value="{ICON}" /><HeroIcon value="{ICON}" /><GroupIcon><Image value="{WIRE}" /></GroupIcon>'
         f'<Wireframe><Image value="{WIRE}" /></Wireframe>'
         '<LifeArmorIcon value="Assets\\Textures\\btn-upgrade-terran-vehicleplatinglevel0.dds" />'
         + ''.join(f'<SoundArray index="{k}" value="Goliath_{k}" />' for k in ('Birth', 'Ready', 'Help', 'What', 'Yes', 'Attack', 'Pissed'))
         + ''.join(f'<GroupSoundArray index="{k}" value="Goliath_{k}" />' for k in ('Birth', 'Ready', 'Help', 'What', 'Yes', 'Attack', 'Pissed'))
         + '<Aliases value="_UnitLarge" /></CActorUnit>'
         '<CActorModel id="RM7_OverloadFX" parent="ModelAnimationStyleOneShot"><Model value="StimpackStartImpact" />'
         '<On Terms="Abil.RM7_BulwarkOverload.SourceCastStart" Send="Create" /><Host Subject="_Selectable" />'
         '<HostSiteOps Ops="SOpAttachOverhead" /><Inherits index="CloakEffect" value="1" /></CActorModel>')

BTN = (f'<CButton id="HireSpartanCompany"><Icon value="{ICON}" /><AlertIcon value="{ICON}" />'
       '<Name value="Button/Name/RM7_HireBulwark" /><Tooltip value="Button/Tooltip/RM7_HireBulwark" /><Hotkey value="Button/Hotkey/RM7_HireBulwark" /></CButton>'
       '<CButton id="RM7_BulwarkOverload"><Icon value="Assets\\Textures\\btn-ability-terran-stimpack-color.dds" />'
       '<Name value="Button/Name/RM7_BulwarkOverload" /><Tooltip value="Button/Tooltip/RM7_BulwarkOverload" /><Hotkey value="Button/Hotkey/RM7_BulwarkOverload" /></CButton>'
       '<CButton id="RM7_BulwarkLock"><Icon value="Assets\\Textures\\btn-upgrade-terran-nova-hellfiremissiles.dds" />'
       '<Name value="Button/Name/RM7_BulwarkLock" /><Tooltip value="Button/Tooltip/RM7_BulwarkLock" /><Hotkey value="Button/Hotkey/RM7_BulwarkLock" /></CButton>'
       '<CButton id="RM7_BulwarkSplashFace"><Icon value="Assets\\Textures\\btn-upgrade-terran-vehicleweaponslevel3.dds" />'
       '<Name value="Button/Name/RM7_BulwarkSplashFace" /><Tooltip value="Button/Tooltip/RM7_BulwarkSplashFace" /><Hotkey value="Button/Hotkey/RM7_BulwarkSplashFace" /></CButton>')

REQ = '<CRequirement id="RM7_CanHireBulwark"><NodeArray index="Show" Link="RMA_GoliathGate" /><NodeArray index="Use" Link="RMA_GoliathGate" /></CRequirement>'
VAL = ('<CValidatorUnitType id="RM7_CasterBulwark"><WhichUnit Value="Caster" /><Value value="RM7_Bulwark" /></CValidatorUnitType>'
       '<CValidatorCombine id="RM7_LockdownOK"><Type value="Or" /><CombineArray value="RM7_HaveLockdown" /><CombineArray value="RM7_CasterBulwark" /></CValidatorCombine>')

STRINGS = {
    f'Unit/Name/{U}': '방벽 중대 /// Bulwark Company',
    'Weapon/Name/RM7_BulwarkG': '근위대 기관포 /// Royal Guard Autocannons',
    'Weapon/Name/RM7_BulwarkA': '근위대 대공 미사일 /// Royal Guard AA Missiles',
    'Abil/Name/RM7_BulwarkOverload': '코어 시스템 과부하 /// Core System Overload',
    'Button/Name/RM7_HireBulwark': '방벽 중대 고용 /// Hire Bulwark Company',
    'Button/Tooltip/RM7_HireBulwark': '정예 방벽 중대 2기를 고용합니다. 기당 인구 5. 지상·공중 동시 공격, 대공 미사일 6발과 잠금, 지상 범위 피해, 코어 시스템 과부하를 처음부터 사용합니다. 차량 공방업과 아레스급 조준 시스템이 적용됩니다. 골리앗을 얻은 뒤부터 고용할 수 있습니다.<n/><n/>자치령 근위대의 중화기 골리앗입니다. '
                                     '/// Hires 2 elite Bulwark Company Goliaths. 5 supply each. Fire at ground and air together, 6 AA missiles with Lockdown, splash autocannons and Core System Overload from the start. Receives vehicle weapon and armor upgrades and the Ares-Class Targeting System. Available once the Goliath is acquired.<n/><n/>Dominion Royal Guard heavy Goliaths.',
    'Button/Name/RM7_BulwarkOverload': '코어 시스템 과부하 /// Core System Overload',
    'Button/Tooltip/RM7_BulwarkOverload': '10초 동안 공격·이동 속도가 2배가 됩니다. 효과가 끝나면 10초 동안 주는 피해가 50% 줄어듭니다. 재사용 대기 30초. /// Doubles attack and movement speed for 10 seconds. Afterwards, damage dealt is reduced by 50% for 10 seconds. 30 second cooldown.',
    'Button/Name/RM7_BulwarkLock': '잠금 미사일 /// Lockdown Missiles',
    'Button/Tooltip/RM7_BulwarkLock': '대공 미사일에 맞은 기계 유닛이 3초 동안 기절하고 탐지가 꺼집니다. 같은 대상은 10초 뒤에 다시 걸립니다. 영웅에게는 걸리지 않습니다. /// Mechanical units hit by the AA missiles are stunned and lose detection for 3 seconds. The same target again after 10 seconds. Heroic units are immune.',
    'Button/Name/RM7_BulwarkSplashFace': '근위대 화력 /// Royal Guard Firepower',
    'Button/Tooltip/RM7_BulwarkSplashFace': '처음부터 정예입니다. 피해 +50%, 사거리 8, 시야 13. 대공 미사일을 6발 쏘고, 지상 기관포가 주변 1.25 범위에 절반 피해를 줍니다. /// Elite from the start. +50% damage, range 8, sight 13. Fires 6 AA missiles; autocannons deal half damage in a 1.25 radius.',
    'Behavior/Name/RM7_Overload': '코어 시스템 과부하 /// Core System Overload',
    'Behavior/Tooltip/RM7_Overload': '공격·이동 속도가 2배입니다. /// Attack and movement speed doubled.',
    'Behavior/Name/RM7_OverloadWeak': '과부하 후유증 /// Overload Aftermath',
    'Behavior/Tooltip/RM7_OverloadWeak': '주는 피해가 50% 줄었습니다. /// Damage dealt reduced by 50%.',
}
HOTKEYS = {'RM7_HireBulwark': 'C', 'RM7_BulwarkOverload': 'O', 'RM7_BulwarkLock': 'L', 'RM7_BulwarkSplashFace': 'F'}


def upgrade_mirror():
    """Bulwark weapon level/icon/range and armor entries, copied from the SpartanCompany entries of the campaign upgrades."""
    out = ''
    for layer in ('liberty.sc2campaign', 'libertystory.sc2campaign'):
        t = (ROOT / f'source/{layer}/base.sc2data/gamedata/upgradedata.xml').read_text('utf-8')
        for m in re.finditer(r'<CUpgrade ([^>]*?)id="([^"]+)"[^>]*>(.*?)</CUpgrade>', t, re.S):   # also default="1" parents
            dflt, uid, body = 'default="1" ' if 'default="1"' in m.group(1) else '', m.group(2), m.group(3)
            if not re.match(r'TerranVehicle(Weapons|Armors)|AresClassWeaponsSystem$', uid): continue
            add, seen = [], set()
            for e in re.findall(r'<EffectArray[^>]*/>', body):
                ref = re.search(r'Reference="([^"]+)"', e).group(1)
                parts = ref.split(',')
                if parts[0] == 'Weapon' and parts[1].startswith('SpartanCompany'):
                    w = 'RM7_BulwarkG' if parts[1] in ('SpartanCompanyG', 'SpartanCompanyGUpgraded') else 'RM7_BulwarkA'
                    new = ','.join(['Weapon', w] + parts[2:])
                elif parts[0] in ('Unit', 'Actor') and parts[1] == 'SpartanCompany':
                    new = ','.join([parts[0], U] + parts[2:])
                else:
                    continue
                if new in seen: continue
                seen.add(new)
                add.append(e.replace(f'Reference="{ref}"', f'Reference="{new}"').replace('/>', ' />').replace('  />', ' />'))
            if add:
                out += f'<CUpgrade {dflt}id="{uid}">' + ''.join(add) + '</CUpgrade>'
    assert all(k in out for k in ('AresClassWeaponsSystem', 'TerranVehicleWeaponsLevel1', 'TerranVehicleArmorsLevel1', 'default="1" id="TerranVehicleWeaponsUltraCapacitors"', 'default="1" id="TerranVehicleArmorsVanadiumPlating"'))
    return out


SCRIPT_OLD = '    TechTreeUpgradeAllow(1,"RM7_Lockdown",true);\n}\n'
SCRIPT_NEW = ('    TechTreeUpgradeAllow(1,"RM7_Lockdown",true);\n'
              '    // 0.6.72: Bulwark Company in the Spartan Company hire slot (button requires the Goliath unlock).\n'
              '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",2),true);\n'
              '    TechTreeUnitAllow(1,"RM7_Bulwark",true);\n'
              '    TechTreeAbilityAllow(1,AbilityCommand("RM7_BulwarkOverload",0),true);\n}\n')


def append(raw, xml):
    t = raw.decode('utf-8')
    k = t.rindex('</Catalog>')
    return (t[:k] + xml + t[k:]).encode('utf-8')


def build(src, wom, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(wom) as w:
        assets = {a: w.read(WOM + a) for a in ASSETS}
    data = {'modeldata.xml': MODEL, 'unitdata.xml': UNIT, 'weapondata.xml': WEAP, 'effectdata.xml': EFF, 'behaviordata.xml': BEH,
            'abildata.xml': ABIL, 'actordata.xml': ACTOR, 'buttondata.xml': BTN, 'requirementdata.xml': REQ,
            'validatordata.xml': VAL, 'upgradedata.xml': upgrade_mirror()}
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        infos = prev.infolist()
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        new_names = []
        for m in MAPS:
            for f, xml in data.items():
                p = f'{m}.SC2Map/{GD}{f}'
                t = files[p].decode('utf-8')
                for i in re.findall(r'<C\w+ id="([^"]+)"', xml):
                    assert f'id="{i}"' not in t or f == 'upgradedata.xml', (m, i)
                assert 'id="HireSpartanCompany"' not in t
                files[p] = append(files[p], xml); changed.add(p)
            p = f'{m}.SC2Map/{GD}abildata.xml'
            t = files[p].decode('utf-8')
            assert t.count(TRAIN3_OLD) == 1, m
            files[p] = t.replace(TRAIN3_OLD, TRAIN3_NEW).encode('utf-8')
            p = f'{m}.SC2Map/{GD}effectdata.xml'
            t = files[p].decode('utf-8')
            old = '<CEffectSet id="RM7_LockdownSet"><ValidatorArray value="RM7_HaveLockdown" />'
            assert t.count(old) == 1
            files[p] = t.replace(old, '<CEffectSet id="RM7_LockdownSet"><ValidatorArray value="RM7_LockdownOK" />').encode('utf-8')
            # the Bulwark missile impact also goes through the Spartan impact set (SpartanCompanyALM), so it locks by default
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'; t = raw.replace('\r\n', '\n')
            assert t.count(SCRIPT_OLD) == 1, m
            files[p] = t.replace(SCRIPT_OLD, SCRIPT_NEW).replace('\n', nl).encode('utf-8'); changed.add(p)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], STRINGS); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
            for loc in LOCS:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'
                files[q] = set_lines(files[q], {f'Button/Hotkey/{b}': h for b, h in HOTKEYS.items()}); changed.add(q)
            for a, d in assets.items():
                n = f'{m}.SC2Map/{a}'
                assert n not in files
                files[n] = d; new_names.append(n)
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in infos:
                i = copy.copy(info); i.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(i, files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            for n in new_names:
                zi = zipfile.ZipInfo(n, date_time=(2026, 11, 22, 0, 0, 0)); zi.external_attr = 0o644 << 16
                z.writestr(zi, files[n], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('wom', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.wom, x.out)
