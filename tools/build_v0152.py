#!/usr/bin/env python3
"""0.15.1 -> 0.15.2: 발굴 작업 버그 3개 (사용자 2026-11-28 보고).

1. TTychus02: 정화자 대의회·데하카의 굴이 엉뚱한 곳에 생김 — 전술 단계엔 레이너 사령부가 없어 시작 위치(수송선)를 기준으로 놓았다.
   이제 레이너 사령부가 생길 때까지 기다렸다가(시간 제한 없음) 그 옆에 놓는다.
2. TTychus02: 시작 병력 자극제 없음 — 히페리온 무기고 구매 반영(gf_m15_Armory)이 기지 인수 뒤에만 돌았다. 모드 초기화 때도 부른다(겹치지 않음).
3. 땅무지 숙주 알 오류 구 — 협동전 스킨 모델 SwarmHostEgg_Primal_Collection에 파일 경로가 없었다(10개 맵).
   원작 땅무지 숙주 알 모델(SwarmHostEggEx1B.m3, 같은 맵의 알 미사일이 이미 씀)로 경로를 적는다.
Game not run. Usage: python3 tools/build_v0152.py <0.15.1 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.15.1', b'version=0.15.2'
GD = 'base.sc2data/gamedata/modeldata.xml'
EGG = '<CModel id="SwarmHostEgg_Primal_Collection" parent="Unit" Race="Zerg">'
EGGM = EGG + '\n        <Model value="Assets\\Units\\Zerg\\SwarmHostEggEx1B\\SwarmHostEggEx1B.m3" />'
K = 'TTychus02.SC2Map/mapscript.galaxy'


def sub1(t, a, b):
    assert t.count(a) == 1, a[:80]
    return t.replace(a, b)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt', K}
        n = 0
        for k in files:
            if k.endswith('/' + GD):
                t = files[k].decode('utf-8')
                if EGG in t:
                    assert t.count(EGG) == 1 and 'SwarmHostEggEx1B.m3" />\n' not in t[t.index(EGG):t.index(EGG) + 200], k
                    files[k] = t.replace(EGG, EGGM).encode('utf-8'); changed.add(k); n += 1
        assert n == 10, n
        t = files[K].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
        t = sub1(t, '    if (cc != null) { c = UnitGetPosition(cc); } else { c = PlayerStartLocation(1); }\n',
                 '    // 0.15.2: The Dig has no Raynor Command Center until the base is handed over; wait for it.\n'
                 '    if (cc == null) { return false; }\n    c = UnitGetPosition(cc);\n')
        t = sub1(t, 'if (!gv_rm7Placed && GameGetMissionTime() >= 2.0 && GameGetMissionTime() < 300.0) {',
                 'if (!gv_rm7Placed && GameGetMissionTime() >= 2.0) {')
        a = '    gf_m15_Mercs();\n    PlayerSetColorIndex(8,2,true);\n'
        t = sub1(t, a, '    gf_m15_Mercs();\n    gf_m15_Armory();  // 0.15.2: opening dropship units get Hyperion stim too\n    PlayerSetColorIndex(8,2,true);\n')
        files[K] = t.replace('\n', nl).encode('utf-8')
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
