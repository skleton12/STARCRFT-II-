#!/usr/bin/env python3
"""0.6.1 -> 0.6.2: 연구실 저그 1단계를 보급 벙커·멩스크 건물에 연결, 동맹 지원 증원 (사용자 2026-10-28).

사용자: "까치날개 연구하면 그 멩스크 포격 건물 풀리게 해줘, 벙커 생명력은 보급 벙커도 적용되게",
        "동맹 좀더 2~3명(마리) 추가 해줘".
대상 맵: 4·5·6번 (TTychus01, TTosh01, THanson01). 연구실은 3번 뒤에 열리므로 1~3번은 그대로.
- 까치날개 포탑(연구실 ShrikeTurret)을 고르면 SCV 기본 건설 (1,3) 칸에 대지파괴 포(협동전 멩스크 ArtilleryMengsk) 건설이 보인다.
  원작 까치날개 효과(일반 벙커 포탑)는 그대로. 이식은 port_units.py --with-mengsk.
  모드 변경: 원본 포격은 실린 노동자·부대원 수와 스크립트로 포탄을 떨어뜨린다. 이 모드에는 노동자가 없으므로
  탑재·집결·오염 공격·사거리 연구·사령관 레벨 버튼을 빼고, 무기가 직접 포탄 4발(원본 낙하 효과, 한 발 지상 100 범위 3)을
  표적 주변에 떨어뜨리게 한다. 공격 주기 10초 (원본 30초에서 노동자로 빨라지는 구조, 시험값). 건설 시간 40초 (시험값), 비용 원본 150/100.
- 강화 벙커(연구실 FortifiedBunkerCarapace)를 고르면 보급 벙커(BunkerDepotMengsk)도 생명력 +150.
  0.3.37 '보급 벙커는 협동전 업그레이드만'을 이 항목에 한해 넓힌다 (사용자 2026-10-28). 신소재 강화 장갑과 더해진다.
- 동맹 지원 묶음 증원 (5·6번 지원 버튼): 정화자 +2 (군단병 1, 피닉스 사도 1), 원시저그 +3 (원시 저글링 2, 원시 히드라 1). 동맹 돈으로 낸다.

Usage: python3 tools/build_v062.py <0.6.1 zip> <new output zip>
"""
import argparse, copy, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.6.1', b'version=0.6.2'
MAPS = {'TTychus01': 'm4', 'TTosh01': 'm5', 'THanson01': 'm6'}
SUPPORT_MAPS = ('TTosh01', 'THanson01')
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
LOCS = 'kokr dede enus eses esmx frfr itit plpl ptbr ruru zhcn zhtw'.split()
DROP = r'ExperimentalStrike|CloudSickness|ArtilleryMengskFear|MengskLevel|Prestige|ArtilleryMengskRange|CoopCaster|Mastery'
SEEDS = ['ArtilleryMengsk', 'ArtilleryMengskBombardmentDropDelayCP', 'ArtilleryMengskBombardmentDamageSearch']
KEEP_FACES = {'Salvage', 'Halt', 'CancelBuilding', 'Stop', 'SelectBuilder', 'ArtilleryMengskBombardment'}

