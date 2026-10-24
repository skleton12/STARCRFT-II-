#!/usr/bin/env python3
"""0.4.79 -> 0.4.80: 레이저 조준 시스템 아이콘을 협동전 아이콘으로 (3·4번, 사용자 2026-10-24 "레이저 타겟팅 아이콘 협동전처럼").

모드 연구 RM3_Laser 의 연구 버튼·업그레이드·명령 카드 패시브(RMP_RM3_Laser)가 고급 자동 추적(hisecautotracking) 아이콘을 쓰고 있었다.
협동전(노바·코랄의 후예)이 쓰는 btn-upgrade-terran-lazertargetingsystem.dds 로 바꾼다. 효과·비용은 그대로.

Usage: python3 tools/build_v0480.py <0.4.79 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.79', b'version=0.4.80'
OLDI, NEWI = 'btn-upgrade-terran-hisecautotracking.dds', 'btn-upgrade-terran-lazertargetingsystem.dds'
TARGETS = {'buttondata': [('CButton', 'RM3_Laser'), ('CButton', 'RMP_RM3_Laser')], 'upgradedata': [('CUpgrade', 'RM3_Laser')]}


def fix(t):
    n = 0
    for tag, i in TARGETS[fix.kind]:
        m = re.search(rf'<{tag} id="{i}"[^>]*>.*?</{tag}>', t, re.S)
        if m and OLDI in m.group(0):
            t = t[:m.start()] + m.group(0).replace(OLDI, NEWI) + t[m.end():]; n += 1
    return t, n


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed, total = {'metadata.txt'}, 0
        for m in ['TRaynor03', 'TTychus01']:
            for kind in TARGETS:
                p = f'{m}.SC2Map/base.sc2data/gamedata/{kind}.xml'
                fix.kind = kind
                t, n = fix(files[p].decode('utf-8'))
                if n: files[p] = t.encode('utf-8'); changed.add(p); total += n
        assert total >= 4, total
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
    print(output, total, 'icons')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
