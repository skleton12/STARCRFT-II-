#!/usr/bin/env python3
"""Build 0.4.64 from the user's 0.4.63 ZIP; patch only mission 4.

Restore mercenary Stimpack without Hyperion purchase, campaign/co-op Adept
weapon and researched shades, support autocasts, and Aegis rank abilities.
Shrapnel remains paid research. Super Concussive Shells is the original
Mengsk research (100/100, 60), placed on the mission's co-op tech-lab page.
Curated missing records in data/v0464 come from SC2Mapster/SC2GameData
6dd323aae4209a01f110719a00b4e8f7a88389bc, with commander gates removed.
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
OLD, NEW = b'version=0.4.63', b'version=0.4.64'
LOCALES = ('enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw')


def one(root, ident):
    found = [e for e in root if e.get('id') == ident]
    assert len(found) == 1, (ident, len(found))
    return found[0]


def field(el, tag, value, **attrs):
    nodes = [c for c in el.findall(tag) if all(c.get(k) == v for k, v in attrs.items())]
    assert len(nodes) <= 1, (el.get('id'), tag, attrs)
    c = nodes[0] if nodes else E.SubElement(el, tag, attrs)
    c.set('value', str(value))
    return c


def add(root, xml):
    e = E.fromstring(xml)
    assert not any(c.get('id') == e.get('id') for c in root), e.get('id')
    root.append(e)
    return e


def patch_catalogs(files):
    cats = {Path(n).stem: E.fromstring(v) for n, v in files.items() if n.startswith(GD) and n.endswith('.xml')}
    changed = set()
    def cat(name):
        changed.add(name)
        return cats[name]
    for f in sorted((HERE / 'data/v0464').glob('*.xml')):
        r = cat(f.stem)
        for e in E.parse(f).getroot():
            assert not any(c.get('id') == e.get('id') for c in r), e.get('id')
            r.append(e)

    ab, un, eff, beh = (cat(n) for n in ('abildata', 'unitdata', 'effectdata', 'behaviordata'))
    req, nodes, val = (cat(n) for n in ('requirementdata', 'requirementnodedata', 'validatordata'))
    up, weapons, buttons = (cat(n) for n in ('upgradedata', 'weapondata', 'buttondata'))

    # LibertyStory marks Stimpack Restricted, independently of its requirements.
    # A separate ability avoids unlocking ordinary/enemy Marines globally.
    add(ab, '<CAbilEffectInstant id="RM4_MercStimpack" parent="Stimpack">'
               '<Effect index="0" value="RM4_MercStimSet"/><AINotifyEffect value="RM4_MercStimSet"/>'
               '<CmdButtonArray index="Execute" DefaultButtonFace="Stim" State="Available" Requirements="RM3_Stim1Use"/>'
               '</CAbilEffectInstant>')
    for uid in ('WarPig', 'HammerSecurity', 'RMK_MarineMengsk'):
        u = one(un, uid)
        for c in u.findall('AbilArray'):
            if c.get('Link') == 'Stimpack': c.set('Link', 'RM4_MercStimpack')
        E.SubElement(u, 'AbilArray', Link='Stimpack', removed='1')
        for c in u.iter('LayoutButtons'):
            if c.get('AbilCmd') == 'Stimpack,Execute': c.set('AbilCmd', 'RM4_MercStimpack,Execute')

    # Strip the previous stage's buff before applying the current stage.
    buffs = ('Stimpack', 'SuperStim', 'RMK_MarineMengskAttackSpeedBoost')
    for i, buff in enumerate(buffs):
        add(eff, f'<CEffectRemoveBehavior id="RM4_StimRemove{i}"><Behavior value="{buff}"/><WhichUnit Value="Caster"/></CEffectRemoveBehavior>')
    for ability, setid, apply in (
        ('RM4_MercStimpack', 'RM4_MercStimSet', 'Stimpack'),
        ('SuperStimpackMarine', 'RM4_MercSuperStimSet', 'SuperStimpackMarine'),
        ('RMK_MarineMengskAttackSpeedBoost', 'RM4_MercRoyalStimSet', 'RMK_MarineMengskAttackSpeedBoostAB'),
    ):
        s = add(eff, f'<CEffectSet id="{setid}"/>')
        for i in range(3): E.SubElement(s, 'EffectArray', value=f'RM4_StimRemove{i}')
        E.SubElement(s, 'EffectArray', value=apply)
        a = one(ab, ability)
        for c in list(a.findall('Effect')): a.remove(c)
        E.SubElement(a, 'Effect', index='0', value=setid)
        field(a, 'AINotifyEffect', setid)
        onecmd = a.find("CmdButtonArray[@index='Execute']")
        onecmd.set('State', 'Available')

    # Void campaign supplies range 5 and air targeting; co-op adds shade set.
    w = copy.deepcopy(one(weapons, 'Adept'))
    w.set('id', 'RM4_AdeptFenixWeapon')
    field(w, 'Range', '5')
    field(w, 'TargetFilters', 'Visible;Missile,Stasis,Dead,Hidden,Invulnerable')
    field(w, 'Effect', 'AdeptLMSet')
    field(w, 'Name', 'Weapon/Name/Adept')
    weapons.append(w)
    one(un, 'AdeptFenix').find('WeaponArray').set('Link', 'RM4_AdeptFenixWeapon')
    cooldown = one(beh, 'FenixAdeptShadeCooldown')
    for c in list(cooldown.findall('RemoveValidatorArray')):
        if c.get('value') == 'IsFenixCoopCommander': cooldown.remove(c)
    # Only AdeptFenix uses the new attack set, so the commander check is unnecessary.
    for ident in ('FenixAdeptShadeSpawnShade', 'FenixAdeptShadeSetCooldown'):
        for c in one(eff, ident).findall('ValidatorArray'):
            assert c.get('value') != 'IsFenixCoopCommander'
    # Dead campaign phase-shift controls are not part of the co-op Adept.
    for card in one(un, 'AdeptFenix').findall('CardLayouts'):
        for c in list(card):
            if c.get('AbilCmd') == 'AdeptPhaseShiftCancel,Execute': card.remove(c)

    # Existing support beam must be able to target this mod's uncommandable allies.
    beam = one(ab, 'RM21_VoidSentryChronoBeam')
    for tag in ('TargetFilters', 'AutoCastFilters'):
        c = beam.find(tag)
        assert ',Uncommandable' in c.get('value')
        c.set('value', c.get('value').replace(',Uncommandable', ''))
    zone = one(ab, 'FenixSentryGuardianZone')
    field(zone, 'Flags', '1', index='AutoCast')
    field(zone, 'Flags', '1', index='AutoCastOn')
    field(zone, 'AutoCastRange', '8')
    field(zone, 'AutoCastFilters', 'Visible;Neutral,Enemy,Structure,Missile,Stasis,Dead,Hidden,Invulnerable')
    E.SubElement(zone, 'AutoCastValidatorArray', value='TargetIsFiringWeapon')
    E.SubElement(zone, 'AutoCastValidatorArray', value='RM4_NoGuardianZone')
    add(val, '<CValidatorUnitCompareBehaviorCount id="RM4_NoGuardianZone"><Behavior value="FenixSentryGuardianZone"/><Compare value="EQ"/><Value value="0"/></CValidatorUnitCompareBehaviorCount>')

    # Existing trial kill-XP thresholds stay unchanged: rank 1 shield, rank 3 stim.
    veterancy = one(beh, 'RMK_MengskVeterancyMarauderMengsk')
    levels = veterancy.findall('VeterancyLevelArray')
    assert len(levels) == 4
    levels[1].set('LevelGainEffect', 'MarauderMengskAbsorbAB')
    add(nodes, '<CRequirementCountBehavior id="RM4_AegisRank"><Count Link="RMK_MengskVeterancyMarauderMengsk" State="CompleteOnlyAtUnit"/></CRequirementCountBehavior>')
    for rank, internal in ((1, 2), (3, 4)):
        add(nodes, f'<CRequirementGTE id="RM4_AegisRank{rank}"><OperandArray index="0" value="RM4_AegisRank"/><OperandArray index="1" value="{internal}"/></CRequirementGTE>')
        add(req, f'<CRequirement id="RM4_AegisRank{rank}Use"><NodeArray index="Use" Link="RM4_AegisRank{rank}"/></CRequirement>')
    a = one(ab, 'MarauderMengskAttackSpeedBoost')
    a.find('CmdButtonArray').set('Requirements', 'RM4_AegisRank3Use')
    a.find('CmdButtonArray').set('State', 'Available')
    u = one(un, 'MarauderMengsk')
    E.SubElement(u, 'AbilArray', Link='MarauderMengskAttackSpeedBoost')
    card = u.find('CardLayouts')
    E.SubElement(card, 'LayoutButtons', Face='MarauderMengskShield', Type='Passive', Behavior='MarauderMengskAbsorbReapplicator', Requirements='RM4_AegisRank1Use', Row='1', Column='2')
    E.SubElement(card, 'LayoutButtons', Face='MarauderMengskSlow', Type='Passive', Requirements='HaveMarauderMengskSlow', Row='1', Column='3')
    E.SubElement(card, 'LayoutButtons', Face='MarauderMengskAttackSpeedBoost', Type='AbilCmd', AbilCmd='MarauderMengskAttackSpeedBoost,Execute', Row='2', Column='0')

    # Shrapnel is activated by the existing paid research, not supplied for free.
    shrapnel = one(eff, 'RMA_AegisShrapnelSearch')
    shrapnel.find('AreaArray').set('Radius', '0')
    shrapnel.find('AreaArray').set('Effect', 'RM4_AegisShrapnelHit')
    add(eff, '<CEffectSet id="RM4_AegisShrapnelHit"><EffectArray value="RM4_ShrapnelDamage"/><EffectArray value="MarauderMengskShrapnelSlowAB"/></CEffectSet>')
    E.SubElement(one(up, 'RM4_Shrapnel'), 'EffectArray', Reference='Effect,RMA_AegisShrapnelSearch,AreaArray[0].Radius', Value='3')
    for actor in cat('actordata'):
        for on in actor.findall('On'):
            terms = on.get('Terms', '')
            if 'Effect.RMA_AegisShrapnelSearch.Start' in terms and 'ValidateEffect' not in terms:
                on.set('Terms', terms + '; ValidateEffect RM4_HaveShrapnel')

    # Restore the actual co-op slowing research, with no commander-level lock.
    add(nodes, '<CRequirementCountUpgrade id="RM4_AegisSlowQueued"><Count Link="MarauderMengskSlow" State="QueuedOrBetter"/></CRequirementCountUpgrade>')
    add(nodes, '<CRequirementNot id="RM4_AegisSlowNotQueued"><OperandArray index="0" value="RM4_AegisSlowQueued"/></CRequirementNot>')
    add(nodes, '<CRequirementAnd id="RM4_AegisSlowShow"><OperandArray value="RM4_HaveHammer"/><OperandArray value="RM4_AegisSlowNotQueued"/></CRequirementAnd>')
    add(req, '<CRequirement id="RM4_AegisSlowLearn"><NodeArray index="Show" Link="RM4_AegisSlowShow"/></CRequirement>')
    research = one(ab, 'RM3_TechResearch')
    assert research.find("InfoArray[@index='Research17']") is None
    info = E.SubElement(research, 'InfoArray', index='Research17', Time='60', Upgrade='MarauderMengskSlow')
    for res in ('Minerals', 'Vespene'): E.SubElement(info, 'Resource', index=res, value='100')
    E.SubElement(info, 'Button', DefaultButtonFace='MarauderMengskSlowResearch', State='Available', Requirements='RM4_AegisSlowLearn')
    card = one(un, 'BarracksTechLab').find("CardLayouts[@CardId='RMC1']")
    E.SubElement(card, 'LayoutButtons', Face='MarauderMengskSlowResearch', Type='AbilCmd', AbilCmd='RM3_TechResearch,Research17', Row='1', Column='0')
    # Explicit owner for the restored effect validator.
    E.SubElement(one(val, 'HaveMarauderMengskSlow'), 'WhichPlayer', Value='Caster')

    # Gate cards retain their original shared ability; update faces for player 8
    # in the script, preventing enemy Warp Gate UI changes.
    add(buttons, '<CButton id="RM4_WarpAdept"><Icon value="Assets\\Textures\\btn-unit-protoss-adeptfenix-purifier.dds"/></CButton>')
    add(buttons, '<CButton id="RM4_WarpEnergizer"><Icon value="Assets\\Textures\\btn-unit-protoss-sentry-purifier.dds"/></CButton>')
    for name in changed:
        E.indent(cats[name])
        files[GD + name + '.xml'] = E.tostring(cats[name], encoding='utf-8', xml_declaration=True)


STRINGS = {
    'Weapon/Name/RM4_AdeptFenixWeapon': '공명포 /// Resonance Glaives',
    'Unit/Name/FenixAdeptShade': '사이오닉 분신 /// Psionic Projection',
    'Unit/Name/FenixAdeptShadeWeapon': '사이오닉 분신 투사체 /// Psionic Projection Missile',
    'Weapon/Name/FenixAdeptShade': '공명포 /// Resonance Glaives',
    'Behavior/Name/FenixAdeptShadeSpawnShadTimedLife': '사이오닉 분신 /// Psionic Projection',
    'Behavior/Name/MarauderMengskAbsorb': '보호막 /// Barrier',
    'Behavior/Name/MarauderMengskAbsorbReapplicator': '보호막 재충전 /// Barrier Recharge',
    'Behavior/Name/MarauderMengskAttackSpeedBoost': '황제의 자극제 /// Royal Stimpack',
    'Behavior/Name/MarauderMengskShrapnelSlow': '불곰 감속탄 /// Super Concussive Shells',
    'Button/Name/MarauderMengskAttackSpeedBoost': '황제의 자극제 /// Royal Stimpack',
    'Button/Tooltip/MarauderMengskAttackSpeedBoost': '이지스 근위대 3등급에 해금됩니다. 10초 동안 공격 속도가 200% 증가합니다. 재사용 대기시간 30초. /// Unlocked at Aegis Guard rank 3. Increases attack speed by 200% for 10 seconds. Cooldown: 30 seconds.',
    'Button/Tooltip/MarauderMengskShield': '이지스 근위대 1등급에 해금됩니다. 피해 300을 흡수하는 보호막을 얻습니다. 재충전 대기시간 60초. /// Unlocked at Aegis Guard rank 1. Grants a barrier absorbing 300 damage, with a 60-second recharge.',
    'Button/Name/MarauderMengskSlowResearch': '불곰 감속탄 연구 /// Research Super Concussive Shells',
    'Button/Tooltip/MarauderMengskSlowResearch': '이지스 근위대의 공격이 대상의 이동 속도를 3초 동안 60% 감소시킵니다. 파편탄을 연구하면 파편에 맞은 적에게도 적용됩니다. /// Aegis Guard attacks slow targets by 60% for 3 seconds. Also affects shrapnel targets after Shrapnel Shells is researched.',
    'Button/Tooltip/RM4_Shrapnel': '망치 경호대와 이지스 근위대의 공격이 대상 뒤 부채꼴 범위에 파편 피해 4를 줍니다. 중장갑 상대 추가 피해 4. /// Hammer Security and Aegis Guard attacks deal 4 shrapnel damage in a cone behind the target, plus 4 versus armored units.',
    'Button/Name/RM4_WarpAdept': '사도 소환 /// Warp In Adept',
    'Button/Tooltip/RM4_WarpAdept': '피닉스 사도입니다. 지상 및 공중 유닛을 공격합니다. 사거리 5. 사이오닉 분신 연구 효과가 적용됩니다. /// Fenix Adept. Attacks ground and air at range 5. Receives Psionic Projection research.',
    'Button/Name/RM4_WarpEnergizer': '동력기 소환 /// Warp In Energizer',
    'Button/Tooltip/RM4_WarpEnergizer': '시간 광선으로 아군의 공격 속도와 이동 속도를 높입니다. /// Uses Chrono Beam to increase allied attack and movement speed.',
}


def script_patch(data):
    text = data.decode('utf-8')
    marker = 'void gf_m4_Mercs () {'
    assert text.count(marker) == 1
    # This function has no local declarations in the pinned 0.4.63 input.
    offset = text.index(marker) + len(marker) + 1
    grant = ('    // 0.4.64: mission research gates the mercenary abilities, not Hyperion command availability.\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("RM4_MercStimpack",0),true);\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("SuperStimpackMarine",0),true);\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("RMK_MarineMengskAttackSpeedBoost",0),true);\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("MarauderMengskAttackSpeedBoost",0),true);\n'
             '    TechTreeUpgradeAllow(1,"MarauderMengskSlow",true);\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",16),true);\n')
    text = text[:offset] + grant + text[offset:]
    marker = '    CatalogLinkReplace(8,c_gameCatalogUnit,"Stalker","AdeptFenix");'
    assert text.count(marker) == 1
    text = text.replace(marker, marker + '\n'
        '    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[Train2].Button.DefaultButtonFace",8,"RM4_WarpAdept");\n'
        '    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[Train6].Button.DefaultButtonFace",8,"RM4_WarpEnergizer");\n'
        '    CatalogFieldValueSet(c_gameCatalogUnit,"WarpGate","CardLayouts[0].LayoutButtons[1].Face",8,"RM4_WarpAdept");\n'
        '    CatalogFieldValueSet(c_gameCatalogUnit,"WarpGate","CardLayouts[0].LayoutButtons[6].Face",8,"RM4_WarpEnergizer");')
    return text.encode('utf-8')


def update_lines(data, additions):
    t = data.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in t else '\n'
    lines = t.splitlines()
    seen = set()
    for i, line in enumerate(lines):
        k = line.split('=', 1)[0]
        if k in additions:
            lines[i] = k + '=' + additions[k]
            seen.add(k)
    lines.extend(k + '=' + v for k, v in additions.items() if k not in seen)
    return (nl.join(lines) + nl).encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        patch_catalogs(files)
        files[M4 + 'mapscript.galaxy'] = script_patch(files[M4 + 'mapscript.galaxy'])
        for loc in ('kokr',) + LOCALES:
            p = M4 + loc + '.sc2data/localizeddata/'
            values = STRINGS if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in STRINGS.items()}
            files[p + 'gamestrings.txt'] = update_lines(files[p + 'gamestrings.txt'], values)
            files[p + 'gamehotkeys.txt'] = update_lines(files[p + 'gamehotkeys.txt'], {
                'Button/Hotkey/RM4_WarpAdept': 'A', 'Button/Hotkey/RM4_WarpEnergizer': 'E',
                'Button/Hotkey/MarauderMengskSlowResearch': 'G', 'Button/Hotkey/MarauderMengskAttackSpeedBoost': 'T',
            })
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        assert set(files) == set(prev.namelist())
        for n in files:
            if n != 'metadata.txt' and not n.startswith(M4): assert files[n] == prev.read(n), n
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    build(a.source, a.output)
