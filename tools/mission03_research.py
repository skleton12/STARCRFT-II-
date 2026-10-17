"""Standalone mission 3 research. Costs are documented trial settings."""
import xml.etree.ElementTree as E


def catalogs():
    out = {}
    def add(file, text):
        el = E.fromstring(text)
        out.setdefault(file + 'data.xml', []).append(el)
        return el
    strings = {}
    def button(ident, name, tip, icon):
        add('button', f'<CButton id="{ident}"><Icon value="{icon}"/><Name value="Button/Name/{ident}"/><Tooltip value="Button/Tooltip/{ident}"/><TooltipFlags index="ShowLevel" value="0"/></CButton>')
        strings['Button/Name/'+ident] = name
        strings['Button/Tooltip/'+ident] = tip
    def count(ident, upgrade, state):
        add('requirementnode', f'<CRequirementCountUpgrade id="{ident}"><Count Link="{upgrade}" State="{state}"/></CRequirementCountUpgrade>')
    def req(ident, use='', show=''):
        el = add('requirement', f'<CRequirement id="{ident}"/>')
        for index, link in [('Use',use),('Show',show)]:
            if link: E.SubElement(el,'NodeArray',index=index,Link=link)
    research = add('abil', '<CAbilResearch id="RM3_TechResearch"/>')
    bay = add('abil', '<CAbilResearch id="RM3_BayResearch"/>')
    specs = [('Stim1','전투 자극제',100,100,60,'공격 속도 +50%, 이동 속도 +50%, 체력 10 소모. 11초 지속.'),
             ('Stim2','초 전투 자극제',150,150,90,'자극제를 교체합니다. 공격 속도 +75%, 이동 속도 +50%, 초당 체력 2 회복. 15초 지속.'),
             ('Stim3','고급 전투 자극제',250,250,120,'자극제를 교체합니다. 공격 속도 +100%, 이동 속도 +50%, 초당 체력 5 회복. 15초 지속.'),
             ('Shield','전투 방패',100,100,60,'해병 역할 용병의 최대 체력 +10. 기존 코랄의 후예 방패 능력과 별개의 체력 연구입니다.'),
             ('Laser','레이저 조준 시스템',100,100,60,'해병 역할 용병의 무기 사거리 +1, 새벽·황혼 시야 보너스 +2.'),
             ('SupplyBunker','보급 벙커 건설',150,100,60,'SCV가 보급 벙커를 건설할 수 있습니다. 건설비는 별도입니다.'),
             ('Armor','건물 장갑',150,150,90,'테란 기지 건물의 방어력 +2. 일반·보급 벙커 포함.')]
    for i,(suffix,name,m,g,time,tip) in enumerate(specs):
        ident='RM3_'+suffix
        button(ident,name,tip,r'Assets\Textures\btn-techupgrade-terran-combatshield-color.dds' if suffix=='Shield' else r'Assets\Textures\btn-upgrade-terran-infantryarmorlevel1.dds')
        up=add('upgrade',f'<CUpgrade id="{ident}"><MaxLevel value="1"/></CUpgrade>')
        count(ident+'Done',ident,'CompleteOnly');count(ident+'Queued',ident,'QueuedOrBetter')
        add('requirementnode',f'<CRequirementNot id="{ident}NotQueued"><OperandArray index="0" value="{ident}Queued"/></CRequirementNot>')
        previous = 'RM3_Stim'+str(int(suffix[-1])-1)+'Done' if suffix in ['Stim2','Stim3'] else ''
        req(ident+'Learn',previous,ident+'NotQueued')
        parent=research if i<5 else bay
        info=E.SubElement(parent,'InfoArray',index='Research'+str(i+1),Time=str(time),Upgrade=ident)
        E.SubElement(info,'Resource',index='Minerals',value=str(m));E.SubElement(info,'Resource',index='Vespene',value=str(g))
        E.SubElement(info,'Button',DefaultButtonFace=ident,State='Available',Requirements=ident+'Learn')
        if suffix=='Shield':
            for unit in ['WarPig','RMK_MarineMengsk']:
                for field in ['LifeMax','LifeStart']: E.SubElement(up,'EffectArray',Reference=f'Unit,{unit},{field}',Value='10')
        if suffix=='Laser':
            for unit in ['WarPig','RMK_MarineMengsk']:
                for field in ['SightBonus[Dusk]','SightBonus[Dawn]']: E.SubElement(up,'EffectArray',Reference=f'Unit,{unit},{field}',Value='2')
            for weapon in ['KelmorianMinerGaussRifle','RMK_MarineMengskGaussRifle']:
                for field in ['Range','MinScanRange']: E.SubElement(up,'EffectArray',Reference=f'Weapon,{weapon},{field}',Value='1')
        if suffix=='Armor':
            for unit in ['CommandCenter','OrbitalCommand','PlanetaryFortress','SupplyDepot','SupplyDepotLowered','Barracks','BarracksFlying','BarracksTechLab','BarracksReactor','EngineeringBay','Bunker','RM3_SupplyBunker','MissileTurret','Refinery','RefineryRich','MercCompound']:
                E.SubElement(up,'EffectArray',Reference=f'Unit,{unit},LifeArmor',Value='2')
    # One visible stim at a time; every tier shares a cooldown and removes old buffs.
    for tier,speed,regen,duration,cooldown in [(1,'1.5','0',11,15),(2,'1.75','2',15,30),(3,'2','5',15,30)]:
        ident=f'RM3_Stim{tier}'
        active=ident+'Done'
        if tier<3:
            add('requirementnode',f'<CRequirementNot id="{ident}NotNext"><OperandArray index="0" value="RM3_Stim{tier+1}Done"/></CRequirementNot>')
            add('requirementnode',f'<CRequirementAnd id="{ident}Active"><OperandArray index="0" value="{ident}Done"/><OperandArray index="1" value="{ident}NotNext"/></CRequirementAnd>')
            active=ident+'Active'
        req(ident+'Use',active,active)
        cost='<Vital index="Life" value="10"/>' if tier==1 else ''
        add('abil',f'<CAbilEffectInstant id="{ident}Cast"><Effect value="{ident}Set"/><Flags index="Transient" value="1"/><Cost>{cost}<Cooldown Link="RM3_StimShared" TimeUse="{cooldown}"/></Cost><CmdButtonArray index="Execute" DefaultButtonFace="{ident}" Requirements="{ident}Use"/></CAbilEffectInstant>')
        add('behavior',f'<CBehaviorBuff id="{ident}Buff"><Duration value="{duration}"/><MaxStackCount value="1"/><Modification MoveSpeedMultiplier="1.5" AttackSpeedMultiplier="{speed}"><VitalRegenArray index="Life" value="{regen}"/></Modification></CBehaviorBuff>')
        effect=add('effect',f'<CEffectSet id="{ident}Set"/>')
        for old in range(1,4): E.SubElement(effect,'EffectArray',value=f'RM3_Stim{old}Remove')
        E.SubElement(effect,'EffectArray',value=ident+'Apply')
        add('effect',f'<CEffectApplyBehavior id="{ident}Apply"><Behavior value="{ident}Buff"/><WhichUnit Value="Caster"/></CEffectApplyBehavior>')
        add('effect',f'<CEffectRemoveBehavior id="{ident}Remove"><Behavior value="{ident}Buff"/><WhichUnit Value="Caster"/></CEffectRemoveBehavior>')
    # Keep native infantry research; attach separate abilities to avoid campaign slots.
    for unit,ability,offset in [('BarracksTechLab','RM3_TechResearch',0),('EngineeringBay','RM3_BayResearch',5)]:
        el=add('unit',f'<CUnit id="{unit}"><AbilArray Link="{ability}"/><CardLayouts index="0"/></CUnit>')
        layout=el.find('CardLayouts')
        for local,suffix in enumerate(['Stim1','Stim2','Stim3','Shield','Laser'] if offset==0 else ['SupplyBunker','Armor']):
            E.SubElement(layout,'LayoutButtons',Face='RM3_'+suffix,Type='AbilCmd',AbilCmd=f'{ability},Research{local+offset+1}',Row=str(local//3 if offset==0 else 2),Column=str(local%3))
    # Suppress native duplicates: one shield/stim/armor research path only.
    add('abil','<CAbilResearch id="BarracksTechLabResearch"><InfoArray index="Research1"><Button State="Suppressed"/></InfoArray><InfoArray index="Research2"><Button State="Suppressed"/></InfoArray></CAbilResearch>')
    add('abil','<CAbilResearch id="EngineeringBayResearch"><InfoArray index="Research1"><Button State="Suppressed"/></InfoArray><InfoArray index="Research2"><Button State="Suppressed"/></InfoArray><InfoArray index="Research6"><Button State="Suppressed"/></InfoArray></CAbilResearch>')
    # Standard bunker mechanics with a supply contribution; no commander subsystem.
    add('unit','<CUnit id="RM3_SupplyBunker" parent="Bunker"><Name value="Unit/Name/RM3_SupplyBunker"/><Food value="12"/><CostResource index="Minerals" value="100"/><CostResource index="Vespene" value="0"/><Footprint value="Footprint2x2CreepNormalContour"/><PlacementFootprint value="Footprint2x2CreepNormal"/><AbilArray Link="BunkerTransport" removed="1"/><AbilArray Link="RM3_SupplyTransport"/><CardLayouts index="0"><LayoutButtons Face="BunkerLoad" Type="AbilCmd" AbilCmd="RM3_SupplyTransport,Load" Row="2" Column="1"/><LayoutButtons Face="BunkerUnloadAll" Type="AbilCmd" AbilCmd="RM3_SupplyTransport,UnloadAll" Row="2" Column="2"/></CardLayouts></CUnit>')
    add('abil','<CAbilTransport id="RM3_SupplyTransport" parent="BunkerTransport"><MaxCargoCount value="6"/><TotalCargoSpace value="6"/></CAbilTransport>')
    add('model',r'<CModel id="RM3_SupplyBunkerModel" parent="Building"><Model value="Assets\COOP\Mengsk\Buildings\SupplyBunker_Mengsk_COOP\SupplyBunker_Mengsk_COOP.m3"/><ScaleMax value="0.75,0.75,0.75"/><ScaleMin value="0.75,0.75,0.75"/></CModel>')
    add('model',r'<CModel id="RM3_SupplyBunkerDeath" parent="BuildingDeath"><Model value="Assets\COOP\Mengsk\Buildings\SupplyBunker_Mengsk_COOP_Death\SupplyBunker_Mengsk_COOP_Death.m3"/></CModel>')
    strings['Unit/Name/RM3_SupplyBunker']='보급 벙커'
    button('RM3_BuildSupplyBunker','보급 벙커 건설','병력 수용 공간 6과 보급품 12를 제공합니다. 건설비: 광물 100.',r'Assets\Textures\btn-building-terran-bunker.dds')
    req('RM3_CanBuildSupplyBunker','RM3_SupplyBunkerDone')
    add('abil','<CAbilBuild id="TerranBuild"><InfoArray index="Build17" Unit="RM3_SupplyBunker" Time="30"><Button DefaultButtonFace="RM3_BuildSupplyBunker" State="Available" Requirements="RM3_CanBuildSupplyBunker"/></InfoArray><InfoArray index="Build13"><Button State="Available" Requirements="HaveBarracks"/></InfoArray></CAbilBuild>')
    add('unit','<CUnit id="SCV"><CardLayouts index="1" CardId="TBl1"><LayoutButtons Face="RM3_BuildSupplyBunker" Type="AbilCmd" AbilCmd="TerranBuild,Build17" Row="2" Column="3"/><LayoutButtons Face="MercCompound" Type="AbilCmd" AbilCmd="TerranBuild,Build13" Row="1" Column="2"/></CardLayouts></CUnit>')
    # Mercenary research targets use their real unit IDs, rather than Marine only.
    for unit in ['WarPig','RMK_MarineMengsk']:
        el=add('unit',f'<CUnit id="{unit}"><AbilArray Link="Stimpack" removed="1"/><AbilArray Link="RMK_MarineMengskAttackSpeedBoost" removed="1"/><CardLayouts index="0"/></CUnit>')
        layout=el.find('CardLayouts')
        for tier in range(1,4):
            E.SubElement(el,'AbilArray',Link=f'RM3_Stim{tier}Cast')
            E.SubElement(layout,'LayoutButtons',Face=f'RM3_Stim{tier}',Type='AbilCmd',AbilCmd=f'RM3_Stim{tier}Cast,Execute',Requirements=f'RM3_Stim{tier}Use',Row='2',Column='1')
    # Solar strike deals real effect damage, restricted to enemy players by script.
    add('effect','<CEffectDamage id="RM3_SolarDamage" parent="DU_WEAP"><Amount value="250"/></CEffectDamage>')
    add('model',r'<CModel id="RM3_SolarLance" parent="PersistentSpellFX"><Model value="Assets\Effects\Protoss\SOA_SolarLance_Upgrade\SOA_SolarLance_Upgrade.m3"/></CModel>')
    return out, strings
