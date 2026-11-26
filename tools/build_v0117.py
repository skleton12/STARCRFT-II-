#!/usr/bin/env python3
"""0.11.6 -> 0.11.7: 발할라(THorner03) 아스테리아 망령 외형 (사용자 "그냥 망령 키워놓은 것 같은데").
협동전 HHWraith 기본 모델은 Wraith.m3 1.3배. 미라 강화 때 MiraHorner_Transformation_Coop_Wraith가
Wraith_Junker_Collection(고철 레이스)으로 바꾼다. 스킨 모델은 데이터에 경로가 없어(0.9.3 규칙) HHWraith 모델 첫 정의의
경로를 고철 레이스 파일로 직접 적는다. 경로는 다른 *_Junker_Collection 모델의 이름 규칙으로 추정 — 오류 구면 되돌린다.
Game not run.  Usage: python3 tools/build_v0117.py <0.11.6 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.11.6', b'version=0.11.7'
MP = 'THorner03.SC2Map/base.sc2data/gamedata/modeldata.xml'
A = '<CModel id="HHWraith" parent="Unit">\n        <Model value="Assets\\Units\\Terran\\Wraith\\Wraith.m3" />'
B = '<CModel id="HHWraith" parent="Unit">\n        <Model value="Assets\\Units\\Terran\\Wraith_Junker_Collection\\Wraith_Junker_Collection.m3" />'


def fix(t):
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    assert t.count(A) == 1, t.count(A)
    t = t.replace(A, B)
    return t.replace('\n', '\r\n') if crlf else t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    elif info.filename == MP: d = fix(d.decode('utf-8')).encode('utf-8')
                    o.writestr(copy.copy(info), d, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as o:
                assert o.testzip() is None
                for n in prev.namelist():
                    if n not in ('metadata.txt', MP): assert o.read(n) == prev.read(n), n
        except BaseException:
            out.unlink(missing_ok=True); raise


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
