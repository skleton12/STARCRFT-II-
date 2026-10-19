#!/usr/bin/env python3
"""0.4.33: correct inverted paid-research validators (Find must be true).
Core CValidatorPlayerRequirement defaults Find=false; Liberty NoMarineShield and
MissingMarineShieldUpgrade use the omitted field, while PunisherGrenadesResearched
sets Find=1. RM4's two validators accidentally tested missing research.
"""
import argparse,copy,zipfile,xml.etree.ElementTree as E
from pathlib import Path
OLD=b'version=0.4.32';NEW=b'version=0.4.33'
KEY='TTychus01.SC2Map/base.sc2data/gamedata/validatordata.xml'
def patch(data):
 root=E.fromstring(data)
 for id in ['RM4_HaveSuppression','RM4_HaveShrapnel']:
  e=next(e for e in root if e.get('id')==id)
  assert e.tag=='CValidatorPlayerRequirement' and e.find('Find') is None
  E.SubElement(e,'Find',value='1')
  # Research belongs to the attacker, never the target's owner.
  assert e.find('WhichPlayer') is None
  E.SubElement(e,'WhichPlayer',Value='Caster')
 return E.tostring(root,encoding='utf-8',xml_declaration=True)
def build(source,output):
 assert not output.exists()
 with zipfile.ZipFile(source) as prev:
  assert OLD in prev.read('metadata.txt').splitlines() and prev.testzip() is None
  with zipfile.ZipFile(output,'x') as out:
   for info in prev.infolist():
    d=prev.read(info.filename)
    if info.filename==KEY:d=patch(d)
    if info.filename=='metadata.txt':d=d.replace(OLD,NEW)
    out.writestr(copy.copy(info),d)
  with zipfile.ZipFile(output) as out:
   assert out.testzip() is None and out.namelist()==prev.namelist()
   for n in prev.namelist():
    if n not in [KEY,'metadata.txt']:assert prev.read(n)==out.read(n),n
 print(output)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
 a=p.parse_args();build(a.source,a.output)
