#!/usr/bin/env python3
"""0.12.11 -> 0.12.12: 코덱스 검토(0.12.11) 반영 — 코랄 영웅 지원.

THorner04:
  - 땅무지(DehakaCreeperFlying) 카드의 급강하 버튼은 정의 없는 능력을 가리켜 아무 일도 안 했다 → 버튼 줄과 0.12.11의 급강하 문자열·단축키를 지움.
  - 클로라리온 본체 무기 칸 3종(FenixClolarionPrismaticBeamDummy·InterceptorsDummy·BombersDummy) 이름 문자열.
  - 수리 드론: 수리 중(CarrierRepairDroneHeal 명령)에는 1초 호위 이동 명령을 건너뛴다(이동 명령이 수리를 덮어쓰던 것).
  - 퇴장: 클로라리온·수리 드론 모두 높이를 올리며(UnitSetHeight 3초) 날아간 뒤 사라진다.
Game not run.

Usage: python3 tools/build_v01212.py <0.12.11 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.12.11', b'version=0.12.12'
M = 'THorner04.SC2Map/'
LOCS = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
ADD = {'Weapon/Name/FenixClolarionPrismaticBeamDummy': '분광 광선 /// Prismatic Beam',
       'Weapon/Name/FenixClolarionInterceptorsDummy': '요격기 /// Interceptors',
       'Weapon/Name/FenixClolarionBombersDummy': '폭격기 /// Bombers'}
DROP = ('Button/Name/DehakaLocustFlyingSwoop', 'Button/Tooltip/DehakaLocustFlyingSwoop', 'Button/Hotkey/DehakaLocustFlyingSwoop')


def rep(t, a, b):
    assert t.count(a) == 1, a[:80]
    return t.replace(a, b)


def lines_edit(data, add=None, drop=()):
    txt = data.decode('utf-8-sig'); bom = data.startswith(b'\xef\xbb\xbf'); nl = '\r\n' if '\r\n' in txt else '\n'
    ls = [l for l in txt.split(nl) if l and l.split('=', 1)[0] not in drop]
    have = {l.split('=', 1)[0] for l in ls}
    for k, v in (add or {}).items():
        assert k not in have, k
        ls.append(f'{k}={v}')
    return (b'\xef\xbb\xbf' if bom else b'') + (nl.join(ls) + nl).encode('utf-8')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        k = M + 'base.sc2data/gamedata/unitdata.xml'; t = files[k].decode('utf-8')
        t = rep(t, '            <LayoutButtons Face="DehakaLocustFlyingSwoop" Type="AbilCmd" AbilCmd="DehakaLocustFlyingSwoop,Execute" Row="2" Column="0" />\n', '')
        E.fromstring(t.encode()); files[k] = t.encode('utf-8'); changed.add(k)
        k = M + 'mapscript.galaxy'; raw = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'; s = raw.replace('\r\n', '\n')
        for v in ('gv_rm12Sv1', 'gv_rm12Sv2'):
            s = rep(s, f'    if ({v} != null && UnitIsAlive({v}) && DistanceBetweenPoints(',
                    f'    if ({v} != null && UnitIsAlive({v}) && !UnitOrderHasAbil({v}, "CarrierRepairDroneHeal") && DistanceBetweenPoints(')
        s = rep(s, '    if (gv_rm12Sv1 != null && UnitIsAlive(gv_rm12Sv1)) { UnitSetState(gv_rm12Sv1, c_unitStateInvulnerable, true); }\n'
                   '    if (gv_rm12Sv2 != null && UnitIsAlive(gv_rm12Sv2)) { UnitSetState(gv_rm12Sv2, c_unitStateInvulnerable, true); }\n',
                '    if (UnitIsAlive(gv_rm12Clo)) { UnitSetHeight(gv_rm12Clo, UnitGetHeight(gv_rm12Clo) + 12.0, 3.0); }\n'
                '    if (gv_rm12Sv1 != null && UnitIsAlive(gv_rm12Sv1)) { UnitSetState(gv_rm12Sv1, c_unitStateInvulnerable, true); UnitIssueOrder(gv_rm12Sv1, OrderTargetingUnit(AbilityCommand("move", 0), gv_rm12Clo), c_orderQueueReplace); UnitSetHeight(gv_rm12Sv1, UnitGetHeight(gv_rm12Sv1) + 12.0, 3.0); }\n'
                '    if (gv_rm12Sv2 != null && UnitIsAlive(gv_rm12Sv2)) { UnitSetState(gv_rm12Sv2, c_unitStateInvulnerable, true); UnitIssueOrder(gv_rm12Sv2, OrderTargetingUnit(AbilityCommand("move", 0), gv_rm12Clo), c_orderQueueReplace); UnitSetHeight(gv_rm12Sv2, UnitGetHeight(gv_rm12Sv2) + 12.0, 3.0); }\n')
        files[k] = s.replace('\n', nl).encode('utf-8'); changed.add(k)
        k = M + 'kokr.sc2data/localizeddata/gamestrings.txt'
        ko = lines_edit(files[k], ADD, DROP); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
        for loc in V35.OTHER_LOCALES:
            q = M + f'{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
        for loc in LOCS:
            q = M + f'{loc}.sc2data/localizeddata/gamehotkeys.txt'; files[q] = lines_edit(files[q], None, DROP); changed.add(q)
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
