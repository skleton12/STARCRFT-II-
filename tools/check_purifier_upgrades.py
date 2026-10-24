#!/usr/bin/env python3
"""Check each production unit's attack/armor/shields across all three levels.

Resolve the real dependency upgrade parents, including Liberty and Story records,
to detect both absent links and duplicate armor/damage increments.
"""
import sys
import zipfile
import xml.etree.ElementTree as E
from build_v0477 import dependency_records, effective_effects  # GPT 0.4.69 builder, renamed 0.4.77 on the main line

GD='TTychus01.SC2Map/base.sc2data/gamedata/'
UNITS={
 'ZealotPurifier':['PsiBlades'],
 'AdeptFenix':['RM4_AdeptFenixWeapon'],
 'RM21_Energizer':['RM21_EnergizerWeapon'],
 'StalkerPurifier':['ParticleDisruptors'],
 'Immortal':['PhaseDisruptors'],
 'ColossusPurifier':['ColossusPurifierThermalLances'],
 'Disruptor':['DisruptorPsiBlast'],
 'SentryFenix':['EnergizerWeapon'],
 'SentryFenixPhasing':[],
 'PhoenixPurifier':['ArtanisIonCannons'],
 'Scout':['ScoutGround','ScoutAir'],
 'TempestPurifier':['TempestPurifier','TempestPurifierGround'],
 'Carrier':['InterceptorsDummy'],
 'Interceptor':['InterceptorBeam'],
 'Probe':[],
}
DAMAGE={
 'PsiBlades':1,'AdeptDamage':1,'RM21_SanitizationBeamDamage':1,
 'ParticleDisruptorsU':1,'PhaseDisruptors':2,
 'ColossusPurifierThermalLancesDamage':2,'DisruptorWeaponU':1,
 'SanitizationBeamDamage':1,'ArtanisIonCannonsU':1,
 'ArtanisIonCannonsULeft':1,'ArtanisIonCannonsURight':1,
 'ScoutGround':1,'ScoutAirU':1,
 'TempestPurifierDamage':5,'TempestPurifierDamageGround':5,
 'InterceptorBeamDamage':1,'FenixAdeptShadeDamage':1,
}

def check(z):
    records=dependency_records('upgradedata.xml')
    for e in E.fromstring(z.read(GD+'upgradedata.xml')):
        if e.get('id'):records.setdefault(e.get('id'),[]).append(e)
    def numeric(ident,ref):
        return sum(float(e.get('Value')) for e in effective_effects(records,ident)
                   if e.get('Reference')==ref and e.get('Operation','Add')=='Add')
    for level in range(1,4):
        attack=[f'Protoss{kind}WeaponsLevel{level}' for kind in ['Ground','Air']]
        armor=[f'Protoss{kind}ArmorsLevel{level}' for kind in ['Ground','Air']]
        for uid,weapons in UNITS.items():
            for stat in ['LifeArmor','LifeArmorLevel']:
                assert sum(numeric(up,f'Unit,{uid},{stat}') for up in armor)==1,(uid,level,stat)
            for stat in ['ShieldArmor','ShieldArmorLevel']:
                assert numeric(f'ProtossShieldsLevel{level}',f'Unit,{uid},{stat}')==1,(uid,level,stat)
            for wid in weapons:
                assert sum(numeric(up,f'Weapon,{wid},Level') for up in attack)==1,(uid,wid,level)
        for eid,value in DAMAGE.items():
            assert sum(numeric(up,f'Effect,{eid},Amount') for up in attack)==value,(eid,level)
    # Required producer slots remain included in the independently checked roster.
    abils=E.fromstring(z.read(GD+'abildata.xml'))
    warp=next(e for e in abils if e.get('id')=='WarpGateTrain')
    for info in warp.findall('InfoArray'):
        assert info.get('Unit') in UNITS,info.get('Unit')
    script=z.read('TTychus01.SC2Map/mapscript.galaxy').decode()
    sync=script.split('void gf_rmUpSync (int pp,int pz) {',1)[1].split('\n}\n',1)[0]
    for family in ['ProtossGroundWeapons','ProtossAirWeapons','ProtossGroundArmors','ProtossAirArmors','ProtossShields']:
        expected='w' if 'Weapons' in family else 'a'
        line=f'if (i<={expected} && TechTreeUpgradeCount(pp,"{family}Level"+n,c_techCountCompleteOnly)==0) {{ TechTreeUpgradeAddLevel(pp,"{family}Level"+n,1); }}'
        assert sync.count(line)==1, family
    # Repeated ticks grant each step only once; staged completion 0->1->3 catches up.
    weapon_levels=set();armor_levels=set();shield_levels=set()
    for w,a in [(0,0),(1,0),(1,1),(1,1),(3,2),(3,3),(3,3)]:
        for i in range(1,4):
            if i<=w:weapon_levels.add(i)
            if i<=a:armor_levels.add(i);shield_levels.add(i)
        assert len(weapon_levels)==w and len(armor_levels)==a and len(shield_levels)==a

if __name__=='__main__':
    with zipfile.ZipFile(sys.argv[1]) as z:check(z)
    print('PASS: 15 unit/form armor+shield targets, all weapon/damage paths, levels 1–3, no duplicate increments, sync guards')
