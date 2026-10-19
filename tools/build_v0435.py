#!/usr/bin/env python3
"""0.4.35: user-requested first row: slot 3 Concussive/Suppression, slot 4 Shrapnel."""
import argparse,copy,zipfile,xml.etree.ElementTree as E
from pathlib import Path
KEY='TTychus01.SC2Map/base.sc2data/gamedata/unitdata.xml'
def patch(data):
 root=E.fromstring(data);u=next(e for e in root if e.get('id')=='BarracksTechLab');found=[]
 for b in u.iter('LayoutButtons'):
  face=b.get('Face')
  if face in ['RM4_Concussive','RM4_Suppression','RM4_Shrapnel']:
   b.set('Row','0');b.set('Column','3' if face=='RM4_Shrapnel' else '2');found.append(face)
 assert len(found)==3
 return E.tostring(root,encoding='utf-8',xml_declaration=True)
def build(source,output):
 assert not output.exists()
 with zipfile.ZipFile(source) as prev:
  assert b'version=0.4.34' in prev.read('metadata.txt').splitlines() and prev.testzip() is None
  with zipfile.ZipFile(output,'x') as out:
   for info in prev.infolist():
    d=prev.read(info.filename)
    if info.filename==KEY:d=patch(d)
    elif info.filename=='metadata.txt':d=d.replace(b'version=0.4.34',b'version=0.4.35')
    out.writestr(copy.copy(info),d)
  with zipfile.ZipFile(output) as out:
   assert out.testzip() is None and out.namelist()==prev.namelist()
   for n in prev.namelist():
    if n not in [KEY,'metadata.txt']:assert prev.read(n)==out.read(n),n
 print(output)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();build(a.source,a.output)
