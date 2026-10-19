#!/usr/bin/env python3
"""Static regression check: command permissions must retain nonlinear and one-time gates."""
import sys,zipfile,xml.etree.ElementTree as E
with zipfile.ZipFile(sys.argv[1]) as z:
 p='TTychus01.SC2Map/'
 gd=p+'base.sc2data/gamedata/'
 nodes={e.get('id'):e for e in E.fromstring(z.read(gd+'requirementnodedata.xml'))}
 reqs={e.get('id'):e for e in E.fromstring(z.read(gd+'requirementdata.xml'))}
 abil=next(e for e in E.fromstring(z.read(gd+'abildata.xml')) if e.get('id')=='RM3_TechResearch')
 commands={e.get('index'):e for e in abil.findall('InfoArray')}
 def evaluate(link,levels):
  e=nodes[link]
  if e.tag=='CRequirementCountUpgrade':return levels.get(e.find('Count').get('Link'),0)
  operands=[evaluate(x.get('value'),levels) for x in e.findall('OperandArray')]
  if e.tag=='CRequirementAnd':return all(operands)
  if e.tag=='CRequirementNot':return not operands[0]
  raise ValueError(e.tag)
 cases=0
 for idx in range(6,10):
  cmd=commands['Research'+str(idx)];up=cmd.get('Upgrade')
  req=reqs[cmd.find('Button').get('Requirements')]
  show=req.find('NodeArray[@index="Show"]').get('Link')
  prereq={'PunisherGrenades':1} if idx==7 else {}
  assert not evaluate(show,prereq),('locked unit must hide research',idx)
  assert evaluate(show,dict(prereq,RM4_HammerUnlocked=1)),('unlocked unit must show unresearched item',idx)
  levels=dict(prereq,RM4_HammerUnlocked=1);levels[up]=1
  assert not evaluate(show,levels),('queued/completed upgrade must hide duplicate',idx)
  cases+=3
 # Upgrade-completion requirements still enforce the shared Concussive -> Suppression chain.
 req=reqs['RM4_SuppressionLearn'];use=req.find('NodeArray[@index="Use"]').get('Link')
 assert not evaluate(use,{'RM4_HammerUnlocked':1})
 assert evaluate(use,{'RM4_HammerUnlocked':1,'PunisherGrenades':1});cases+=2
 for name in z.namelist():
  if name.lower().endswith('.xml'):E.fromstring(z.read(name))
 print('PASS:',cases,'research visibility/prerequisite cases; all XML parsed; CRC',z.testzip())
