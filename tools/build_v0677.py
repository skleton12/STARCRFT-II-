#!/usr/bin/env python3
"""0.6.76 -> 0.6.77: Fenix champions with the Purifier support, Reconstruction icon removed (user 2026-11-22).

User: "아이콘만 제거" (Legionnaire Reconstruction icon), then "대신 ... 영웅 유닛 감화되는 거", "칼달리스 0단계로부터
시작", "진행해".

Maps 3-7 (TRaynor03 player 10, TTychus01/TTosh01/THanson01/TTosh02 player 8), Purifier ally:
1. Co-op Fenix champions, one per Hyperion lab Protoss tier: 0 Kaldalis (Legionnaire), 1 Talis (Adept),
   2 Taldarin (Immortal), 3 Warbringer (Colossus), 4 Mojo (Scout), 5 Clolarion (Carrier). When the Purifier support
   is called, every unlocked champion that is not alive on the map comes free with the group (one of each at a time;
   a dead one comes back with the next call). They are the first free units, so they get room under the 120 cap
   before the 0.6.76 heavy unit and the light tier units. Ported from co-op data with tools/port_units.py.
2. No commander levels (CLAUDE.md 3-1): the level-locked buttons/requirements are removed and the champion
   upgrades are given at the start: Empowered Blades, Gravimetric Overload, Purification Blast, Chronal Distortion,
   Suppression Procedure, Interdictors, upgraded Ricochet Glaive. All their abilities are auto-cast / auto-build.
3. Talis' Psionic Projection: the 'is Fenix co-op commander' checks are removed (no Fenix commander here).
   PreventDestroy off on the champions (co-op revives them with the commander script, which this mod does not have).
4. The free 'ZealotResearchReconstruction' grant is removed (maps 2-7): Legionnaires have no Reconstruction since
   0.6.36, only the icon remained.
5. Korean '한국어 /// English' strings for the champion names, weapons, abilities and tooltips (Korean names not checked
   against the official translation). Map 3: champion supply from unit data, Colossus_Land sound actor.
Game not run.

Usage: python3 tools/build_v0677.py <0.6.76 zip> <new output zip>
"""
import argparse, copy, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.6.76', b'version=0.6.77'
MAPS = {'TRaynor03': ('m3c', 10), 'TTychus01': ('m4', 8), 'TTosh01': ('m5', 8), 'THanson01': ('m6', 8), 'TTosh02': ('m7', 8)}
CHAMPS = ['FenixKaldalisZealot', 'FenixTalisAdept', 'FenixTaldarinImmortal', 'FenixWarbringerColossus',
          'FenixMojoScout', 'FenixClolarionCarrier']
UPGRADES = ['FenixKaldalisCleave', 'FenixImmortalDetonationShot', 'FenixWarbringerColossusPowerShot',
            'FenixWarbringerColossusIceBeam', 'FenixChampionScoutAOEMissiles', 'FenixChampionCarrierBombers',
            'FenixChampionTalisAdeptBounceShotUpgrade']
DROP = 'FenixCommander|^SOA|AllUnitBehaviorController|FenixDragoon|FenixArbiter|FenixProbius|FenixCoop|FenixChampionPlaceholder'
SEEDS = CHAMPS[1:] + ['FenixTalisAdeptUpgradeWeapon', 'ImmortalOverload', 'FenixChampionTalisAdeptBounceShotUpgrade',
                      'FenixWarbringerColossusIceBeam', 'CountUpgradeFenixChampionTalisAdeptBounceShotUpgradeCompleteOnly',
                      'CountUpgradeFenixWarbringerColossusIceBeamCompleteOnly', 'FenixNetworkedSuperiority',
                      'CountUpgradeFenixNetworkedSuperiorityCompleteOnly']
