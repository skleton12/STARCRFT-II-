#!/usr/bin/env python3
"""Build CCM 0.4.61 from 0.4.60: 차원 관문 정화자 외형·동력기와 보전기 함께 (4번, 사용자 지시 2026-10-21).

1. "모든 프로토스 건물 … 협동전 피닉스 모델": 동맹 건물은 RM3_AllySkin 행동이 붙을 때(On) 정화자 모델로 바뀐다.
   관문이 차원 관문으로 변신하면 액터가 새로 생기는데 행동은 이미 붙어 있어 On 이 다시 오지 않아 일반 차원 관문
   모델로 보였다. 차원 관문 액터가 생길 때 그 행동이 있으면 바로 바꾼다 (검증기 RM4_HasAllySkin).
   연결체·관문·수정탑·광자포·융화소는 이미 정화자 모델 (협동전 피닉스 스킨에는 차원 관문 전용 모델이 없어 관문 모델).
2. "동력기·보전기 둘 다, 처음부터": 정화자 차원 관문 순환에 보전기(SentryFenix, 새 칸 Train13)를 레이너 해금과
   상관없이 넣는다. 동력기(2기 미만일 때)는 그대로. 원시저그의 같은 번호(관통촉수 합체)는 그대로 해금 조건.

Usage: python3 tools/build_v0461.py <0.4.60 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.60', b'version=0.4.61'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
VAL = ('<CValidatorUnitCompareBehaviorCount id="RM4_HasAllySkin"><Compare value="GT" />'
       '<Behavior value="RM3_AllySkin" /></CValidatorUnitCompareBehaviorCount>')
PAIRS = {
    GD + 'actordata.xml': [(
        '<CActorUnit id="WarpGate">\n        <On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap Gateway_Purifier_COOP" />',
        '<CActorUnit id="WarpGate">\n        <On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap Gateway_Purifier_COOP" />'
        '\n        <On Terms="ActorCreation; ValidateUnit RM4_HasAllySkin" Send="ModelSwap Gateway_Purifier_COOP" />')],
    M4 + 'mapscript.galaxy': [
        ('        TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",6+k),gf_m4_Unl(k));',
         '        // Sentinel/Conservator (k=6) from the start, with the Energizer (user 2026-10-21).\n'
         '        TechTreeAbilityAllow(8,AbilityCommand("WarpGateTrain",6+k),gf_m4_Unl(k) || k==6);'),
        ('        if (gf_m4_Unl(k)) { gv_m4_warpSlot[gv_m4_warpExtra]=6+k; gv_m4_warpExtra+=1; }',
         '        if (gf_m4_Unl(k) || k==6) { gv_m4_warpSlot[gv_m4_warpExtra]=6+k; gv_m4_warpExtra+=1; }')],
}


def fix(pairs):
    def fn(d):
        t = d.decode('utf-8')
        for a, b in pairs:
            assert t.count(a) == 1, a
            t = t.replace(a, b)
        return t.encode('utf-8')
    return fn


def validators(d):
    t = d.decode('utf-8')
    assert 'RM4_HasAllySkin' not in t
    i = t.rindex('</Catalog>')
    return (t[:i] + VAL + t[i:]).encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'validatordata.xml': validators}
FIX.update({k: fix(v) for k, v in PAIRS.items()})


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
