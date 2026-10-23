#!/usr/bin/env python3
"""0.4.69 -> 0.4.70: 어부지리 흰 반구(오류 구) 진단판 (진단 전용, 원인 찾으면 다음 판에서 뺀다).

사용자 보고 2026-10-23: 군대 옆에 클릭 안 되는 흰 반구(빨간 띠)가 2~3개 생긴다. 용병 쪽으로 추정.
레이너(1번) 유닛에서 용병 관련 행동이 생기거나 사라질 때 채팅에 [RM diag] 줄로 행동·유닛·위치·시간을 찍는다:
  이지스 보호막(깨지면 Destroy), 이지스·코랄 자극제, 코랄 '무사 통과', 초 전투 자극제.
구가 생긴 순간의 줄과 위치를 맞춰 원인을 찾는다.

Usage: python3 tools/build_v0470.py <0.4.69 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.69', b'version=0.4.70'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'
BEHAVIORS = ['MarauderMengskAbsorb', 'MarauderMengskAttackSpeedBoost', 'RMK_MarineMengskAttackSpeedBoost',
             'RMK_MarineMengskCombatShieldUpgrade', 'SuperStim']
DIAG = '''
// 0.4.70 diagnostic: white dome near mercenaries. Remove once found.
bool gt_m4_DomeDiag_Func (bool testConds,bool runActions) {
    unit u=EventUnit();
    string k="on";
    point p;
    if (!runActions || UnitGetOwner(u)!=1) { return true; }
    if (EventUnitBehaviorChange()==c_unitBehaviorChangeDestroy) { k="off"; }
    p=UnitGetPosition(u);
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("[RM diag] "+EventUnitBehavior()+" "+k+" "
        +UnitGetType(u)+" ("+FixedToString(PointGetX(p),0)+","+FixedToString(PointGetY(p),0)+") t="
        +FixedToString(GameGetMissionTime(),0)));
    return true;
}

void gf_m4_Init () {'''


def script(d):
    t = d.decode('utf-8')
    a = '\nvoid gf_m4_Init () {'
    assert t.count(a) == 1 and 'gt_m4_DomeDiag_Func' not in t
    t = t.replace(a, DIAG)
    b = '    t=TriggerCreate("gt_m4_Ping_Func");\n    TriggerAddEventPing(t,1);\n'
    assert t.count(b) == 1
    reg = '    t=TriggerCreate("gt_m4_DomeDiag_Func");\n' + ''.join(
        f'    TriggerAddEventUnitBehaviorChange(t,null,"{x}",c_unitBehaviorChangeCreate);\n'
        f'    TriggerAddEventUnitBehaviorChange(t,null,"{x}",c_unitBehaviorChangeDestroy);\n' for x in BEHAVIORS)
    t = t.replace(b, b + reg)
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), SCRIPT: script}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