LOCALES = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
ATK_G = '<n/><n/><c val="#ColorAttackInfo">{0}</c>'
STRINGS = {
    'Unit/Name/FenixKaldalisZealot': '칼달리스 /// Kaldalis',
    'Unit/Name/FenixKaldalisZealotReviveCorpse': '칼달리스 /// Kaldalis',
    'Unit/Name/FenixTalisAdept': '탈리스 /// Talis',
    'Unit/Name/FenixTalisAdeptPhaseShift': '그림자 /// Shade',
    'Unit/Name/FenixTaldarinImmortal': '탈다린 /// Taldarin',
    'Unit/Name/FenixWarbringerColossus': '워브링어 /// Warbringer',
    'Unit/Name/FenixMojoScout': '모조 /// Mojo',
    'Unit/Name/FenixClolarionCarrier': '클로라리온 /// Clolarion',
    'Unit/Name/FenixClolarionInterceptor': '요격기 /// Interceptor',
    'Unit/Name/FenixClolarionBomber': '차단기 /// Interdictor',
    'Weapon/Name/FenixKaldalisZealotPsiBlades': '사이오닉 검 /// Psi Blades',
    'Weapon/Name/FenixTalisAdept': '정화자 글레이브 포 /// Purifier Glaive Cannon',
    'Weapon/Name/FenixTaldarinImmortalPhaseDisruptors': '중력자 분열기 /// Graviton Disruptors',
    'Weapon/Name/FenixWarbringerColossusThermalLance': '시간 창 /// Chrono Lance',
    'Weapon/Name/FenixMojoScoutAir': '반물질 미사일 /// Anti-Matter Missiles',
    'Weapon/Name/FenixMojoScoutGround': '광자 분사포 /// Photon Blaster',
    'Weapon/Name/FenixClolarionPrismaticBeam': '태양 광선 /// Solar Beam',
    'Abil/Name/FenixMojoMissiles': '진압 절차 /// Suppression Procedure',
    'Abil/Name/FenixTalisAdeptPhaseShift': '사이오닉 전이 /// Psionic Transfer',
    'Abil/Name/FenixTalisAdeptPhaseShiftCancel': '사이오닉 전이 취소 /// Psionic Transfer Cancel',
    'Abil/Name/ImmortalBarrierBase': '방벽 /// Barrier',
    'Abil/Name/ImmortalOverload': '방벽 /// Barrier',
    'Behavior/Name/AdeptPsionicTransferDamageDebuff': '사이오닉 전이 /// Psionic Transfer',
    'Behavior/Tooltip/AdeptPsionicTransferDamageDebuff': '이 유닛은 받는 피해가 늘어납니다. /// This unit is taking increased damage.',
    'Behavior/Name/FenixMojoScoutAirStun': '기절 /// Stunned',
    'Behavior/Name/ImmortalBarrierBase': '방벽 /// Barrier',
    'Behavior/Tooltip/ImmortalBarrierBase': '이 유닛이 받는 피해를 흡수하고 있습니다. /// This unit is absorbing damage dealt to it.',
    'Behavior/Name/ImmortalOverload': '방벽 /// Barrier',
    'Behavior/Tooltip/ImmortalOverload': '이 유닛이 받는 피해를 흡수하고 있습니다. /// This unit is absorbing damage dealt to it.',
    'Upgrade/Name/FenixKaldalisCleave': '강화된 칼날 /// Empowered Blades',
    'Upgrade/Name/FenixImmortalDetonationShot': '중력 과부하 /// Gravimetric Overload',
    'Upgrade/Name/FenixWarbringerColossusPowerShot': '정화 폭발 /// Purification Blast',
    'Upgrade/Name/FenixWarbringerColossusIceBeam': '시간 왜곡 /// Chronal Distortion',
    'Upgrade/Name/ColossusIceBeam': '시간 창 /// Chrono Lance',
    'Upgrade/Name/FenixChampionScoutAOEMissiles': '진압 절차 /// Suppression Procedure',
    'Upgrade/Name/FenixChampionCarrierBombers': '차단기 /// Interdictors',
    'Upgrade/Name/FenixChampionTalisAdeptBounceShotUpgrade': '강화 도탄 글레이브 /// Upgraded Ricochet Glaive',
    'Button/Name/FenixKaldalisZealot': '칼달리스 차원 전송 /// Warp in Kaldalis',
    'Button/Tooltip/FenixKaldalisZealot': '정화자 세력<n/>아이어 탈환 때 기사단 선봉에서 싸운 남다르게 용맹한 광전사입니다. 교전으로 적에게 뛰어듭니다.'
        + ATK_G.format('지상 유닛을 공격할 수 있습니다.')
        + ' /// Purifier Faction<n/>A zealot of exceptional bravery who fought in the Templar\'s vanguard to retake Aiur. Can use Engage to leap at enemies.'
        + ATK_G.format('Can attack ground units.'),
    'Button/Name/FenixKaldalisZealotCharge': '교전 /// Engage',
    'Button/Tooltip/FenixKaldalisZealotCharge': '칼달리스가 대상 유닛에게 달려듭니다. /// Kaldalis intercepts the target unit.',
    'Button/Name/FenixKaldalisZealotCleave': '강화된 칼날 /// Empowered Blades',
    'Button/Tooltip/FenixKaldalisZealotCleave': '칼달리스의 공격이 주변 대상에게 <d ref="Effect,FenixKaldalisZealotPsiBladesCleave,Amount"/>의 피해를 줍니다. /// Kaldalis\' attacks deal <d ref="Effect,FenixKaldalisZealotPsiBladesCleave,Amount"/> damage to nearby targets.',
    'Button/Name/FenixTalisAdept': '탈리스 차원 전송 /// Warp in Talis',
    'Button/Tooltip/FenixTalisAdept': '정화자 세력<n/>원거리 전문가입니다. 사이오닉 전이를 쓸 수 있습니다.' + ATK_G.format('지상 및 공중 유닛을 공격할 수 있습니다.')
        + ' /// Purifier Faction<n/>Ranged specialist. Can use Psionic Transfer.' + ATK_G.format('Can attack ground and air units.'),
    'Button/Name/FenixTalisAdeptBounceShot': '도탄 글레이브 /// Ricochet Glaive',
    'Button/Tooltip/FenixTalisAdeptBounceShot': '튕겨 나가는 강화 글레이브가 적 유닛을 최대 8기까지 맞혀 각각 <d ref="Effect,FenixTalisAdeptBounceShotDamage1,Amount"/>의 피해를 줍니다. 맞은 대상은 모든 공격에서 피해를 더 받습니다. /// An amplified Glaive that ricochets and hits up to 8 enemy units for <d ref="Effect,FenixTalisAdeptBounceShotDamage1,Amount"/> damage each. Targets hit take additional damage from all attacks.',
    'Button/Name/FenixTalisAdeptPhaseShift': '사이오닉 전이 /// Psionic Transfer',
    'Button/Name/FenixTalisShadeSpawnShade': '사이오닉 투영 /// Psionic Projection',
    'Button/Tooltip/FenixTalisShadeSpawnShade': '공격하면 잠시 적을 공격하는 무적 그림자를 불러냅니다. /// Attacks summon an invulnerable Shade that will attack enemies for a short time.',
    'Button/Name/FenixTaldarinImmortal': '탈다린 차원 전송 /// Warp in Taldarin',
    'Button/Tooltip/FenixTaldarinImmortal': '정화자 세력<n/>최초의 용기병 중 하나로 아둔과 함께 싸운 위대한 전사입니다. 공격하면 적을 끌어당기는 중력장이 생깁니다. 방벽으로 피해를 흡수합니다.'
        + ATK_G.format('지상 유닛을 공격할 수 있습니다.')
        + ' /// Purifier Faction<n/>One of the first dragoons, and a great warrior who fought alongside Adun himself. Attacks create a gravity well that pulls in enemies. Can use Barrier to absorb damage.'
        + ATK_G.format('Can attack ground units.'),
    'Button/Name/FenixImmortalGravitonCannon': '중력자 분열기 /// Graviton Disruptors',
    'Button/Tooltip/FenixImmortalGravitonCannon': '공격하면 주변 적 유닛을 대상 쪽으로 끌어당기는 중력장이 생깁니다. /// Attacks create a gravity well that pulls nearby enemy units to the target.',
    'Button/Name/FenixImmortalDetonationShot': '중력 과부하 /// Gravimetric Overload',
    'Button/Tooltip/FenixImmortalDetonationShot': '공격할 때마다 준 피해의 <d ref="Effect,FenixTaldarinImmortalDetonationDummyFraction,Amount" player="0"/>%를 대상에게 쌓습니다. 그 유닛이 죽으면 폭발하여 쌓인 피해를 모두 주변 적 유닛에게 줍니다. /// Each attack stores <d ref="Effect,FenixTaldarinImmortalDetonationDummyFraction,Amount" player="0"/>% of the damage dealt on the target. When that unit is killed, it explodes, dealing all of the stored damage to nearby enemy units.',
    'Button/Name/ImmortalBarrierBase': '방벽 /// Barrier',
    'Button/Tooltip/ImmortalBarrierBase': '피해를 최대 <d ref="Behavior,ImmortalBarrierBase,DamageResponse.ModifyLimit"/>까지 흡수합니다. <d ref="Behavior,ImmortalBarrierBase,Duration"/>초 동안 지속됩니다. /// Absorbs up to <d ref="Behavior,ImmortalBarrierBase,DamageResponse.ModifyLimit"/> damage. Lasts for <d ref="Behavior,ImmortalBarrierBase,Duration"/> seconds.',
    'Button/Name/ImmortalOverload': '방벽 /// Barrier',
    'Button/Tooltip/ImmortalOverload': '피해를 최대 <d ref="Behavior,ImmortalOverload,DamageResponse.ModifyLimit"/>까지 흡수합니다. <d ref="Behavior,ImmortalOverload,Duration"/>초 동안 지속됩니다. /// Absorbs up to <d ref="Behavior,ImmortalOverload,DamageResponse.ModifyLimit"/> damage. Lasts for <d ref="Behavior,ImmortalOverload,Duration"/> seconds.',
    'Button/Name/FenixWarbringerColossus': '워브링어 차원 전송 /// Warp In Warbringer',
    'Button/Tooltip/FenixWarbringerColossus': '정화자 세력<n/>공격적인 공성전을 위해 설계된 고급 인공지능입니다. 공격이 범위 피해를 주고 적 유닛을 느리게 합니다.'
        + ATK_G.format('지상 유닛을 공격할 수 있습니다.')
        + ' /// Purifier Faction<n/>A highly advanced AI program specifically designed for aggressive siege combat. Attacks deal area damage and slow enemy units.'
        + ATK_G.format('Can attack ground units.'),
    'Button/Name/FenixWarbringerColossusPowerShot': '정화 폭발 /// Purification Blast',
    'Button/Tooltip/FenixWarbringerColossusPowerShot': '강력한 폭발을 쏘아 대상 유닛에게 <d ref="Effect,FenixWarbringerColossusPowerShotDamage,Amount" player="0"/>의 피해를 줍니다. /// Fire a devastating blast that deals <d ref="Effect,FenixWarbringerColossusPowerShotDamage,Amount" player="0"/> damage to target unit.',
    'Button/Name/ColossusIceBeam': '시간 왜곡 /// Chronal Distortion',
    'Button/Tooltip/ColossusIceBeam': '공격이 적 유닛의 공격 속도와 이동 속도를 <d ref="(1 - Behavior,ColossusIceFlatAmount,Modification.MoveSpeedMultiplier) * 100"/>% 늦춥니다. 영웅 유닛은 <d ref="(1 - Behavior,ColossusIceFlatAmountHeroic,Modification.MoveSpeedMultiplier) * 100"/>% 느려집니다. /// Attacks debilitate enemy units, slowing attack and movement speeds by <d ref="(1 - Behavior,ColossusIceFlatAmount,Modification.MoveSpeedMultiplier) * 100"/>%. Heroic units are slowed by <d ref="(1 - Behavior,ColossusIceFlatAmountHeroic,Modification.MoveSpeedMultiplier) * 100"/>%.',
    'Button/Name/FenixMojoScout': '모조 차원 전송 /// Warp in Mojo',
    'Button/Tooltip/FenixMojoScout': '정화자 세력<n/>포로에서 탈출해 코랄의 테란에게 빼앗긴 카이다린 수정을 되찾은 대담한 집정관입니다. 공격이 적 공중 유닛을 기절시킵니다.'
        + ATK_G.format('지상 및 공중 유닛을 공격할 수 있습니다.')
        + ' /// Purifier Faction<n/>A daring praetor who escaped captivity and recovered a stolen khaydarin crystal from the terrans on Korhal. Attacks stun enemy air units.'
        + ATK_G.format('Can attack ground and air units.'),
    'Button/Name/FenixMojoMissiles': '진압 절차 /// Suppression Procedure',
    'Button/Tooltip/FenixMojoMissiles': '반물질 미사일을 일제히 쏘아 <d ref="Effect,FenixMojoScoutAOEAirDamage,Amount"/>(중장갑 상대 <d ref="Effect,FenixMojoScoutAOEAirDamage,Amount+Effect,FenixMojoScoutAOEAirDamage,AttributeBonus[Armored]"/>)의 범위 피해를 주고 주변 적 공중 유닛을 <d time="[d ref=\'Behavior,FenixMojoScoutAirStun,Duration\'/]"/> 동안 기절시킵니다. /// Fire a barrage of Anti-Matter Missiles, dealing <d ref="Effect,FenixMojoScoutAOEAirDamage,Amount"/> (<d ref="Effect,FenixMojoScoutAOEAirDamage,Amount+Effect,FenixMojoScoutAOEAirDamage,AttributeBonus[Armored]"/> vs Armored) area damage and stunning nearby enemy air units for <d time="[d ref=\'Behavior,FenixMojoScoutAirStun,Duration\'/]"/>.',
    'Button/Name/FenixMojoScoutAirStunPassive': '역장 미사일 /// Force Missiles',
    'Button/Tooltip/FenixMojoScoutAirStunPassive': '공격하면 대상 공중 유닛을 <d time="[d ref=\'Behavior,FenixMojoScoutAirStun,Duration\'/]"/> 동안 기절시킵니다. /// Attacks stun the target air unit for <d time="[d ref=\'Behavior,FenixMojoScoutAirStun,Duration\'/]"/>.',
    'Button/Name/FenixClolarionCarrier': '클로라리온 차원 전송 /// Warp in Clolarion',
    'Button/Tooltip/FenixClolarionCarrier': '정화자 세력<n/>고대 정화자들을 이끌고 대의회에 맞서 반란을 일으킨 이름난 집행관입니다. 요격기를 만들어 적을 공격합니다. 태양 광선은 공중 유닛을 공격하며 시간이 지날수록 피해가 커집니다.'
        + ATK_G.format('지상 및 공중 유닛을 공격할 수 있습니다.')
        + ' /// Purifier Faction<n/>A famed executor who led the ancient Purifiers in their rebellion against the Conclave. Builds Interceptors to attack enemies. Solar Beam attacks air units and does more damage over time.'
        + ATK_G.format('Can attack ground and air units.'),
    'Button/Name/FenixClolarionInterceptor': '요격기 생산 /// Build Interceptor',
    'Button/Tooltip/FenixClolarionInterceptor': '클로라리온의 대상을 자동으로 공격하는 요격기를 만듭니다.' + ATK_G.format('지상 및 공중 유닛을 공격할 수 있습니다.')
        + ' /// Builds Interceptors that automatically attack Clolarion\'s target.' + ATK_G.format('Can attack ground and air units.'),
    'Button/Name/FenixClolarionBomber': '차단기 생산 /// Build Interdictor',
    'Button/Tooltip/FenixClolarionBomber': '적 지상 유닛을 자동으로 폭격해 <d ref="Effect,FenixClolarionBomberDamage,Amount"/>의 피해를 주는 차단기를 만듭니다.' + ATK_G.format('지상 유닛을 공격할 수 있습니다.')
        + ' /// Builds Interdictors that automatically bomb enemy ground units for <d ref="Effect,FenixClolarionBomberDamage,Amount"/> damage.' + ATK_G.format('Can attack ground units.'),
    'Button/Name/FenixClolarionSolarBeam': '태양 광선 /// Solar Beam',
    'Button/Tooltip/FenixClolarionSolarBeam': '클로라리온이 한 대상을 오래 공격할수록 태양 광선의 피해가 커집니다. /// The damage of Clolarion\'s Solar Beam increases the longer Clolarion remains on a single target.',
}
# Dummy-face buttons that also show on Clolarion's card.
STRINGS['Button/Name/FenixClolarionBomberDummy'] = STRINGS['Button/Name/FenixClolarionBomber']
STRINGS['Button/Tooltip/FenixClolarionBomberDummy'] = STRINGS['Button/Tooltip/FenixClolarionBomber']


