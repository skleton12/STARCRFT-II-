#!/usr/bin/env python3
"""0.4.34: user excludes Marauder Magrail Munitions. Keep Korhal's Sons separate."""
import argparse,copy,zipfile,xml.etree.ElementTree as E
from pathlib import Path
M='TTychus01.SC2Map/'
OLD=b'version=0.4.33';NEW=b'version=0.4.34'
def xml(data,kind):
 root=E.fromstring(data)
 if kind=='abil':
  e=next(e for e in root if e.get('id')=='RM3_TechResearch')
  x=e.find('InfoArray[@index="Research8"]');assert x is not None and x.get('Upgrade')=='MarauderMagrailMunitions';e.remove(x)
 elif kind=='unit':
  for e in root:
   if e.get('id')=='BarracksTechLab':
    for c in e.findall('CardLayouts'):
     for b in list(c):
      if b.get('Face')=='RM4_Magrail':c.remove(b)
   if e.get('id')=='HammerSecurity':
    for a in list(e):
     if a.tag=='AbilArray' and a.get('Link')=='MarauderMagrailMunitions':e.remove(a)
    for c in e.findall('CardLayouts'):
     for b in list(c):
      if b.get('AbilCmd','').startswith('MarauderMagrailMunitions,'):c.remove(b)
 elif kind=='button':
  for e in list(root):
   if e.get('id')=='RM4_Magrail':root.remove(e)
 return E.tostring(root,encoding='utf-8',xml_declaration=True)
def script(data):
 lines=data.decode().splitlines(keepends=True)
 return ''.join(l for l in lines if not any(x in l for x in ['TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",7),true);','libNtve_gf_SetUpgradeLevelForPlayer(1,"MarauderMagrailMunitions",0);','TechTreeUpgradeAllow(1,"MarauderMagrailMunitions",true);'])).encode()
def strings(data):
 return ''.join(l for l in data.decode().splitlines(keepends=True) if not l.split('=',1)[0].endswith('/RM4_Magrail')).encode()
def patch(name,data):
 if name=='metadata.txt':return data.replace(OLD,NEW)
 if not name.startswith(M):return data
 for file,kind in [('abildata.xml','abil'),('unitdata.xml','unit'),('buttondata.xml','button')]:
  if name==M+'base.sc2data/gamedata/'+file:return xml(data,kind)
 if name==M+'mapscript.galaxy':return script(data)
 if name.endswith(('/gamestrings.txt','/gamehotkeys.txt')):return strings(data)
 return data
def build(source,output):
 assert not output.exists()
 with zipfile.ZipFile(source) as prev:
  assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
  with zipfile.ZipFile(output,'x') as out:
   for info in prev.infolist():out.writestr(copy.copy(info),patch(info.filename,prev.read(info.filename)))
  with zipfile.ZipFile(output) as out:
   assert out.testzip() is None and out.namelist()==prev.namelist()
   for n in prev.namelist():
    if not n.startswith(M) and n!='metadata.txt':assert prev.read(n)==out.read(n),n
 print(output)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
 a=p.parse_args();build(a.source,a.output)
