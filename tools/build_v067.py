#!/usr/bin/env python3
"""0.6.6 -> 0.6.7: 프로메테우스 중대는 대피(THanson01)를 끝낸 뒤에만 (사용자 2026-10-31 "대피 안 갔는데 풀려 있다니까").

0.6.5는 히페리온 악마의 개 계약 상태(libCamp MercDevilDogs = 구매됨)로만 막았는데, 사용자 게임에서 대피 전에도 열렸다
(계약 상태가 왜 열렸는지는 게임 확인 전 — 저장 데이터 등 원인 미확정). 원작 캠페인 기록으로 대피 완료를 직접 확인하는
조건을 함께 건다: libCamp_gf_TS_BattleReportMissionCompleted(libCamp_ge_MapID_MapTHanson01) (원작 전투 보고서가 쓰는 완료 판정,
CampaignLib_h 선언). 4·5·6번 고용소. 대피 임무 안에서는 아직 완료 전이라 나오지 않는다.

Usage: python3 tools/build_v067.py <0.6.6 zip> <new output zip>
"""
import argparse, copy, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.6', b'version=0.6.7'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
A = ('    // 0.6.5: only once the Hyperion Devil Dogs contract is bought (free once unlocked, i.e. after The Evacuation).\n'
     '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",1),'
     'libCamp_gf_MercStatusCheck(libCamp_ge_StoryMercID_MercDevilDogs,libCamp_ge_StoryMercStatus_Purchased));\n')
B = ('    // 0.6.7: Prometheus Company only after The Evacuation is completed (campaign record) and the Devil Dogs contract is bought.\n'
     '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",1),'
     'libCamp_gf_TS_BattleReportMissionCompleted(libCamp_ge_MapID_MapTHanson01) && '
     'libCamp_gf_MercStatusCheck(libCamp_ge_StoryMercID_MercDevilDogs,libCamp_ge_StoryMercStatus_Purchased));\n')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            p = root / f'{m}.SC2Map/mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8')
            nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            assert t.count(A) == 1, m
            p.write_bytes(t.replace(A, B).replace('\n', nl).encode('utf-8'))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n != 'metadata.txt' and not any(n == f'{m}.SC2Map/mapscript.galaxy' for m in MAPS):
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