def once(t, a, b):
    assert t.count(a) == 1, a[:90]
    return t.replace(a, b)


def edit(path, fn):
    raw = path.read_bytes().decode('utf-8')
    crlf = '\r\n' in raw
    t = fn(raw.replace('\r\n', '\n'))
    path.write_bytes((t.replace('\n', '\r\n') if crlf else t).encode('utf-8'))


def data(gd, m):
    sys.path.insert(0, str(HERE))
    import build_v0333 as L
    for f, fn in (('unitdata.xml', L.no_level_buttons), ('requirementdata.xml', L.no_level_reqs)):
        p = gd / f
        d, n = fn(p.read_bytes())
        assert n > 0, (m, f)
        p.write_bytes(d)
    def units(t):
        for c in CHAMPS:
            s = t.index(f'<CUnit id="{c}"'); e = t.index('</CUnit>', s)
            u = t[s:e]
            if '<FlagArray index="PreventDestroy" value="1" />' in u:
                u = once(u, '<FlagArray index="PreventDestroy" value="1" />', '<FlagArray index="PreventDestroy" value="0" />')
            t = t[:s] + u + t[e:]
        return t
    edit(gd / 'unitdata.xml', units)
    # Talis' Psionic Projection checks 'is the Fenix co-op commander' (HaveFenixCommander, not in this mod): drop it.
    def talis(t, cat, ids, line):
        for i in ids:
            s0 = t.index(f'id="{i}"'); e0 = t.index(f'</{cat}>', s0)
            t = t[:s0] + once(t[s0:e0], line, '') + t[e0:]
        return t
    edit(gd / 'effectdata.xml', lambda t: talis(t, 'CEffectCreateUnit', ['FenixTalisShadeSpawnShade'], '        <ValidatorArray value="IsFenixCoopCommander" />\n'))
    edit(gd / 'effectdata.xml', lambda t: talis(t, 'CEffectModifyUnit', ['FenixTalisSpawnShadeSetCooldown'], '        <ValidatorArray value="IsFenixCoopCommander" />\n'))
    edit(gd / 'behaviordata.xml', lambda t: talis(t, 'CBehaviorBuff', ['FenixTalisShadeCooldown'], '        <RemoveValidatorArray value="IsFenixCoopCommander" />\n'))
    a = gd / 'actordata.xml'
    if 'id="Colossus_Land"' not in a.read_text('utf-8'):
        edit(a, lambda t: once(t, '</Catalog>', '    <CActorSound id="Colossus_Land" parent="SoundOneShot" />\n</Catalog>'))
    for f in gd.glob('*.xml'): E.parse(f)


