#!/usr/bin/env python3
"""Build CCM 0.3.13 from 0.3.12 (3번 미션 마무리).

정적 검사 중 발견: 동맹 협동전 외형 표식(gf_m3_Skin)이 기지 완성(gv_m3_ready) 뒤에만 돌아,
건설하는 동안(약 165초) 탐사정·완성된 연결체 등이 일반 외형으로 보였다 (CLAUDE.md 3-1 컨셉 위반).
→ 표식 부여를 준비 여부와 상관없이 2초마다 실행. 건설 중 건물은 0.3.3과 같이 완성 뒤 바꾼다
  (건설 중에 바꾸면 완성 시 원래 모델로 되돌아갈 수 있음).

Usage: python3 tools/build_v0313.py <0.3.12 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.12', b'version=0.3.13'
M3 = 'TRaynor03.SC2Map/'
A_OLD = '    if (!runActions || gv_gameOver || gv_inCinematic) { return true; }\n    if (!gv_m3_ready) { return true; }\n'
A_NEW = ('    if (!runActions || gv_gameOver || gv_inCinematic) { return true; }\n'
         '    gf_m3_Skin(10);\n    gf_m3_Skin(11);\n    if (!gv_m3_ready) { return true; }\n')
B_OLD = '    gf_m3_Skin(10);\n    gf_m3_Skin(11);\n    gf_m3_Attack(10);\n'
B_NEW = '    gf_m3_Attack(10);\n'


def script(data):
    text = data.decode('utf-8')
    for old, new in [(B_OLD, B_NEW), (A_OLD, A_NEW)]:
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    assert text.count('gf_m3_Skin(10);') == 1
    return text.encode('utf-8')


FIX = {M3 + 'mapscript.galaxy': script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX: data = FIX[info.filename](data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path)
    a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
