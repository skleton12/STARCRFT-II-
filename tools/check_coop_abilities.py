#!/usr/bin/env python3
"""0.4.64 regression checks, including purchase/research/rank state matrices.

Checks data and script connections, not SC2 engine execution or asset rendering.
"""
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'


def check(z):
    cats = {}
    for name in z.namelist():
        if name.startswith(GD) and name.endswith('.xml'):
            r = E.fromstring(z.read(name))
            cats[Path(name).stem] = {e.get('id'): e for e in r if e.get('id')}
    ab, un, req, nodes, eff, beh, val, up, weap = (cats[n] for n in (
        'abildata','unitdata','requirementdata','requirementnodedata','effectdata',
        'behaviordata','validatordata','upgradedata','weapondata'))
    def v(e, field): return e.find(field).get('value')
    def evaluate(link, levels, ranks=None):
        if link.isdigit(): return int(link)
        e = nodes[link]
        if e.tag == 'CRequirementCountUpgrade': return levels.get(e.find('Count').get('Link'), 0)
        if e.tag == 'CRequirementCountBehavior': return (ranks or {}).get(e.find('Count').get('Link'), 0)
        children = e.findall('OperandArray')
        if e.tag in ('CRequirementNot', 'CRequirementGTE'):
            assert [x.get('index') for x in children] == [str(i) for i in range(len(children))]
        else: assert all(x.get('index') is None for x in children)
        values = [evaluate(x.get('value'), levels, ranks) for x in children]
        if e.tag == 'CRequirementNot': return not values[0]
        if e.tag == 'CRequirementAnd': return all(values)
        if e.tag == 'CRequirementOr': return any(values)
        if e.tag == 'CRequirementGTE': return values[0] >= values[1]
        raise AssertionError(e.tag)
    def usable(ident, levels, ranks=None):
        return all(evaluate(x.get('Link'), levels, ranks) for x in req[ident].findall('NodeArray'))

    # Purchase and mission research independently unlock stage 1; stages replace it.
    assert 'RM4_MercStimpack' in ab, 'mercenary ability still inherits campaign restriction'
    for purchased in (0, 1):
        for stage in range(4):
            levels = {'MarineStimpack': purchased}
            for i in range(1, stage + 1): levels[f'RM3_Stim{i}'] = 1
            if purchased: levels['RM3_Stim1'] = 1  # existing one-shot start grant
            active = [i for i in range(1, 4) if usable(f'RM3_Stim{i}Use', levels)]
            expected = max(stage, purchased)
            assert active == ([expected] if expected else []), (purchased, stage, active)
    stages = [('RM4_MercStimpack','RM4_MercStimSet','Stimpack'),
              ('SuperStimpackMarine','RM4_MercSuperStimSet','SuperStimpackMarine'),
              ('RMK_MarineMengskAttackSpeedBoost','RM4_MercRoyalStimSet','RMK_MarineMengskAttackSpeedBoostAB')]
    for ability, setid, target in stages:
        assert ab[ability].find('CmdButtonArray').get('State') == 'Available'
        assert v(ab[ability], 'Effect') == setid
        links = [e.get('value') for e in eff[setid].findall('EffectArray')]
        assert links == ['RM4_StimRemove0','RM4_StimRemove1','RM4_StimRemove2',target]
    for uid in ('WarPig','HammerSecurity','RMK_MarineMengsk'):
        assert un[uid].find("AbilArray[@Link='RM4_MercStimpack']") is not None
        assert un[uid].find("AbilArray[@Link='Stimpack'][@removed='1']") is not None
        assert any(e.get('AbilCmd') == 'RM4_MercStimpack,Execute' for e in un[uid].iter('LayoutButtons'))

    w = weap[un['AdeptFenix'].find('WeaponArray').get('Link')]
    assert v(w,'Range') == '5'
    assert v(w,'TargetFilters') == 'Visible;Missile,Stasis,Dead,Hidden,Invulnerable'
    assert v(w,'Effect') == 'AdeptLMSet'
    assert v(weap['Adept'],'Range') == '4', 'shared weapon must remain unchanged'
    assert [x.get('value') for x in eff['AdeptLMSet'].findall('EffectArray')] == ['AdeptLM','FenixAdeptShadeSpawnShade','FenixAdeptShadeSetCooldown']
    for ident in ('FenixAdeptShadeSpawnShade','FenixAdeptShadeSetCooldown'):
        validators = [c.get('value') for c in eff[ident].findall('ValidatorArray')]
        assert 'IsFenixCoopCommander' not in validators
        assert 'FenixAdeptShadeNotOnCooldown' in validators and 'HaveAdeptFenixShadeSpawn' in validators
    assert not usable('HaveAdeptFenixShadeSpawn', {})
    assert usable('HaveAdeptFenixShadeSpawn', {'AdeptFenixShadeSpawn':1})
    assert v(beh['FenixAdeptShadeSpawnShadTimedLife'],'Duration') == '5'
    assert v(beh['FenixAdeptShadeSpawnShadTimedLife'],'ExpireEffect') == 'TimedLifeFate'
    for tag in ('TargetFilters','AutoCastFilters'):
        assert 'Uncommandable' not in v(ab['RM21_VoidSentryChronoBeam'], tag)
    for flag in ('AutoCast','AutoCastOn'):
        assert ab['FenixSentryGuardianZone'].find(f"Flags[@index='{flag}']").get('value') == '1'

    # Rank boundaries: new units start at internal level 1 (displayed rank 0).
    rankid = 'RMK_MengskVeterancyMarauderMengsk'
    if beh[rankid].tag == 'CBehaviorVeterancy':
        for rank in range(4):
            r = {rankid: rank + 1}
            assert usable('RM4_AegisRank1Use', {}, r) == (rank >= 1)
            assert usable('RM4_AegisRank3Use', {}, r) == (rank >= 3)
        levels = beh[rankid].findall('VeterancyLevelArray')
        assert [l.get('MinVeterancyXP') for l in levels] == [None,'1200','2400','3600']
        assert levels[1].get('LevelGainEffect') == 'MarauderMengskAbsorbAB'
    else:
        assert beh[rankid].tag == 'CBehaviorBuff'
        assert usable('RM4_AegisRank1Use', {}, {rankid:1})
        assert usable('RM4_AegisRank3Use', {}, {rankid:1})
        assert un['MarauderMengsk'].find("BehaviorArray[@Link='MarauderMengskAbsorb']") is not None
    assert beh['MarauderMengskAbsorb'].find('DamageResponse/ModifyLimit').get('value') == '300'
    assert v(beh['MarauderMengskAbsorbReapplicator'],'Duration') == '60'
    assert v(beh['MarauderMengskAbsorbReapplicator'],'ExpireEffect') == 'MarauderMengskAbsorbAB'
    assert ab['MarauderMengskAttackSpeedBoost'].find('CmdButtonArray').get('Requirements') == 'RM4_AegisRank3Use'
    assert beh['MarauderMengskAttackSpeedBoost'].find('Modification').get('AttackSpeedMultiplier') == '3'
    assert eff['RMA_AegisShrapnelSearch'].find('AreaArray').get('Radius') == '0'
    increments = [e for e in up['RM4_Shrapnel'].findall('EffectArray') if e.get('Reference') == 'Effect,RMA_AegisShrapnelSearch,AreaArray[0].Radius']
    assert len(increments) == 1 and increments[0].get('Value') == '3'
    for researched in (0, 1):
        assert usable('HaveMarauderMengskSlow', {'MarauderMengskSlow': researched}) == bool(researched)
    assert val['HaveMarauderMengskSlow'].find('WhichPlayer').get('Value') == 'Caster'
    slow = ab['RM3_TechResearch'].find("InfoArray[@index='Research17']")
    assert slow.get('Upgrade') == 'MarauderMengskSlow' and slow.get('Time') == '60'
    assert [r.get('value') for r in slow.findall('Resource')] == ['100', '100']
    assert not usable('RM4_AegisSlowLearn', {})
    assert usable('RM4_AegisSlowLearn', {'RM4_HammerUnlocked':1})
    assert not usable('RM4_AegisSlowLearn', {'RM4_HammerUnlocked':1,'MarauderMengskSlow':1})

    script = z.read(M4+'mapscript.galaxy').decode()
    body = script.split('void gf_m4_Mercs () {',1)[1].split('\n}\n',1)[0]
    for ability, _, _ in stages:
        assert f'TechTreeAbilityAllow(1,AbilityCommand("{ability}",0),true);' in body
    assert 'TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",16),true);' in body
    assert 'if (gf_m4_Unl(k) || k==6) { gv_m4_warpSlot' in script
    assert 'CatalogLinkReplace(8,c_gameCatalogUnit,"Sentry","RM21_Energizer");' in script
    assert 'gf_m4_Grant(-1,"AdeptFenixShadeSpawn");' in script
    assert 'TechTreeUpgradeAddLevel(1,"MarauderMengskSlow"' not in script
    assert 'TechTreeUpgradeAddLevel(1,"RM4_Shrapnel"' not in script
    assert z.testzip() is None


if __name__ == '__main__':
    with zipfile.ZipFile(sys.argv[1]) as z: check(z)
    print('PASS: purchase/research/rank matrices, ability/effect links, support production and autocasts, CRC')
