#!/usr/bin/env python3
"""0.5.14 -> 0.5.15: 레드스톤 지원 지점 능력을 RaynorRogue 상단 능력과 같은 모양으로 (사용자 2026-10-27 "다른 모드는 어떻게 했는지 찾아봐").

RaynorRogue의 상단 지점 능력(PrecisionStrike·NuclearAnnihilation·TerranRecall)은 명령 패널 + CAbilEffectTarget
(Range 500, Arc 360, CursorEffect = 범위 탐색 효과)뿐이고, 명령 버튼에 ToSelection 같은 플래그가 없다. 원(핵·EMP 같은 커서)은
CursorEffect의 반경으로 게임이 그린다. 0.5.12에서 붙인 ToSelection(명령을 현재 선택 유닛에게 보냄 → 상단 패널 버튼을 눌러도
선택된 SCV 등에게 가 버릴 수 있음)을 뗀다. CursorEffect RM5_AllySupportSearch(반경 3)는 그대로.

Usage: python3 tools/build_v0515.py <0.5.14 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.14', b'version=0.5.15'
A = 'TTosh01.SC2Map/base.sc2data/gamedata/abildata.xml'
FLAG = '      <Flags index="ToSelection" value="1" />\n'


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[A].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = t.replace('\r\n', '\n')
        for aid in ('RM5_AllySupport', 'RM5_PrimalSupport'):
            old = f'    <CmdButtonArray index="Execute" DefaultButtonFace="{aid}">\n{FLAG}    </CmdButtonArray>\n'
            assert t.count(old) == 1, aid
            t = t.replace(old, f'    <CmdButtonArray index="Execute" DefaultButtonFace="{aid}" />\n')
        files[A] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (A, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
