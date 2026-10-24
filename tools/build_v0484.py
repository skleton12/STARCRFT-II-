#!/usr/bin/env python3
"""0.4.83 -> 0.4.84: 원시저그 방어 이름 'Unknown' 수정 (1~4번, 사용자 2026-10-24 "원시저그 방어 언노운으로 나옴").

데하카 협동전 유닛의 LifeArmorName 'Unit/LifeArmorName/PrimalZergArmor' 문자열이 맵에 없었다(협동전 문자열은 이식 때 빠짐).
정화자 동력기 무기 이름 'Weapon/Name/Energizer' 도 없어 같이 넣는다. 공식 표기: 원시 갑피(업그레이드 이름과 같게), 동력기.
문자열만 추가하며 데이터·스크립트는 그대로. 해당 키를 쓰는 맵에만 넣는다.

Usage: python3 tools/build_v0484.py <0.4.83 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines

OLD, NEW = b'version=0.4.83', b'version=0.4.84'
STRINGS = {
    'Unit/LifeArmorName/PrimalZergArmor': ('unitdata', '원시 갑피 /// Primal Carapace'),
    'Weapon/Name/Energizer': ('weapondata', '동력기 /// Energizer'),
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m in ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']:
            want = {k: v for k, (cat, v) in STRINGS.items()
                    if k.encode() in files[f'{m}.SC2Map/base.sc2data/gamedata/{cat}.xml']}
            if not want: continue
            for loc in ('kokr',) + LOCALES:
                p = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'
                v = want if loc == 'kokr' else {k: x.split(' /// ', 1)[1] for k, x in want.items()}
                files[p] = update_lines(files[p], v); changed.add(p)
            print(m, sorted(want))
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