ADD = {
    'abildata.xml': '<CAbilBuild id="TerranBuild"><InfoArray index="Build18" Unit="ArtilleryMengsk" Time="40">'
                    '<Button DefaultButtonFace="RM6_BuildArtillery" State="Available" Requirements="RM6_CanBuildArtillery" /></InfoArray></CAbilBuild>',
    'buttondata.xml': '<CButton id="RM6_BuildArtillery"><Icon value="Assets\\Textures\\btn-building-terran-artillerymengsk.dds" />'
                      '<Name value="Button/Name/RM6_BuildArtillery" /><Tooltip value="Button/Tooltip/RM6_BuildArtillery" />'
                      '<TooltipFlags index="ShowLevel" value="0" /></CButton>',
    'requirementnodedata.xml': '<CRequirementCountUpgrade id="RM6_ShrikeDone"><Count Link="ShrikeTurret" State="CompleteOnly" /></CRequirementCountUpgrade>',
    'requirementdata.xml': '<CRequirement id="RM6_CanBuildArtillery"><NodeArray index="Show" Link="RM6_ShrikeDone" />'
                           '<NodeArray index="Use" Link="RM6_ShrikeDone" /></CRequirement>',
    'effectdata.xml': '<CEffectCreatePersistent id="RM6_ArtyVolley"><EditorCategories value="Race:Terran" />'
                      '<WhichLocation Value="TargetUnitOrPoint" /><PeriodCount value="4" /><PeriodicPeriodArray value="0.3" />'
                      '<PeriodicEffectArray value="ArtilleryMengskBombardmentDropDelayCP" />'
                      '<PeriodicOffsetArray value="0,0,0" /><PeriodicOffsetArray value="2,1.5,0" />'
                      '<PeriodicOffsetArray value="-2,1,0" /><PeriodicOffsetArray value="0.5,-2,0" /></CEffectCreatePersistent>',
    # The unit template also wants these (same fix as the supply bunker in 0.3.30).
    'modeldata.xml': '<CModel id="ArtilleryMengskPortrait" parent="AdjutantPortrait" />'
                     '<CModel id="ArtilleryMengskBuild" parent="MissileTurretBuildBase"><ScaleMax value="0.930000,0.930000,0.930000" />'
                     '<ScaleMin value="0.930000,0.930000,0.930000" /><Model value="Assets\\Buildings\\Terran\\TerranBuild\\TerranBuild.m3" /></CModel>',
    'actordata.xml': '<CActorModel id="ArtilleryMengskBuild" parent="TerranBuildingBuildSmall" />',
    'upgradedata.xml': '<CUpgrade id="FortifiedBunkerCarapace"><EffectArray Reference="Unit,BunkerDepotMengsk,LifeMax" Value="150" />'
                       '<EffectArray Reference="Unit,BunkerDepotMengsk,LifeStart" Value="150" /><AffectedUnitArray value="BunkerDepotMengsk" /></CUpgrade>',
}
STRINGS = {
    'Unit/Name/ArtilleryMengsk': '대지파괴 포 /// Earthsplitter Ordnance',
    'Button/Name/RM6_BuildArtillery': '대지파괴 포 건설 /// Build Earthsplitter Ordnance',
    'Button/Tooltip/RM6_BuildArtillery': '먼 거리의 지상 표적 주변에 포탄 4발을 떨어뜨리는 포격 건물입니다. 연구실에서 까치날개 포탑을 고르면 지을 수 있습니다. '
                                         '/// An artillery structure that drops 4 shells around a distant ground target. Available once Shrike Turret is chosen in the lab.',
    'Button/Name/ArtilleryMengskBombardment': '포격 /// Bombardment',
    'Button/Tooltip/ArtilleryMengskBombardment': '표적 주변에 포탄 4발을 떨어뜨립니다. 한 발마다 주변 지상 적에게 피해 100을 줍니다. '
                                                 '/// Drops 4 shells around the target. Each deals 100 damage to nearby enemy ground units.',
    'Weapon/Name/ArtilleryMengskBombardment': '포격 /// Bombardment',
}


def find(root, tag, i):
    r = [e for e in root if e.tag == tag and e.get('id') == i]
    assert len(r) == 1, (tag, i, len(r))
    return r[0]


