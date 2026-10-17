#!/usr/bin/env python3
"""Build CCM 0.3.29 from 0.3.28: 동맹 생산 거점 개수 제한 (3번 미션).

사용자 지시 (2026-10-17): 원시 감시자는 최대 4개. 수정탑 개수는 Claude가 정한다.
  - 원시 감시자: 4개 (사용자 확정).
  - 수정탑: 4개 (Claude 결정, 시험값). 감시자와 같은 수로 맞춰 두 동맹의 소환 거점 수를 같게 한다.
    수정탑 하나가 동맹 전용 보급 100을 주므로 4개면 인구 100 상한에 충분하다.
  - 건설 중·대기 중인 것까지 세어(c_techCountQueuedOrBetter) 상한에 닿으면 그 건설 명령을 막고, 줄면 다시 연다.
    두 일꾼이 동시에 마지막 자리를 지으면 하나 넘칠 수 있다.
  - 광자포·원시 벌레는 제한하지 않는다.

Usage: python3 tools/build_v0329.py <0.3.28 zip> <new output zip>
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.28', b'version=0.3.29'
SCRIPT = 'TRaynor03.SC2Map/mapscript.galaxy'
OLD_TICK = '    gf_m3_Produce();\n    gf_m3_Workers();\n'
NEW_TICK = '''    gf_m3_Produce();
    gf_m3_Workers();
    // Post limits (user 2026-10-17): Primal Wardens 4 (user), Pylons 4 (trial). Counted with queued/in-progress ones.
    TechTreeAbilityAllow(11,AbilityCommand("DehakaDroneMorph",0),TechTreeUnitCount(11,"DehakaBarracks",c_techCountQueuedOrBetter)<4);
    TechTreeAbilityAllow(10,AbilityCommand("ProtossBuild",1),TechTreeUnitCount(10,"Pylon",c_techCountQueuedOrBetter)<4);
'''


def script(data):
    text = data.decode('utf-8')
    assert text.count(OLD_TICK) == 1
    return text.replace(OLD_TICK, NEW_TICK, 1).encode('utf-8')


FIX = {SCRIPT: script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX: data = FIX[info.filename](data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
