#!/usr/bin/env python3
"""Build CCM 0.4.1 from 0.3.37: 4번 미션 TTychus01 (Smash and Grab) 추가.

원본: 사용자 구글 드라이브의 풀어 놓은 ttychus01.sc2map 폴더 (traynor03 mapinfo가 저장소 원본과 같아 원본으로 판단).
공통 묶음 (docs/missions/nonlinear_design.md):
  - 3번 맵의 모드 데이터·에셋을 그대로 가져온다 (용병, 자극제 한 줄 등 연구, 보급 벙커, 동맹 유닛·외형).
    단 3번이 전역으로 바꾼 수정탑 모델(Pylon*)은 빼고, 동맹 수정탑에만 정화자 외형을 씌운다 (적 탈다림도 수정탑을 씀).
  - 동맹 8 정화자 / 9 원시저그. 차원 관문 최대 3, 원시 감시자 최대 3 (사용자 확정 2026-10-18).
  - 7-1: 탈다림(3~6) 능력치 강화, 저그(2) 레이너 공세 +50% (시험값).
  - 레이너 병력: 해병→전쟁광, 의무관→스키비의 천사, 불곰→망치 경호대, 화염방사병→악마의 개 (해금 상태는 원작 그대로).
지형·트리거 데이터·지역은 원본 그대로 둔다.

Usage: python3 tools/build_v041.py <0.3.37 zip> <ttychus01 folder> <new output zip>
"""
import argparse
import copy
import re
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import patch_mission01 as m1

OLD, NEW = b'version=0.3.37', b'version=0.4.1'
M3, M4 = 'TRaynor03.SC2Map/', 'TTychus01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
DROP_MODELS = {'Pylon', 'PylonBirth', 'PylonDeath', 'PylonXPR', 'PylonXPRDeath'}
ALLIES = [(8, b'Prot', '정화자', 'Purifiers'), (9, b'Zerg', '원시저그', 'Primal Zerg')]
STRINGS = {
    'MapInfo/Player08/Name': '정화자 /// Purifiers',
    'MapInfo/Player09/Name': '원시저그 /// Primal Zerg',
    'rm4/AdjName': '부관 /// Adjutant',
    'rm4/Adj1': '정화자와 원시저그가 일꾼을 보냈습니다. 동맹 일꾼을 직접 움직여 동맹 건물을 지을 수 있습니다. /// The Purifiers and Primal Zerg have sent workers. You can move the allied workers and build allied structures.',
    'rm4/Adj2': '탐사정은 수정탑·관문(차원 관문으로 바뀜, 최대 3)·광자포를, 원시 일벌레는 원시 감시자(최대 3)와 원시 벌레를 짓습니다. 동맹은 그 건물에서 자기 자원으로 병력을 보냅니다. /// The Probe builds Pylons, Gateways (become Warp Gates, max 3) and Photon Cannons; Primal Drones build Primal Wardens (max 3) and Primal Wurms. The allies send forces from them with their own resources.',
    'Button/Name/RM_HammerSecurity': '망치 경호대 훈련 /// Train Hammer Security',
    'Button/Tooltip/RM_HammerSecurity': '용병 불곰 망치 경호대를 훈련합니다. /// Trains a Hammer Security mercenary.',
    'Button/Name/RM_DevilDog': '악마의 개 훈련 /// Train Devil Dog',
    'Button/Tooltip/RM_DevilDog': '용병 화염방사병 악마의 개를 훈련합니다. /// Trains a Devil Dog mercenary.',
}
SKIN = ('<C><CActorUnit id="Pylon"><On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap Pylon_Purifier_COOP" /></CActorUnit>'
        '<CActorUnit id="WarpGate"><On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap Gateway_Purifier_COOP" /></CActorUnit></C>')
PYLON_MODEL = (r'<CModel id="Pylon_Purifier_COOP" parent="Building" Race="Protoss">'
               r'<Model value="Assets\Buildings\Protoss\Pylon_Purifier_COOP\Pylon_Purifier_COOP.m3" />'
               r'<Radius value="1.000000" /><ScaleMax value="0.850000,0.850000,0.850000" /><ScaleMin value="0.850000,0.850000,0.850000" /></CModel>')


def merge(base, extra):
    """Append the original mission records into the mod catalog (same id: attributes + children added)."""
    root = E.fromstring(base)
    for new in E.fromstring(extra):
        hit = [e for e in root if e.tag == new.tag and e.get('id') == new.get('id')]
        if hit:
            hit[0].attrib.update(new.attrib); hit[0].extend(copy.deepcopy(list(new)))
        else:
            root.append(copy.deepcopy(new))
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def mapinfo(d):
    count = struct_u32(d, 0x87)
    assert count == 8 and d[0x8b] == 0
    pos = 0xa2  # player 0 is a short 23-byte record (same layout as patch_mission01.patch_mapinfo)
    for player in range(1, count):
        assert d[pos] == player, (player, pos)
        pos = d.index(0, pos + 26) + 1
    recs = b''.join(bytes([n, 2]) + b'\0' * 3 + (-1).to_bytes(4, 'little', signed=True) + race + b'\0' * 14 for n, race, *_ in ALLIES)
    out = bytearray(d[:pos] + recs + d[pos:])
    out[0x87:0x8b] = (count + len(ALLIES)).to_bytes(4, 'little')
    return bytes(out)


def struct_u32(d, o):
    return int.from_bytes(d[o:o + 4], 'little')


