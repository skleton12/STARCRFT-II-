#!/usr/bin/env python3
"""0.4.66 -> 0.4.67: restore the Aegis Guard's missing projectile unit.

PunisherGrenadesMengskLM inherits AmmoUnit=##id##Weapon from Core.
The corresponding unit was omitted by the porter (only explicit links followed).
Actor and model already exist. Restore the exact projectile unit from
SC2Mapster/SC2GameData 6dd323aae4209a01f110719a00b4e8f7a88389bc,
arcturusmengsk.sc2mod UnitData.xml, and make AmmoUnit explicit.
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

GD='TTychus01.SC2Map/base.sc2data/gamedata/'
OLD,NEW=b'version=0.4.66',b'version=0.4.67'
MISSILE='PunisherGrenadesMengskLMWeapon'

def patch_unit(data):
    r=E.fromstring(data)
    assert not any(e.get('id')==MISSILE for e in r)
    r.append(E.fromstring('<CUnit id="PunisherGrenadesMengskLMWeapon" parent="MISSILE">'
                        '<Race value="Terr"/><Mover value="PunisherGrenadesWeapon"/>'
                        '<EditorCategories value="ObjectType:Projectile,ObjectFamily:Melee"/></CUnit>'))
    return E.tostring(r,encoding='utf-8',xml_declaration=True)

def patch_effect(data):
    r=E.fromstring(data)
    e=next(e for e in r if e.get('id')=='PunisherGrenadesMengskLM')
    assert e.find('AmmoUnit') is None
    E.SubElement(e,'AmmoUnit',value=MISSILE)
    return E.tostring(r,encoding='utf-8',xml_declaration=True)

def build(source,output):
    if output.exists():raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        changes={'metadata.txt':prev.read('metadata.txt').replace(OLD,NEW),
                 GD+'unitdata.xml':patch_unit(prev.read(GD+'unitdata.xml')),
                 GD+'effectdata.xml':patch_effect(prev.read(GD+'effectdata.xml'))}
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
