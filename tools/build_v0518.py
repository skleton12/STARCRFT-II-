#!/usr/bin/env python3
"""0.5.17 -> 0.5.18: 레드스톤 지원 커서 제거 — 버튼 → 지도 클릭 위치에 투하 (사용자 2026-10-27).

사용자: "동맹 유닛은 잘 나오고 커서는 걍 빼자, 클릭 위치에 투하하는 것만 나오면 될 듯, 근데 클릭하면 뭔가 또 나오는데".
0.5.17이 버튼을 누를 때 보이지 않는 시전 유닛을 선택하고(초상화·명령 카드가 뜸) 지점 커서를 열던 것을 지운다.
버튼(또는 Ctrl+V·Ctrl+B)을 누르면 안내만 뜨고, 다음 지도 왼쪽 클릭 위치에 그 동맹이 소환·투하한다 (오른쪽 클릭 취소).

Usage: python3 tools/build_v0518.py <0.5.17 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.17', b'version=0.5.18'
S = 'TTosh01.SC2Map/mapscript.galaxy'

SCRIPT = [
    ('    if (gv_m5_selSaved==null) { gv_m5_selSaved=UnitGroupCopy(UnitGroupSelected(1)); }\n'
     '    UnitClearSelection(1);\n'
     '    UnitSelect(gv_m5_caster,1,true);\n'
     '    Wait(0.0625,c_timeReal);\n'
     '    if (gv_m5_aimP!=p) { return; }\n'
     '    UISetTargetingOrder(PlayerGroupSingle(1),gv_m5_casterGroup,OrderTargetingPoint(AbilityCommand(gv_m5_callAbil[p],0),UnitGetPosition(gv_m5_caster)),false);\n',
     '    // 0.5.18 (user): no cursor and no caster selection; the next left click on the map is the drop point.\n'),
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[S].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = sub(t.replace('\r\n', '\n'), SCRIPT)
        assert 'UISetTargetingOrder(' not in t and 'UnitSelect(gv_m5_caster' not in t
        files[S] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (S, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
