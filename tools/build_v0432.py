#!/usr/bin/env python3
"""0.4.32: start mission-only Marauder research at level zero, once at map initialization.
Do not reset in ticks/start-of-combat callbacks or on save loading. Preserve Hyperion
purchases and all research costs/prerequisites/effects. Magrail's UI leader is itself.
"""
import argparse,copy,zipfile,xml.etree.ElementTree as E
from pathlib import Path
OLD=b'version=0.4.31';NEW=b'version=0.4.32'
MAP='TTychus01.SC2Map/'
ANCHOR='    int ally;\n    gv_m4_eggUnit[0]'
INIT='''    int ally;
    // Mission research starts unresearched. Run once on map init, never every tick.
    libNtve_gf_SetUpgradeLevelForPlayer(1,"RM4_Suppression",0);
    libNtve_gf_SetUpgradeLevelForPlayer(1,"MarauderMagrailMunitions",0);
    libNtve_gf_SetUpgradeLevelForPlayer(1,"RM4_Shrapnel",0);
    gv_m4_eggUnit[0]'''
def script(data):
 text=data.decode();nl='\r\n' if '\r\n' in text else '\n';text=text.replace('\r\n','\n')
 assert text.count(ANCHOR)==1
 return text.replace(ANCHOR,INIT).replace('\n',nl).encode()
def upgrades(data):
 root=E.fromstring(data)
 e=next(e for e in root if e.get('id')=='MarauderMagrailMunitions')
 assert e.find('LeaderAlias').get('value')=='MarineSuperStim'
 e.find('LeaderAlias').set('value','MarauderMagrailMunitions')
 return E.tostring(root,encoding='utf-8',xml_declaration=True)
def build(source,output):
 assert not output.exists()
 changes={MAP+'mapscript.galaxy':script,MAP+'base.sc2data/gamedata/upgradedata.xml':upgrades,'metadata.txt':lambda d:d.replace(OLD,NEW)}
 with zipfile.ZipFile(source) as prev:
  assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
  with zipfile.ZipFile(output,'x') as out:
   for info in prev.infolist():
    data=prev.read(info.filename)
    out.writestr(copy.copy(info),changes[info.filename](data) if info.filename in changes else data)
  with zipfile.ZipFile(output) as out:
   assert out.testzip() is None and out.namelist()==prev.namelist()
   for n in prev.namelist():
    if n not in changes:assert prev.read(n)==out.read(n),n
 print(output)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
 a=p.parse_args();build(a.source,a.output)