def waves(script):
    """Zerg attack waves at Raynor +50% (7-1 zerg = more units, trial). Only the player-wave trigger."""
    a = script.index('bool gt_ZergAttackWavesPlayer_Func')
    b = script.index('\n}\n', a)
    body = script[a:b]
    up = lambda m: m.group(1) + ', '.join(str(int(n) + int(n) // 2) for n in m.group(2).split(', ')) + m.group(3)
    body, n1 = re.subn(r'(AIAttackWaveAddUnits4\()(\d+(?:, \d+){3})(, )', up, body)
    body, n2 = re.subn(r'(CreateUnitsAtPoint2\(libNtve_gf_DifficultyValueInt\()(\d+(?:, \d+){3})(\))', up, body)
    assert n1 >= 20 and n2 == 3, (n1, n2)
    return script[:a] + body + script[b:]


def script(raw):
    t = raw.decode('utf-8-sig').replace('\r\n', '\n')
    assert t.count('"Marauder"') == 2 and '"Marine"' not in t and '"Medic"' not in t
    t = t.replace('"Marauder"', '"HammerSecurity"')
    t = waves(t)
    for anchor, add, before in [
        ('void InitGlobals () {', (HERE / 'data/mission04_support.galaxy').read_text() + '\n', True),
        ('    libCamp_gf_PurchaseStorymodeTech();\n', '    gf_m4_Init();\n', False),
        ('    if ((libNtve_gf_DifficultyValueInt(0, 0, 1, 1) == 1)) {\n        TimerStart(gv_achievementHardTimer', '    gf_m4_Start();\n', True)]:
        assert t.count(anchor) == 1, anchor
        t = t.replace(anchor, add + anchor if before else anchor + add, 1)
    return t.encode('utf-8')


def objects(data):
    root = E.fromstring(data)
    n = 0
    for el in root:
        if el.tag == 'ObjectUnit' and el.get('Player') == '1' and el.get('UnitType') in ('Marine', 'Medic'):
            el.set('UnitType', {'Marine': 'WarPig', 'Medic': 'MercMedic'}[el.get('UnitType')]); n += 1
    assert n == 4
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def strings(orig, mod3, orig3_keys):
    text = orig.decode('utf-8-sig').replace('\r\n', '\n').rstrip('\n')
    have = {l.split('=', 1)[0] for l in text.split('\n') if '=' in l}
    add = {}
    for line in mod3.decode('utf-8-sig').replace('\r\n', '\n').split('\n'):
        if '=' not in line: continue
        k, v = line.split('=', 1)
        if k in have or k in orig3_keys or k.startswith(('MapInfo/', 'DocInfo/', 'Param/', 'rm3/')): continue
        add[k] = v
    add.update(STRINGS)
    return (text + '\n' + '\n'.join(f'{k}={v}' for k, v in add.items()) + '\n').replace('\n', '\r\n').encode('utf-8')


def build(source, folder, output, allow_missing):
    if output.exists(): raise ValueError('Output must be new')
    orig = {str(p.relative_to(folder)).replace('\\', '/'): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
    if 't3texturemasks' not in orig:
        if not allow_missing: raise SystemExit('t3texturemasks missing (terrain textures)')
        print('WARNING: t3texturemasks missing - test build only, do not deliver')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.startswith(M4) for n in prev.namelist())
        files = dict(orig)
        for n in prev.namelist():
            if not n.startswith(M3): continue
            rel = n[len(M3):]
            if rel.lower().startswith('assets/'): files[rel] = prev.read(n)
            elif rel.startswith(GD) and not rel.endswith('terraindata.xml'):
                files[rel] = merge(prev.read(n), orig[rel]) if rel in orig else prev.read(n)
        md = E.fromstring(files[GD + 'modeldata.xml'])
        for e in [e for e in md if e.tag == 'CModel' and e.get('id') in DROP_MODELS]: md.remove(e)
        md.append(E.fromstring(PYLON_MODEL))
        files[GD + 'modeldata.xml'] = E.tostring(md, encoding='utf-8', xml_declaration=True)
        files[GD + 'actordata.xml'] = merge(files[GD + 'actordata.xml'], SKIN.encode())
        orig3 = prev.read(M3 + KO)
        import mpyq
        # original mission 3 keys: its narrative strings stay out of mission 4
        o3k = {l.split('=', 1)[0] for l in mpyq.MPQArchive(str(HERE.parent / 'maps/original_wol/TRaynor03.SC2Map')).read_file('koKR.SC2Data\\LocalizedData\\GameStrings.txt').decode('utf-8-sig').splitlines() if '=' in l}
        files[KO] = strings(orig[KO], orig3, o3k)
        V35.gate('kokr', files[KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[KO])
        files['objects'] = objects(files['objects'])
        files['mapinfo'] = mapinfo(files['mapinfo'])
        saved = m1.ALLY_PLAYERS
        m1.ALLY_PLAYERS = ALLIES
        try: files['documentheader'] = m1.patch_header(files['documentheader'])
        finally: m1.ALLY_PLAYERS = saved
        files['mapscript.galaxy'] = script(files['mapscript.galaxy'])
        for name, data in orig.items():
            if name.startswith('t3') or name in ('triggers', 'regions', 'paintedpathinglayer', 'documentinfo'):
                assert files[name] == data, name
        for name, data in files.items():
            if name.endswith('.xml') or name == 'objects': E.fromstring(data)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    out.writestr(copy.copy(info), d)
                for name in sorted(files): out.writestr(M4 + name, files[name])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and len(out.namelist()) == len(set(out.namelist()))
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('folder', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--allow-missing-texture', action='store_true')
    a = p.parse_args(); build(a.source, a.folder, a.output, a.allow_missing_texture)
