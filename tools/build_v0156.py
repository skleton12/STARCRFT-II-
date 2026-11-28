#!/usr/bin/env python3
"""0.15.5 -> 0.15.6: 충격 전차 공성 모드가 노바 블랙옵스 전차 모델로 나오던 것 수정 (사용자 2026-11-28 스크린샷, "애초에 나와야하는게 저 전차가 아니잖아").
원인: 협동전에서 옮긴 액터에 'HaveBlackOps면 SiegeTank_BlackOps로 ModelSwap' 이벤트가 남았고, 그 요구조건이 가리키는 노드
CountUpgradeBlackOpsCompleteOnly가 맵에 없어 조건이 참으로 처리됨(0.4.54 빈 피연산자와 같은 유형). BlackOps 이벤트 줄을 모든 맵 액터에서 지운다.
또 멩스크 유닛 색 매크로(MengskUnitColorMacro)의 조건 IsMengskCoopCommander가 맵에서 거짓이라 멩스크 빨강 팀 색이 안 입혀졌다(일반 모드 금색)
→ 조건을 지워 충격 전차·보급 벙커·이지스·대지파괴 포가 협동전처럼 멩스크 빨강으로 나오게 한다.
Usage: build_v0156.py <0.15.5 zip> <out>"""
import copy, re, sys, zipfile
from pathlib import Path
OLD, NEW = b'version=0.15.5', b'version=0.15.6'
LINE = re.compile(r'^[ \t]*<On Terms="[^"]*BlackOps[^"]*"[^>]*/>\r?\n|^[ \t]*<On [^>]*Send="[^"]*BlackOps[^"]*"[^>]*/>\r?\n', re.M)


def build(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}; tot = 0
        for n in z.namelist():
            if n.endswith('/gamedata/actordata.xml'):
                t = z.read(n).decode('utf-8'); t2, k = LINE.subn('', t)
                if '; ValidateUnit IsMengskCoopCommander' in t2: t2 = t2.replace('; ValidateUnit IsMengskCoopCommander', ''); k += 1
                if k: rep[n] = t2.encode('utf-8'); tot += k; assert 'BlackOps"' not in t2.replace('SiegeTank_BlackOps_JumpJets_Land"', ''), n
        assert tot >= 60, tot
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out, tot)


if __name__ == '__main__': build(*sys.argv[1:])
