#!/usr/bin/env python3
"""0.4.87 -> 0.4.88: 동맹→레이너 자원 공유 다시 켬 (3·4번, 사용자 보고 2026-10-24 "공유 꺼서 그런지 건물 건설을 못 함").

0.4.87 A안(공유 끔)에서는 레이너가 동맹 일꾼으로 건물을 짓지 못했다 → 엔진이 명령한 플레이어(레이너)의 자원 권한으로 비용을 본다.
c_allianceIdSpend 동맹→레이너를 다시 켠다. 확장 기지·채굴·50% 분배·상한 +2 는 그대로.
누가 내는지(레이너 먼저인지 동맹인지) 게임 확인 후 B안(돈 정산)을 정한다.

Usage: python3 tools/build_v0488.py <0.4.87 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.87', b'version=0.4.88'
PAIRS = {'TRaynor03': [10, 11], 'TTychus01': [8, 9]}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, allies in PAIRS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            for p in allies:
                a = f'    PlayerSetAlliance({p},c_allianceIdSpend,1,false);'
                assert t.count(a) == 1, (m, p)
                t = t.replace(a, f'    PlayerSetAlliance({p},c_allianceIdSpend,1,true);')
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
