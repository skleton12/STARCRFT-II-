#!/usr/bin/env python3
"""Build CCM 0.4.62 from 0.4.61: 프로비우스 뒤 챔피언 원반 (4번, 사용자 스크린샷 2026-10-21 "프로비우스 저 뒤에 뭐 있잖음").

협동전 피닉스 프로비우스 뒤의 둥근 원반 = 챔피언 표시 FenixChampionSwapImpactProbe: 행동 FenixProbiusProbe 가 켜질 때
탐사정 부착점에서 0.75 뒤로 밀어 붙는 계속 재생 모델 (AI_Champion_Ground_Coop_WarpIn, 0.8 × 액터 0.65).
협동전 원본 그대로 옮긴다 (기본 액터·모델은 광전사 이식 때 이미 들어옴). 0.4.60 에서 빠뜨린 것.

Usage: python3 tools/build_v0462.py <0.4.61 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.61', b'version=0.4.62'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'
# 기본 액터 FenixChampionSwapImpactBase·모델 FenixChampionSwapImpactZealot 는 이미 맵에 있다 (광전사 이식).
ACTORS = ('<CActorModel id="FenixChampionSwapImpactProbe" parent="FenixChampionSwapImpactBase">'
          '<On Terms="Behavior.FenixProbiusProbe.On" Send="Create" />'
          '<HostSiteOps Ops="SOpAttachHardPoint SOpMoveBackByDot75" />'
          '<Model value="FenixChampionSwapImpactZealot" /><Scale value="0.650000" /></CActorModel>')


def append(extra, guard):
    def fn(d):
        t = d.decode('utf-8')
        assert guard not in t
        i = t.rindex('</Catalog>')
        return (t[:i] + extra + t[i:]).encode('utf-8')
    return fn


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW),
       GD + 'actordata.xml': append(ACTORS, 'id="FenixChampionSwapImpactProbe"')}


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
