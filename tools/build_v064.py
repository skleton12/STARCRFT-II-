#!/usr/bin/env python3
"""0.6.3 -> 0.6.4: 고용소 프로메테우스 중대 (사용자 2026-10-31 "그럼 어디 해봐" — 블리자드 에셋 재구성안).

조사: docs/research/prometheus_company_wom.md. Wings of Mengsk 모드의 파일(커스텀 Incinerator 모델 등)은 가져오지 않는다.
블리자드 데이터 구조로 새로 만들고, 능력·수치만 그 모드를 참고한다.
대상 맵: 4·5·6번 (TTychus01, TTosh01, THanson01) — 이지스 근위대가 있는 고용소.

- 유닛 RM6_Prometheus: 자날 일반 화염방사병 모델(Firebat.m3)에 검붉은 색조 (악마의 개 용병 모델과 구분).
  초상화·아이콘·소리는 자날 화염방사병 것.
- 고용: 원작 '악마의 개' 고용 칸(SummonMercenaries Train2, 0행 1열)에 2기. 가격·충전·대기는 원작 그 칸 그대로
  (광물 100·가스 75, 2회, 300초) — 이지스가 원작 망치 경호대 칸을 따른 것과 같은 방식.
- 0.4.68 규칙대로 처음부터 3등급, 경험치 없음. 인구 4 (이지스와 같음, 시험값).
  기본 생명력 350·장갑 2·피해 15(+5 경장갑·생체), 3등급 합계 생명력 +200·장갑 +5·피해 +100%·영웅 속성 (참고 모드 값, 시험값).
- 진급 능력 (처음부터):
  점프 제트 강습 — 공격 명령 때 자동, 2~4칸 떨어진 적에게 2초간 이동 속도 ×2.5로 돌진 (자날 광전사 돌진 구조).
    불을 뿜기 시작하거나 2초가 지나면 주변(반경 1) 적 지상 유닛 2초 기절, 5초간 장갑 +2. 재사용 5초.
    참고 모드의 포물선 도약(군심 랩터 도약 구조)은 게임 확인 없이 쓰기 어려워 돌진으로 바꿨다.
  저거너트 장갑 — 한 번에 30 넘게 받는 일반 피해를 30으로 줄인다 (주문 피해 제외).
  고급 전투 자극제 — 불을 뿜을 때 자동, 15초 공격·이동 속도 +50%, 초당 생명력 10, 재사용 30초.
- 보병 공격(피해 +1)·방어(+1) 업그레이드 적용.

Usage: python3 tools/build_v064.py <0.6.3 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import find, xml_edit, add_xml, set_lines, LOCS, KO, GD

OLD, NEW = b'version=0.6.3', b'version=0.6.4'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
U = 'RM6_Prometheus'
LIFE, ARMOR, DAMAGE, ELITE_DAMAGE = '550', '7', '15', '1'
TINT = '150,45,40'

ADD = {
    'modeldata.xml':
        f'<CModel id="{U}" parent="Unit" Race="Terran"><Model value="Assets\\Units\\Terran\\Firebat\\Firebat.m3" />'
        '<Occlusion value="Show" /><UnitGlossaryCamera value="Star2CameraMid04" /></CModel>',
    'unitdata.xml':
        f'<CUnit id="{U}"><DeathRevealRadius value="3" /><Race value="Terr" /><Mob value="Campaign" />'
        '<FlagArray index="UseLineOfSight" value="1" /><FlagArray index="ArmySelect" value="1" />'
        '<PlaneArray index="Ground" value="1" /><Collide index="Ground" value="1" /><Collide index="Small" value="1" />'
        '<Attributes index="Armored" value="1" /><Attributes index="Biological" value="1" />'
        f'<LifeStart value="{LIFE}" /><LifeMax value="{LIFE}" /><LifeArmor value="{ARMOR}" />'
        '<LifeArmorName value="Unit/LifeArmorName/TerranInfantryArmor" />'
        '<Speed value="2.5" /><Acceleration value="1000" /><LateralAcceleration value="46.0625" />'
        '<StationaryTurningRate value="719.4726" /><TurningRate value="719.4726" /><Sight value="8" />'
        '<Food value="-4" /><CostCategory value="Army" /><CostResource index="Minerals" value="50" />'
        '<CostResource index="Vespene" value="38" /><RepairTime value="20" /><AttackTargetPriority value="20" />'
        '<RankDisplay value="Never" />'
        '<AbilArray Link="stop" /><AbilArray Link="attack" /><AbilArray Link="move" />'
        '<AbilArray Link="RM6_PromJump" /><AbilArray Link="RM6_PromStim" />'
        '<BehaviorArray Link="RM6_PromElite" /><BehaviorArray Link="RM6_PromJuggernaut" />'
        f'<WeaponArray Link="{U}" />'
        '<CardLayouts><LayoutButtons Face="Move" Type="AbilCmd" AbilCmd="move,Move" Row="0" Column="0" />'
        '<LayoutButtons Face="Stop" Type="AbilCmd" AbilCmd="stop,Stop" Row="0" Column="1" />'
        '<LayoutButtons Face="MoveHoldPosition" Type="AbilCmd" AbilCmd="move,HoldPos" Row="0" Column="2" />'
        '<LayoutButtons Face="MovePatrol" Type="AbilCmd" AbilCmd="move,Patrol" Row="0" Column="3" />'
        '<LayoutButtons Face="Attack" Type="AbilCmd" AbilCmd="attack,Execute" Row="0" Column="4" />'
        '<LayoutButtons Face="RMK_MarineMengskVeterancy" Type="Passive" Row="1" Column="0" />'
        '<LayoutButtons Face="RM6_PromJump" Type="AbilCmd" AbilCmd="RM6_PromJump,Execute" Row="2" Column="0" />'
        '<LayoutButtons Face="RM6_PromStim" Type="AbilCmd" AbilCmd="RM6_PromStim,Execute" Row="2" Column="1" />'
        '<LayoutButtons Face="RM6_PromJuggernaut" Type="Passive" Row="2" Column="2" /></CardLayouts>'
        '<InnerRadius value="0.4375" /><CargoSize value="4" /><SubgroupPriority value="5" />'
        '<EditorCategories value="ObjectType:Unit,ObjectFamily:Campaign" /><TacticalAI value="Firebat" />'
        '<AIEvaluateAlias value="Firebat" /></CUnit>',
    'weapondata.xml':
        f'<CWeaponLegacy id="{U}"><EditorCategories value="Race:Terran" />'
        '<Icon value="Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel0.dds" />'
        '<DisplayEffect value="RM6_PromDamage" /><TargetFilters value="Ground,Visible;Missile,Stasis,Dead,Hidden,Invulnerable" />'
        '<Range value="2" /><Marker><MatchFlags index="Id" value="1" /></Marker><Period value="1.4" />'
        '<DamagePoint value="0.5" /><Backswing value="0.25" /><Effect value="RM6_PromSet" /></CWeaponLegacy>',
    'effectdata.xml':
        f'<CEffectDamage id="RM6_PromDamage" parent="DU_WEAP_SPLASH"><ValidatorArray value="noMarkers" />'
        '<EditorCategories value="Race:Terran" /><AttributeBonus index="Light" value="5" />'
        f'<AttributeBonus index="Biological" value="5" /><Amount value="{DAMAGE}" /><Death value="Fire" /><Kind value="Ranged" /></CEffectDamage>'
        '<CEffectEnumArea id="RM6_PromSearch" parent="EA_WEAP"><EditorCategories value="Race:Terran" />'
        '<SearchFilters value="Ground;Player,Ally,Missile,Stasis,Dead,Hidden,Invulnerable" />'
        '<AreaArray Radius="1" Effect="RM6_PromDamage" /></CEffectEnumArea>'
        '<CEffectCreatePersistent id="RM6_PromPersistent"><EditorCategories value="Race:Terran" />'
        '<WhichLocation Value="SourcePoint" /><OffsetVectorStartLocation Value="SourcePoint" />'
        '<Flags index="Channeled" value="1" /><PeriodCount value="4" /><PeriodicEffectArray value="RM6_PromSearch" />'
        '<PeriodicOffsetArray value="0,-0.5,0" /><PeriodicOffsetArray value="0,-1,0" />'
        '<PeriodicOffsetArray value="0,-1.5,0" /><PeriodicOffsetArray value="0,-2,0" />'
        '<PeriodicPeriodArray value="0.022" /><PeriodicPeriodArray value="0.022" />'
        '<PeriodicPeriodArray value="0.022" /><PeriodicPeriodArray value="0.022" /></CEffectCreatePersistent>'
        '<CEffectSet id="RM6_PromSet"><EditorCategories value="Race:Terran" />'
        '<EffectArray value="RM6_PromPersistent" /><EffectArray value="RM6_PromDamage" /></CEffectSet>'
        # 점프 제트 강습 (자날 광전사 돌진 구조)
        '<CEffectSet id="RM6_PromJumpSet"><EditorCategories value="Race:Terran" />'
        '<ValidatorArray value="ChargeMinTriggerDistance" /><ValidatorArray value="ChargeMaxDistance" />'
        '<EffectArray value="RM6_PromJumpAB" /><EffectArray value="RM6_PromArmorAB" /></CEffectSet>'
        '<CEffectApplyBehavior id="RM6_PromJumpAB"><EditorCategories value="Race:Terran" />'
        '<Behavior value="RM6_PromJumping" /><WhichUnit Value="Caster" /></CEffectApplyBehavior>'
        '<CEffectApplyBehavior id="RM6_PromArmorAB"><EditorCategories value="Race:Terran" />'
        '<Behavior value="RM6_PromArmor" /><WhichUnit Value="Caster" /></CEffectApplyBehavior>'
        '<CEffectEnumArea id="RM6_PromStunSearch"><EditorCategories value="Race:Terran" />'
        '<LaunchLocation Value="CasterUnit" /><ImpactLocation Value="CasterUnit" />'
        '<SearchFilters value="Ground;Player,Ally,Neutral,Structure,Heroic,Missile,Stasis,Dead,Hidden,Invulnerable" />'
        '<AreaArray Radius="1" Effect="RM6_PromStunAB" /><SearchFlags index="ExtendByUnitRadius" value="1" /></CEffectEnumArea>'
        '<CEffectApplyBehavior id="RM6_PromStunAB"><ValidatorArray value="NotHeroic" /><ValidatorArray value="NotStructure" />'
        '<EditorCategories value="Race:Terran" /><Behavior value="RM6_PromStun" /></CEffectApplyBehavior>'
        # 고급 전투 자극제
        '<CEffectApplyBehavior id="RM6_PromStimAB"><EditorCategories value="Race:Terran" />'
        '<Behavior value="RM6_PromStimBuff" /><WhichUnit Value="Caster" /></CEffectApplyBehavior>',
    'behaviordata.xml':
        '<CBehaviorBuff id="RM6_PromElite"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" />'
        '<InfoIcon value="Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel3.dds" /><Modification>'
        f'<DamageDealtFraction index="Melee" value="{ELITE_DAMAGE}" /><DamageDealtFraction index="Ranged" value="{ELITE_DAMAGE}" />'
        f'<DamageDealtFraction index="Splash" value="{ELITE_DAMAGE}" /><StateFlags index="UnitAttrOnHeroic" value="1" />'
        '</Modification></CBehaviorBuff>'
        '<CBehaviorBuff id="RM6_PromJuggernaut"><InfoFlags index="Hidden" value="1" /><BehaviorFlags index="Permanent" value="1" />'
        '<EditorCategories value="Race:Terran,AbilityorEffectType:Units" />'
        '<DamageResponse ClampMaximum="30" Minimum="30"><Kind index="Spell" value="0" /><Chance value="1" /></DamageResponse></CBehaviorBuff>'
        '<CBehaviorBuff id="RM6_PromJumping"><InfoIcon value="Assets\\Textures\\BTN-Ability-Terran-JetPack-color.dds" />'
        '<EditorCategories value="Race:Terran,AbilityorEffectType:Units" /><Alignment value="Positive" />'
        '<Duration value="2" /><Modification MoveSpeedMultiplier="2.5" /><BuffFlags index="Channeling" value="1" />'
        '<RemoveValidatorArray value="RM6_PromNotFiring" /><FinalEffect value="RM6_PromStunSearch" /></CBehaviorBuff>'
        '<CBehaviorBuff id="RM6_PromArmor"><InfoIcon value="Assets\\Textures\\BTN-Ability-Terran-JetPack-color.dds" />'
        '<EditorCategories value="Race:Terran,AbilityorEffectType:Units" /><Alignment value="Positive" />'
        '<Duration value="5" /><Modification><LifeArmorBonus value="2" /></Modification></CBehaviorBuff>'
        '<CBehaviorBuff id="RM6_PromStun"><Alignment value="Negative" /><InfoIcon value="Assets\\Textures\\BTN-Ability-Terran-JetPack-color.dds" />'
        '<BehaviorCategories index="Stun" value="1" /><EditorCategories value="Race:Terran,AbilityorEffectType:Units" />'
        '<Duration value="2" /><Modification><StateFlags index="Stun" value="1" /><StateFlags index="SuppressAttack" value="1" />'
        '<AbilClassDisableArray index="CAbilAttack" value="1" /></Modification></CBehaviorBuff>'
        '<CBehaviorBuff id="RM6_PromStimBuff"><Alignment value="Positive" /><InfoIcon value="Assets\\Textures\\btn-ability-terran-stimpack-color.dds" />'
        '<BehaviorCategories index="Fast" value="1" /><EditorCategories value="Race:Terran,AbilityorEffectType:Units" />'
        '<Duration value="15" /><Modification MoveSpeedMultiplier="1.5" AttackSpeedMultiplier="1.5">'
        '<VitalRegenArray index="Life" value="10" /></Modification></CBehaviorBuff>',
    'validatordata.xml':
        f'<CValidatorUnitWeaponFiring id="RM6_PromNotFiring"><WhichUnit Value="Caster" /><Weapon value="{U}" /><Find value="0" /></CValidatorUnitWeaponFiring>'
        f'<CValidatorUnitWeaponFiring id="RM6_PromFiring"><WhichUnit Value="Caster" /><Weapon value="{U}" /><Find value="1" /></CValidatorUnitWeaponFiring>',
    'abildata.xml':
        '<CAbilAugment id="RM6_PromJump"><EditorCategories value="Race:Terran,AbilityorEffectType:Units" />'
        '<CmdButtonArray index="Execute" DefaultButtonFace="RM6_PromJump" /><AbilCmd value="attack,Execute" />'
        '<Flags index="AutoCast" value="1" /><Flags index="AutoCastOn" value="1" />'
        '<Cost><Cooldown Link="RM6_PromJump" Location="Unit" TimeUse="5" /></Cost>'
        '<Effect value="RM6_PromJumpSet" /><AutoCastValidatorArray value="CasterNotHoldingPosition" /></CAbilAugment>'
        '<CAbilEffectInstant id="RM6_PromStim"><EditorCategories value="Race:Terran,AbilityorEffectType:Units" />'
        '<Effect index="0" value="RM6_PromStimAB" /><Flags index="AutoCast" value="1" /><Flags index="AutoCastOn" value="1" />'
        '<Flags index="Transient" value="1" /><Cost><Cooldown Link="RM6_PromStim" Location="Unit" TimeUse="30" /></Cost>'
        '<AutoCastRange value="6" /><AutoCastValidatorArray value="RM6_PromFiring" />'
        '<CmdButtonArray index="Execute" DefaultButtonFace="RM6_PromStim" /></CAbilEffectInstant>',
    'actordata.xml':
        f'<CActorUnit id="{U}" parent="GenericUnitStandard" unitName="{U}">'
        '<Macros value="UnloadDropAnim" /><DeathArray index="Normal" ModelLink="FirebatDeath" SoundLink="Firebat_Explode" />'
        '<WalkAnimMoveSpeed value="1.875" /><PortraitModel value="FirebatPortrait" /><BarWidth value="45" /><BarOffset value="77" />'
        f'<On Terms="ActorCreation" Send="SetTintColor {TINT}" />'
        '<On Terms="Behavior.MercGroundDrop.Create" Send="Create DevilDogDropModel" />'
        '<On Terms="Abil.attack.ReadyStop" Target="FirebatAttackModel" Send="SetOpacity 0.000000 0.250000" />'
        '<UnitIcon value="Assets\\Textures\\btn-unit-terran-firebat.dds" /><HeroIcon value="Assets\\Textures\\btn-unit-terran-firebat.dds" />'
        '<GroupIcon><Image value="Assets\\Textures\\Wireframe-Terran-firebat.dds" /></GroupIcon>'
        '<Wireframe><Image value="Assets\\Textures\\Wireframe-Terran-firebat.dds" /></Wireframe>'
        '<LifeArmorIcon value="Assets\\Textures\\btn-upgrade-terran-infantryarmorlevel0.dds" />'
        '<SoundArray index="Birth" value="FirebatBirth" /><SoundArray index="Ready" value="Firebat_Ready" />'
        '<SoundArray index="Help" value="Firebat_Help" /><SoundArray index="What" value="Firebat_What" />'
        '<SoundArray index="Yes" value="Firebat_Yes" /><SoundArray index="Attack" value="Firebat_Attack" />'
        '<SoundArray index="Pissed" value="Firebat_Pissed" /><SoundArray index="Movement" value="FirebatMovement" />'
        '<SoundArray index="Turning" value="FirebatTurning" /><SoundArray index="Board" value="FirebatBoard" />'
        '<SoundArray index="Click" value="FirebatClick" /><SoundArray index="ClickError" value="FirebatClickError" />'
        '<SoundArray index="Highlight" value="FirebatHighlight" /><GroupSoundArray index="What" value="FirebatGroupWhat" />'
        '<GroupSoundArray index="Yes" value="FirebatGroupYes" /><GroupSoundArray index="Attack" value="FirebatGroupAttack" />'
        '<GroupSoundArray index="Board" value="FirebatGroupBoard" /><Aliases value="_UnitMedium" /></CActorUnit>'
        '<CActorAction id="RM6_PromAttack" parent="GenericAttackBase" effectAttack="RM6_PromPersistent">'
        '<LaunchAttachQuery Methods="Weapon" /><LaunchAssets Model="FirebatAttackLaunch" Sound="FirebatAttackLaunch" />'
        '<LaunchModel value="FirebatAttackModel" /><ContainerAssets Model="FirebatBunkerAttackLaunch" Sound="FirebatAttackLaunch" />'
        '<ImpactMap index="None" Sound="Firebat_AttackImpact" />'
        '<On Terms="Effect.RM6_PromSet.Start; At Caster" Send="Create" />'
        '<On Terms="Effect.RM6_PromDamage.Start; At Caster; FromEffectTreeDescendant" Send="ActionDamage" /></CActorAction>'
        '<CActorModel id="RM6_PromFlames" parent="ModelAnimationStyleOneShot"><Model value="ImpactModelFlames" />'
        '<Terms value="Cap 1" /><On Terms="Effect.RM6_PromDamage.Start; At Target" Send="Create" />'
        '<On Terms="ActorOrphan" Send="Destroy" /><Host Subject="_Selectable" /><HostSiteOps Ops="SOpAttachRandomDamage" /></CActorModel>'
        '<CActorModel id="RM6_PromStimFX" parent="ModelAnimationStyleOneShot"><Model value="StimpackStartImpact" />'
        '<On Terms="Abil.RM6_PromStim.SourceCastStart" Send="Create" /><Host Subject="_Selectable" />'
        '<HostSiteOps Ops="SOpAttachOverhead" /><Inherits index="CloakEffect" value="1" /></CActorModel>',
    'buttondata.xml':
        '<CButton id="RM6_HirePrometheus"><Icon value="Assets\\Textures\\btn-unit-terran-firebat.dds" />'
        '<AlertIcon value="Assets\\Textures\\btn-unit-terran-firebat.dds" />'
        '<Name value="Button/Name/RM6_HirePrometheus" /><Tooltip value="Button/Tooltip/RM6_HirePrometheus" /></CButton>'
        '<CButton id="RM6_PromJump"><Icon value="Assets\\Textures\\BTN-Ability-Terran-JetPack-color.dds" />'
        '<Name value="Button/Name/RM6_PromJump" /><Tooltip value="Button/Tooltip/RM6_PromJump" /></CButton>'
        '<CButton id="RM6_PromStim"><Icon value="Assets\\Textures\\btn-ability-terran-stimpack-color.dds" />'
        '<Name value="Button/Name/RM6_PromStim" /><Tooltip value="Button/Tooltip/RM6_PromStim" /></CButton>'
        '<CButton id="RM6_PromJuggernaut"><Icon value="Assets\\Textures\\btn-techupgrade-terran-juggernautplating.dds" />'
        '<Name value="Button/Name/RM6_PromJuggernaut" /><Tooltip value="Button/Tooltip/RM6_PromJuggernaut" /></CButton>',
}

STRINGS = {
    f'Unit/Name/{U}': '프로메테우스 중대 /// Prometheus Company',
    f'Weapon/Name/{U}': '근위대 화염방사기 /// Royal Guard Flamethrower',
    'Abil/Name/RM6_PromJump': '점프 제트 강습 /// Jump Jet Assault',
    'Abil/Name/RM6_PromStim': '고급 전투 자극제 /// Advanced Stimpack',
    'Behavior/Name/RM6_PromElite': '3등급 프로메테우스 중대 /// Rank 3 Prometheus Company',
    'Behavior/Tooltip/RM6_PromElite': '3등급 능력치로 고용된 정예 용병입니다. /// An elite mercenary hired at rank 3.',
    'Behavior/Name/RM6_PromJumping': '점프 제트 강습 /// Jump Jet Assault',
    'Behavior/Tooltip/RM6_PromJumping': '적에게 돌진하고 있습니다. /// Charging toward an enemy.',
    'Behavior/Name/RM6_PromArmor': '점프 제트 강습 /// Jump Jet Assault',
    'Behavior/Tooltip/RM6_PromArmor': '일시적으로 방어력이 증가했습니다. /// This unit temporarily gains increased armor.',
    'Behavior/Name/RM6_PromStun': '기절 /// Stunned',
    'Behavior/Tooltip/RM6_PromStun': '이 유닛은 기절했습니다. /// This unit has been stunned.',
    'Behavior/Name/RM6_PromStimBuff': '고급 전투 자극제 /// Advanced Stimpack',
    'Behavior/Tooltip/RM6_PromStimBuff': '공격 속도·이동 속도가 증가하고 생명력이 회복됩니다. /// This unit gains bonus attack speed, movement speed and life regeneration.',
    'Button/Name/RM6_HirePrometheus': '프로메테우스 중대 /// Prometheus Company',
    'Button/Tooltip/RM6_HirePrometheus': '3등급 프로메테우스 중대 2기를 고용합니다. 기당 인구 4, 총 인구 8. 점프 제트 강습·저거너트 장갑·고급 전투 자극제를 처음부터 사용합니다. 보병 공방업이 적용됩니다.<n/><n/>자치령 근위대의 중화염방사병입니다. '
                                         '/// Hires 2 rank 3 Prometheus Company troopers. 4 supply each, 8 total. Jump Jet Assault, Juggernaut Plating and Advanced Stimpack are available immediately. Receives infantry weapon and armor upgrades.<n/><n/>Dominion Royal Guard heavy flamethrower troopers.',
    'Button/Name/RM6_PromJump': '점프 제트 강습 /// Jump Jet Assault',
    'Button/Tooltip/RM6_PromJump': '공격 명령을 받으면 2~4 거리의 적에게 2초 동안 빠르게 돌진합니다. 도착하면 주변 지상 적을 2초 동안 기절시키고, 5초 동안 방어력이 2 증가합니다. 재사용 대기시간 5초. 자동 시전. '
                                   '/// When ordered to attack, charges at an enemy 2-4 range away for up to 2 seconds. On arrival, stuns nearby ground enemies for 2 seconds and gains +2 armor for 5 seconds. Cooldown: 5 seconds. Autocast.',
    'Button/Name/RM6_PromStim': '고급 전투 자극제 /// Advanced Stimpack',
    'Button/Tooltip/RM6_PromStim': '15초 동안 공격 속도와 이동 속도가 50% 증가하고 초당 생명력 10을 회복합니다. 생명력을 소모하지 않습니다. 재사용 대기시간 30초. 공격 중 자동 시전. '
                                   '/// Increases attack speed and movement speed by 50% and regenerates 10 life per second for 15 seconds. Costs no life. Cooldown: 30 seconds. Autocast while attacking.',
    'Button/Name/RM6_PromJuggernaut': '저거너트 장갑 /// Juggernaut Plating',
    'Button/Tooltip/RM6_PromJuggernaut': '한 번에 받는 주문이 아닌 피해가 30을 넘으면 30으로 줄어듭니다. '
                                         '/// Non-spell damage from a single hit is reduced to 30 if it exceeds 30.',
}
HOTKEYS = {'Button/Hotkey/RM6_HirePrometheus': 'D', 'Button/Hotkey/RM6_PromJump': 'J', 'Button/Hotkey/RM6_PromStim': 'T',
           'Button/Hotkey/RM6_PromJuggernaut': 'G'}

ALLOW = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",3),true);\n'
ALLOW_ADD = ('    // 0.6.4: Prometheus Company in the Devil Dogs hire slot (user 2026-10-31).\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",1),true);\n'
             f'    TechTreeUnitAllow(1,"{U}",true);\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("RM6_PromJump",0),true);\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("RM6_PromStim",0),true);\n')


def edit_map(d):
    g = d / GD
    for fn, xml in ADD.items():
        add_xml(g / fn, xml)

    def abils(root):
        s = find(root, 'CAbilTrain', 'SummonMercenaries')
        t2 = [i for i in s.findall('InfoArray') if i.get('index') == 'Train2']
        assert len(t2) == 1 and [b.get('State') for b in t2[0].findall('Button')] == ['Suppressed'], 'Train2'
        t2[0].clear(); t2[0].set('index', 'Train2')
        for n in '01':
            E.SubElement(t2[0], 'Unit', index=n, value=U)
        E.SubElement(t2[0], 'Button', DefaultButtonFace='RM6_HirePrometheus', State='Available', Requirements='')
    xml_edit(g / 'abildata.xml', abils)

    def units(root):
        cards = find(root, 'CUnit', 'MercCompound').findall('CardLayouts')
        assert len(cards) == 1 and not [b for b in cards[0] if (b.get('Row'), b.get('Column')) == ('0', '1')]
        cards[0].append(E.fromstring('<LayoutButtons Face="RM6_HirePrometheus" Type="AbilCmd" AbilCmd="SummonMercenaries,Train2" Row="0" Column="1" />'))
    xml_edit(g / 'unitdata.xml', units)

    def upgrades(root):
        w = find(root, 'CUpgrade', 'TerranInfantryWeapons')
        w.append(E.fromstring('<EffectArray Reference="Effect,RM6_PromDamage,Amount" Value="1" />'))
        w.append(E.fromstring(f'<EffectArray Reference="Weapon,{U},Level" Value="1" />'))
        a = find(root, 'CUpgrade', 'TerranInfantryArmors')
        for f in ('LifeArmor', 'LifeArmorLevel'):
            a.append(E.fromstring(f'<EffectArray Reference="Unit,{U},{f}" Value="1" />'))
        for lv in (1, 2, 3):
            find(root, 'CUpgrade', f'TerranInfantryWeaponsLevel{lv}').append(E.fromstring(
                f'<EffectArray Operation="Set" Reference="Weapon,{U},Icon" Value="Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel{lv}.dds" />'))
            find(root, 'CUpgrade', f'TerranInfantryArmorsLevel{lv}').append(E.fromstring(
                f'<EffectArray Operation="Set" Reference="Actor,{U},LifeArmorIcon" Value="Assets\\Textures\\btn-upgrade-terran-infantryarmorlevel{lv}.dds" />'))
    xml_edit(g / 'upgradedata.xml', upgrades)

    p = d / 'mapscript.galaxy'
    raw = p.read_bytes().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    assert t.count(ALLOW) == 1
    t = t.replace(ALLOW, ALLOW + ALLOW_ADD)
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
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in MAPS) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
