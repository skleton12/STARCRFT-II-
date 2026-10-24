#!/usr/bin/env python3
"""0.4.80 -> 0.4.81: 전투 방패 연구가 코랄의 후예에게는 협동전 전투 방패로 적용 (3·4번, 사용자 2026-10-24).

사용자: "코랄의 후예의 컴벳 쉴드도 또 있던데, 그냥 컴벳 쉴드 업그레이드 되면 코랄의 후예는 그 업그레이드가 적용되게".
코랄의 후예는 협동전 전투 방패(행동 RMK_MarineMengskCombatShield: 받는 피해 25% 감소)를 갖고 있지만, 그 행동은
따로 얻을 길이 없는 업그레이드 RMK_MarineMengskCombatShield 를 요구해 꺼져 있었다.
수정: 그 요구 노드(RMK_CountUpgradeMarineMengskCombatShieldCompleteOnly…)가 모드 전투 방패 연구 RM3_Shield 를 세게 한다.
→ 전투 방패를 연구하면 전쟁광은 원작 효과(생명력 +10), 코랄의 후예는 협동전 효과(받는 피해 25% 감소, 방패 외형).
코랄의 후예에게 주던 생명력 +10 은 빼서 두 효과가 겹치지 않게 한다. 같은 조건을 쓰는 '무사 통과'도 함께 켜진다(원작 연결 그대로).

Usage: python3 tools/build_v0481.py <0.4.80 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.80', b'version=0.4.81'
MAPS = ['TRaynor03', 'TTychus01']


def nodes(t):
    a = '<Count Link="RMK_MarineMengskCombatShield" State="CompleteOnly" />'
    assert t.count(a) == 1
    return t.replace(a, '<Count Link="RM3_Shield" State="CompleteOnly" />')


def upgrades(t):
    m = re.search(r'<CUpgrade id="RM3_Shield">.*?</CUpgrade>', t, re.S)
    b, n = re.subn(r'\s*<EffectArray Reference="Unit,RMK_MarineMengsk,Life(?:Max|Start)" Value="10" />', '', m.group(0))
    assert n == 2 and 'WarPig,LifeMax' in b
    return t[:m.start()] + b + t[m.end():]


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m in MAPS:
            for f, fn in [('requirementnodedata', nodes), ('upgradedata', upgrades)]:
                p = f'{m}.SC2Map/base.sc2data/gamedata/{f}.xml'
                files[p] = fn(files[p].decode('utf-8')).encode('utf-8'); changed.add(p)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
