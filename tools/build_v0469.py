#!/usr/bin/env python3
"""0.4.68 -> 0.4.69: 제로 아워(3번)의 코랄의 후예도 3등급 정예로 고용 (사용자 2026-10-23 "용병있으면 맞춰야지").

0.4.68(tools/build_v0468.py, GPT)이 어부지리에만 적용한 규칙을 용병이 나오는 3번 맵에 같게 적용한다.
1·2번 맵에는 코랄의 후예 정의만 있고 고용·배치가 없어 바꾸지 않는다.
- 진급 행동 RMK_MengskVeterancyMarineMengsk 를 영구 고정 버프로 바꾸고, 세 계급 수정값을 합쳐 기본값에 넣는다:
  체력 150 → 250 (LifeStart 같이), 방어력 +3, 공격 피해 +100%, 시야 +2, 사거리 6, 영웅 속성. 경험치 성장 없음.
- 진급 조건(GTE) 은 고정 버프 1개로 충족 → 진급 능력은 처음부터.
- 인구 1 → 2 (사용자 0.4.68 결정, 4번과 같음).
- 보병 무기 1~3단계: 가우스 소총 피해 변형 2개 단계당 +1, 장갑 1~3단계: 방어력 +1. 단계 아이콘 연결.
- 유료 미션 연구(자극제·전투 방패·레이저 조준)는 그대로 따로 연구한다.

Usage: python3 tools/build_v0469.py <0.4.68 zip> <new output zip>
"""
import argparse, copy, zipfile
import xml.etree.ElementTree as E
from pathlib import Path
from build_v0464 import LOCALES, update_lines

M3 = 'TRaynor03.SC2Map/'
GD = M3 + 'base.sc2data/gamedata/'
OLD, NEW = b'version=0.4.68', b'version=0.4.69'
MARINE, RANK = 'RMK_MarineMengsk', 'RMK_MengskVeterancyMarineMengsk'


def one(root, i):
    found = [e for e in root if e.get('id') == i]
    assert len(found) == 1, (i, len(found))
    return found[0]


def setval(el, tag, value):
    c = el.find(tag)
    if c is None: c = E.SubElement(el, tag)
    c.set('value', str(value))


