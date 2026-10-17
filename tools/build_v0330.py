#!/usr/bin/env python3
"""Build CCM 0.3.30 from 0.3.29 (3번 미션).

사용자 보고·지시 (2026-10-17):
1. "원시저그 포탑이 공격하지 않음" — 원시 벌레 무기가 쓰는 포탑 회전 데이터 NydusCanalAttacker가 맵에 없었다
   (군단 모드에만 있음, 0.3.28 이식 도구가 포탑 파일을 따라가지 않음). 포탑 없이는 조준을 못 해 공격하지 않는다.
   NydusCanalAttacker를 맵 turretdata.xml에 직접 정의한다 (360도 회전). 원본은 부모 FreeRotate지만 그 정의가 자날 층에서 확인되지 않아 값으로 적는다.
   원시 벌레 명령 칸의 빈 칸 두 개(이식에서 뺀 산성 광선·깊은 땅굴 잠금 버튼)도 지운다.
2. "보급벙커랑 벙커가 있어야 함, 멩스크 모드에서 찾을 것, 둘의 차이가 큼" — 0.3.1~0.3.29의 보급 벙커(RM3_SupplyBunker)는
   일반 벙커를 복제하고 멩스크 모델만 씌운 것이었다. 협동전 멩스크 사령관의 진짜 보급 벙커 BunkerDepotMengsk를 옮긴다
   (보급 12, 생명력 400, 장갑 1, 6칸, 탑승 병력 사거리 +1, 회수, 집결 지점, 점막 위 건설 가능 발판).
   일반 벙커는 그대로 둔다. SCV 건설 버튼과 공학 연구소 '보급 벙커 건설 해금' 연구가 이 진짜 유닛을 가리키게 한다.
   모드 변경: 원본은 멩스크 부대원·노동자만 탑승할 수 있다. 레이너에게는 그 유닛이 없으므로 탑승 제한을 풀었다
   (생체 지상 유닛이면 탑승, 원래 벙커와 같은 조건).
   멩스크 부대원 징집(EnlistNearby), 자극제 전달, 투하형 보급 벙커, 사령관 레벨 잠금은 따라오지 않게 했다.
   건물 장갑 +2 연구는 새 보급 벙커에도 적용한다.

Usage: python3 tools/build_v0330.py <0.3.29 zip> <new output zip>
"""
import argparse
import copy
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.3.29', b'version=0.3.30'
M3 = 'TRaynor03.SC2Map'
GD = M3 + '/base.sc2data/gamedata/'
BUNKER_DROP = r'EnlistNearby|StimpackMengskRedirect|BunkerDepotMengskDrop|MengskLevel'

TURRET = '<CTurret id="NydusCanalAttacker"><YawArc value="360" /><YawRate value="720" /><YawIdleRate value="360" /></CTurret>'
# co-op arcturusmengsk models/actor the template expects but the port does not pull
BUNKER_MODELS = ('<CModel id="BunkerDepotMengskBuild" parent="BunkerBuildBase"><ScaleMax value="0.450000,0.450000,0.450000" />'
                 '<ScaleMin value="0.450000,0.450000,0.450000" /></CModel>'
                 '<CModel id="BunkerDepotMengskPortrait" parent="AdjutantPortrait" />'
                 r'<CModel id="BunkerDepotMengskPlacement" parent="BunkerPlacementBase"><Model value="Assets\Buildings\Terran\BunkerPlacement\BunkerPlacement.m3" /></CModel>')
