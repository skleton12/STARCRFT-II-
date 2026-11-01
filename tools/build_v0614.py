#!/usr/bin/env python3
"""0.6.13 -> 0.6.14: 초반 두 미션 아군 업그레이드 +1 (사용자 2026-11-01 "초반 두 미션은 우리 업그레이드 +1로, 첫번째는 방어력 1").

0.6.13 적 강화 상향의 보정. 시작할 때 한 번, 원본이 이미 준 단계와 겹치지 않게 부족분만 채운다.
- 1번(TRaynor01): 레이너(1) 보병 방어 1단계.
- 2번(TRaynor02): 레이너 보병 공격·방어 1단계.
동맹은 뺐다: 1·2번 맵에는 원시 업그레이드 정의도, 정화자 유닛을 프로토스 업그레이드에 잇는 연결(0.4.69, 4번~)도 없어 효과가 없다.

Usage: python3 tools/build_v0614.py <0.6.13 zip> <new output zip>
"""
import argparse, copy, tempfile, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.13', b'version=0.6.14'
ARMOR = [(1, 'TerranInfantryArmorsLevel1')]
WEAPON = [(1, 'TerranInfantryWeaponsLevel1')]
MAPS = {'TRaynor01': ARMOR, 'TRaynor02': ARMOR + WEAPON}
ANCHOR = '    gf_rm_EnemyDifficultyBuff();\n'


def lines(ups):
    out = '    // 0.6.14: our side starts with these upgrades (user 2026-11-01), only what is missing.\n'
    for p, u in ups:
        out += f'    TechTreeUpgradeAddLevel({p},"{u}",MaxI(0,1-TechTreeUpgradeCount({p},"{u}",c_techCountCompleteOnly)));\n'
    return out


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        changed = {'metadata.txt'}
        for m, ups in MAPS.items():
            p = root / f'{m}.SC2Map' / 'mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8')
            nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            assert t.count(ANCHOR) == 1, m
            t = t.replace(ANCHOR, ANCHOR + lines(ups))
            p.write_bytes(t.replace('\n', nl).encode('utf-8'))
            changed.add(f'{m}.SC2Map/mapscript.galaxy')
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n not in changed:
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
