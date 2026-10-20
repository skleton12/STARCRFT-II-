#!/usr/bin/env python3
"""Build CCM 0.4.43 from 0.4.42: 이지스 근위대(고용소)는 처음부터 파편을 쏜다 (4번, 사용자 선택 B 2026-10-20).

원작: 멩스크 협동전 이지스 근위대 2등급 진급 능력 (공격 시 대상 뒤 부채꼴 파편, 피해 4·장갑 +4).
0.4.28 이식에서 진급 체계를 뺄 때 무기 효과 묶음이 가리키던 MarauderMengskShrapnelSet 도 빠져 파편이 나가지 않았다.
진급 없이 기본 능력으로 붙인다 (모드 변경): 망치 경호대 파편탄 연구와 같은 파편 피해·연출을 쓰되 연구 검사는 없다.
감속은 붙이지 않는다 (원작 2등급은 피해만). 망치 경호대의 파편탄 연구(2페이지)는 그대로.

Usage: python3 tools/build_v0443.py <0.4.42 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.42', b'version=0.4.43'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'
SEARCH = ('<CEffectEnumArea id="RMA_AegisShrapnelSearch"><LaunchLocation Value="CasterUnit" /><ImpactLocation Value="TargetUnit" />'
          '<ExcludeArray Value="Target" /><SearchFilters value="Ground;Self,Player,Ally,Missile,Stasis,Dead,Hidden,Invulnerable" />'
          '<AreaArray Arc="59.9963" Radius="3" Effect="RM4_ShrapnelDamage" /></CEffectEnumArea>')


def rep(a, b):
    def fn(d):
        t = d.decode('utf-8')
        assert t.count(a) == 1, a
        return t.replace(a, b).encode('utf-8')
    return fn


def effects(d):
    d = rep('<EffectArray value="MarauderMengskShrapnelSet" />', '<EffectArray value="RMA_AegisShrapnelSearch" />')(d)
    i = d.rindex(b'</Catalog>')
    return d[:i] + SEARCH.encode('utf-8') + d[i:]


def actors(d):
    t = d.decode('utf-8')
    for aid, term in (('RM4_ShrapnelLaunch', 'At Target'), ('RM4_ShrapnelSound', 'At Caster')):
        head = f'<C{"ActorModel" if aid.endswith("Launch") else "ActorSound"} id="{aid}"'
        i = t.index(head)
        j = t.index('>', i) + 1
        t = t[:j] + f'<On Terms="Effect.RMA_AegisShrapnelSearch.Start; {term}" Send="Create" />' + t[j:]
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'effectdata.xml': effects, GD + 'actordata.xml': actors}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), FIX[info.filename](d) if info.filename in FIX else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
