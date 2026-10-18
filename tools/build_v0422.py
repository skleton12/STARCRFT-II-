#!/usr/bin/env python3
"""Build CCM 0.4.22 from 0.4.21: 동맹 자원 공유는 한쪽 방향만 (사용자 2026-10-18 "동맹 건물 건설을 못함, 내 자원만 쓰지 않으면 됨").

libNtve_gf_SetAlliance는 양쪽 방향으로 같은 설정을 건다. 그래서 0.4.17까지는 레이너도 동맹에게 자원을 열어 줬고,
0.4.18은 자원 공유를 통째로 빼서 플레이어가 동맹 일꾼으로 동맹 건물을 지을 수 없었다.
공식 PlayerSetAlliance로 방향을 나눈다 (3번 10·11, 4번 8·9):
  동맹 → 레이너: 자원 공유 켬 (레이너가 동맹 자원으로 동맹 건물 건설)
  레이너 → 동맹: 자원 공유·조종 끔 (동맹은 레이너 자원·유닛을 못 씀)

Usage: python3 tools/build_v0422.py <0.4.21 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.21', b'version=0.4.22'
MAPS = {'TRaynor03.SC2Map/mapscript.galaxy': (10, 11), 'TTychus01.SC2Map/mapscript.galaxy': (8, 9)}
LINE = '    libNtve_gf_SetAlliance({a},1,libNtve_ge_AllianceSetting_AllyWithSharedVisionAndControl);\n'
ADD = '''    // One-way (user 2026-10-18): the player builds with ally workers on ally money; allies never spend Raynor's money or use his units.
    PlayerSetAlliance({a},c_allianceIdSpend,1,true);
    PlayerSetAlliance(1,c_allianceIdSpend,{a},false);
    PlayerSetAlliance(1,c_allianceIdControl,{a},false);
'''


def patch(t, allies):
    for a in allies:
        line = LINE.format(a=a)
        assert t.count(line) == 1, line
        t = t.replace(line, line + ADD.format(a=a))
    return t


def fix(allies):
    def f(d):
        crlf = b'\r\n' in d
        t = patch(d.decode('utf-8').replace('\r\n', '\n'), allies)
        return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')
    return f


FIX = {n: fix(a) for n, a in MAPS.items()}
FIX['metadata.txt'] = lambda d: d.replace(OLD, NEW)


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
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    sup = HERE / 'data/mission04_support.galaxy'
    sup.write_text(patch(sup.read_text(), (8, 9)))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
