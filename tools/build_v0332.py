#!/usr/bin/env python3
"""Build CCM 0.3.32 from 0.3.31: 자극제 연구를 한 줄로 (3번 미션).

사용자 지시 (2026-10-17): "연구를 전투 자극제 1가지로 바꾸되, 업그레이드하면 초 전투 자극제, 그다음이 멩스크 전투 자극제".
  - 병영 기술실에는 자극제 연구 버튼이 한 자리(첫 칸)만 있다. 연구가 끝날 때마다 같은 자리에 다음 단계가 나온다.
      1단계 전투 자극제 (광물 100·가스 100·60초)      → 원작 자극제 Stimpack
      2단계 초 전투 자극제 (150·150·90초, 협동전 노바)  → 협동전 SuperStimpackMarine
      3단계 고급 전투 자극제 (250·250·120초, 시험값)    → 멩스크 협동전 코랄의 후예 고급 자극제
         (15초 동안 공격 속도 +100%, 이동 속도 +50%, 초당 체력 5 회복, 재사용 대기 30초)
  - 유닛 버튼도 같은 자리에서 단계마다 바뀐다 (이전 단계 버튼은 숨김).
  - 전쟁광·코랄의 후예 모두 적용. 코랄의 후예가 원래 갖던 고급 자극제 버튼도 3단계 연구 전에는 숨긴다.
  - 고급 전투 자극제 설명의 '2계급부터 사용'은 이 모드에서 계급을 쓰지 않으므로 뺀다.

Usage: python3 tools/build_v0332.py <0.3.31 zip> <new output zip>
"""
import argparse
import copy
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35  # noqa: E402

OLD, NEW = b'version=0.3.31', b'version=0.3.32'
M3 = 'TRaynor03.SC2Map/'
GD = M3 + 'base.sc2data/gamedata/'
KO = M3 + 'kokr.sc2data/localizeddata/gamestrings.txt'
MENGSK = 'RMK_MarineMengskAttackSpeedBoost'

NODES = ('<CRequirementAnd id="RM3_Stim2Show"><OperandArray index="0" value="RM3_Stim1Done" />'
         '<OperandArray index="1" value="RM3_Stim2NotQueued" /></CRequirementAnd>'
         '<CRequirementAnd id="RM3_Stim3Show"><OperandArray index="0" value="RM3_Stim2Done" />'
         '<OperandArray index="1" value="RM3_Stim3NotQueued" /></CRequirementAnd>')

STRINGS = {
    'Button/Name/RM3_Stim3': '고급 전투 자극제 연구 /// Research Advanced Stimpack',
    'Button/Tooltip/RM3_Stim3': '초 전투 자극제가 멩스크 협동전의 고급 전투 자극제로 바뀝니다. 15초 동안 공격 속도 +100%, 이동 속도 +50%, 초당 체력 5 회복. 재사용 대기시간 30초. /// Super Stimpack becomes the Mengsk co-op Advanced Stimpack: +100% attack speed, +50% movement speed and 5 life regeneration per second for 15 seconds. 30 second cooldown.',
    'Button/Tooltip/RMK_MarineMengskAttackSpeedBoost': '15초 동안 공격 속도가 100%, 이동 속도가 50% 증가하고 초당 체력을 5 회복합니다. 재사용 대기시간 30초. /// For 15 seconds: +100% attack speed, +50% movement speed and 5 life regeneration per second. 30 second cooldown.',
}


def xml_fix(fn):
    def f(data):
        root = E.fromstring(data)
        fn(root)
        return E.tostring(root, encoding='utf-8', xml_declaration=True)
    return f


def find(root, tag, i):
    r = [e for e in root if e.tag == tag and e.get('id') == i]
    return r[0] if r else None


def abils(root):
    r = find(root, 'CAbilResearch', 'RM3_TechResearch')
    for info in r.findall('InfoArray'):
        if info.get('index') == 'Research3':
            info.find('Button').set('State', 'Available')
    m = find(root, 'CAbilEffectInstant', MENGSK)
    cmds = [c for c in m.findall('CmdButtonArray') if c.get('index') == 'Execute']
    if cmds:
        for c in cmds: c.set('Requirements', 'RM3_Stim3Use')
    else:
        E.SubElement(m, 'CmdButtonArray', index='Execute', Requirements='RM3_Stim3Use')


def units(root):
    lab = find(root, 'CUnit', 'BarracksTechLab')
    card = lab.find('CardLayouts')
    for b in list(card):
        if b.get('Face') == 'RM3_Stim2':
            b.set('Column', '0')
    card.append(E.fromstring('<LayoutButtons Face="RM3_Stim3" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research3" Row="0" Column="0" />'))
    for uid in ('WarPig', 'RMK_MarineMengsk'):
        recs = [e for e in root if e.tag == 'CUnit' and e.get('id') == uid]
        for u in recs:
            for a in list(u.findall('AbilArray')):
                if a.get('Link') == MENGSK and a.get('removed') == '1':
                    u.remove(a)
        u = recs[-1]
        if not any(a.get('Link') == MENGSK for r in recs for a in r.findall('AbilArray')):
            E.SubElement(u, 'AbilArray', Link=MENGSK)
        stim_card = [c for c in u.findall('CardLayouts') if any(b.get('Face') == 'Stim' for b in c)]
        assert len(stim_card) == 1, uid
        stim_card[0].append(E.fromstring(f'<LayoutButtons Face="{MENGSK}" Type="AbilCmd" AbilCmd="{MENGSK},Execute" Requirements="RM3_Stim3Use" Row="2" Column="1" />'))


def reqs(root):
    for i, show in (('RM3_Stim2Learn', 'RM3_Stim2Show'), ('RM3_Stim3Learn', 'RM3_Stim3Show')):
        r = find(root, 'CRequirement', i)
        for n in r.findall('NodeArray'):
            if n.get('index') == 'Show':
                n.set('Link', show)


def nodes(data):
    text = data.decode('utf-8')
    assert 'id="RM3_Stim2Show"' not in text
    out = text.replace('</Catalog>', NODES + '</Catalog>', 1).encode('utf-8')
    E.fromstring(out)
    return out


def kokr(data):
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = text.split(nl)
    done = set()
    for i, line in enumerate(lines):
        k = line.split('=', 1)[0]
        if k in STRINGS:
            lines[i] = f'{k}={STRINGS[k]}'; done.add(k)
    assert done == set(STRINGS), set(STRINGS) - done
    out = nl.join(lines).encode('utf-8')
    V35.gate('kokr', out)
    return out


FIX = {GD + 'abildata.xml': xml_fix(abils), GD + 'unitdata.xml': xml_fix(units), GD + 'requirementdata.xml': xml_fix(reqs),
       GD + 'requirementnodedata.xml': nodes, KO: kokr, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
