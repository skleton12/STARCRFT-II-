#!/usr/bin/env python3
"""0.5.7 -> 0.5.8: 레드스톤 스크립트 컴파일 오류 수정 (사용자 2026-10-27 "뭔가 깨졌는지 파악해 볼래").

0.5.7에서 [동맹 지원]을 협동전 상단 패널로 바꾸며 gv_m5_callReady 선언을 지웠는데, 시작 처리(gt_m5_Arrive_Func)에
그 변수에 값을 넣는 줄이 남았다. Galaxy는 선언 없는 변수를 쓰면 맵 스크립트 전체를 컴파일하지 못한다
(동맹·적 강화·승리 조건 등 모드 스크립트가 통째로 안 돎). 그 줄을 지운다. 첫 사용 대기는 능력 데이터
(RM5_AllySupport 재사용 대기 TimeStart 55초)가 이미 맡는다.

check_release에 '선언 없는 전역 변수(gv_)·함수(gf_)' 검사를 추가했다 (0.5.7에서 실패 재현 확인).

Usage: python3 tools/build_v058.py <0.5.7 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.7', b'version=0.5.8'
S = 'TTosh01.SC2Map/mapscript.galaxy'
BAD = '    gv_m5_callReady=GameGetMissionTime()+55.0;\n'


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[S].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = t.replace('\r\n', '\n')
        assert t.count(BAD) == 1 and t.count('gv_m5_callReady') == 1
        t = t.replace(BAD, '')
        files[S] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (S, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
