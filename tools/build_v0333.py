#!/usr/bin/env python3
"""Build CCM 0.3.33 from 0.3.32: 동맹 대기 위치 이동(3번, 드래그 원인 후보)과 사령관 레벨 잠금 제거(1~3번).

사용자 판단 (2026-10-17): "1·2번은 드래그가 잘 되고, 3번 그 지역(벙커 근처) 문제 같다".
확인한 것:
  - 3번 벙커 관련 스크립트(벙커 핑·글자 표시)와 벙커 데이터는 원본과 같다. 모드가 바꾸지 않았다.
  - 그런데 동맹 병력이 위협이 없을 때 모이는 곳이 바로 그 벙커 두 채((87.5,45.5), (82.5,40.5))와
    전쟁광 8기 사이다: 정화자 (84,48), 원시저그 (80,46) (0.3.17부터).
    0.3.11 첫 드래그 보고 때 동맹이 모이던 서쪽 방어선 (65,47)도 벙커 (67.5,48.5)와 전쟁광 8기 바로 옆이었다.
  - 두 번 모두 '드래그가 안 되는 자리 = 동맹 병력이 모여 서 있는 자리'다. 동맹 병력은 공유 조종·명령 불가 유닛이라
    상자 선택에 섞이면 선택 결과가 흔들릴 수 있다고 보고, 대기 위치를 레이너 병력·벙커가 없는 본진 언덕 안쪽 빈터로 옮긴다.
  - 정화자 (96,49), 원시저그 (100,48) (시험값). 벙커·전쟁광 무리와 10칸 이상 떨어진 같은 언덕 위다.
위협 대응·적 건물 공격·핑 30초 규칙은 그대로다. 이것은 원인 후보 제거이며 해결을 확인한 것이 아니다.

사용자 확정 (2026-10-17): "레벨 관련된 거 없애", "레벨 시스템은 자치령 용병 쪽에만 존재".
  - 협동전 이식에 딸려 온 사령관 레벨 잠금 버튼을 지운다: 정화자 광전사 '칼달리스 베기' 잠금(피닉스 4레벨, 1~3번),
    재구축 잠금(카락스 4레벨, 1번), 보급 벙커 사거리 잠금(멩스크 6레벨, 3번 — 요구조건 정의도 없던 연결).
  - 그 버튼만 쓰던 요구조건 FenixLevel04·KaraxLevel04 정의도 지운다.
  - 코랄의 후예(자치령 용병)의 진급 레벨(RMK_…Veterancy…)은 그대로 둔다.
  - 일반 벙커(원작)와 보급 벙커(멩스크 협동전)는 지금처럼 따로 둔다 (사용자 확정, 바꿀 것 없음).

Usage: python3 tools/build_v0333.py <0.3.32 zip> <new output zip>
"""
import argparse
import copy
import re
import zipfile
from pathlib import Path

OLD, NEW = b'version=0.3.32', b'version=0.3.33'
SCRIPT = 'TRaynor03.SC2Map/mapscript.galaxy'
RALLY = {
    b'    gv_m3_rally10=Point(84.0,48.0);': b'    gv_m3_rally10=Point(96.0,49.0);',
    b'    gv_m3_rally11=Point(80.0,46.0);': b'    gv_m3_rally11=Point(100.0,48.0);',
    b'    // Both allies defend Raynor\'s base; with no threat and enough army they attack the nearest enemy structure.':
    b'    // Both allies defend Raynor\'s base; with no threat and enough army they attack the nearest enemy structure.'
    b'\n    // Idle spots stay clear of Raynor\'s bunkers and troops (box-selection problem candidate, 0.3.33).',
}


def script(data):
    nl = b'\r\n' if b'\r\n' in data else b'\n'
    for a, b in RALLY.items():
        assert data.count(a) == 1, a
        data = data.replace(a, b.replace(b'\n', nl))
    return data


LEVEL = rb'(?:Raynor|Kerrigan|Artanis|Swann|Zagara|Vorazun|Karax|Abathur|Alarak|Nova|Stukov|Fenix|Dehaka|Horner|Han|Tychus|Zeratul|Stetmann|Mengsk)Level\d\d'


def no_level_buttons(data):
    out, n = re.subn(rb'[ \t]*<LayoutButtons [^>]*Requirements="' + LEVEL + rb'"[^>]*/>\r?\n', b'', data)
    return out, n


def no_level_reqs(data):
    return re.subn(rb'[ \t]*<CRequirement id="' + LEVEL + rb'">.*?</CRequirement>\r?\n', b'', data, flags=re.S)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files[SCRIPT] = script(files[SCRIPT])
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {SCRIPT, 'metadata.txt'}
        removed = {}
        for n in files:
            if n.endswith('/base.sc2data/gamedata/unitdata.xml'):
                files[n], removed[n] = no_level_buttons(files[n])
            elif n.endswith('/base.sc2data/gamedata/requirementdata.xml'):
                files[n], removed[n] = no_level_reqs(files[n])
            else:
                continue
            if removed[n]: changed.add(n)
            assert not re.search(rb'"' + LEVEL + rb'"', files[n]), n
        print({k.split('/')[0] + ' ' + k.split('/')[-1]: v for k, v in removed.items() if v})
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
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
