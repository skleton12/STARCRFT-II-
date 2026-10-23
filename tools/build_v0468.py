#!/usr/bin/env python3
"""0.4.67 -> 0.4.68: rank-3 mercenaries at hire, infantry upgrades, co-op supply.

Mission 4: Korhal supply 2 (mod value), Aegis supply 4 (Mengsk original).
Replace veterancy with permanent fixed buffs, bake rank vitality/armor/sight/range
into units, and remove shared-XP script. Paid mission research remains separate.
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path
from build_v0464 import LOCALES, update_lines

M4='TTychus01.SC2Map/'
GD=M4+'base.sc2data/gamedata/'
OLD,NEW=b'version=0.4.67',b'version=0.4.68'
MARINE='RMK_MarineMengsk'
AEGIS='MarauderMengsk'
RANKS={MARINE:'RMK_MengskVeterancyMarineMengsk',AEGIS:'RMK_MengskVeterancyMarauderMengsk'}

def one(root,i):
    found=[e for e in root if e.get('id')==i]
    assert len(found)==1,(i,len(found))
    return found[0]

def setval(el,tag,value):
    c=el.find(tag)
    if c is None:c=E.SubElement(el,tag)
    c.set('value',str(value))

def script(data):
    t=data.decode('utf-8')
    a=t.index('// 0.4.65: Mengsk co-op kill XP sharing')
    b=t.index('void gf_m4_Init () {',a)
    t=t[:a]+t[b:]
    reg='    t=TriggerCreate("gt_m4_GuardXP_Func");\n    TriggerAddEventUnitDied(t,null);\n'
    assert t.count(reg)==1
    t=t.replace(reg,'')
    assert 'UnitXPAddXP' not in t
    return t.encode('utf-8')

def patch_catalogs(files):
    cats={f:E.fromstring(files[GD+f+'.xml']) for f in ['unitdata','behaviordata','effectdata','weapondata','requirementnodedata','upgradedata','buttondata']}
    un,beh,eff,weapon,nodes,up,buttons=(cats[n] for n in cats)
    # Convert the two existing stable behavior IDs to buffs; no XP or level changes.
    for uid,rank in RANKS.items():
        old=one(beh,rank)
        assert old.tag=='CBehaviorVeterancy'
        levels=old.findall('VeterancyLevelArray')
        assert len(levels)==4
        life=sum(float(m.find("VitalMaxArray[@index='Life']").get('value')) for l in levels[1:] for m in l.findall('Modification'))
        armor=sum(float(m.find('LifeArmorBonus').get('value')) for l in levels[1:] for m in l.findall('Modification'))
        damage=sum(float(m.find("DamageDealtFraction[@index='Ranged']").get('value')) for l in levels[1:] for m in l.findall('Modification'))
        u=one(un,uid)
        base_life=float(u.find('LifeMax').get('value'))
        base_armor=float(u.find('LifeArmor').get('value')) if u.find('LifeArmor') is not None else 0
        for tag in ['LifeStart','LifeMax']:setval(u,tag,f'{base_life+life:g}')
        setval(u,'LifeArmor',f'{base_armor+armor:g}')
        setval(u,'Food','-2' if uid==MARINE else '-4')
        setval(u,'RankDisplay','Never')
        for tag in ['DamageDealtXP','DamageTakenXP']:setval(u,tag,'0')
        buff=E.Element('CBehaviorBuff',id=rank)
        E.SubElement(buff,'BehaviorFlags',index='Permanent',value='1')
        E.SubElement(buff,'MaxStackCount',value='1')
        E.SubElement(buff,'InfoIcon',value='Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel3.dds')
        mod=E.SubElement(buff,'Modification')
        for kind in ['Melee','Ranged','Splash']:E.SubElement(mod,'DamageDealtFraction',index=kind,value=f'{damage:g}')
        if uid==MARINE:
            # Preserve the former rank-1 bonuses and rank-3 Heroic attribute.
            setval(u,'Sight',str(int(float(u.find('Sight').get('value')))+2))
            E.SubElement(mod,'StateFlags',index='UnitAttrOnHeroic',value='1')
            w=one(weapon,'RMK_MarineMengskGaussRifle')
            assert w.find('Range') is None  # Core default range 5 + rank bonus 1.
            setval(w,'Range','6');setval(w,'MinScanRange','6.5')
        else:
            # Shield must exist immediately, without a rank-up event.
            assert u.find("BehaviorArray[@Link='MarauderMengskAbsorb']") is None
            E.SubElement(u,'BehaviorArray',Link='MarauderMengskAbsorb')
            E.SubElement(u.find('CardLayouts'),'LayoutButtons',Face='RMK_MarineMengskVeterancy',Type='Passive',Row='1',Column='0')
        beh.remove(old);beh.append(buff)
    # Existing rank-gated passive/active abilities now require one fixed elite buff.
    counts={e.get('id') for e in nodes if e.tag=='CRequirementCountBehavior' and e.find('Count') is not None and e.find('Count').get('Link') in RANKS.values()}
    for e in nodes:
        if e.tag=='CRequirementGTE' and e.find("OperandArray[@index='0']") is not None and e.find("OperandArray[@index='0']").get('value') in counts:
            e.find("OperandArray[@index='1']").set('value','1')
    # Dedicated Aegis shrapnel preserves 20% scaling without changing Hammer Security.
    shrapnel=copy.deepcopy(one(eff,'RM4_ShrapnelDamage'))
    shrapnel.set('id','RM4_AegisEliteShrapnelDamage');eff.append(shrapnel)
    hit=one(eff,'RM4_AegisShrapnelHit')
    hit.find("EffectArray[@value='RM4_ShrapnelDamage']").set('value',shrapnel.get('id'))
    # Core RemoveBehavior uses BehaviorLink. Only remove the named stim buffs.
    for i,buffid in enumerate(['Stimpack','SuperStim','RMK_MarineMengskAttackSpeedBoost']):
        remove=one(eff,f'RM4_StimRemove{i}')
        old=remove.find('Behavior')
        assert old is not None and old.get('value')==buffid
        remove.remove(old)
        E.SubElement(remove,'BehaviorLink',value=buffid)
    # All three normal infantry upgrades inherit these base upgrade templates.
    for upgrade,refs in {
        'TerranInfantryWeapons':[
            ('Effect,RMK_MarineMengskGaussRifleDamage,Amount','1'),
            ('Effect,RMK_MarineMengskGaussRifleDamageUpgrade,Amount','1'),
            ('Weapon,RMK_MarineMengskGaussRifle,Level','1'),
            ('Effect,PunisherGrenadesMengskU,Amount','1'),
            ('Effect,PunisherGrenadesMengskU,AttributeBonus[Armored]','1'),
            ('Weapon,PunisherGrenadesMengsk,Level','1'),
            ('Effect,RM4_AegisEliteShrapnelDamage,Amount','0.2'),
            ('Effect,RM4_AegisEliteShrapnelDamage,AttributeBonus[Armored]','0.2')],
        'TerranInfantryArmors':[(f'Unit,{uid},{field}','1') for uid in RANKS for field in ['LifeArmor','LifeArmorLevel']],
    }.items():
        assert not any(e.get('id')==upgrade for e in up)
        e=E.SubElement(up,'CUpgrade',id=upgrade)
        for ref,value in refs:E.SubElement(e,'EffectArray',Reference=ref,Value=value)
    for level in range(1,4):
        for family in ['Weapons','Armors']:
            ident=f'TerranInfantry{family}Level{level}'
            e=next((e for e in up if e.get('id')==ident),None)
            if e is None:e=E.SubElement(up,'CUpgrade',id=ident)
            if family=='Armors':
                for uid in RANKS:
                    E.SubElement(e,'EffectArray',Operation='Set',Reference=f'Actor,{uid},LifeArmorIcon',Value=f'Assets\\Textures\\btn-upgrade-terran-infantryarmorlevel{level}.dds')
            else:
                for wid in ['RMK_MarineMengskGaussRifle','PunisherGrenadesMengsk']:
                    E.SubElement(e,'EffectArray',Operation='Set',Reference=f'Weapon,{wid},Icon',Value=f'Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel{level}.dds')
    # Current technologies already cover Korhal shield/range/stim. Aegis receives
    # the matching Marauder vitality research as well as its own slow/shrapnel.
    foam=next((e for e in up if e.get('id')=='MarauderLifeBoost'),None)
    if foam is None:foam=E.SubElement(up,'CUpgrade',id='MarauderLifeBoost')
    for field in ['LifeStart','LifeMax']:
        E.SubElement(foam,'EffectArray',Reference=f'Unit,{AEGIS},{field}',Value='25')
    for name,r in cats.items():files[GD+name+'.xml']=E.tostring(r,encoding='utf-8',xml_declaration=True)

STRINGS={
    'Button/Name/RMK_MarineMengskVeterancy':'3등급 정예 용병 /// Rank 3 Elite Mercenary',
    'Button/Tooltip/RMK_MarineMengskVeterancy':'처음부터 3등급 능력치와 진급 능력을 갖고 소환됩니다. 경험치 성장은 없습니다. 보병 공격력·방어력과 해당 유닛의 미션 연구가 적용됩니다. /// Hired with rank 3 stats and rank abilities. Does not gain experience. Receives infantry weapon and armor upgrades and applicable mission research.',
    'Behavior/Name/RMK_MengskVeterancyMarineMengsk':'3등급 코랄의 후예 /// Rank 3 Heir of Korhal',
    'Behavior/Name/RMK_MengskVeterancyMarauderMengsk':'3등급 이지스 근위대 /// Rank 3 Aegis Guard',
    'Button/Tooltip/RM3_HireKorhal':'3등급 코랄의 후예 4기를 고용합니다. 기당 인구 2, 총 인구 8. 보병 공방업과 해당 미션 연구가 적용됩니다. /// Hires 4 rank 3 Heirs of Korhal. 2 supply each, 8 total. Receives infantry weapon/armor upgrades and applicable mission research.',
    'Button/Tooltip/HireHammerSecurities':'3등급 이지스 근위대 2기를 고용합니다. 기당 인구 4, 총 인구 8. 보호막과 황제의 자극제를 처음부터 사용할 수 있습니다. /// Hires 2 rank 3 Aegis Guards. 4 supply each, 8 total. Barrier and Royal Stimpack are available immediately.',
    'Button/Tooltip/MarauderMengskAttackSpeedBoost':'3등급 이지스 근위대의 황제의 자극제입니다. 10초 동안 공격 속도가 200% 증가합니다. 재사용 대기시간 30초. /// Rank 3 Aegis Guard Royal Stimpack. Attack speed +200% for 10 seconds. Cooldown: 30 seconds.',
    'Button/Tooltip/MarauderMengskShield':'처음부터 피해 300을 흡수하는 보호막을 갖습니다. 재충전 대기시간 60초. /// Starts with a barrier absorbing 300 damage. Recharge: 60 seconds.',
}

def build(source,output):
    if output.exists():raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files={n:prev.read(n) for n in prev.namelist()}
        patch_catalogs(files);files[M4+'mapscript.galaxy']=script(files[M4+'mapscript.galaxy'])
        for loc in ('kokr',)+LOCALES:
            path=M4+loc+'.sc2data/localizeddata/gamestrings.txt'
            values=STRINGS if loc=='kokr' else {k:v.split(' /// ',1)[1] for k,v in STRINGS.items()}
            files[path]=update_lines(files[path],values)
        files['metadata.txt']=files['metadata.txt'].replace(OLD,NEW)
        for n in files:
            if n!='metadata.txt' and not n.startswith(M4):assert files[n]==prev.read(n)
        output.parent.mkdir(parents=True,exist_ok=True)
        try:
            with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():out.writestr(copy.copy(info),files[info.filename])
            with zipfile.ZipFile(output) as out:assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True);raise
    print(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();build(a.source,a.output)
