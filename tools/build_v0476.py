#!/usr/bin/env python3
"""0.4.75 -> 0.4.76: 원시 일벌레 보충 드롭 포드 모델이 쌓이던 것 정리 (4번).

0.4.70 기록: gf_m4_Workers 는 원시 일벌레가 2기 미만이면 30초마다 (67,27)에 ZergDropPod 모델을 만들고 지우지 않았다.
보충될 때마다 포드 껍데기가 같은 자리에 하나씩 쌓인다. 첫 도착 연출(gf_m4_Arrive)처럼 잠시 뒤 지운다:
만든 포드를 전역에 두고, 10초(시험값) 지나면 다음 틱에서 Destroy. 일벌레 보충 수·간격·위치는 그대로.

Usage: python3 tools/build_v0476.py <0.4.75 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.75', b'version=0.4.76'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'
PAIRS = [
    ('\nvoid gf_m4_Workers () {', '\nactor gv_m4_workerPod;\nfixed gv_m4_workerPodKill;\n\nvoid gf_m4_Workers () {'),
    ('    if (GameGetMissionTime()<gv_m4_nextWorkers) { return; }\n    have=',
     '    // 0.4.76: remove the refill drop pod shell 10 s after it lands (it used to pile up at (67,27)).\n'
     '    if (gv_m4_workerPod!=null && GameGetMissionTime()>=gv_m4_workerPodKill) {\n'
     '        ActorSend(gv_m4_workerPod,"Destroy");\n        gv_m4_workerPod=null;\n    }\n'
     '    if (GameGetMissionTime()<gv_m4_nextWorkers) { return; }\n    have='),
    ('        ActorSend(pod,"AnimPlay Drop Birth NonLooping");\n        for (i=have;i<2;i+=1)',
     '        ActorSend(pod,"AnimPlay Drop Birth NonLooping");\n'
     '        if (gv_m4_workerPod!=null) { ActorSend(gv_m4_workerPod,"Destroy"); }\n'
     '        gv_m4_workerPod=pod;\n        gv_m4_workerPodKill=GameGetMissionTime()+10.0;\n        for (i=have;i<2;i+=1)'),
]


def script(d):
    t = d.decode('utf-8')
    for a, b in PAIRS:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
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
