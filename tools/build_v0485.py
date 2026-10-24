#!/usr/bin/env python3
"""0.4.84 -> 0.4.85: 코랄의 후예 레일건(자기 가속 탄약) 광선이 보이게 (1~4번, 사용자 2026-10-24 "레일건 쏘는 게 안 보임").

원작(공허 캠페인 노바)의 레일건은 탄환이 투명하고, 발사자→대상을 잇는 광선 액터 MagrailMunitionBeam(GenericAttackBeam,
모델 MagrailMunition_Missile)이 보이는 부분이다. 공격 액터 기본값 Beam=##id##Beam 이라 액터 이름으로 이어진다.
0.4.75 에서 RMK_MagrailMunition 공격 액터만 옮기고 광선을 빠뜨렸다. RMK_MagrailMunitionBeam 과 모델 정의를 네 맵에 넣는다.

Usage: python3 tools/build_v0485.py <0.4.84 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.84', b'version=0.4.85'
BEAM = '<CActorBeamSimple id="RMK_MagrailMunitionBeam" parent="GenericAttackBeam"><Model value="MagrailMunition_Missile" /></CActorBeamSimple>'
MODEL = '<CModel id="MagrailMunition_Missile" parent="RaceMissileFX" Race="Terran" />'


def append(t, extra):
    i = t.rindex('</Catalog>')
    return t[:i] + extra + t[i:]


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m in ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']:
            g = f'{m}.SC2Map/base.sc2data/gamedata/'
            a = files[g + 'actordata.xml'].decode('utf-8')
            assert 'id="RMK_MagrailMunition"' in a and 'RMK_MagrailMunitionBeam' not in a
            files[g + 'actordata.xml'] = append(a, BEAM).encode('utf-8')
            md = files[g + 'modeldata.xml'].decode('utf-8')
            assert 'id="MagrailMunition_Missile"' not in md
            files[g + 'modeldata.xml'] = append(md, MODEL).encode('utf-8')
            changed |= {g + 'actordata.xml', g + 'modeldata.xml'}
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
