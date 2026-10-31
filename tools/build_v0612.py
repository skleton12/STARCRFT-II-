#!/usr/bin/env python3
"""0.6.11 -> 0.6.12: 해병 '멀티샷' 연구 (사용자 2026-10-31 "멀티샷 업그레이드 만들 수 있음, 마린 쪽에" →
"총을 한 번 쏠 때 2번 나감, 사실상 1번 쏠 때 2마리에게 그 총알이 나간다고 생각하면 됨", 대상 전쟁광 + 코랄의 후예, 공학 연구소).

모드에서 재설계한 미션 내 연구 (원작에 없는 연구). 3·4·5·6번 맵 (공학 연구소 RM3_BayResearch가 있는 맵).
- 연구 RM6_Multishot: 공학 연구소 첫 화면 2행 2열, 단축키 M, 광물 150·가스 150·90초 (시험값).
- 효과: 해병이 한 번 쏠 때마다 맞은 적 근처(반경 4, 시험값)의 가장 가까운 다른 적 1기에게도 같은 피해의 총알이 나간다.
  두 번째 총알은 원래 피해 효과를 그대로 써서 보병 공격 업그레이드·자극제 강화(코랄의 후예 고급 자극제 피해)도 같이 받는다.
  업그레이드가 데이터 값을 바꾸는 방식(0.4.46): 탐색 반경 기본 0 → 연구 시 +4.
- 전쟁광(WarPig): 무기 KelmorianMinerGaussRifle → 효과 묶음(원래 피해 + 추가 대상 탐색).
  코랄의 후예(RMK_MarineMengsk): 무기 RMK_MarineMengskGaussRifle → 효과 묶음(원래 피해 분기 + 추가 대상 탐색).
- 두 번째 대상에 원작 해병 피격 연출(MarineAttackImpact)을 띄운다.
- 아이콘: 협동전 스완 다중 목표 무기 체계(btn-upgrade-swann-multilockweaponsystem, 이 모드에서 처음 쓰는 아이콘).

Usage: python3 tools/build_v0612.py <0.6.11 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import find, xml_edit, add_xml, set_lines, LOCS, KO, GD

OLD, NEW = b'version=0.6.11', b'version=0.6.12'
MAPS = ('TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
UP = 'RM6_Multishot'
RADIUS = '4'
COST, TIME = '150', '90'
FILTERS = 'Visible;Self,Player,Ally,Neutral,Missile,Item,Stasis,Dead,Hidden,Invulnerable'
ICON = 'Assets\\Textures\\btn-upgrade-swann-multilockweaponsystem.dds'
# (tag, weapon, original weapon effect)
SETS = (('WP', 'KelmorianMinerGaussRifle', 'KelmorianMinerDamage'),
        ('RMK', 'RMK_MarineMengskGaussRifle', 'RMK_MarineMengskGaussRifleDamageSwitch'))


def effects_xml():
    x = ''
    for tag, _, dmg in SETS:
        x += (f'<CEffectSet id="RM6_MultiHit{tag}"><EditorCategories value="Race:Terran" /><EffectArray value="{dmg}" /></CEffectSet>'
              f'<CEffectEnumArea id="RM6_MultiSearch{tag}"><EditorCategories value="Race:Terran" /><ExcludeArray Value="Target" />'
              f'<SearchFilters value="{FILTERS}" /><TargetSorts><SortArray value="TSDistanceToTarget" /></TargetSorts>'
              f'<AreaArray MaxCount="1" Radius="0" Effect="RM6_MultiHit{tag}" /></CEffectEnumArea>'
              f'<CEffectSet id="RM6_MultiSet{tag}"><EditorCategories value="Race:Terran" /><EffectArray value="{dmg}" />'
              f'<EffectArray value="RM6_MultiSearch{tag}" /></CEffectSet>')
    return x


ADD = {
    'effectdata.xml': effects_xml(),
    'upgradedata.xml': f'<CUpgrade id="{UP}"><Race value="Terr" /><Alert value="ResearchComplete" /><Icon value="{ICON}" />'
                       '<AffectedUnitArray value="WarPig" /><AffectedUnitArray value="RMK_MarineMengsk" />'
                       + ''.join(f'<EffectArray Reference="Effect,RM6_MultiSearch{t},AreaArray[0].Radius" Value="{RADIUS}" />' for t, _, _ in SETS)
                       + '</CUpgrade>',
    'buttondata.xml': f'<CButton id="{UP}"><Icon value="{ICON}" /><Name value="Button/Name/{UP}" />'
                      f'<Tooltip value="Button/Tooltip/{UP}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>',
    'actordata.xml': '<CActorModel id="RM6_MultiImpact" parent="ModelAnimationStyleOneShot"><Model value="MarineAttackImpact" />'
                     '<Terms value="Cap 1" />'
                     + ''.join(f'<On Terms="Effect.RM6_MultiHit{t}.Start; At Target" Send="Create" />' for t, _, _ in SETS)
                     + '<On Terms="ActorOrphan" Send="Destroy" /><Host Subject="_Selectable" /><HostSiteOps Ops="SOpAttachRandomDamage" /></CActorModel>',
}
STRINGS = {
    f'Upgrade/Name/{UP}': '멀티샷 /// Multishot',
    f'Button/Name/{UP}': '멀티샷 연구 /// Research Multishot',
    f'Button/Tooltip/{UP}': '전쟁광과 코랄의 후예가 한 번 쏠 때마다 맞은 적 근처(반경 4)의 다른 적 1기에게도 같은 피해의 총알을 쏩니다. 보병 공격 업그레이드가 함께 적용됩니다. '
                            '/// Each shot from War Pigs and Heirs of Korhal also hits one more enemy within 4 range of the target for the same damage. Infantry weapon upgrades apply.',
}
ALLOW_ANCHOR = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",0),true);\n'


def edit_map(d):
    g = d / GD

    def weapons(root):
        for tag, wid, dmg in SETS:
            hit = [e for e in root if e.get('id') == wid]
            if hit:
                eff = hit[0].find('Effect')
                assert eff.get('value') == dmg, wid
                eff.set('value', f'RM6_MultiSet{tag}')
            else:
                root.append(E.fromstring(f'<CWeaponLegacy id="{wid}"><Effect value="RM6_MultiSet{tag}" /></CWeaponLegacy>'))
    xml_edit(g / 'weapondata.xml', weapons)
    for fn, xml in ADD.items():
        add_xml(g / fn, xml)

    def abils(root):
        r = find(root, 'CAbilResearch', 'RM3_BayResearch')
        assert not [i for i in r.findall('InfoArray') if i.get('index') == 'Research21']
        r.append(E.fromstring(f'<InfoArray index="Research21" Time="{TIME}" Upgrade="{UP}">'
                              f'<Resource index="Minerals" value="{COST}" /><Resource index="Vespene" value="{COST}" />'
                              f'<Button DefaultButtonFace="{UP}" State="Available" /></InfoArray>'))
    xml_edit(g / 'abildata.xml', abils)

    def units(root):
        bay = find(root, 'CUnit', 'EngineeringBay')
        page = [c for c in bay.findall('CardLayouts') if c.get('index') == '0']
        assert len(page) == 1 and not [b for b in page[0] if (b.get('Row'), b.get('Column')) == ('2', '2')]
        page[0].append(E.fromstring(f'<LayoutButtons Face="{UP}" Type="AbilCmd" AbilCmd="RM3_BayResearch,Research21" Row="2" Column="2" />'))
    xml_edit(g / 'unitdata.xml', units)

    p = d / 'mapscript.galaxy'
    raw = p.read_bytes().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    assert t.count(ALLOW_ANCHOR) == 1
    t = t.replace(ALLOW_ANCHOR, ALLOW_ANCHOR + '    // 0.6.12: Multishot research (Engineering Bay).\n'
                  '    TechTreeAbilityAllow(1,AbilityCommand("RM3_BayResearch",20),true);\n'
                  f'    TechTreeUpgradeAllow(1,"{UP}",true);\n')
    p.write_bytes(t.replace('\n', nl).encode('utf-8'))


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
                h.write_bytes(set_lines(h.read_bytes(), {f'Button/Hotkey/{UP}': 'M'}))
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
