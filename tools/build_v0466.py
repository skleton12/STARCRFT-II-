#!/usr/bin/env python3
"""0.4.65 -> 0.4.66: restore Aegis default health bar without missing co-op UI.

This fixes an observed catalog/UI dependency defect, not a confirmed unit
disappearance or rapid-death cause. Combat stats and XP remain unchanged.
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

ACTOR='TTychus01.SC2Map/base.sc2data/gamedata/actordata.xml'
OLD,NEW=b'version=0.4.65',b'version=0.4.66'

def actors(data):
    root=E.fromstring(data)
    a=next(e for e in root if e.get('id')=='MarauderMengsk')
    assert a.find('CustomUnitStatusFrame').get('value')=='Coop_UnitStatus_Mengsk/MengskMarauder_StatusFrame'
    a.find('CustomUnitStatusFrame').set('value','')
    a.find("StatusBarOn[@index='Custom']").set('value','0')
    a.find("UnitFlags[@index='SuppressDefaultStatusBar']").set('value','0')
    return E.tostring(root,encoding='utf-8',xml_declaration=True)

def build(source,output):
    if output.exists():raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        changes={'metadata.txt':prev.read('metadata.txt').replace(OLD,NEW),ACTOR:actors(prev.read(ACTOR))}
        output.parent.mkdir(parents=True,exist_ok=True)
        try:
            with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():out.writestr(copy.copy(info),changes.get(info.filename,prev.read(info.filename)))
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changes:assert prev.read(n)==out.read(n),n
        except BaseException:
            output.unlink(missing_ok=True);raise
    print(output)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();build(a.source,a.output)
