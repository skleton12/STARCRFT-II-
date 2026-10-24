#!/usr/bin/env python3
"""Check full-tier mercenary stats and actual infantry upgrade effect references."""
import sys
import zipfile
import xml.etree.ElementTree as E

GD='TTychus01.SC2Map/base.sc2data/gamedata/'

def check(z):
    def records(f):return {e.get('id'):e for e in E.fromstring(z.read(GD+f+'.xml')) if e.get('id')}
    un,beh,up,eff,nodes=(records(f) for f in ['unitdata','behaviordata','upgradedata','effectdata','requirementnodedata'])
    for uid,life,armor,food,damage in [('RMK_MarineMengsk',250,3,2,1),('MarauderMengsk',525,4,4,0.75)]:
        u=un[uid];rank='RMK_MengskVeterancy'+('MarineMengsk' if uid=='RMK_MarineMengsk' else 'MarauderMengsk')
        for tag in ['LifeStart','LifeMax']:assert float(u.find(tag).get('value'))==life,(uid,tag)
        assert float(u.find('LifeArmor').get('value'))==armor
        assert float(u.find('Food').get('value'))==-food
        assert u.find(f"BehaviorArray[@Link='{rank}']") is not None
        assert beh[rank].tag=='CBehaviorBuff' and not beh[rank].findall('VeterancyLevelArray')
        for kind in ['Melee','Ranged','Splash']:
            assert float(beh[rank].find(f"Modification/DamageDealtFraction[@index='{kind}']").get('value'))==damage
    # 0.4.92: the co-op absorb buff became real 300 shields (user choice); the barrier must exist in one form only.
    aegis=un['MarauderMengsk']
    if aegis.find('ShieldsMax') is not None:
        assert float(aegis.find('ShieldsMax').get('value'))==300 and aegis.find("BehaviorArray[@Link='MarauderMengskAbsorb']") is None
    else:
        assert aegis.find("BehaviorArray[@Link='MarauderMengskAbsorb']") is not None
    for nid in ['RM4_AegisRank1','RM4_AegisRank3','RMK_GTECountBehaviorMengskVeterancyMarineMengskCompleteOnlyAtUnit2','RMK_GTECountBehaviorMengskVeterancyMarineMengskCompleteOnlyAtUnit4']:
        assert nodes[nid].find("OperandArray[@index='1']").get('value')=='1'
    def increment(template,ref):
        found=[e for e in up[template].findall('EffectArray') if e.get('Reference')==ref]
        assert len(found)==1,(template,ref,len(found))
        return float(found[0].get('Value'))
    # Check all 0..3 upgrade stages and exact Aegis shrapnel/main ratio.
    for level in range(4):
        for uid in ['RMK_MarineMengsk','MarauderMengsk']:
            armor=float(un[uid].find('LifeArmor').get('value'))
            armor+=level*increment('TerranInfantryArmors',f'Unit,{uid},LifeArmor')
            assert armor==(3 if uid=='RMK_MarineMengsk' else 4)+level
        for main_id in ['RMK_MarineMengskGaussRifleDamage','RMK_MarineMengskGaussRifleDamageUpgrade']:
            main=(float(eff[main_id].find('Amount').get('value'))+level*increment('TerranInfantryWeapons',f'Effect,{main_id},Amount'))*2
            assert main==(11+level)*2
        main=(20+level*increment('TerranInfantryWeapons','Effect,PunisherGrenadesMengskU,Amount'))*1.75
        shard=(4+level*increment('TerranInfantryWeapons','Effect,RM4_AegisEliteShrapnelDamage,Amount'))*1.75
        assert abs(shard/main-0.2)<1e-8
        main_armored=main+(20+level*increment('TerranInfantryWeapons','Effect,PunisherGrenadesMengskU,AttributeBonus[Armored]'))*1.75
        shard_armored=shard+(4+level*increment('TerranInfantryWeapons','Effect,RM4_AegisEliteShrapnelDamage,AttributeBonus[Armored]'))*1.75
        assert abs(shard_armored/main_armored-0.2)<1e-8
    assert eff['RM4_AegisShrapnelHit'].find("EffectArray[@value='RM4_AegisEliteShrapnelDamage']") is not None
    for i,buff in enumerate(['Stimpack','SuperStim','RMK_MarineMengskAttackSpeedBoost']):
        e=eff[f'RM4_StimRemove{i}']
        assert e.find('BehaviorLink').get('value')==buff
        assert e.find('Behavior') is None
        assert 'Veterancy' not in e.find('BehaviorLink').get('value')
    s=z.read('TTychus01.SC2Map/mapscript.galaxy').decode()
    assert 'UnitXPAddXP' not in s and 'gt_m4_GuardXP' not in s
    # Ordinary mercs and legacy enemies retain their existing values.
    assert un['WarPig'].find("BehaviorArray[@Link='RMK_MengskVeterancyMarineMengsk']") is None
    a=records('abildata')['SummonMercenaries']
    batches={idx:sum(1 for row in a.findall('InfoArray') if row.get('index')==idx for c in row.findall('Unit')) for idx in ['Train1','Train4']}
    assert batches=={'Train1':4,'Train4':2}
    assert batches['Train1']*2==8 and batches['Train4']*4==8

if __name__=='__main__':
    with zipfile.ZipFile(sys.argv[1]) as z:check(z)
    print('PASS: rank-3 stats, starting shield, rank abilities, infantry upgrades 0..3, shrapnel 20%, supply per hire, XP removed')
