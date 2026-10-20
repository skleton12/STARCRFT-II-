#!/usr/bin/env python3
"""Build CCM 0.4.49 from 0.4.48: And/Or 요구조건의 피연산자 번호를 뺀다 — 기술실 연구 버튼이 숨던 원인.

0.4.48 진단 (사용자 스크린샷 2026-10-20, 새 임무 0:11): 모든 연구가 미연구(q=0 c=0)·업그레이드 허용·명령 허용인데
엔진이 버튼을 숨겼다(hidden=1). 보이는 것(고급 의무관 훈련·자극제·방패·레이저)은 Show 가 곧바로 Not 노드,
숨은 것(파편탄·충격완화복·전투 안정제 두 판·화염 연구)은 모두 And 노드를 거친다.
원인: 우리 And 노드는 <OperandArray index="0" …>처럼 번호를 붙였다. And/Or 의 피연산자는 늘어나는 배열이고,
블리자드 원본 And/Or 약 780개는 번호를 한 번도 쓰지 않는다 (Not·Eq 같은 고정 칸 노드만 번호를 쓴다).
번호 붙은 칸은 무시돼 And 가 거짓 → 버튼 숨김. 0.4.38(파편탄)·0.4.44(협동전 전투 안정제) 증상도 같은 원인.
수정: 네 맵의 CRequirementAnd/Or 에서 OperandArray 의 index 속성만 지운다 (순서·값은 그대로).
  3번 맵의 초 전투 자극제·고급 전투 자극제 단계 표시(RM3_Stim2Show·Stim3Show)도 같은 결함이라 함께 고쳐진다.
0.4.48 진단 스크립트는 뺀다 (어부지리 mapscript 를 0.4.47 것으로 되돌림). check_release 에 같은 결함 검사 추가.

Usage: python3 tools/build_v0449.py <0.4.48 zip> <0.4.47 zip (mapscript source)> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.48', b'version=0.4.49'
MAPS = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'


def nodes(d):
    t = d.decode('utf-8')
    def fix(m):
        return re.sub(r'<OperandArray index="\d+" ', '<OperandArray ', m.group(0))
    t2, n = re.subn(r'<(CRequirement(?:And|Or))\s+id="[^"]+"[^>]*>.*?</\1>', fix, t, flags=re.S)
    return t2.encode('utf-8')


def build(source, script_src, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(script_src) as old:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert b'version=0.4.47' in old.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        files[SCRIPT] = old.read(SCRIPT)
        assert b'gt_m4_Diag_Func' in prev.read(SCRIPT) and b'gt_m4_Diag_Func' not in files[SCRIPT]
        changed = {'metadata.txt', SCRIPT}
        for m in MAPS:
            n = f'{m}.SC2Map/base.sc2data/gamedata/requirementnodedata.xml'
            new = nodes(files[n])
            if new != files[n]:
                files[n] = new; changed.add(n)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, sorted(changed))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('script_src', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.script_src, a.output)
