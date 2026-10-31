#!/usr/bin/env python3
"""0.6.10 -> 0.6.11: 대피 전 고용소에 프로메테우스 중대가 보이는 문제 (사용자 2026-10-31 재보고 "대피 안 가서 화염방사병 안 풀렸는데
왜 고용소에 프로메테우스 중대가 있는 건데").

0.6.5/0.6.7은 스크립트 TechTreeAbilityAllow(고용 명령 허용)만으로 막았는데, 게임에서 버튼이 그대로 보였다
(허용을 꺼도 버튼이 숨지 않거나 캠페인 스크립트가 다시 허용하는 것으로 보임 — 어느 쪽인지는 미확정).
버튼 자체에 요구조건을 건다 (RMA_DevilDogUnlocked와 같은 방식):
- 표시 업그레이드 RM6_PrometheusUnlocked (효과 없음).
- 요구조건 RM6_CanHirePrometheus: Show·Use = RM6_PrometheusUnlocked 완료. 고용소 Train2 버튼에 연결 → 없으면 버튼이 안 보인다.
- 스크립트: 대피 완료 기록 && 악마의 개 계약 구매됨일 때만 RM6_PrometheusUnlocked를 1로 (시작 때 한 번).
4·5·6번.

Usage: python3 tools/build_v0611.py <0.6.10 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_v062 import find, xml_edit, add_xml, GD

OLD, NEW = b'version=0.6.10', b'version=0.6.11'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
UP, REQ, NODE = 'RM6_PrometheusUnlocked', 'RM6_CanHirePrometheus', 'RM6_PrometheusUnlockedCount'
ADD = {
    'upgradedata.xml': f'<CUpgrade id="{UP}"><Race value="Terr" /></CUpgrade>',
    'requirementnodedata.xml': f'<CRequirementCountUpgrade id="{NODE}"><Count Link="{UP}" State="CompleteOnly" /></CRequirementCountUpgrade>',
    'requirementdata.xml': f'<CRequirement id="{REQ}"><NodeArray index="Show" Link="{NODE}" /><NodeArray index="Use" Link="{NODE}" /></CRequirement>',
}
COND = ('libCamp_gf_TS_BattleReportMissionCompleted(libCamp_ge_MapID_MapTHanson01) && '
        'libCamp_gf_MercStatusCheck(libCamp_ge_StoryMercID_MercDevilDogs,libCamp_ge_StoryMercStatus_Purchased)')
A = f'    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",1),{COND});\n'
B = A + (f'    // 0.6.11: the hire button itself requires this upgrade (button hidden before The Evacuation).\n'
         f'    TechTreeUpgradeAllow(1,"{UP}",true);\n'
         f'    if ({COND} && TechTreeUpgradeCount(1,"{UP}",c_techCountQueuedOrBetter)==0) {{\n'
         f'        TechTreeUpgradeAddLevel(1,"{UP}",1);\n'
         f'    }}\n')


def abils(root):
    t2 = [i for i in find(root, 'CAbilTrain', 'SummonMercenaries').findall('InfoArray') if i.get('index') == 'Train2']
    assert len(t2) == 1
    b = t2[0].find('Button')
    assert b.get('DefaultButtonFace') == 'HireDevilDogs' and b.get('Requirements') == ''
    b.set('Requirements', REQ)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            d = root / f'{m}.SC2Map'
            xml_edit(d / GD / 'abildata.xml', abils)
            for fn, xml in ADD.items():
                add_xml(d / GD / fn, xml)
            p = d / 'mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8')
            nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            assert t.count(A) == 1, m
            p.write_bytes(t.replace(A, B).replace('\n', nl).encode('utf-8'))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        changed = {'metadata.txt'} | {f'{m}.SC2Map/{x}' for m in MAPS for x in
                   ['mapscript.galaxy'] + [GD + f for f in ['abildata.xml', *ADD]]}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n not in changed:
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
