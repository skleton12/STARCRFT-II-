#!/usr/bin/env python3
"""0.12.12 -> 0.12.13: 코랄 동맹 호출 '자원 부족'·클로라리온 폭격기 (사용자 2026-11-27 "동맹 소환 막혀있는데",
"기지 넘겨 받은뒤 동맹 소환이 바로 가능하길래 해봤는데 옆에 빨간색으로 영어로 … 소환 불가", "태양광선 어디갔누").

THorner04:
  - 원인: 다른 임무는 동맹 호출 첫 사용이 임무 4분이라 그동안 동맹이 2초마다 수입(정화자 광물 25·가스 8, 원시저그 40·8)을
    모은다. 코랄은 2단계(기지 인수)가 4분 넘어 시작해 버튼은 바로 열리는데, 동맹 돈은 시작값(정화자 300/0, 원시저그 500/0)뿐이라
    'rm5/CallNoMoney'(그 동맹의 자원이나 인구가 모자라 …) 빨간 오류가 났다(가스 0). 이제 2단계 시작 때 동맹 돈을
    시작값 + (min(임무 시간, 240초) / 2) × 수입으로 맞춘다 = 다른 임무에서 4분에 갖는 돈과 같다.
  - 클로라리온(레이너 소유)에 용사 폭격기 업그레이드(FenixChampionCarrierBombers)를 준다 — 지금까지 동맹(8번)에게만 줘서
    레이너의 클로라리온은 폭격기('태양 폭격기')를 못 만들었다. 정보 창 '태양 광선'(분광 광선) 무기 데이터는 맵에 다 있음.
Game not run.

Usage: python3 tools/build_v01213.py <0.12.12 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.12.12', b'version=0.12.13'
K = 'THorner04.SC2Map/mapscript.galaxy'
INC = 'FixedToInt(MinF(GameGetMissionTime(), 240.0) / 2.0)'


def rep(t, a, b):
    assert t.count(a) == 1, a[:80]
    return t.replace(a, b)


def patch(t):
    t = rep(t, '    PlayerModifyPropertyInt(8,c_playerPropMinerals,c_playerPropOperSetTo,300);\n'
               '    PlayerModifyPropertyInt(8,c_playerPropVespene,c_playerPropOperSetTo,0);\n'
               '    PlayerModifyPropertyInt(9,c_playerPropMinerals,c_playerPropOperSetTo,500);\n'
               '    PlayerModifyPropertyInt(9,c_playerPropVespene,c_playerPropOperSetTo,0);\n',
            '    // 0.12.13: Korhal stage 2 starts after 4:00, so the allies get the income they would have saved by then\n'
            f'    PlayerModifyPropertyInt(8,c_playerPropMinerals,c_playerPropOperSetTo,300 + 25 * {INC});\n'
            f'    PlayerModifyPropertyInt(8,c_playerPropVespene,c_playerPropOperSetTo,8 * {INC});\n'
            f'    PlayerModifyPropertyInt(9,c_playerPropMinerals,c_playerPropOperSetTo,500 + 40 * {INC});\n'
            f'    PlayerModifyPropertyInt(9,c_playerPropVespene,c_playerPropOperSetTo,8 * {INC});\n')
    t = rep(t, '    UnitCreate(1, "FenixClolarionCarrier", c_unitCreateIgnorePlacement, 1, PointWithOffsetPolar(o, 4.0, f + 150.0), f);\n',
            '    // 0.12.13: Raynor\'s Clolarion gets the champion bomber upgrade (it was granted to the Purifier ally only)\n'
            '    if (TechTreeUpgradeCount(1, "FenixChampionCarrierBombers", c_techCountCompleteOnly) == 0) { TechTreeUpgradeAddLevel(1, "FenixChampionCarrierBombers", 1); }\n'
            '    UnitCreate(1, "FenixClolarionCarrier", c_unitCreateIgnorePlacement, 1, PointWithOffsetPolar(o, 4.0, f + 150.0), f);\n')
    return t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        raw = files[K].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
        files[K] = patch(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8')
        changed = {'metadata.txt', K}
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
