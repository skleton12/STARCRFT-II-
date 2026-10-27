#!/usr/bin/env python3
"""0.5.4 -> 0.5.5: 정화자 동맹 병력 = 공허의 유산 정화자 + 협동전 피닉스, 신기루 제외 (사용자 2026-10-27).

사용자: "정화자 꺼 피닉스 꺼랑 카락스 꺼 있네… 피닉스 유닛만, 신기루는 제외" → "공허의 유산 정화자랑 피닉스 유닛 융합".
- 공허 정화자: 파수병·선동자·동력기·거신·신기루·폭풍함 / 피닉스 협동전: 군단병(파수병과 같은 ID)·사도·보전기·불멸자·거신·분열기·정찰기·우주모함.
- 지금 편성에서 이 두 묶음 밖에 있는 것은 신기루(PhoenixPurifier)뿐이다 (공허 정화자지만 사용자가 제외).
  바이킹 해금 → 신기루 칸(WarpGateTrain 6+4)을 정화자에게 열지 않고, 레드스톤 30초 지원 묶음에서도 뺀다.
- 4번(TTychus01)·5번(TTosh01). 3번은 해금 연동 칸이 없어 그대로.

레드스톤 승리 조건 추가 (사용자 2026-10-27 "맵 내 모든 저그 기지 처리하면 승리 판정"):
- 원작 광물 8000 모으기는 그대로 두고, 저그(2·4번) 건물이 하나도 안 남아도 승리한다 (2초마다 확인).
- 점막 종양은 세지 않는다. 연출 중이거나 이미 끝났으면 건너뛴다. 승리 처리는 광물 목표 달성과 같은 순서
  (목표 완료 → libCamp_gf_RunMissionVictorySequence(gt_VictoryQ)).

Usage: python3 tools/build_v055.py <0.5.4 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.4', b'version=0.5.5'
WIPE = (
    '// 0.5.5: Redstone is also won once every Zerg structure (players 2 and 4) is gone (user 2026-10-27).\n'
    'bool gt_m5_ZergWipe_Func (bool testConds, bool runActions) {\n'
    '    unitgroup g;\n'
    '    int p;\n'
    '    int i;\n'
    '    string k;\n'
    '    if (!runActions || gv_gameOver || gv_inCinematic || !gv_m5_started) { return true; }\n'
    '    for (p=2;p<=4;p+=2) {\n'
    '        g=UnitGroup(null,p,RegionEntireMap(),UnitFilter((1 << c_targetFilterStructure),0,0,(1 << (c_targetFilterDead - 32))),0);\n'
    '        i=UnitGroupCount(g,c_unitCountAll);\n'
    '        for (;i>0;i-=1) {\n'
    '            k=UnitGetType(UnitGroupUnit(g,i));\n'
    '            if (k!="CreepTumor" && k!="CreepTumorBurrowed" && k!="CreepTumorQueen") { return true; }\n'
    '        }\n'
    '    }\n'
    '    TriggerEnable(TriggerGetCurrent(), false);\n'
    '    TriggerEnable(gt_VictoryCollectedQuota, false);\n'
    '    gv_gameOver = true;\n'
    '    TriggerExecute(gt_ObjectiveCollectComplete, true, true);\n'
    '    libCamp_gf_RunMissionVictorySequence(gt_VictoryQ);\n'
    '    return true;\n'
    '}\n\n'
)
INIT = 'void gt_VictoryCollectedQuota_Init () {\n    gt_VictoryCollectedQuota = TriggerCreate("gt_VictoryCollectedQuota_Func");\n'

EDITS = {
    'TTychus01': [
        ('TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",6+k),gf_m4_Unl(k) || k==6);',
         'TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",6+k),(gf_m4_Unl(k) || k==6) && k!=4);  // no Mirage (user 2026-10-27)'),
        ('if (gf_m4_Unl(k) || k==6) { gv_m4_warpSlot', 'if ((gf_m4_Unl(k) || k==6) && k!=4) { gv_m4_warpSlot'),
    ],
    'TTosh01': [
        ('TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",6+k),gf_m5_Unl(k) || k==6);',
         'TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",6+k),(gf_m5_Unl(k) || k==6) && k!=4);  // no Mirage (user 2026-10-27)'),
        ('if (gf_m5_Unl(k) || k==6) { gv_m5_warpSlot', 'if ((gf_m5_Unl(k) || k==6) && k!=4) { gv_m5_warpSlot'),
        ('if (gf_m5_Unl(k) || k==6) { extra[n]', 'if ((gf_m5_Unl(k) || k==6) && k!=4) { extra[n]'),
        (INIT, WIPE + INIT + '    TriggerAddEventTimePeriodic(TriggerCreate("gt_m5_ZergWipe_Func"), 2.0, c_timeGame);\n'),
    ],
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for m, edits in EDITS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            nl = '\r\n' if '\r\n' in t else '\n'
            t = t.replace('\r\n', '\n')
            for a, b in edits:
                assert t.count(a) == 1, (m, a)
                t = t.replace(a, b)
            files[s] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'} | {f'{m}.SC2Map/mapscript.galaxy' for m in EDITS}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
