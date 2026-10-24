#!/usr/bin/env python3
"""0.4.77 -> 0.4.78: 'RM4_ShieldShown' 이 유닛 정보 칸에 Unknown 으로 보이던 것 숨김 (3·4번, 사용자 2026-10-24).

0.4.74 의 방패 외형 표식 버프 RM4_ShieldShown 은 효과도 이름도 없는 내부 표식인데, 버프라서 정보 칸에 이름 없이(Unknown) 떴다.
InfoFlags Hidden 을 켜 정보 칸에서 숨긴다(원작 내부 버프와 같은 방식). 혹시 보일 때를 위해 이름도 넣는다. 동작은 그대로.

Usage: python3 tools/build_v0478.py <0.4.77 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines

OLD, NEW = b'version=0.4.77', b'version=0.4.78'
MAPS = ['TRaynor03', 'TTychus01']
OLDB = '<CBehaviorBuff id="RM4_ShieldShown"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" /></CBehaviorBuff>'
NEWB = ('<CBehaviorBuff id="RM4_ShieldShown"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" />'
        '<InfoFlags index="Hidden" value="1" /></CBehaviorBuff>')
STRINGS = {'Behavior/Name/RM4_ShieldShown': '전투 방패 외형 /// Combat Shield Visual'}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m in MAPS:
            b = f'{m}.SC2Map/base.sc2data/gamedata/behaviordata.xml'
            t = files[b].decode('utf-8')
            assert t.count(OLDB) == 1, m
            files[b] = t.replace(OLDB, NEWB).encode('utf-8'); changed.add(b)
            for loc in ('kokr',) + LOCALES:
                p = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'
                v = STRINGS if loc == 'kokr' else {k: x.split(' /// ', 1)[1] for k, x in STRINGS.items()}
                files[p] = update_lines(files[p], v); changed.add(p)
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
