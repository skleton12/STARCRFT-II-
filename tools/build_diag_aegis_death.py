#!/usr/bin/env python3
"""이지스 근위대 사망 진단판 (4번, 진단 전용). 2026-10-23 내 0.4.64 진단판으로 냈으나 GPT 0.4.64~0.4.67 계열이 본선이 되어 쓰지 않음 (번호 충돌 때문에 이름 바꿈).

사용자 보고 2026-10-23: 이지스 근위대(MarauderMengsk, 고용소 '망치 경호대' 2기)가 적에게 다가가다가 이유 불명으로 죽는다.
데이터 대조: 무기·효과·파편(자기·아군 제외)·계급은 협동전 원본과 같고 스크립트도 죽이지 않는다 → 원인 미발견.
감속 행동 MarauderMengskShrapnelSlow 정의가 없지만 감속 연구 전에는 검증기에서 막혀 쓰이지 않는다.
진단: 이지스 근위대(1번)가 받은 피해마다 '가한 유닛 종류·소유자·효과 ID·피해량'을 기록하고, 이지스가 준 피해 횟수를 센다.
이지스가 죽으면 채팅창에 [RM diag] 줄로 출력한다. 원인을 찾으면 다음 판에서 이 진단을 뺀다.

Usage: python3 tools/build_diag_aegis_death.py <0.4.63 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.63', b'version=0.4.64'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'
DIAG = '''
// 0.4.64 diagnostic: why Aegis Guard dies (player 1 MarauderMengsk). Remove once found.
int gv_m4_dgHits;
string gv_m4_dgLog;

bool gt_m4_AegisDmg_Func (bool testConds,bool runActions) {
    unit v=EventUnit();
    unit s=EventUnitDamageSourceUnit();
    string src="none";
    if (!runActions) { return true; }
    if (s!=null) {
        src=UnitGetType(s)+"/p"+IntToString(UnitGetOwner(s));
        if (UnitGetType(s)=="MarauderMengsk" && UnitGetOwner(s)==1) { gv_m4_dgHits+=1; }
    }
    if (UnitGetType(v)!="MarauderMengsk" || UnitGetOwner(v)!=1) { return true; }
    gv_m4_dgLog=src+" "+EventUnitDamageEffect()+" "+FixedToString(EventUnitDamageAmount(),1)
        +" (hp "+FixedToString(UnitGetPropertyFixed(v,c_unitPropLife,c_unitPropCurrent),0)+") | "+gv_m4_dgLog;
    if (StringLength(gv_m4_dgLog)>400) { gv_m4_dgLog=StringSub(gv_m4_dgLog,1,400); }
    return true;
}

bool gt_m4_AegisDied_Func (bool testConds,bool runActions) {
    unit v=EventUnit();
    if (!runActions || UnitGetType(v)!="MarauderMengsk" || UnitGetOwner(v)!=1) { return true; }
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringToText("[RM diag] Aegis died. Aegis hits dealt="
        +IntToString(gv_m4_dgHits)+" / last damage taken: "+gv_m4_dgLog));
    gv_m4_dgLog="";
    return true;
}

void gf_m4_Init () {'''
REG = '''    t=TriggerCreate("gt_m4_Ping_Func");
    TriggerAddEventPing(t,1);
    t=TriggerCreate("gt_m4_AegisDmg_Func");
    TriggerAddEventUnitDamaged(t,null,c_unitDamageTypeAny,c_unitDamageEither,null);
    t=TriggerCreate("gt_m4_AegisDied_Func");
    TriggerAddEventUnitDied(t,null);
}'''


def script(d):
    t = d.decode('utf-8')
    a = '\nvoid gf_m4_Init () {'
    assert t.count(a) == 1 and 'gt_m4_AegisDmg_Func' not in t
    t = t.replace(a, DIAG)
    b = '''    t=TriggerCreate("gt_m4_Ping_Func");
    TriggerAddEventPing(t,1);
}'''
    assert t.count(b) == 1
    t = t.replace(b, REG)
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
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
