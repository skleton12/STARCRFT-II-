#!/usr/bin/env python3
"""0.12.9 -> 0.12.10: 코덱스 2차 검토(0.12.8·0.12.9) 반영.

  - 코랄 무르바르 [땅무지 소환](CoopMurvarSpawnCreepers)에 효과가 안 걸려 있던 것: 이식한 같은 이름 효과를 연결.
  - 코랄 수비대 강화가 원본 유닛당 1기까지만 복제하던 것: 누적값이 1 이상인 동안 반복 (기본 +50% + 연구 점수분, 최대 +150%).
  - 유령 사관학교를 못 짓는 임무 대비: 보병 4·5단계 연구 버튼(RMPL_Research)을 공학 연구소 연구실 메뉴 (2,0)·(2,1)에도.
  - 열화탄: 피해 유형만으로는 무기 구분이 안 되어(악령 정신 폭발이 범위 피해) 유령·악령은 제외.
Game not run.

Usage: python3 tools/build_v01210.py <0.12.9 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.12.9', b'version=0.12.10'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
G = '.SC2Map/base.sc2data/gamedata/'


def rep(t, a, b):
    assert t.count(a) == 1, a[:80]
    return t.replace(a, b)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            k = m + G + 'unitdata.xml'; t = files[k].decode('utf-8')
            e = list(re.finditer(r'<CUnit id="EngineeringBay"[^>]*>.*?</CUnit>', t, re.S)); assert len(e) == 1
            b = e[0].group(0)
            c = re.search(r'<CardLayouts CardId="RML1">(.*?)</CardLayouts>', b, re.S)
            assert 'Row="2" Column="0"' not in c.group(1) and 'Row="2" Column="1"' not in c.group(1), m
            add = ''.join(f'            <LayoutButtons Face="RMPL_Inf{x}" Type="AbilCmd" AbilCmd="RMPL_Research,Research{i}" Row="2" Column="{col}" />\n'
                          for i, (x, col) in enumerate((('W4', 0), ('W5', 0), ('A4', 1), ('A5', 1)), 1))
            b = b[:c.end(1)] + add + b[c.end(1):]
            b = rep(b, '<AbilArray Link="RML_Research" />', '<AbilArray Link="RML_Research" />\n        <AbilArray Link="RMPL_Research" />')
            t = t[:e[0].start()] + b + t[e[0].end():]
            E.fromstring(t.encode()); files[k] = t.encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/mapscript.galaxy'; raw = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
            s = raw.replace('\r\n', '\n')
            s = rep(s, '        && !UnitTestPlane(s, c_planeAir) && UnitIsAlive(v)) {',
                    '        && !UnitTestPlane(s, c_planeAir) && UnitIsAlive(v) && st != "Ghost" && st != "Spectre") {')
            if m == 'THorner04':
                s = rep(s, '                    carry += pct;\n                    if (carry >= 1.0) {', '                    carry += pct;\n                    while (carry >= 1.0) {')
            files[k] = s.replace('\n', nl).encode('utf-8'); changed.add(k)
        k = 'THorner04' + G + 'abildata.xml'; t = files[k].decode('utf-8')
        e = list(re.finditer(r'<CAbilEffectInstant id="CoopMurvarSpawnCreepers">.*?</CAbilEffectInstant>', t, re.S)); assert len(e) == 1
        b = rep(e[0].group(0), '<Arc value="360" />', '<Arc value="360" />\n        <Effect value="CoopMurvarSpawnCreepers" />')
        t = t[:e[0].start()] + b + t[e[0].end():]; E.fromstring(t.encode()); files[k] = t.encode('utf-8'); changed.add(k)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
