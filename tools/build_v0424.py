#!/usr/bin/env python3
"""Build CCM 0.4.24 from 0.4.23 (maps 3·4).

1. 일반 벙커 모델 이상·드래그 선택 문제 (사용자 보고 2026-10-18): 옛 보급 벙커 복제 액터
   RM3_SupplyBunker(parent="Bunker")가 원작 Bunker 액터의 'UnitBirth.Bunker → Create'를 물려받아
   일반 벙커가 생길 때마다 보급 벙커 모델 액터가 하나 더 겹쳐 생겼다. 보급 벙커는 0.3.30부터
   BunkerDepotMengsk이므로 쓰이지 않는 옛 유닛·액터·모델을 지운다 (연구 RM3_SupplyBunker 업그레이드는 유지).
2. 원시 알 비용 두 번 (사용자 보고): 알을 낳을 때 알 유닛 비용, 부화(변태) 때 다시 같은 비용을 냈다.
   변태 비용을 0으로 한다. 알을 낳을 때 한 번만 낸다 (모드 변경).

Usage: python3 tools/build_v0424.py <0.4.23 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.23', b'version=0.4.24'
MAPS = ('TRaynor03.SC2Map/', 'TTychus01.SC2Map/')
DROP = {'actordata.xml': [r'<CActorUnit id="RM3_SupplyBunker" .*?</CActorUnit>', r'<CActorModel id="RM3_SupplyBunkerBuild"[^>]*/>'],
        'unitdata.xml': [r'<CUnit id="RM3_SupplyBunker" .*?</CUnit>'],
        'modeldata.xml': [r'<CModel id="RM3_SupplyBunker\w+"[^>]*/>', r'<CModel id="RM3_SupplyBunker\w+"[^/>]*>.*?</CModel>']}


def drop(pats):
    def fn(d):
        t = d.decode('utf-8')
        for p in pats:
            t, n = re.subn(r'\n?[ \t]*' + p, '', t, flags=re.S)
            assert n >= 1, p
        return t.encode('utf-8')
    return fn


def abil(d):
    t = d.decode('utf-8')
    def zero(m):
        return re.sub(r'(<Resource index="\w+" value=")\d+(" />)', r'\g<1>0\2', m.group(0))
    t, n = re.subn(r'<CAbilTrain id="DehakaTrainEggMorphTo\w+">.*?</CAbilTrain>', zero, t, flags=re.S)
    assert n == 3
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW)}
for m in MAPS:
    g = m + 'base.sc2data/gamedata/'
    for f, p in DROP.items(): FIX[g + f] = drop(p)
    FIX[g + 'abildata.xml'] = abil


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
                for m in MAPS:
                    g = m + 'base.sc2data/gamedata/'
                    a = out.read(g + 'actordata.xml') + out.read(g + 'unitdata.xml') + out.read(g + 'modeldata.xml')
                    assert b'id="RM3_SupplyBunker' not in a
                    assert b'Upgrade="RM3_SupplyBunker"' in out.read(g + 'abildata.xml')
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
