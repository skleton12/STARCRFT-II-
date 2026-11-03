#!/usr/bin/env python3
"""0.6.17 -> 0.6.18: 적 AI 한 단계 위 바로잡기 + 아주 어려움 → 정예 (사용자 2026-11-03
"쉬움은 보통 보통은 어려움 어려움은 아주어려움 아주어려움은 정예로", "그다음이 치터이니").

원작 AI 라이브러리(core TriggerLibs/AI.galaxy) 확인:
- AI 난이도 칸: 1 매우 쉬움, 2 쉬움, 3 보통, 4 어려움, 5 더 어려움, 6 매우 어려움, 7 정예, 8~10 치터.
- 캠페인 공세(AIAttackWaveAddUnits4)는 2·3·4·5칸(쉬움/보통/어려움/아주 어려움)에만 병력 수를 넣는다.
  공세 병력은 적 AI 플레이어의 난이도 칸 값을 쓰므로, 캠페인 적 AI는 2~5칸에 있다.
0.6.17은 적 난이도를 '플레이어 난이도(1번) + 1, 최대 4'로 두어, 칸 체계가 달라 한 단계가 안 오르거나
아주 어려움을 낮출 수 있었다. 이를 고친다:
- 적 AI 난이도 = 그 적 자신의 원래 칸 + 1 (쉬움→보통→어려움→아주 어려움). 아주 어려움(5)은 정예(7)로. 한 번만.
- 정예 칸에는 원작 공세 수가 없으므로 모든 공세 줄에 6~10칸 값을 채운다: 아주 어려움 수 × 1.25 (올림, 시험값
  ELITE_WAVE_MULT). 안 채우면 정예 적의 공세가 0기가 된다. (공세 수에는 0.6.13의 ×1.25가 이미 들어 있다.)
피해 %·업그레이드·미션 트리거의 난이도 분기는 그대로다. 게임 미실행 (AI가 실제로 정예로 움직이는지 게임 확인 필요).

Usage: python3 tools/build_v0618.py <0.6.17 zip> <new output zip>
"""
import argparse, copy, tempfile, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.17', b'version=0.6.18'
ELITE_WAVE_MULT = 1.25
MAPS = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')

UP_OLD = '''void gf_rmAIUp (int p) {
    PlayerSetDifficulty(p,MinI(4,PlayerDifficulty(1)+gv_rmAIStepUp));
}
'''
UP_NEW = f'''// 0.6.18: AI slots 2-5 = Casual..Brutal (core AI.galaxy); one slot up from the enemy's own slot, Brutal -> Elite (7).
bool[16] gv_rmAIUpDone;
void gf_rmAIUp (int p) {{
    int d;
    if (gv_rmAIUpDone[p]) {{ return; }}
    gv_rmAIUpDone[p]=true;
    d=PlayerDifficulty(p)+gv_rmAIStepUp;
    if (d>=6) {{ d=7; }}
    PlayerSetDifficulty(p,d);
}}

// Elite has no wave counts in the original data: slots 6-10 get the Brutal count x {ELITE_WAVE_MULT} (trial ELITE_WAVE_MULT).
const fixed gv_rmEliteWaveMult = {ELITE_WAVE_MULT};
void gf_rmWave4 (int n1, int n2, int n3, int n4, string kind) {{
    int d;
    AIAttackWaveAddUnits4(n1,n2,n3,n4,kind);
    for (d=6;d<=10;d+=1) {{ AIAttackWaveAddUnits(d,CeilingI(IntToFixed(n4)*gv_rmEliteWaveMult),kind); }}
}}
'''


def edit(m, t):
    n = t.count('AIAttackWaveAddUnits4(')
    head = t.index(UP_OLD)
    assert t.count(UP_OLD) == 1
    if n:
        assert t.index('AIAttackWaveAddUnits4(') > head, m   # every wave line comes after the new function
        t = t.replace('AIAttackWaveAddUnits4(', 'gf_rmWave4(')
    t = t.replace(UP_OLD, UP_NEW)
    assert t.count('AIAttackWaveAddUnits4(') == 1
    return t, n


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
            t, n = edit(m, raw.replace('\r\n', '\n'))
            p.write_bytes(t.replace('\n', nl).encode('utf-8'))
            changed.add(f'{m}.SC2Map/mapscript.galaxy')
            print(m, 'wave lines', n)
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