def script(t, pre, ally):
    grant = f'    TechTreeUpgradeAddLevel({ally},"ZealotResearchReconstruction",1);\n'
    t = once(t, grant, '    // 0.6.77: no Reconstruction for Legionnaires; co-op Fenix champion upgrades instead (no commander levels).\n'
             + ''.join(f'    TechTreeUpgradeAddLevel({ally},"{u}",1);\n' for u in UPGRADES))
    fill = f'void gf_{pre}_SupFill (int p) {{'
    ok = (f'// 0.6.77: Fenix champion is not on the map yet (one of each at a time).\n'
          f'bool gf_{pre}_ChampOK (int p, string kind) {{\n'
          f'    return UnitGroupCount(UnitGroup(kind,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0),c_unitCountAlive)==0;\n'
          f'}}\n\n')
    t = once(t, fill, ok + fill)
    i = t.index(fill)
    paid = f'        gv_{pre}_supPaid[p]=gv_{pre}_supN[p];\n'
    j = t.index(paid, i); assert j - i < 2500 and t.index(f'    gv_{pre}_supPaid[p]=gv_{pre}_supN[p];\n', i) > j
    champ = (f'        // 0.6.77: Fenix champions, free, by lab Protoss tier (0 Kaldalis ... 5 Clolarion, trial).\n'
             + ''.join(f'        if (gv_{pre}_tier[p]>={k} && gf_{pre}_ChampOK(p,"{c}")) {{ gf_{pre}_SupAdd(p,"{c}"); }}\n'
                       for k, c in enumerate(CHAMPS)))
    t = t[:j] + paid + champ + t[j + len(paid):]
    if pre == 'm3c':
        t = once(t, '    if (kind=="DehakaZerglingLevel2") { return 1.0; }\n    return 2.0;\n',
                 '    if (kind=="DehakaZerglingLevel2") { return 1.0; }\n'
                 '    if (StringSub(kind,1,5)=="Fenix") { return UnitTypeGetProperty(kind,c_unitPropSuppliesUsed); }  // 0.6.77 champions\n'
                 '    return 2.0;\n')
    return t