# co-op strings that came over without Korean (official terms where they exist)
KO_FIX = {
    'Abil/Name/ArtilleryMengskTransport': '탑재 (자치령 대포) /// Load (Artillery)',
    'Abil/Name/BunkerMengskSalvage': '회수 /// Salvage',
    'Abil/Name/BunkerMengskTransport': '탑승·하차 (보급 벙커) /// Load-Unload (Supply Bunker)',
    'Abil/Name/MedivacMengskTransport': '탑승·하차 (의료선) /// Load-Unload (Medivac)',
    'Abil/Name/TrooperMengskMorphSCV': '건설로봇으로 전환 /// Morph to SCV',
    'Behavior/Name/BunkerMengskSalvage': '회수 중 /// Salvaging',
    'Behavior/Name/BunkerMengskWeaponRangeBonus': '사거리 증가 /// Range Bonus',
    'Turret/Name/ArtilleryMengsk': '자치령 대포 포탑 /// Artillery Turret',
    'Turret/Name/MissileTurretMengsk': '미사일 포탑 /// Missile Turret',
}
BUNKER_ACTOR = '<CActorModel id="BunkerDepotMengskBuild" parent="TerranBuildingBuild" />'


def xml_edit(path, fn):
    root = E.parse(path).getroot()
    fn(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def find(root, tag, i):
    r = [e for e in root if e.tag == tag and e.get('id') == i]
    return r[0] if r else None


def add_missing(root, xml):
    have = {(e.tag, e.get('id')) for e in root}
    for el in E.fromstring('<C>' + xml + '</C>'):
        if (el.tag, el.get('id')) not in have:
            root.append(el)


def edit(gd):
    def units(root):
        w = find(root, 'CUnit', 'DehakaNydusDestroyer')
        for card in w.findall('CardLayouts'):
            for b in list(card):
                if b.get('Face') in ('BileStreamLocked', 'DehakaDeepTunnelLocked'):
                    card.remove(b)
        assert find(root, 'CUnit', 'BunkerDepotMengsk') is not None
    xml_edit(gd / 'unitdata.xml', units)

    def abils(root):
        t = find(root, 'CAbilBuild', 'TerranBuild')
        info = [i for i in t.findall('InfoArray') if i.get('index') == 'Build17']
        assert len(info) == 1 and info[0].get('Unit') == 'RM3_SupplyBunker'
        info[0].set('Unit', 'BunkerDepotMengsk')
        tr = find(root, 'CAbilTransport', 'BunkerMengskTransport')
        for v in tr.findall('LoadValidatorArray'):
            tr.remove(v)  # mod change: Raynor's infantry may board (co-op: Mengsk troopers only)
    xml_edit(gd / 'abildata.xml', abils)

    def upgrades(root):
        u = find(root, 'CUpgrade', 'RM3_Armor')
        old = [e for e in u.findall('EffectArray') if e.get('Reference') == 'Unit,RM3_SupplyBunker,LifeArmor']
        assert len(old) == 1
        old[0].set('Reference', 'Unit,BunkerDepotMengsk,LifeArmor')
    xml_edit(gd / 'upgradedata.xml', upgrades)

    xml_edit(gd / 'modeldata.xml', lambda r: add_missing(r, BUNKER_MODELS))
    xml_edit(gd / 'actordata.xml', lambda r: add_missing(r, BUNKER_ACTOR))
    tp = gd / 'turretdata.xml'
    if tp.exists():
        xml_edit(tp, lambda r: add_missing(r, TURRET))
    else:
        root = E.Element('Catalog')
        root.append(E.fromstring(TURRET))
        E.ElementTree(root).write(tp, encoding='utf-8', xml_declaration=True)


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
                        '--skip-existing', f'--drop={BUNKER_DROP}', 'BunkerDepotMengsk'], check=True)
        (root / M3 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        edit(root / GD)
        ko = root / M3 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        text = ko.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        lines = text.split(nl)
        for i, line in enumerate(lines):
            k = line.split('=', 1)[0]
            if k in KO_FIX: lines[i] = f'{k}={KO_FIX[k]}'
        ko.write_bytes(nl.join(lines).encode('utf-8'))
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (root / M3 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        assert extra in ([], [GD + 'turretdata.xml']), extra
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra:
                    out.write(root / f, f)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names + extra
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
