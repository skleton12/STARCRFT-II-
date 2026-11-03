#!/usr/bin/env python3
"""0.6.16 -> 0.6.17: 적 피해 % 살짝 낮추고 적 AI 난이도 한 단계 올림 (사용자 2026-11-03 "저거 피해를 살짝줄이고 AI를 한단계 올리자").

모든 임무 맵(1~6번)의 원본 적 슬롯만. 모두 시험값.
- 테란·프로토스 적 피해 % (ENEMY_BUFF_PERCENT): 5/15/30/60 -> 5/10/25/50 (1·2번, 4번 탈다림).
- 저그 적 능력치: 10/15/20/30 -> 5/10/15/25 (3~6번; 기본 gv_rmZergBuffPercent 10 + 난이도별 -5/0/5/15).
- 적 AI 한 단계 위 (AI_STEP_UP): 적 플레이어의 난이도를 플레이어(1번) 난이도 +1로 둔다 (PlayerSetDifficulty, 캠페인 1~4, 최대 4).
  원작 캠페인 AI와 공세 수(AIAttackWaveAddUnits4의 쉬움/보통/어려움/아주 어려움 값)가 한 단계 위 값을 쓴다.
  아주 어려움은 이미 4라 그대로. 미션 진행 트리거(PlayerDifficulty(1))와 모드 난이도별 값은 플레이어 난이도를 따르므로 바뀌지 않는다.
  시작 때 적 규칙을 거는 곳(gf_rmVHTerran / gf_rmVHProtoss / gf_rmZergBuff)에서 적 플레이어마다 한 번 건다.

Usage: python3 tools/build_v0617.py <0.6.16 zip> <new output zip>
"""
import argparse, copy, tempfile, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.16', b'version=0.6.17'
ENEMY_BUFF_PERCENT = (5, 10, 25, 50)
ZERG_EXTRA = (-5, 0, 5, 15)            # + gv_rmZergBuffPercent (10) -> 5/10/15/25
AI_STEP_UP = 1

AI_FN = f'''// 0.6.17 (user 2026-11-03): enemy AI plays one campaign difficulty above the player's (1-4, trial AI_STEP_UP).
const int gv_rmAIStepUp = {AI_STEP_UP};
void gf_rmAIUp (int p) {{
    PlayerSetDifficulty(p,MinI(4,PlayerDifficulty(1)+gv_rmAIStepUp));
}}

'''
MAPS = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')


def once(t, old, new):
    assert t.count(old) == 1, old[:70]
    return t.replace(old, new)


def edit(m, t):
    if m in ('TRaynor01', 'TRaynor02', 'TTychus01'):
        t = once(t, 'libNtve_gf_DifficultyValueInt(5,15,30,60)', 'libNtve_gf_DifficultyValueInt({},{},{},{})'.format(*ENEMY_BUFF_PERCENT))
    if m not in ('TRaynor01', 'TRaynor02'):
        t = once(t, 'libNtve_gf_DifficultyValueInt(0,5,10,20)', 'libNtve_gf_DifficultyValueInt({},{},{},{})'.format(*ZERG_EXTRA))
    head = 'void gf_rmVHTerran (int p) {\n'
    t = once(t, head, AI_FN + head)
    for fn in ('void gf_rmVHTerran (int p) {\n', 'void gf_rmVHProtoss (int p) {\n', 'void gf_rmVHZerg (int p) {\n'):
        t = once(t, fn, fn + '    gf_rmAIUp(p);\n')
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        changed = {'metadata.txt'}
        for m in MAPS:
            p = root / f'{m}.SC2Map' / 'mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8')
            nl = '\r\n' if '\r\n' in raw else '\n'
            p.write_bytes(edit(m, raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'))
            changed.add(f'{m}.SC2Map/mapscript.galaxy')
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n not in changed:
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