def xml_edit(path, fn):
    root = E.parse(path).getroot()
    fn(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def add_xml(path, xml):
    def go(root):
        for el in E.fromstring('<C>' + xml + '</C>'):
            hit = [e for e in root if e.tag == el.tag and e.get('id') == el.get('id')]
            if hit:
                if el.get('id') == 'TerranBuild': hit[0].extend(list(el))
            else:
                root.append(el)
    xml_edit(path, go)


def edit_map(d):
    g = d / GD

    def units(root):
        a = find(root, 'CUnit', 'ArtilleryMengsk')
        for ab in list(a.findall('AbilArray')):
            if ab.get('Link') in ('ArtilleryMengskTransport', 'Rally'):
                a.remove(ab)
        for card in a.findall('CardLayouts'):
            for b in list(card):
                if b.get('Face') not in KEEP_FACES:
                    card.remove(b)
        scv = find(root, 'CUnit', 'SCV')
        cards = [c for c in scv.findall('CardLayouts') if c.get('index') == '1']
        assert len(cards) == 1
        cards[0].append(E.fromstring('<LayoutButtons Face="RM6_BuildArtillery" Type="AbilCmd" AbilCmd="TerranBuild,Build18" Row="1" Column="3" />'))
    xml_edit(g / 'unitdata.xml', units)

    def weapons(root):
        w = find(root, 'CWeaponLegacy', 'ArtilleryMengskBombardment')
        w.find('Effect').set('value', 'RM6_ArtyVolley')
        w.find('Period').set('value', '10')
    xml_edit(g / 'weapondata.xml', weapons)
    for fn, xml in ADD.items():
        add_xml(g / fn, xml)


def script(t, tag, support):
    nl = '\r\n' if '\r\n' in t else '\n'
    t = t.replace('\r\n', '\n')
    a = '    TechTreeUnitAllow(1,"MarauderMengsk",true);\n'
    assert t.count(a) == 1
    t = t.replace(a, a + '    TechTreeUnitAllow(1,"ArtilleryMengsk",true);\n')
    if support:
        a = f'        gf_{tag}_SupAdd(p,"AdeptFenix");\n'
        assert t.count(a) == 1, a
        t = t.replace(a, a + f'        // 0.6.2: +2 per group (user 2026-10-28 "동맹 좀더 2~3명 추가").\n'
                             f'        gf_{tag}_SupAdd(p,"ZealotPurifier");\n        gf_{tag}_SupAdd(p,"AdeptFenix");\n')
        a = f'    for (k=0;k<4;k+=1) {{ gf_{tag}_SupAdd(p,"DehakaZerglingLevel2"); }}\n'
        assert t.count(a) == 1, a
        t = t.replace(a, f'    // 0.6.2: +3 per group (user 2026-10-28): 2 more zerglings, 1 more hydralisk.\n'
                         f'    for (k=0;k<6;k+=1) {{ gf_{tag}_SupAdd(p,"DehakaZerglingLevel2"); }}\n')
        a = f'    gf_{tag}_SupAdd(p,"DehakaHydraliskLevel2");\n'
        assert t.count(a) == 1, a
        t = t.replace(a, a + a)
        # Room for the larger groups (Primal: 6+1+2 + unlocks 2 + tiers 6 = 17).
        for a, b, n in ((f'string[16][16] gv_{tag}_supKind;', f'string[16][20] gv_{tag}_supKind;', 1),
                        (f'point[16][16] gv_{tag}_supAt;', f'point[16][20] gv_{tag}_supAt;', 1),
                        (f'    if (gv_{tag}_supN[p]>=16) {{ return; }}', f'    if (gv_{tag}_supN[p]>=20) {{ return; }}', 1),
                        ('    string[16] kind;\n    point[16] at;\n    actor[16] fx;\n', '    string[20] kind;\n    point[20] at;\n    actor[20] fx;\n', 2)):
            assert t.count(a) == n, a
            t = t.replace(a, b)
    return t.replace('\n', nl)


def set_lines(raw, vals):
    t = raw.decode('utf-8-sig')
    bom = raw.startswith(b'\xef\xbb\xbf')
    nl = '\r\n' if '\r\n' in t else '\n'
    lines = t.replace('\r\n', '\n').rstrip('\n').split('\n')
    idx = {l.split('=', 1)[0]: i for i, l in enumerate(lines) if '=' in l}
    for k, v in vals.items():
        if k in idx: lines[idx[k]] = f'{k}={v}'
        else: lines.append(f'{k}={v}')
    return (b'\xef\xbb\xbf' if bom else b'') + ('\n'.join(lines) + '\n').replace('\n', nl).encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m, tag in MAPS.items():
            d = root / f'{m}.SC2Map'
            subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(d), '--liberty-base', '--with-mengsk',
                            '--skip-existing', f'--drop={DROP}'] + SEEDS, check=True, stdout=subprocess.DEVNULL)
            (d / 'ported_shared_refs.txt').unlink(missing_ok=True)
            edit_map(d)
            s = d / 'mapscript.galaxy'
            s.write_bytes(script(s.read_bytes().decode('utf-8'), tag, m in SUPPORT_MAPS).encode('utf-8'))
            ko = set_lines((d / KO).read_bytes(), STRINGS)
            (d / KO).write_bytes(ko)
            V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
            for loc in LOCS:
                h = d / f'{loc}.sc2data/localizeddata/gamehotkeys.txt'
                h.write_bytes(set_lines(h.read_bytes(), {'Button/Hotkey/RM6_BuildArtillery': 'O'}))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        for f in files:
            if f.endswith('.xml'): E.parse(root / f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra:
                    out.write(root / f, f)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names + extra
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in MAPS) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, 'new files:', extra)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
