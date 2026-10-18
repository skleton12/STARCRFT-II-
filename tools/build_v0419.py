#!/usr/bin/env python3
"""Build CCM 0.4.19 from 0.4.18: 동맹 생산 충전 (사용자 지시 2026-10-18).

- 정화자 차원 관문: 소환 3회까지 모아 둔다 (충전 최대 3, 시작 3). 재충전은 원작 재사용 시간(광전사 23초, 추적자·파수기 32초),
  재사용 대기는 없앤다. 정화자(8)에만 적용 (플레이어별 데이터 값), 적 관문은 그대로. 4번 맵.
- 원시 감시자 알 생산: 종류마다 충전 최대 5 → 10 (협동전 DehakaBarracksTrainEgg). 3·4번 맵.

Usage: python3 tools/build_v0419.py <0.4.18 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.18', b'version=0.4.19'
ANCHOR = '    CatalogLinkReplace(8,c_gameCatalogUnit,"Sentry","RM21_Energizer");\n'
CHARGES = ''.join(
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.Link",8,"RM4_WarpGate");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.CountMax",8,"3");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.CountStart",8,"3");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.CountUse",8,"1");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Charge.TimeUse",8,"{s}");\n'
    f'    CatalogFieldValueSet(c_gameCatalogAbil,"WarpGateTrain","InfoArray[{t}].Cooldown.TimeUse",8,"0");\n'
    for t, s in (('Train1', 23), ('Train2', 32), ('Train6', 32)))
COMMENT = '    // Purifier Warp Gates store 3 warp-ins (user 2026-10-18); recharge uses the original cooldown times.\n'


def patch(t):
    assert t.count(ANCHOR) == 1 and 'RM4_WarpGate' not in t
    return t.replace(ANCHOR, ANCHOR + COMMENT + CHARGES)


def script(d):
    crlf = b'\r\n' in d
    t = patch(d.decode('utf-8').replace('\r\n', '\n'))
    return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')


def eggs(d):
    t = d.decode('utf-8')
    i = t.index('<CAbilTrain id="DehakaBarracksTrainEgg">'); j = t.index('</CAbilTrain>', i)
    body, n = re.subn(r'<CountMax value="5" />', '<CountMax value="10" />', t[i:j])
    assert n == 3, n
    return (t[:i] + body + t[j:]).encode('utf-8')


FIX = {'TTychus01.SC2Map/mapscript.galaxy': script,
       'TRaynor03.SC2Map/base.sc2data/gamedata/abildata.xml': eggs,
       'TTychus01.SC2Map/base.sc2data/gamedata/abildata.xml': eggs,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
    sup.write_text(patch(sup.read_text()))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
