#!/usr/bin/env python3
"""Build CCM 0.4.57 from 0.4.56: 파편탄에 맞은 적 위의 오류 구 (4번, 사용자 보고 2026-10-21).

파편 피해(RM4_ShrapnelDamage)마다 붙는 충돌 연출 RM4_ShrapnelImpact 의 모델이 멩스크 협동전 원본 그대로
MarauderMengskShrapnelImpact → Assets\\Effects\\Terran\\Nova_PenetratingShot_Impact (노바 관통 사격 충돌)이다.
이 파일은 자날 맵이 불러오는 묶음(core·자날 모드·자날 캠페인)에 없는 것으로 보이고 맵 안에도 넣지 않았다 → 오류 구 후보.
자날 모드 데이터에 원래 있는 불곰 기본 공격 충돌 모델(MarauderBaseAttackImpact)로 바꾼다. 이지스 근위대 기본 파편도
같은 액터라 함께 바뀐다. 발사 연출(대상 뒤 부채꼴, Assets\\COOP\\Mengsk\\…)은 그대로 — 다른 협동전 모델처럼 보인다면 정상.

Usage: python3 tools/build_v0457.py <0.4.56 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.56', b'version=0.4.57'
ACTORS = 'TTychus01.SC2Map/base.sc2data/gamedata/actordata.xml'


def actors(d):
    t = d.decode('utf-8')
    head = '<CActorModel id="RM4_ShrapnelImpact" parent="ModelAnimationStyleOneShot">'
    i = t.index(head)
    j = t.index('</CActorModel>', i)
    b = t[i:j]
    assert t.count(head) == 1 and b.count('<Model value="MarauderMengskShrapnelImpact" />') == 1
    b = b.replace('<Model value="MarauderMengskShrapnelImpact" />', '<Model value="MarauderBaseAttackImpact" />')
    return (t[:i] + b + t[j:]).encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), ACTORS: actors}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
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
