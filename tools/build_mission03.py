#!/usr/bin/env python3
"""Build CCM 0.3.1 from verified 0.2.24 and the original mission 3 MPQ.

Requires mpyq==0.2.5. Never regenerates earlier maps or saves them in Editor.
"""
import argparse
import copy
from pathlib import Path
import re
import struct
import zipfile
import xml.etree.ElementTree as E
import mpyq
from mission03_research import catalogs
import patch_mission01 as m1

ROOT=Path(__file__).resolve().parent.parent
GD='base.sc2data/gamedata/'


def merge(data, additions):
    root=E.fromstring(data)
    for new in additions:
        matches=[e for e in root if e.get('id')==new.get('id') and e.tag==new.tag]
        if len(matches)>1: raise ValueError('Ambiguous definition: '+str(new.get('id')))
        if matches:
            matches[0].attrib.update(new.attrib)
            matches[0].extend(copy.deepcopy(list(new)))
        else: root.append(copy.deepcopy(new))
    return E.tostring(root,encoding='utf-8',xml_declaration=True)


def mapinfo(data):
    start=data.index(b'Neut')-9
    count=struct.unpack_from('<I',data,start-4)[0]
    assert count==10 and data[start:start+2]==b'\0\3'
    pos=start
    for player in range(count):
        assert data[pos]==player
        pos=data.index(0,pos+26)+1
    records=b''.join(bytes([p,2])+b'\0'*3+struct.pack('<i',-1)+race+b'\0'*14
                     for p,race in [(10,b'Prot'),(11,b'Zerg')])
    result=bytearray(data[:pos]+records+data[pos:])
    struct.pack_into('<I',result,start-4,12)
    return bytes(result)


def original_files(path):
    archive=mpyq.MPQArchive(str(path))
    result={}
    for name in archive.files:
        key=name.decode().replace('\\','/').lower()
        if key.startswith('('): continue
        if '..' in Path(key).parts or key.startswith('/'): raise ValueError('Unsafe MPQ entry')
        result[key]=archive.read_file(name)
    if len(result)!=34: raise ValueError('Expected audited original mission 3')
    return result


