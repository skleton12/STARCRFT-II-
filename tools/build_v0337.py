#!/usr/bin/env python3
"""Build CCM 0.3.37 from 0.3.36: 보급 벙커에는 협동전 업그레이드를 적용 (3번 미션).

사용자 지시 (2026-10-18): "ㄴㄴ 보급 벙커는 협동전 업그레이드가 적용되게 해줘."
  - 0.3.36에서 보급 벙커에 붙인 자날 캠페인 업그레이드(신소재 강철 벙커·강화 벙커·화재 진압)를 되돌린다.
  - 멩스크 협동전 공학 연구소 연구 두 개를 3번 맵 공학 연구소에 넣는다 (협동전 데이터 그대로):
      신소재 강화 장갑 (MengskStructureArmor): 광물 100·가스 100·90초. 보급 벙커 생명력 +200, 방어력 +2, 강화 외형.
      조준 지원 총안 (BunkerDepotMengskRange): 광물 100·가스 100·60초. 보급 벙커 안 유닛 사거리 +1 더.
    보급 벙커 명령 칸의 두 연구 표시(이미 있음)는 협동전 그대로 연구가 끝나면 보인다.
  - 신소재 강화 장갑의 미사일 포탑·대지파괴 포 효과는 그 유닛이 이 모드에 없어서 뺀다.
  - 모드 연구 '건물 장갑 +2'(RM3_Armor)에서 보급 벙커를 뺀다. 보급 벙커 방어력은 협동전 연구로만 오른다 (겹침 방지).
  - 협동전 보급 벙커 사거리 행동에 원래 들어 있던 자날 탄환 가속기 효과는 협동전 데이터 그대로 둔다.
일반 벙커는 그대로다 (원작 외형·자날 업그레이드).

Usage: python3 tools/build_v0337.py <0.3.36 zip> <new output zip>
"""
import argparse
import copy
import re
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.3.36', b'version=0.3.37'
M3 = 'TRaynor03.SC2Map'
GD = M3 + '/base.sc2data/gamedata/'
PORT = ('MengskStructureArmor', 'BunkerDepotMengskRange', 'LearnMengskStructureArmor', 'LearnBunkerDepotMengskRange',
        'HaveMengskStructureArmor', 'HaveBunkerDepotMengskRange', 'StructureArmorMengskResearch',
        'BunkerDepotMengskRangeResearch', 'StructureArmorMengsk')
DROP = r'MissileTurretMengsk|ArtilleryMengsk|MengskLevel|Prestige'
# co-op research button for the armor is StructureArmorMengskResearch (MengskStructureArmorResearch has no button record)
# only the supply bunker exists in this mod (no Mengsk missile turret / Earthsplitter)
KO_FIX = {
    'Button/Tooltip/StructureArmorMengskResearch': '<c val="ffff8a">보급 벙커</c>의 생명력이 200, 방어력이 2 증가합니다. /// Increases the life of <c val="ffff8a">Supply Bunkers</c> by 200 and their armor by 2.',
    'Upgrade/Name/MengskStructureArmor': '신소재 강화 장갑 /// Neosteel Fortified Armor',
}
RESEARCH = [
    ('Research8', 'MengskStructureArmor', 90, 'StructureArmorMengskResearch', 'LearnMengskStructureArmor', 0, 2),
    ('Research9', 'BunkerDepotMengskRange', 60, 'BunkerDepotMengskRangeResearch', 'LearnBunkerDepotMengskRange', 0, 3),
]


def xml_edit(path, fn):
    root = E.parse(path).getroot()
    fn(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def only(root, tag, i):
    r = [e for e in root if e.tag == tag and e.get('id') == i]
    assert len(r) == 1, (tag, i, len(r))
    return r[0]


def edit(gd):
    def upgrades(root):
        # undo 0.3.36 (WoL campaign upgrades on the supply bunker)
        for i in ('NeoSteelFrame', 'FortifiedBunkerCarapace'):
            root.remove(only(root, 'CUpgrade', i))
        a = only(root, 'CUpgrade', 'MengskStructureArmor')
        for e in list(a.findall('EffectArray')):
            if re.search(r'MissileTurretMengsk|ArtilleryMengsk', e.get('Reference', '')):
                a.remove(e)
        for e in list(a.findall('AffectedUnitArray')):
            if e.get('value') in ('MissileTurretMengsk', 'ArtilleryMengsk'):
                a.remove(e)
        assert a.findall('EffectArray'), 'MengskStructureArmor lost its effects'
        r = only(root, 'CUpgrade', 'RM3_Armor')
        old = [e for e in r.findall('EffectArray') if e.get('Reference') == 'Unit,BunkerDepotMengsk,LifeArmor']
        assert len(old) == 1
        r.remove(old[0])
    xml_edit(gd / 'upgradedata.xml', upgrades)

    def units(root):
        u = only(root, 'CUnit', 'BunkerDepotMengsk')
        fs = [b for b in u.findall('BehaviorArray') if b.get('Link') == 'FireSuppressionSystem']
        assert len(fs) == 1
        u.remove(fs[0])
        bay = [e for e in root if e.tag == 'CUnit' and e.get('id') == 'EngineeringBay']
        card = bay[-1].find('CardLayouts')
        for idx, up, t, face, req, row, col in RESEARCH:
            card.append(E.fromstring(f'<LayoutButtons Face="{face}" Type="AbilCmd" AbilCmd="RM3_BayResearch,{idx}" Row="{row}" Column="{col}" />'))
    xml_edit(gd / 'unitdata.xml', units)

    def abils(root):
        a = only(root, 'CAbilResearch', 'RM3_BayResearch')
        have = {i.get('index') for i in a.findall('InfoArray')}
        for idx, up, t, face, req, row, col in RESEARCH:
            assert idx not in have
            a.append(E.fromstring(f'<InfoArray index="{idx}" Time="{t}" Upgrade="{up}"><Resource index="Minerals" value="100" />'
                                  f'<Resource index="Vespene" value="100" /><Button DefaultButtonFace="{face}" State="Available" Requirements="{req}" /></InfoArray>'))
    xml_edit(gd / 'abildata.xml', abils)


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(root / M3), '--liberty-base', '--with-mengsk',
                        '--skip-existing', f'--drop={DROP}', *PORT], check=True)
        (root / M3 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        edit(root / GD)
        ko = root / M3 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        text = ko.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        lines = text.split(nl)
        done = set()
        for i, line in enumerate(lines):
            k = line.split('=', 1)[0]
            if k in KO_FIX: lines[i] = f'{k}={KO_FIX[k]}'; done.add(k)
        lines += [f'{k}={v}' for k, v in KO_FIX.items() if k not in done]
        ko.write_bytes(nl.join(lines).encode('utf-8'))
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (root / M3 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        assert [f for f in files if f not in names] == []
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not n.startswith(M3 + '/') and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
