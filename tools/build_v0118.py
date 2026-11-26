#!/usr/bin/env python3
"""0.11.7 -> 0.11.8: 정화자 정찰기 외형 (사용자 "정화자 정찰기가 그냥 정찰기 모델임").
정찰기(Scout)는 불멸자·우주모함·관측선과 달리 동맹 외형 바꿈(RM3_AllySkin ModelSwap)이 빠져 있었다.
협동전 피닉스 정찰기 모델(FenixMojoScout = Scout_Purifier_Coop.m3, 이미 맵에 있음)로 동맹 소유만 바꾼다.
차원 소환이 끝날 때 원작이 ModelSwap Scout로 되돌리므로 그 뒤에도 다시 바꾼다(상태 RMSkin).
Scout 액터 첫 정의 안에 넣는다(두 번째 정의 금지). Game not run.
Usage: python3 tools/build_v0118.py <0.11.7 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.11.7', b'version=0.11.8'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03']
HEAD = '<CActorUnit id="Scout">\n'
TAIL = '        <HeroIcon value="Assets\\Textures\\btn-unit-protoss-scout-purifier.dds" />\n'
ADD_H = ('        <On Terms="Behavior.RM3_AllySkin.On" Send="StatusSet RMSkin 1" />\n'
         '        <On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap FenixMojoScout" />\n')
ADD_T = '        <On Terms="Behavior.WarpInEffect.Off; IsStatus RMSkin 1" Send="ModelSwap FenixMojoScout" />\n'


def fix(t):
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    assert t.count(HEAD) == 1, t.count(HEAD)
    i = t.index(HEAD); j = t.index('</CActorUnit>', i)
    body = t[i:j]
    assert body.count(TAIL) == 1 and 'RM3_AllySkin' not in body
    body = body.replace(HEAD, HEAD + ADD_H).replace(TAIL, TAIL + ADD_T)
    t = t[:i] + body + t[j:]
    return t.replace('\n', '\r\n') if crlf else t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    targets = {f'{m}.SC2Map/base.sc2data/gamedata/actordata.xml' for m in MAPS}
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        for m in MAPS:
            assert 'id="FenixMojoScout"' in prev.read(f'{m}.SC2Map/base.sc2data/gamedata/modeldata.xml').decode(), m
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                done = 0
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    elif info.filename in targets: d = fix(d.decode('utf-8')).encode('utf-8'); done += 1
                    o.writestr(copy.copy(info), d, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                assert done == len(MAPS), done
            with zipfile.ZipFile(out) as o:
                assert o.testzip() is None
                for n in prev.namelist():
                    if n != 'metadata.txt' and n not in targets: assert o.read(n) == prev.read(n), n
        except BaseException:
            out.unlink(missing_ok=True); raise


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
