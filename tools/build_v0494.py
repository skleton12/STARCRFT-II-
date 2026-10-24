#!/usr/bin/env python3
"""0.4.93 -> 0.4.94: 원시 감시자 알 순서 A안 — 저글링 → 바퀴 → 히드라 (3·4번, 사용자 선택 2026-10-24).

사용자 보고 "원시저그가 저글링만 많이 보낸다". 기존 순서 저글링 → 저글링 → 바퀴 → 히드라에 저글링 알 하나가 2마리라
한 바퀴가 저글링 4 : 바퀴 1 : 히드라 1이었다. A안으로 저글링 → 바퀴 → 히드라(저글링 2 : 바퀴 1 : 히드라 1).
4번의 해금 알(원시 숙주·울트라리스크)은 지금처럼 순서 뒤에 끼어든다.

Usage: python3 tools/build_v0494.py <0.4.93 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.93', b'version=0.4.94'
PAIRS = {
    'TRaynor03': [
        ('    // order zergling, zergling, roach, hydralisk (trial). Ally army supply stays under 100.\n',
         '    // order zergling, roach, hydralisk (user choice A, 0.4.94). Ally army supply stays under 100.\n'),
        ('        c=ModI(gv_m3_turn11,4)-1;\n        if (c<0) { c=0; }\n', '        c=ModI(gv_m3_turn11,3);\n'),
    ],
    'TTychus01': [
        ('    // Each Primal Warden spits an egg (co-op DehakaBarracksTrainEgg): zergling, zergling, roach, hydralisk (trial).\n',
         '    // Each Primal Warden spits an egg (co-op DehakaBarracksTrainEgg): zergling, roach, hydralisk (user choice A, 0.4.94).\n'),
        ('        // Base order zergling, zergling, roach, hydralisk; unlocked host/ultralisk join the rotation (trial).\n'
         '        c=ModI(gv_m4_turn9,4+gv_m4_eggExtra)-1;\n        if (c<0) { c=0; }\n',
         '        // Base order zergling, roach, hydralisk; unlocked host/ultralisk join the rotation (trial).\n'
         '        c=ModI(gv_m4_turn9,3+gv_m4_eggExtra);\n'),
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
