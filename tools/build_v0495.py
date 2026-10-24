#!/usr/bin/env python3
"""0.4.94 -> 0.4.95: 원시 감시자 알 순서 3:1:1 (3·4번, 사용자 2026-10-24 "아님 3-1-1", 선택 "알 개수 3:1:1").

알 순서 저글링 → 저글링 → 저글링 → 바퀴 → 히드라. 저글링 알 하나 = 2마리라 머릿수는 저글링 6 : 바퀴 1 : 히드라 1.
4번 해금 알(원시 숙주·울트라리스크)은 지금처럼 순서 뒤에 끼어든다.

Usage: python3 tools/build_v0495.py <0.4.94 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.94', b'version=0.4.95'
PAIRS = {
    'TRaynor03': [
        ('    // order zergling, roach, hydralisk (user choice A, 0.4.94). Ally army supply stays under 100.\n',
         '    // egg order zergling x3, roach, hydralisk (user 3:1:1, 0.4.95). Ally army supply stays under 100.\n'),
        ('        c=ModI(gv_m3_turn11,3);\n', '        c=ModI(gv_m3_turn11,5)-2;\n        if (c<0) { c=0; }\n'),
    ],
    'TTychus01': [
        ('zergling, roach, hydralisk (user choice A, 0.4.94).\n', 'zergling x3, roach, hydralisk (user 3:1:1, 0.4.95).\n'),
        ('        // Base order zergling, roach, hydralisk; unlocked host/ultralisk join the rotation (trial).\n'
         '        c=ModI(gv_m4_turn9,3+gv_m4_eggExtra);\n',
         '        // Base order zergling x3, roach, hydralisk; unlocked host/ultralisk join the rotation (trial).\n'
         '        c=ModI(gv_m4_turn9,5+gv_m4_eggExtra)-2;\n        if (c<0) { c=0; }\n'),
    ],
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, pairs in PAIRS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            for a, b in pairs:
                assert t.count(a) == 1, (m, a)
                t = t.replace(a, b)
            files[s] = t.encode('utf-8'); changed.add(s)
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
