#!/usr/bin/env python3
"""GPT 0.4.69 (codex/coop-fixes-0464, bebfbde) 를 Claude 0.4.76 위에 다시 적용한 판 = 0.4.77.
번호 충돌(Claude 0.4.69 = 제로 아워 코랄 3등급)로 파일 이름·버전만 바꿨고 내용은 GPT 원본 그대로.

0.4.68 -> 0.4.69: complete Purifier weapon/armor/shield upgrade coverage.

Mission 4. Keep original upgrade inheritance and add only missing references.
Air upgrades match Raynor infantry levels; shield armor matches infantry armor.
Original increments: pinned SC2GameData 6dd323aae4209a01f110719a00b4e8f7a88389bc.
Source dependency XML is also required by check_release.py.
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
DEPS=['core.sc2mod','liberty.sc2mod','liberty.sc2campaign','libertystory.sc2campaign']
M4='TTychus01.SC2Map/'
GD=M4+'base.sc2data/gamedata/'
OLD,NEW=b'version=0.4.76',b'version=0.4.77'
GROUND=['Probe','ZealotPurifier','AdeptFenix','RM21_Energizer','StalkerPurifier','Immortal','ColossusPurifier','Disruptor','SentryFenix','SentryFenixPhasing']
AIR=['PhoenixPurifier','Scout','TempestPurifier','Carrier','Interceptor']
GW={
 'PsiBlades':('PsiBlades',1), 'ParticleDisruptors':('ParticleDisruptorsU',1),
 'PhaseDisruptors':('PhaseDisruptors',2),
 'RM4_AdeptFenixWeapon':('AdeptDamage',1), 'FenixAdeptShade':('FenixAdeptShadeDamage',1),
 'RM21_EnergizerWeapon':('RM21_SanitizationBeamDamage',1),
 'EnergizerWeapon':('SanitizationBeamDamage',1),
 'ColossusPurifierThermalLances':('ColossusPurifierThermalLancesDamage',2),
 'DisruptorPsiBlast':('DisruptorWeaponU',1),
}
AW={
 'ArtanisIonCannons':('ArtanisIonCannonsU',1), 'IonCannons':('IonCannonsU',1),
 'ScoutGround':('ScoutGround',1), 'ScoutAir':('ScoutAirU',1),
 'TempestPurifier':('TempestPurifierDamage',5),
 'TempestPurifierGround':('TempestPurifierDamageGround',5),
 'InterceptorBeam':('InterceptorBeamDamage',1),
}

def dependency_records(filename):
    result={}
    for layer in DEPS:
        f=ROOT/'source'/layer/'base.sc2data/gamedata'/filename
        assert f.exists(),f
        for e in E.parse(f).getroot():
            if e.get('id'):result.setdefault(e.get('id'),[]).append(e)
    return result

def effective_effects(records,ident,seen=()):
    assert ident not in seen,ident
    entries=records.get(ident,[])
    parent=next((e.get('parent') for e in reversed(entries) if e.get('parent')),None)
    out=effective_effects(records,parent,seen+(ident,)) if parent else []
    return out+[c for e in entries for c in e.findall('EffectArray')]

def required(family):
    refs={}
    if family in ['GroundArmors','AirArmors','Shields']:
        units=GROUND if family=='GroundArmors' else AIR if family=='AirArmors' else GROUND+AIR
        stat='ShieldArmor' if family=='Shields' else 'LifeArmor'
        for uid in units:
            for field in [stat,stat+'Level']:refs[f'Unit,{uid},{field}']=1
    else:
        weapons=GW if family=='GroundWeapons' else AW
        for wid,(damage,inc) in weapons.items():
            refs[f'Weapon,{wid},Level']=1
            refs[f'Effect,{damage},Amount']=inc
        if family=='GroundWeapons':
            refs['Effect,AdeptDamage,AttributeBonus[Light]']=1
            refs['Effect,PhaseDisruptors,AttributeBonus[Armored]']=3
        else:
            for eid in ['ArtanisIonCannonsULeft','ArtanisIonCannonsURight']:refs[f'Effect,{eid},Amount']=1
            refs['Effect,ScoutGround,AttributeBonus[Light]']=1
            for wid in ['InterceptorLaunch','InterceptorsDummy']:refs[f'Weapon,{wid},Level']=1
    return refs

def upgrades(data,actor_ids):
    root=E.fromstring(data)
    records=dependency_records('upgradedata.xml')
    for e in root:
        if e.get('id'):records.setdefault(e.get('id'),[]).append(e)
    for level in range(1,4):
        for family in ['GroundWeapons','AirWeapons','GroundArmors','AirArmors','Shields']:
            ident=f'Protoss{family}Level{level}'
            local=next((e for e in root if e.get('id')==ident),None)
            if local is None:
                local=E.SubElement(root,'CUpgrade',id=ident)
                records.setdefault(ident,[]).append(local)
            inherited={e.get('Reference'):e for e in effective_effects(records,ident)}
            for ref,value in required(family).items():
                if ref not in inherited:E.SubElement(local,'EffectArray',Reference=ref,Value=str(value))
            icon_kind={'GroundWeapons':'groundweapons','AirWeapons':'airweapons','GroundArmors':'groundarmor','AirArmors':'airarmor','Shields':'shields'}[family]
            icon=f'Assets\\Textures\\btn-upgrade-protoss-{icon_kind}level{level}.dds'
            if 'Weapons' in family:
                for wid in (GW if family=='GroundWeapons' else AW):
                    ref=f'Weapon,{wid},Icon'
                    if ref not in inherited:E.SubElement(local,'EffectArray',Operation='Set',Reference=ref,Value=icon)
            else:
                units=GROUND if family=='GroundArmors' else AIR if family=='AirArmors' else GROUND+AIR
                stat='ShieldArmorIcon' if family=='Shields' else 'LifeArmorIcon'
                for uid in units:
                    ref=f'Actor,{uid},{stat}'
                    if uid in actor_ids and ref not in inherited:E.SubElement(local,'EffectArray',Operation='Set',Reference=ref,Value=icon)
    return E.tostring(root,encoding='utf-8',xml_declaration=True)

def script(data):
    t=data.decode('utf-8')
    a='        if (i<=w && TechTreeUpgradeCount(pp,"ProtossGroundWeaponsLevel"+n,c_techCountCompleteOnly)==0) { TechTreeUpgradeAddLevel(pp,"ProtossGroundWeaponsLevel"+n,1); }'
    b='        if (i<=a && TechTreeUpgradeCount(pp,"ProtossGroundArmorsLevel"+n,c_techCountCompleteOnly)==0) { TechTreeUpgradeAddLevel(pp,"ProtossGroundArmorsLevel"+n,1); }'
    assert t.count(a)==t.count(b)==1
    air=a.replace('ProtossGroundWeapons','ProtossAirWeapons')
    armor=b.replace('ProtossGroundArmors','ProtossAirArmors')
    shields=b.replace('ProtossGroundArmors','ProtossShields')
    return t.replace(a,a+'\n'+air).replace(b,b+'\n'+armor+'\n'+shields).encode('utf-8')

def build(source,output):
    if output.exists():raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        actors=dependency_records('actordata.xml')
        for e in E.fromstring(prev.read(GD+'actordata.xml')):
            if e.get('id'):actors.setdefault(e.get('id'),[]).append(e)
        changes={'metadata.txt':prev.read('metadata.txt').replace(OLD,NEW),
                 GD+'upgradedata.xml':upgrades(prev.read(GD+'upgradedata.xml'),set(actors)),
                 M4+'mapscript.galaxy':script(prev.read(M4+'mapscript.galaxy'))}
        output.parent.mkdir(parents=True,exist_ok=True)
        try:
            with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():out.writestr(copy.copy(info),changes.get(info.filename,prev.read(info.filename)))
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changes:assert out.read(n)==prev.read(n),n
        except BaseException:
            output.unlink(missing_ok=True);raise
    print(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();build(a.source,a.output)
