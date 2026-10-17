#!/usr/bin/env python3
"""Build CCM 0.3.26 from 0.3.25 (3번 미션).

사용자 보고 (2026-10-17):
1. "사도는 왜 공격이 없음" — 피닉스 사도(AdeptFenix)의 무기 'Adept'와 그 효과·투사체·공격 연출이 맵에 없었다
   (공허 모드에만 있음, 0.3.4 이식에서 빠짐). 그래서 공격하지 못했다.
   공허 모드 원본 + 협동전 값으로 무기 Adept, 발사 AdeptLM, 피해 AdeptDamage(협동전: 16, 경장갑 +6),
   투사체 유닛·이동 AdeptWeapon, 공격 연출 AdeptAttack·AdeptAttackMissile를 옮긴다.
   협동전 피닉스 사도의 '공격 시 그림자 생성'(AdeptLMSet의 FenixAdeptShade…)은 따라오는 데이터가 많아 넣지 않는다.
2. "동맹은 왜 선택이 안 됨, 선택은 되고 조종이 안 돼야 하는 거 아님?" — 0.3.24는 동맹 병력을 '선택 불가'로 만들었다.
   이것을 되돌리고, 동맹 병력 유닛 종류(3번 맵 데이터만)에 '명령 불가(Uncommandable)'를 건다.
   플레이어는 선택해서 정보를 볼 수 있지만 명령은 못 한다. 동맹 AI 스크립트의 명령은 받는다(게임 미확인).
   일꾼(탐사정·원시 일벌레)과 건물은 그대로 플레이어가 조종한다.

Usage: python3 tools/build_v0326.py <0.3.25 zip> <new output zip>
"""
import argparse
import copy
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v035 as V35  # noqa: E402

OLD, NEW = b'version=0.3.25', b'version=0.3.26'
M3 = 'TRaynor03.SC2Map/'
GD = M3 + 'base.sc2data/gamedata/'
KO = M3 + 'kokr.sc2data/localizeddata/gamestrings.txt'
ARMY = ['ZealotPurifier', 'AdeptFenix', 'RM21_Energizer', 'DehakaZerglingLevel2', 'DehakaRoachLevel2',
        'DehakaHydraliskLevel2', 'DehakaRavasaur']

WEAPON = ('<CWeaponLegacy id="Adept"><EditorCategories value="Race:Protoss" />'
          r'<Icon value="Assets\Textures\btn-upgrade-protoss-groundweaponslevel0.dds" />'
          '<DisplayEffect value="AdeptDamage" /><TargetFilters value="Ground,Visible;Missile,Stasis,Dead,Hidden,Invulnerable" />'
          '<Range value="4" /><Period value="2.25" /><MinScanRange value="5.5" /><Effect value="AdeptLM" /></CWeaponLegacy>')
EFFECTS = ('<CEffectLaunchMissile id="AdeptLM"><EditorCategories value="Race:Protoss" /><ImpactEffect value="AdeptDamage" />'
           '<AmmoUnit value="AdeptWeapon" /><Movers Link="AdeptWeapon" /></CEffectLaunchMissile>'
           '<CEffectDamage id="AdeptDamage" parent="DU_WEAP"><EditorCategories value="Race:Protoss" /><Kind value="Ranged" />'
           '<Amount value="16" /><AttributeBonus index="Light" value="6" /><Death value="Blast" />'
           '<ValidatorArray value="noMarkers" /></CEffectDamage>')
UNIT = '<CUnit id="AdeptWeapon" parent="MISSILE"><Race value="Prot" /><EditorCategories value="ObjectType:Projectile,ObjectFamily:Melee" /></CUnit>'
MOVER = '<CMoverMissile id="AdeptWeapon" parent="MissileDefault" />'
ACTORS = ('<CActorAction id="AdeptAttack" parent="GenericAttack" effectImpact="AdeptDamage" effectLaunch="AdeptLM">'
          '<LaunchAssets Sound="Adept_AttackLaunch" /><ImpactMap index="None" Model="AdeptImpact" Sound="Adept_AttackImpact" />'
          '</CActorAction><CActorMissile id="AdeptAttackMissile" parent="GenericAttackMissile" unitName="AdeptWeapon" />')
STRINGS = {'Weapon/Name/Adept': '쐐기포 /// Glaive Cannon'}

SEL_OLD = '            UnitSetState(UnitLastCreated(),c_unitStateSelectable,false);\n'
NOTE_OLD = '    // Ally armies stay AI-only: they are made unselectable, so the shared control only reaches the workers and posts.\n'
NOTE_NEW = '    // Ally armies stay AI-only: their unit types are Uncommandable (selectable, but the player cannot order them).\n'


def append(xml, absent):
    def f(data):
        text = data.decode('utf-8')
        for x in absent: assert f'id="{x}"' not in text, x
        out = text.replace('</Catalog>', xml + '</Catalog>', 1).encode('utf-8')
        E.fromstring(out)
        return out
    return f


def units(data):
    root = E.fromstring(append(UNIT, ['AdeptWeapon'])(data))
    found = set()
    for el in root:
        if el.tag == 'CUnit' and el.get('id') in ARMY:
            found.add(el.get('id'))
            E.SubElement(el, 'FlagArray', index='Uncommandable', value='1')
    missing = [u for u in ARMY if u not in found]
    for u in missing:  # types defined only in a dependency layer get a small override
        E.SubElement(E.SubElement(root, 'CUnit', id=u), 'FlagArray', index='Uncommandable', value='1')
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def script(data):
    text = data.decode('utf-8')
    assert text.count(SEL_OLD) == 2 and text.count(NOTE_OLD) == 1
    return text.replace(SEL_OLD, '').replace(NOTE_OLD, NOTE_NEW, 1).encode('utf-8')


def kokr(data):
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    for k in STRINGS: assert f'\n{k}=' not in text, k
    out = (text.rstrip('\r\n') + nl + nl.join(f'{k}={v}' for k, v in STRINGS.items()) + nl).encode('utf-8')
    V35.gate('kokr', out)
    return out


FIX = {M3 + 'mapscript.galaxy': script, GD + 'unitdata.xml': units,
       GD + 'weapondata.xml': append(WEAPON, ['Adept']), GD + 'effectdata.xml': append(EFFECTS, ['AdeptLM', 'AdeptDamage']),
       GD + 'moverdata.xml': append(MOVER, ['AdeptWeapon']), GD + 'actordata.xml': append(ACTORS, ['AdeptAttack', 'AdeptAttackMissile']),
       KO: kokr, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for name, fn in FIX.items(): files[name] = fn(files[name])
        changed = set(FIX)
        for loc in V35.OTHER_LOCALES:
            n = f'{M3}{loc}.sc2data/localizeddata/gamestrings.txt'
            files[n] = V35.other_locale(files[KO]); changed.add(n)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
