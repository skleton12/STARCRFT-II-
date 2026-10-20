#!/usr/bin/env python3
"""Build CCM 0.4.46 from 0.4.45: 충격탄 연구의 파편·주변 감속을 Raynor Rogue 방식(업그레이드가 반경을 바꿈)으로 켠다.

사용자 지시 2026-10-20 ("일단 해봐"): 파편탄은 구매가 아니라 기술실 연구로 켜져야 한다. 지금까지는 효과마다 검증기
(RM4_HaveShrapnel)가 "연구했나"를 검사했고, Find 누락·스토리 층 덮어쓰기 같은 사고가 반복됐다.
Raynor Rogue(Redfrog·Benny)의 Aftershock 은 피해 효과에 반경 0 범위를 두고 업그레이드가 반경을 올린다.
같은 구조를 우리 데이터로 새로 짰다 (그 모드의 코드·에셋은 가져오지 않음).
  - RM4_ShrapnelSearch(대상 뒤 부채꼴 파편) 반경 3 → 0, RM4_SuppressAOE(대상 주변 감속) 반경 1 → 0, 검증기 제거.
  - 충격탄 연구 업그레이드 PunisherGrenades 가 반경을 +3, +1 한다. 연구 완료(또는 잭해머 구매로 완료 처리) 때만 켜진다.
  - 파편 발사 연출·소리는 원작 충격탄 연출처럼 액터 조건(ValidateEffect RM4_HaveShrapnel)으로만 거른다 (게임 효과와 무관).
  - 이지스 근위대 기본 파편(RMA_AegisShrapnelSearch)은 반경 3 그대로.
수치는 0.4.45와 같다 (파편 피해 4·장갑 +4, 부채꼴 60도 반경 3, 감속 반경 1). 4번 맵만.

Usage: python3 tools/build_v0446.py <0.4.45 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.45', b'version=0.4.46'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'


def rep(t, a, b):
    assert t.count(a) == 1, a
    return t.replace(a, b)


def block(t, head, fn):
    i = t.index(head)
    j = t.index('</CEffectEnumArea>', i)
    assert t.count(head) == 1
    return t[:i] + fn(t[i:j]) + t[j:]


def effects(d):
    t = d.decode('utf-8')
    def suppress(b):
        b = rep(b, '<AreaArray Radius="1" Effect="RM4_ShrapnelSlow" />', '<AreaArray Radius="0" Effect="RM4_ShrapnelSlow" />')
        return rep(b, '<ValidatorArray value="RM4_HaveShrapnel" />', '')
    def search(b):
        b = rep(b, '<AreaArray Arc="59.9963" Radius="3" Effect="RM4_ShrapnelHitSet" />',
                '<AreaArray Arc="59.9963" Radius="0" Effect="RM4_ShrapnelHitSet" />')
        return rep(b, '<ValidatorArray value="RM4_HaveShrapnel" />', '')
    t = block(t, '<CEffectEnumArea id="RM4_SuppressAOE">', suppress)
    t = block(t, '<CEffectEnumArea id="RM4_ShrapnelSearch">', search)
    return t.encode('utf-8')


def upgrades(d):
    t = d.decode('utf-8')
    assert 'id="PunisherGrenades"' not in t
    i = t.rindex('</Catalog>')
    up = ('<CUpgrade id="PunisherGrenades">'
          '<EffectArray Reference="Effect,RM4_ShrapnelSearch,AreaArray[0].Radius" Value="3" />'
          '<EffectArray Reference="Effect,RM4_SuppressAOE,AreaArray[0].Radius" Value="1" />'
          '</CUpgrade>')
    return (t[:i] + up + t[i:]).encode('utf-8')


def actors(d):
    t = d.decode('utf-8')
    t = rep(t, '<On Terms="Effect.RM4_ShrapnelSearch.Start; At Target" Send="Create" />',
            '<On Terms="Effect.RM4_ShrapnelSearch.Start; At Target; ValidateEffect RM4_HaveShrapnel" Send="Create" />')
    t = rep(t, '<On Terms="Effect.RM4_ShrapnelSearch.Start; At Caster" Send="Create" />',
            '<On Terms="Effect.RM4_ShrapnelSearch.Start; At Caster; ValidateEffect RM4_HaveShrapnel" Send="Create" />')
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'effectdata.xml': effects,
       GD + 'upgradedata.xml': upgrades, GD + 'actordata.xml': actors}


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
