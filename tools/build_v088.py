#!/usr/bin/env python3
"""0.8.7 -> 0.8.8: 동맹 탐지기 (사용자 2026-11-23 "우리 동맹에 탐지기 하나만 넣어줘").

maps 3~8: 정화자 지원을 부를 때 정화자 관측선(Observer)이 맵에 없으면 무료로 1기 같이 온다 (무료분 맨 앞 = 인구 120 남은 자리를
먼저 받음, 한 번에 1기만, 죽으면 다음 지원 때 다시). 외형은 동맹 소유일 때만 정화자 관측선(Observer_Purifier_Collection, 자날 기본
데이터의 모델) - 불멸자·우주모함과 같은 RM3_AllySkin ModelSwap 방식이라 적 프로토스 관측선은 그대로. 은폐 탐지는 원작 관측선 그대로.
3번은 병력 목록(gf_m3_Army)에 관측선·선동자·피닉스 용사를 넣었다(코덱스 지적, 0.8.6·0.6.77 누락분).
Game not run.

Usage: python3 tools/build_v088.py <0.8.7 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.8.7', b'version=0.8.8'
MAPS = {'TRaynor03': 'm3c', 'TTychus01': 'm4', 'TTosh01': 'm5', 'THanson01': 'm6', 'TTosh02': 'm7', 'THorner01': 'm8'}
ACTOR = '<CActorUnit id="Observer"><On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap Observer_Purifier_Collection" /></CActorUnit>'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m, t in MAPS.items():
            k = f'{m}.SC2Map/base.sc2data/gamedata/actordata.xml'
            a = files[k].decode('utf-8')
            assert 'id="Observer"' not in a and 'RM3_AllySkin' in a, m
            i = a.rindex('</Catalog>'); files[k] = (a[:i] + ACTOR + a[i:]).encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/mapscript.galaxy'
            s = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in s else '\n'; s = s.replace('\r\n', '\n')
            f = s.index(f'void gf_{t}_SupFill (int p) {{')
            anchor = f'        gv_{t}_supPaid[p]=gv_{t}_supN[p];\n'
            j = s.index(anchor, f)
            assert j < s.index('\n}\n', f) and '"Observer"' not in s[f:s.index('\n}\n', f)], m
            add = (f'        // 0.8.8 (user 2026-11-23): one free Purifier Observer (detector) while none is alive.\n'
                   f'        if (UnitGroupCount(UnitGroup("Observer",p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0),c_unitCountAlive)==0) {{ gf_{t}_SupAdd(p,"Observer"); }}\n')
            s = s[:j + len(anchor)] + add + s[j + len(anchor):]
            # the anchor in the Purifier branch must come before the Zerg branch's own supPaid line
            assert s.index(add) < s.index(f'    gv_{t}_supPaid[p]=gv_{t}_supN[p];\n', j + len(anchor) + len(add)), m
            if m == 'TRaynor03':
                # Codex review: mission 3 lists its army by unit type - the Observer, the 0.8.6 Instigators (StalkerPurifier)
                # and the 0.6.77 Fenix champions were missing, so they got no attack-move / ping orders.
                x = 't=="ZealotPurifier" || t=="AdeptFenix" || t=="RM21_Energizer" ||'
                assert s.count(x) == 1, m
                s = s.replace(x, x + ' t=="StalkerPurifier" || t=="Observer" || StringSub(t,1,5)=="Fenix" ||')
            files[k] = s.replace('\n', nl).encode('utf-8'); changed.add(k)
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
