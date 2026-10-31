#!/usr/bin/env python3
"""0.6.2 -> 0.6.3: 대지파괴 포 기본 사거리 20, 강화 연구 '반구형 가속제' (사용자 2026-10-31).

근거: docs/missions/NEXT_artillery_prometheus_2026-10-31.md (GPT 기록, 사용자 지정·제시 값)와 사용자 "그 대지 파괴포의 새로운 연구… 해도됨".
대상 맵: 4·5·6번 (TTychus01, TTosh01, THanson01).
- 기본 사거리 50 → 20 (사용자 지정). 최소 사거리 7은 그대로.
- 공학 연구소 협동전 페이지 (1,0)에 '반구형 가속제' 연구 (RM6_ArtyAccel, 단축키 A). 까치날개 포탑을 골라 대지파괴 포가 열렸을 때만 보인다.
  연구하면 (업그레이드가 데이터 값을 바꾸는 방식, 0.4.46):
    포격 1회 포탄 4 → 8발 (사용자 지정), 공격 속도 +50% = 주기 10초 → 6.67초 (사용자 제시),
    사거리 +8 (사용자 범위 +5~10 중 시험값), 포탄 피해 100 → 120 (+20%, 시험값; GPT 제안이며 사용자 미확정).
  비용 100/100·60초 (미션 연구 공통 시험값).

Usage: python3 tools/build_v063.py <0.6.2 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import find, xml_edit, add_xml, set_lines, LOCS, KO, GD

OLD, NEW = b'version=0.6.2', b'version=0.6.3'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
BASE_RANGE, ADD_RANGE, ADD_SHELLS, FAST_PERIOD, ADD_DAMAGE = '20', '8', '4', '6.6667', '20'
EXTRA_OFFSETS = ('-1.5,-1.5,0', '2.5,-0.5,0', '-0.5,2.5,0', '1,1,0')

ADD = {
    'upgradedata.xml': '<CUpgrade id="RM6_ArtyAccel"><Race value="Terr" /><Alert value="ResearchComplete" />'
                       '<AffectedUnitArray value="ArtilleryMengsk" />'
                       f'<EffectArray Reference="Effect,RM6_ArtyVolley,PeriodCount" Value="{ADD_SHELLS}" />'
                       f'<EffectArray Operation="Set" Reference="Weapon,ArtilleryMengskBombardment,Period" Value="{FAST_PERIOD}" />'
                       f'<EffectArray Reference="Weapon,ArtilleryMengskBombardment,Range" Value="{ADD_RANGE}" />'
                       f'<EffectArray Reference="Effect,ArtilleryMengskBombardmentDamage,Amount" Value="{ADD_DAMAGE}" /></CUpgrade>',
    'buttondata.xml': '<CButton id="RM6_ArtyAccel"><Icon value="Assets\\Textures\\btn-upgrade-mengsk-engineeringbay-improvedartilleryrange.dds" />'
                      '<Name value="Button/Name/RM6_ArtyAccel" /><Tooltip value="Button/Tooltip/RM6_ArtyAccel" />'
                      '<TooltipFlags index="ShowLevel" value="0" /></CButton>',
    'requirementnodedata.xml': '<CRequirementCountUpgrade id="RM6_ArtyAccelQueued"><Count Link="RM6_ArtyAccel" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
                               '<CRequirementNot id="RM6_ArtyAccelNotQueued"><OperandArray index="0" value="RM6_ArtyAccelQueued" /></CRequirementNot>'
                               '<CRequirementAnd id="RM6_ArtyAccelShow"><OperandArray value="RM6_ShrikeDone" /><OperandArray value="RM6_ArtyAccelNotQueued" /></CRequirementAnd>',
    'requirementdata.xml': '<CRequirement id="RM6_ArtyAccelLearn"><NodeArray index="Show" Link="RM6_ArtyAccelShow" /></CRequirement>',
}
STRINGS = {
    'Upgrade/Name/RM6_ArtyAccel': '반구형 가속제 /// Hemispheric Accelerants',
    'Button/Name/RM6_ArtyAccel': '반구형 가속제 연구 /// Research Hemispheric Accelerants',
    'Button/Tooltip/RM6_ArtyAccel': '대지파괴 포의 포격 1회 포탄이 4발에서 8발로 늘고, 공격 속도 +50%, 사거리 +8, 포탄 피해 +20%가 됩니다. '
                                    '/// Earthsplitter Ordnance drops 8 shells per bombardment instead of 4, with +50% attack speed, +8 range and +20% shell damage.',
    'Button/Tooltip/RM6_BuildArtillery': '사거리 20 안의 지상 표적 주변에 포탄 4발을 떨어뜨리는 포격 건물입니다. 연구실에서 까치날개 포탑을 고르면 지을 수 있습니다. '
                                         '공학 연구소의 반구형 가속제로 강화합니다. '
                                         '/// An artillery structure that drops 4 shells around a ground target within range 20. Available once Shrike Turret is chosen in the lab. '
                                         'Upgraded by Hemispheric Accelerants at the Engineering Bay.',
}


def edit_map(d):
    g = d / GD

    def weapons(root):
        find(root, 'CWeaponLegacy', 'ArtilleryMengskBombardment').find('Range').set('value', BASE_RANGE)
    xml_edit(g / 'weapondata.xml', weapons)

    def effects(root):
        v = find(root, 'CEffectCreatePersistent', 'RM6_ArtyVolley')
        assert len(v.findall('PeriodicOffsetArray')) == 4
        for o in EXTRA_OFFSETS:
            v.append(E.fromstring(f'<PeriodicOffsetArray value="{o}" />'))
    xml_edit(g / 'effectdata.xml', effects)

    def abils(root):
        r = find(root, 'CAbilResearch', 'RM3_BayResearch')
        assert not [i for i in r.findall('InfoArray') if i.get('index') == 'Research20']
        r.append(E.fromstring('<InfoArray index="Research20" Time="60" Upgrade="RM6_ArtyAccel">'
                              '<Resource index="Minerals" value="100" /><Resource index="Vespene" value="100" />'
                              '<Button DefaultButtonFace="RM6_ArtyAccel" State="Available" Requirements="RM6_ArtyAccelLearn" /></InfoArray>'))
    xml_edit(g / 'abildata.xml', abils)

    def units(root):
        bay = find(root, 'CUnit', 'EngineeringBay')
        page = [c for c in bay.findall('CardLayouts') if c.get('CardId') == 'RMC1']
        assert len(page) == 1 and not [b for b in page[0] if (b.get('Row'), b.get('Column')) == ('1', '0')]
        page[0].append(E.fromstring('<LayoutButtons Face="RM6_ArtyAccel" Type="AbilCmd" AbilCmd="RM3_BayResearch,Research20" Row="1" Column="0" />'))
    xml_edit(g / 'unitdata.xml', units)
    for fn, xml in ADD.items():
        add_xml(g / fn, xml)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            d = root / f'{m}.SC2Map'
            edit_map(d)
            ko = set_lines((d / KO).read_bytes(), STRINGS)
            (d / KO).write_bytes(ko)
            V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
            for loc in LOCS:
                h = d / f'{loc}.sc2data/localizeddata/gamehotkeys.txt'
                h.write_bytes(set_lines(h.read_bytes(), {'Button/Hotkey/RM6_ArtyAccel': 'A'}))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in MAPS) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