def add_lines(path, items):
    raw = path.read_bytes().decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in raw else '\n'
    keys = {l.split('=', 1)[0] for l in raw.splitlines() if '=' in l}
    add = [f'{k}={v}' for k, v in items.items() if k not in keys]
    out = raw.rstrip('\r\n') + nl + nl.join(add) + nl if add else raw
    path.write_bytes(out.encode('utf-8'))
    return len(add)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m, (pre, ally) in MAPS.items():
            md = root / f'{m}.SC2Map'
            subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(md), '--liberty-base', '--skip-existing',
                            f'--drop={DROP}', *SEEDS], check=True, stdout=subprocess.DEVNULL)
            (md / 'ported_shared_refs.txt').unlink(missing_ok=True)
            data(md / 'base.sc2data/gamedata', m)
            edit(md / 'mapscript.galaxy', lambda t, pre=pre, ally=ally: script(t, pre, ally))
            ko = md / 'kokr.sc2data/localizeddata/gamestrings.txt'
            print(m, 'strings', add_lines(ko, STRINGS))
            V35.gate('kokr', ko.read_bytes())
            for loc in V35.OTHER_LOCALES:
                (md / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        # map 2: drop the leftover Reconstruction grant too
        edit(root / 'TRaynor02.SC2Map/mapscript.galaxy',
             lambda t: once(t, '    TechTreeUpgradeAddLevel(8,"ZealotResearchReconstruction",1);\n', ''))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        assert not extra, extra
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes(),
                                 compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            touched = tuple(f'{m}.SC2Map/' for m in MAPS) + ('TRaynor02.SC2Map/mapscript.galaxy', 'metadata.txt')
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if not n.startswith(touched): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