def patch(files):
    cats = {f: E.fromstring(files[GD + f + '.xml']) for f in ['unitdata', 'behaviordata', 'weapondata', 'requirementnodedata', 'upgradedata']}
    un, beh, weapon, nodes, up = cats.values()
    old = one(beh, RANK)
    assert old.tag == 'CBehaviorVeterancy'
    levels = old.findall('VeterancyLevelArray')
    assert len(levels) == 4
    mods = [m for l in levels[1:] for m in l.findall('Modification')]
    life = sum(float(m.find("VitalMaxArray[@index='Life']").get('value')) for m in mods)
    armor = sum(float(m.find('LifeArmorBonus').get('value')) for m in mods)
    damage = sum(float(m.find("DamageDealtFraction[@index='Ranged']").get('value')) for m in mods)
    assert (life, armor, damage) == (100, 3, 1.0), (life, armor, damage)
    u = one(un, MARINE)
    base_life = float(u.find('LifeMax').get('value'))
    base_armor = float(u.find('LifeArmor').get('value')) if u.find('LifeArmor') is not None else 0
    for tag in ['LifeStart', 'LifeMax']: setval(u, tag, f'{base_life + life:g}')
    setval(u, 'LifeArmor', f'{base_armor + armor:g}')
    setval(u, 'Food', '-2')
    setval(u, 'RankDisplay', 'Never')
    for tag in ['DamageDealtXP', 'DamageTakenXP']: setval(u, tag, '0')
    setval(u, 'Sight', str(int(float(u.find('Sight').get('value'))) + 2))
    buff = E.Element('CBehaviorBuff', id=RANK)
    E.SubElement(buff, 'BehaviorFlags', index='Permanent', value='1')
    E.SubElement(buff, 'MaxStackCount', value='1')
    E.SubElement(buff, 'InfoIcon', value='Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel3.dds')
    mod = E.SubElement(buff, 'Modification')
    for kind in ['Melee', 'Ranged', 'Splash']: E.SubElement(mod, 'DamageDealtFraction', index=kind, value=f'{damage:g}')
    E.SubElement(mod, 'StateFlags', index='UnitAttrOnHeroic', value='1')
    beh.remove(old); beh.append(buff)
    w = one(weapon, 'RMK_MarineMengskGaussRifle')
    assert w.find('Range') is None
    setval(w, 'Range', '6'); setval(w, 'MinScanRange', '6.5')
    counts = {e.get('id') for e in nodes if e.tag == 'CRequirementCountBehavior' and e.find('Count') is not None and e.find('Count').get('Link') == RANK}
    n = 0
    for e in nodes:
        op = e.find("OperandArray[@index='0']")
        if e.tag == 'CRequirementGTE' and op is not None and op.get('value') in counts:
            e.find("OperandArray[@index='1']").set('value', '1'); n += 1
    assert n == 3, n
    for ident, refs in {
        'TerranInfantryWeapons': [('Effect,RMK_MarineMengskGaussRifleDamage,Amount', '1'),
                                  ('Effect,RMK_MarineMengskGaussRifleDamageUpgrade,Amount', '1'),
                                  ('Weapon,RMK_MarineMengskGaussRifle,Level', '1')],
        'TerranInfantryArmors': [(f'Unit,{MARINE},LifeArmor', '1'), (f'Unit,{MARINE},LifeArmorLevel', '1')],
    }.items():
        assert not any(e.get('id') == ident for e in up)
        e = E.SubElement(up, 'CUpgrade', id=ident)
        for ref, value in refs: E.SubElement(e, 'EffectArray', Reference=ref, Value=value)
    for level in range(1, 4):
        for family in ['Weapons', 'Armors']:
            ident = f'TerranInfantry{family}Level{level}'
            e = next((e for e in up if e.get('id') == ident), None)
            if e is None: e = E.SubElement(up, 'CUpgrade', id=ident)
            if family == 'Armors':
                E.SubElement(e, 'EffectArray', Operation='Set', Reference=f'Actor,{MARINE},LifeArmorIcon', Value=f'Assets\\Textures\\btn-upgrade-terran-infantryarmorlevel{level}.dds')
            else:
                E.SubElement(e, 'EffectArray', Operation='Set', Reference='Weapon,RMK_MarineMengskGaussRifle,Icon', Value=f'Assets\\Textures\\btn-upgrade-terran-infantryweaponslevel{level}.dds')
    for name, r in cats.items(): files[GD + name + '.xml'] = E.tostring(r, encoding='utf-8', xml_declaration=True)


STRINGS = {
    'Button/Name/RMK_MarineMengskVeterancy': '3등급 정예 용병 /// Rank 3 Elite Mercenary',
    'Button/Tooltip/RMK_MarineMengskVeterancy': '처음부터 3등급 능력치와 진급 능력을 갖고 소환됩니다. 경험치 성장은 없습니다. 보병 공격력·방어력과 해당 유닛의 미션 연구가 적용됩니다. /// Hired with rank 3 stats and rank abilities. Does not gain experience. Receives infantry weapon and armor upgrades and applicable mission research.',
    'Behavior/Name/RMK_MengskVeterancyMarineMengsk': '3등급 코랄의 후예 /// Rank 3 Heir of Korhal',
    'Button/Tooltip/RM3_HireKorhal': '3등급 코랄의 후예 4기를 고용합니다. 기당 인구 2, 총 인구 8. 보병 공방업과 해당 미션 연구가 적용됩니다. /// Hires 4 rank 3 Heirs of Korhal. 2 supply each, 8 total. Receives infantry weapon/armor upgrades and applicable mission research.',
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        patch(files)
        for loc in ('kokr',) + LOCALES:
            path = M3 + loc + '.sc2data/localizeddata/gamestrings.txt'
            values = STRINGS if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in STRINGS.items()}
            files[path] = update_lines(files[path], values)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for n in files:
            if n != 'metadata.txt' and not n.startswith(M3): assert files[n] == prev.read(n), n
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
