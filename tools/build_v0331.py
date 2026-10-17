#!/usr/bin/env python3
"""Build CCM 0.3.31 from 0.3.30: 자극제 다시 설계 (3번 미션).

사용자 결정 (2026-10-17): "자날·멜리 원작 자극제 그대로 하고, 업그레이드하면 협동전처럼 강화된 자극제".
0.3.1~0.3.30의 자극제는 모드가 만든 3단계 버프(RM3_Stim1~3 시전)였다. 원작 붉은 연출이 없고 15·30초 재사용 대기가 있었다.
  - 1단계 연구 '전투 자극제'(기존 RM3_Stim1 연구, 비용·시간 그대로): 원작 자극제 능력 Stimpack을 쓸 수 있게 한다.
    체력 10 소모, 15초 동안 공격·이동 속도 +50% (자날 데이터 값), 원작 연출.
  - 2단계 연구 '초 전투 자극제'(기존 RM3_Stim2 연구 자리, 협동전 노바 정예 해병 연구와 같은 광물 150·가스 150·90초):
    협동전 SuperStimpackMarine으로 바뀐다. 체력 소모 없이 15초 동안 공격·이동 속도 +50%, 초당 체력 2 회복.
    협동전처럼 자동 시전이 켜진 상태로 나온다(우클릭으로 끌 수 있음).
  - 3단계 연구(고급 자극제)는 없앤다.
  - 전쟁광과 코랄의 후예 둘 다 같은 방식이다.
  협동전 데이터: SuperStimpackMarine 능력·효과, SuperStim 버프, 시작·끝 연출 액터를 옮긴다 (노바·마스터 힘 체계는 제외).
  원작 자극제 능력의 사용 조건을 '1단계 연구 완료, 2단계 미완료'로 바꾼다 (3번 맵 데이터).

Usage: python3 tools/build_v0331.py <0.3.30 zip> <new output zip>
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
OLD, NEW = b'version=0.3.30', b'version=0.3.31'
M3 = 'TRaynor03.SC2Map'
GD = M3 + '/base.sc2data/gamedata/'
STIM_UNITS = ('WarPig', 'RMK_MarineMengsk')

STRINGS = {
    'Button/Name/RM3_Stim1': '전투 자극제 연구 /// Research Stimpack',
    'Button/Tooltip/RM3_Stim1': '전쟁광과 코랄의 후예가 원작 전투 자극제를 쓸 수 있습니다. 체력 10을 소모하고 15초 동안 공격 및 이동 속도가 50% 증가합니다. /// War Pigs and Heirs of Korhal can use the original Stimpack: costs 10 life, +50% attack and movement speed for 15 seconds.',
    'Button/Name/RM3_Stim2': '초 전투 자극제 연구 /// Research Super Stimpack',
    'Button/Tooltip/RM3_Stim2': '전투 자극제가 초 전투 자극제로 바뀝니다. 체력을 소모하지 않고 15초 동안 공격 및 이동 속도가 50% 증가하며 초당 체력 2를 회복합니다. 협동전 연구입니다. /// Stimpack becomes Super Stimpack: no life cost, +50% attack and movement speed and 2 life regeneration per second for 15 seconds. A co-op research.',
    'Button/Tooltip/MarineSuperStimpack': '15초 동안 체력을 소모하지 않고 공격 및 이동 속도가 50% 증가하며 초당 체력 2를 회복합니다. /// For 15 seconds, attack and movement speed +50% and 2 life regeneration per second, with no life cost.',
}


def xml_edit(path, fn):
    root = E.parse(path).getroot()
    fn(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def find(root, tag, i):
    r = [e for e in root if e.tag == tag and e.get('id') == i]
    return r[0] if r else None


def edit(gd):
    def abils(root):
        s = find(root, 'CAbilEffectInstant', 'SuperStimpackMarine')
        for c in s.findall('CmdButtonArray'):
            c.set('Requirements', 'RM3_Stim2Use')
        st = find(root, 'CAbilEffectInstant', 'Stimpack')
        if st is None:
            st = E.SubElement(root, 'CAbilEffectInstant', id='Stimpack')
        E.SubElement(st, 'CmdButtonArray', index='Execute', Requirements='RM3_Stim1Use')
        r = find(root, 'CAbilResearch', 'RM3_TechResearch')
        for info in r.findall('InfoArray'):
            if info.get('index') == 'Research3':
                info.find('Button').set('State', 'Suppressed')
    xml_edit(gd / 'abildata.xml', abils)

    def units(root):
        for uid in STIM_UNITS:
            u = find(root, 'CUnit', uid)
            for a in list(u.findall('AbilArray')):
                if (a.get('Link') == 'Stimpack' and a.get('removed') == '1') or a.get('Link', '').startswith('RM3_Stim'):
                    u.remove(a)
            for card in u.findall('CardLayouts'):
                for b in list(card):
                    if b.get('Face') == 'RM3_Stim1':
                        b.set('Face', 'Stim'); b.set('AbilCmd', 'Stimpack,Execute')
                    elif b.get('Face') == 'RM3_Stim2':
                        b.set('Face', 'MarineSuperStimpack'); b.set('AbilCmd', 'SuperStimpackMarine,Execute')
                    elif b.get('Face') == 'RM3_Stim3':
                        card.remove(b)
            E.SubElement(u, 'AbilArray', Link='Stimpack')
            E.SubElement(u, 'AbilArray', Link='SuperStimpackMarine')
        lab = find(root, 'CUnit', 'BarracksTechLab')
        for card in lab.findall('CardLayouts'):
            for b in list(card):
                if b.get('Face') == 'RM3_Stim3':
                    card.remove(b)
    xml_edit(gd / 'unitdata.xml', units)


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(root / M3), '--liberty-base', '--skip-existing',
                        '--drop=Nova|Mastery|RaynorCommander', 'SuperStimpackMarine', 'SuperStim'], check=True)
        (root / M3 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        edit(root / GD)
        ko = root / M3 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        text = ko.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        lines = text.split(nl)
        done = set()
        for i, line in enumerate(lines):
            k = line.split('=', 1)[0]
            if k in STRINGS:
                lines[i] = f'{k}={STRINGS[k]}'; done.add(k)
        assert done == set(STRINGS), set(STRINGS) - done
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
