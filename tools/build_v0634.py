#!/usr/bin/env python3
"""0.6.33 -> 0.6.34: 멀티샷 연구를 공학 연구소에서 병영 기술실로 (사용자 2026-11-15 "멀티샷 그 기술실/반응로에 넣어야함").

반응로는 연구를 못 하므로 병영 기술실로 옮긴다. 3·4·5·6번. 비용·시간·효과(0.6.12/0.6.28)는 그대로.
- 3번: 기술실 첫 화면 1행 2열 (전투 방패·레이저 조준 옆).
- 4·5·6번: 기술실 첫 화면이 꽉 차 있어 '협동전 연구' 페이지(RMC1) 1행 1열.
- 단축키 M -> S (기술실 첫 화면의 안정제 의료팩·협동전 페이지 안정제가 M을 씀).
- 공학 연구소의 멀티샷 버튼과 연구 항목(RM3_BayResearch Research21)은 지운다. 고갈되지 않는 자원(Research22)은 그대로.
- 피닉스(3번) 대사 (사용자 "피닉스는 3번 맵에만 나오는 유닛임 근데 대사가 않나옴"): 0.6.33은 공허 캠페인 음성
  Fenix_*를 연결했는데, 그 파일(LocalizedData\\Sounds\\VO\\Protoss\\Fenix_What00.ogg 등)은 공허 캠페인 안에만 있어
  자날 맵에서 소리가 안 난다. 협동전 용기병 피닉스 전용 대사 FenixDragoon_What/Yes/Attack/Ready/Pissed/Help
  (협동전 데이터, 맵이 이미 협동전 모델을 불러 쓰는 것과 같은 경로)로 바꾼다. 협동전 음향 배타 그룹은 맵에 없어 뺐다.
게임 미실행.

Usage: python3 tools/build_v0634.py <0.6.33 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_v062 import find, xml_edit, set_lines, LOCS, GD

OLD, NEW = b'version=0.6.33', b'version=0.6.34'
MAPS = ('TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
UP = 'RM6_Multishot'
KEY = 'S'


def edit_map(m, d):
    g = d / GD
    info = {}

    def abils(root):
        bay = find(root, 'CAbilResearch', 'RM3_BayResearch')
        old = [i for i in bay.findall('InfoArray') if i.get('Upgrade') == UP]
        assert len(old) == 1 and old[0].get('index') == 'Research21', m
        info['xml'] = copy.deepcopy(old[0])
        bay.remove(old[0])
        tech = find(root, 'CAbilResearch', 'RM3_TechResearch')
        n = max(int(i.get('index')[8:]) for i in tech.findall('InfoArray')) + 1
        new = info['xml']; new.set('index', f'Research{n}'); new.tail = None
        tech.append(new)
        info['n'] = n
    xml_edit(g / 'abildata.xml', abils)

    def units(root):
        bay = find(root, 'CUnit', 'EngineeringBay')
        hit = [(c, b) for c in bay.findall('CardLayouts') for b in c.findall('LayoutButtons') if b.get('Face') == UP]
        assert len(hit) == 1, m
        hit[0][0].remove(hit[0][1])
        lab = find(root, 'CUnit', 'BarracksTechLab')
        if m == 'TRaynor03':
            page, row, col = [c for c in lab.findall('CardLayouts') if c.get('index') == '0'][0], '1', '2'
        else:
            page, row, col = [c for c in lab.findall('CardLayouts') if c.get('CardId') == 'RMC1'][0], '1', '1'
        assert not [b for b in page.findall('LayoutButtons') if (b.get('Row'), b.get('Column')) == (row, col)], m
        page.append(E.fromstring(f'<LayoutButtons Face="{UP}" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research{info["n"]}" Row="{row}" Column="{col}" />'))
    xml_edit(g / 'unitdata.xml', units)

    p = d / 'mapscript.galaxy'
    raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    old = '    TechTreeAbilityAllow(1,AbilityCommand("RM3_BayResearch",20),true);\n'
    assert t.count(old) == 1, m
    t = t.replace(old, f'    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",{info["n"] - 1}),true);\n')
    t = t.replace('// 0.6.12: Multishot research (Engineering Bay).', '// 0.6.12/0.6.34: Multishot research (Barracks Tech Lab).')
    p.write_bytes(t.replace('\n', nl).encode('utf-8'))
    for loc in LOCS:
        h = d / f'{loc}.sc2data/localizeddata/gamehotkeys.txt'
        h.write_bytes(set_lines(h.read_bytes(), {f'Button/Hotkey/{UP}': KEY}))
    print(m, 'Multishot -> RM3_TechResearch Research', info['n'])


VO = ('What', 'Yes', 'Attack', 'Ready', 'Pissed', 'Help')
ROOT = HERE.parent


def fenix_voice(d):
    g = d / GD
    coop = {e.get('id'): e for e in E.parse(ROOT / 'source/starcoop/starcoop.sc2mod' / GD / 'sounddata.xml').getroot()}
    add = ''
    for k in VO:
        e = copy.deepcopy(coop[f'FenixDragoon_{k}'])
        for x in e.findall('Exclusivity'): e.remove(x)
        e.tail = None
        add += E.tostring(e, encoding='unicode')
    p = g / 'sounddata.xml'; t = p.read_text('utf-8')
    assert 'id="FenixDragoon_What"' not in t
    p.write_text(t.replace('</Catalog>', add + '</Catalog>'), 'utf-8')
    p = g / 'actordata.xml'; t = p.read_text('utf-8')
    s = t.index('<CActorUnit id="FenixDragoon"'); e = t.index('</CActorUnit>', s)
    a = t[s:e]
    for k in VO:
        old = f'<SoundArray index="{k}" value="Fenix_{k}" />'
        assert a.count(old) == 1, k
        a = a.replace(old, f'<SoundArray index="{k}" value="FenixDragoon_{k}" />')
    p.write_text(t[:s] + a + t[e:], 'utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            edit_map(m, root / f'{m}.SC2Map')
        fenix_voice(root / 'TRaynor03.SC2Map')
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in MAPS) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