def objects(data):
    root=E.fromstring(data)
    rich=0
    for el in root:
        if el.tag!='ObjectUnit': continue
        owner=el.get('Player','0')
        if owner=='1' and el.get('UnitType') in ['Marine','Medic']:
            el.set('UnitType',{'Marine':'WarPig','Medic':'MercMedic'}[el.get('UnitType')])
        x,y,_=map(float,el.get('Position').split(','))
        # Reclaimed west deposits and Raynor's starting base. Other enemy bases stay intact.
        if owner=='0' and ((20<=x<=36 and 20<=y<=26) or (80<=x<=115 and y<40)) and el.get('UnitType') in ['MineralField','VespeneGeyser']:
            el.set('UnitType','Rich'+el.get('UnitType'))
            default=1500 if el.get('UnitType')=='RichMineralField' else 2500
            el.set('Resources',str(int(el.get('Resources',str(default)))*6//5))
            for n in el.iter('Resources'):
                if n.get('Value'): n.set('Value',str(int(n.get('Value'))*6//5))
            rich+=1
    # New eastern expansion. Keep its minerals away from both hall footprints.
    oid=30000
    for x,y in [(39,22),(41,21),(43,21),(45,21),(47,22),(39,24),(43,23),(47,24)]:
        E.SubElement(root,'ObjectUnit',Id=str(oid),Position=f'{x},{y},0',Scale='1,1,1',UnitType='RichMineralField',Resources='1800');oid+=1
    for x,y in [(21.5,35.5),(48.5,29.5)]:
        E.SubElement(root,'ObjectUnit',Id=str(oid),Position=f'{x},{y},0',Scale='1,1,1',UnitType='RichVespeneGeyser',Resources='3000');oid+=1
    assert rich>=8
    return E.tostring(root,encoding='utf-8',xml_declaration=True)


def mission02(data):
    text=data.decode('utf-8-sig')
    count=0
    def replace(m):
        nonlocal count
        el=E.fromstring(m[0])
        if el.get('Player')=='4' and el.get('UnitType') in ['Marine','Medic']:
            old=el.get('UnitType');count+=1
            return m[0].replace(f'UnitType="{old}"',f'UnitType="'+{'Marine':'WarPig','Medic':'MercMedic'}[old]+'"',1)
        return m[0]
    text=re.sub(r'<ObjectUnit\b[^>]*?(?:/>|>.*?</ObjectUnit>)',replace,text,flags=re.S)
    if count==0: raise ValueError('No mission 2 rebel troops found')
    print('Mission 2 rebel troops converted:',count)
    return text.encode('utf-8')


def mission02_script(data):
    for old,new in [('Marine','WarPig'),('Medic','MercMedic')]:
        before=f'UnitGroup("{old}", gv_pLAYER_04_REBELS,'.encode()
        assert before in data
        data=data.replace(before,f'UnitGroup("{new}", gv_pLAYER_04_REBELS,'.encode())
    return data


def build(source, original, output):
    if output.exists(): raise ValueError('Output must be new')
    files=original_files(original)
    pristine=dict(files)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None
        assert b'version=0.2.24' in prev.read('metadata.txt').splitlines()
        donor='TRaynor02.SC2Map/'
        for name in prev.namelist():
            if name.startswith(donor) and (name[len(donor):].lower().startswith(GD) or name[len(donor):].lower().startswith('assets/')):
                rel=name[len(donor):]
                if rel.endswith('terraindata.xml'): continue
                files[rel]=prev.read(name)
        extras,strings=catalogs()
        for fn,entries in extras.items(): files[GD+fn]=merge(files.get(GD+fn,b'<Catalog/>'),entries)
        # Mengsk supply bunker presentation; native bunker mechanics without commander enlistment.
        files[GD+'actordata.xml']=merge(files[GD+'actordata.xml'],[E.fromstring('<CActorUnit id="RM3_SupplyBunker" parent="Bunker" unitName="RM3_SupplyBunker"><Model value="RM3_SupplyBunkerModel"/><DeathArray index="Normal" ModelLink="RM3_SupplyBunkerDeath"/><DeathCustoms Name="Empty" ModelLink="RM3_SupplyBunkerDeath"/><On Terms="UnitBirth.RM3_SupplyBunker" Send="Create"/></CActorUnit>')])
        files[GD+'modeldata.xml']=merge(files[GD+'modeldata.xml'],[E.fromstring(r'<CModel id="RM3_PrimalHallModel" parent="Building"><Model value="Assets\Buildings\Zerg\PrimalTownHall\PrimalTownHall.m3"/></CModel>')])
        # Native paid hiring, exactly four Korhal marines, no other mercenaries unlocked.
        hire=E.fromstring('<CAbilTrain id="SummonMercenaries"><InfoArray index="Train1"><Button DefaultButtonFace="RM3_HireKorhal" State="Available" Requirements=""/></InfoArray></CAbilTrain>')
        for i in range(2,9):
            info=E.SubElement(hire,'InfoArray',index='Train'+str(i))
            E.SubElement(info,'Button',State='Suppressed')
        files[GD+'abildata.xml']=merge(files[GD+'abildata.xml'],[hire])
        files[GD+'buttondata.xml']=merge(files[GD+'buttondata.xml'],[E.fromstring(r'<CButton id="RM3_HireKorhal"><Icon value="Assets\Textures\btn-unit-terran-SoKmarine.dds"/><Name value="Button/Name/RM3_HireKorhal"/><Tooltip value="Button/Tooltip/RM3_HireKorhal"/></CButton>')])
        files[GD+'unitdata.xml']=merge(files[GD+'unitdata.xml'],[E.fromstring('<CUnit id="MercCompound"><CardLayouts index="0"><LayoutButtons Face="RM3_HireKorhal" Type="AbilCmd" AbilCmd="SummonMercenaries,Train1" Row="0" Column="0"/></CardLayouts></CUnit>')])
        strings.update({'Button/Name/RM3_HireKorhal':'코랄의 후예 고용','Button/Tooltip/RM3_HireKorhal':'코랄의 후예 4기를 유료 고용합니다. 기본 캠페인 고용 횟수와 재사용 대기시간을 따릅니다.',
                        'rm3/Arrival':'정화자: 남서쪽 적 기지를 정화합니다. 지원군 진입을 준비하십시오.',
                        'rm3/Ready':'정화자·원시저그 기지 확보 완료. 레이너 부대를 지원합니다.',
                        'MapInfo/Player10/Name':'정화자','MapInfo/Player11/Name':'원시저그'})
        text=files['kokr.sc2data/localizeddata/gamestrings.txt'].decode('utf-8-sig')
        # Reuse unit strings/assets without overwriting original mission narrative keys.
        old=prev.read(donor+'kokr.sc2data/localizeddata/gamestrings.txt').decode('utf-8-sig')
        for line in old.splitlines():
            if '=' in line and not line.startswith(('Param/','MapInfo/')):
                key,value=line.split('=',1);strings.setdefault(key,value)
        for key,value in strings.items():
            pat=re.compile(r'^'+re.escape(key)+r'=[^\r\n]*',re.M)
            if pat.search(text): text=pat.sub(lambda _:key+'='+value,text)
            else: text+='\n'+key+'='+value
        files['kokr.sc2data/localizeddata/gamestrings.txt']=text.encode('utf-8')
        files['objects']=objects(files['objects'])
        files['mapinfo']=mapinfo(files['mapinfo'])
        before=m1.ALLY_PLAYERS
        m1.ALLY_PLAYERS=[(10,b'Prot','정화자','Purifiers'),(11,b'Zerg','원시저그','Primal Zerg')]
        try: files['documentheader']=m1.patch_header(files['documentheader'])
        finally: m1.ALLY_PLAYERS=before
        script=files['mapscript.galaxy'].decode('utf-8-sig').replace('\r\n','\n')
        # All ordinary Marines/Medics in this mission are player/rebel/cinematic troops; enemies are Zerg.
        script=script.replace('"Marine"','"WarPig"').replace('"Medic"','"MercMedic"')
        custom=(ROOT/'tools/data/mission03_support.galaxy').read_text()
        assert script.count('void InitGlobals () {')==1
        script=script.replace('void InitGlobals () {',custom+'\nvoid InitGlobals () {',1)
        anchor='    libCamp_gf_PurchaseStorymodeTech();'
        assert script.count(anchor)==1
        script=script.replace(anchor,anchor+'\n    gf_m3_Init();',1)
        anchor='    TriggerExecute(gt_CreateUnitTooltips, true, false);'
        assert script.count(anchor)==1
        script=script.replace(anchor,anchor+'\n    gf_m3_Start();',1)
        files['mapscript.galaxy']=script.encode('utf-8')
        # Preserve original terrain, objectives, and intro/end cinematic trigger data.
        for name,data in pristine.items():
            if name.startswith('t3') or name in ['triggers','regions','documentinfo','paintedpathinglayer']:
                assert files[name]==data,name
        for name,data in files.items():
            if name.endswith('.xml') or name in ['objects','documentinfo']: E.fromstring(data)
        output.parent.mkdir(parents=True,exist_ok=True)
        try:
            with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data=prev.read(info.filename)
                    if info.filename=='metadata.txt': data=data.replace(b'version=0.2.24',b'version=0.3.1')
                    if info.filename=='TRaynor02.SC2Map/objects': data=mission02(data)
                    if info.filename=='TRaynor02.SC2Map/mapscript.galaxy': data=mission02_script(data)
                    out.writestr(copy.copy(info),data)
                for name,data in sorted(files.items()): out.writestr('TRaynor03.SC2Map/'+name,data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                assert len(out.namelist())==len(set(out.namelist()))
                for name in prev.namelist():
                    if name not in ['metadata.txt','TRaynor02.SC2Map/objects','TRaynor02.SC2Map/mapscript.galaxy']: assert out.read(name)==prev.read(name),name
        except BaseException:
            output.unlink(missing_ok=True);raise
    print(output)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('original',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args();build(args.source,args.original,args.output)
