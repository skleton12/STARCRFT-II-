#!/usr/bin/env python3
"""0.6.18 -> 0.6.27: 적 강화 개편 (사용자 2026-11-14).

0.6.19~0.6.26은 Codex가 다른 컴퓨터에서만 만들고 GitHub·드라이브에 올리지 않아 찾지 못했다.
사용자 결정으로 GitHub에 남은 0.6.18에서 다시 출발하며, 번호가 겹치지 않게 0.6.27로 한다.

사용자 지시 (Wings of Mengsk 나이트메어 모드 구성을 참고한 사용자 기억 + 이번 답변):
1. 피해 % 강화를 지우고 공격만 50% ("1은 그 공격력 예시이고 0.5는 그 퍼센트, 50%").
   - 모든 적 플레이어(테란·프로토스·저그 모두): 주는 피해 150%, 받는 피해 100%(방어 % 삭제).
   - 난이도별 값은 ENEMY_ATK_PERCENT (쉬움·보통·어려움·아주 어려움) 하나로 둔다. 지금은 모두 50 (시험값).
2. 방어 % 대신 적 업그레이드를 빠르게 ("업그레이드 속도가 100이면 난이도마다 조정해 최대 75").
   - 원본의 시간제 적 업그레이드 트리거의 Wait 시간에 UPGRADE_TIME (쉬움·보통·어려움·아주 어려움)을 곱한다.
     대상: 2번 StartUpgradesH/I, 3번 AIResearchHard/Insane, 4번 AIUpgradesH/I.
     이 트리거들은 원본에서 어려움·아주 어려움에서만 돈다 (쉬움·보통은 원래 시간제 업그레이드가 없다).
   - 5번 레드스톤(용암 주기에 묶임)·6번 대피(구출 차수에 묶임)·1번(시작 때 한 번)은 시간이 아니라 사건 기준이라 그대로.
3. 병력은 난이도마다 늘리고, 정예(아주 어려움)는 더 ("정예만 더 늘림", "병력 늘리는거 난이도 마다 잘 늘려봐").
   - 0.6.18의 gf_rmWave4가 원본 공세 수(0.6.13의 x1.25, 저그는 기존 +50% 포함)에 적 AI 칸별 배수를 더 곱한다.
     0.6.18부터 적 AI는 한 칸 위라: 쉬움 -> 3칸(보통 수), 보통 -> 4칸, 어려움 -> 5칸, 아주 어려움 -> 정예(7칸).
   - WAVE_SLOT_MULT: 2칸 1.0, 3칸 1.0, 4칸 1.1, 5칸 1.2 / 정예(6~10칸) = 아주 어려움 수 x 1.5 (0.6.18은 1.25). 올림, 0은 0.
최소 업그레이드·아주 어려움 +1단계·1·2번 공방업 너프(0.6.15)·AI 한 칸 위(0.6.18)는 그대로다. 모두 시험값.

Usage: python3 tools/build_v0627.py <0.6.18 zip> <new output zip>
"""
import argparse, copy, re, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.18', b'version=0.6.27'
MAPS = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')

ENEMY_ATK_PERCENT = (50, 50, 50, 50)          # easy, normal, hard, very hard (trial)
UPGRADE_TIME = (1.0, 0.92, 0.83, 0.75)        # x original wait (trial; max speed 100 -> 75)
WAVE_SLOT_MULT = (1.0, 1.0, 1.1, 1.2)         # AI slots 2,3,4,5 (trial)
ELITE_WAVE_MULT = 1.5                          # slots 6-10 = Brutal count x this (was 1.25)

UPGRADE_TRIGGERS = {
    'TRaynor02': ('gt_StartUpgradesH_Func', 'gt_StartUpgradesI_Func'),
    'TRaynor03': ('gt_AIResearchHard_Func', 'gt_AIResearchInsane_Func'),
    'TTychus01': ('gt_AIUpgradesH_Func', 'gt_AIUpgradesI_Func'),
}

ATK = 'libNtve_gf_DifficultyValueInt({},{},{},{})'.format(*ENEMY_ATK_PERCENT)
UPT = 'libNtve_gf_DifficultyValueFixed({},{},{},{})'.format(*UPGRADE_TIME)

DEALT = re.compile(r'(PlayerModifyPropertyInt\(\s*[^,]+,\s*c_playerPropDamageDealtPercent,\s*c_playerPropOperSetTo,\s*)([^;]+?)(\);)')
TAKEN = re.compile(r'(PlayerModifyPropertyInt\(\s*[^,]+,\s*c_playerPropDamageTakenPercent,\s*c_playerPropOperSetTo,\s*)([^;]+?)(\);)')

WAVE_OLD_HEAD = '// Elite has no wave counts in the original data: slots 6-10 get the Brutal count x 1.25 (trial ELITE_WAVE_MULT).\n'
WAVE_OLD = '''const fixed gv_rmEliteWaveMult = 1.25;
void gf_rmWave4 (int n1, int n2, int n3, int n4, string kind) {
    int d;
    AIAttackWaveAddUnits4(n1,n2,n3,n4,kind);
    for (d=6;d<=10;d+=1) { AIAttackWaveAddUnits(d,CeilingI(IntToFixed(n4)*gv_rmEliteWaveMult),kind); }
}
'''
WAVE_NEW_HEAD = ('// 0.6.27 (user 2026-11-14): waves grow per AI slot (trial). Since 0.6.18 the enemy plays one slot up:\n'
                 '// Easy -> slot 3, Normal -> 4, Hard -> 5, Very Hard -> Elite (7). Elite (6-10) = Brutal count x %s.\n' % ELITE_WAVE_MULT)
WAVE_NEW = '''const fixed gv_rmEliteWaveMult = %s;
const fixed gv_rmWaveMult2 = %s;
const fixed gv_rmWaveMult3 = %s;
const fixed gv_rmWaveMult4 = %s;
const fixed gv_rmWaveMult5 = %s;
int gf_rmWaveN (int n, fixed mult) {
    if (n<=0) { return 0; }
    return CeilingI(IntToFixed(n)*mult);
}
void gf_rmWave4 (int n1, int n2, int n3, int n4, string kind) {
    int d;
    AIAttackWaveAddUnits(2,gf_rmWaveN(n1,gv_rmWaveMult2),kind);
    AIAttackWaveAddUnits(3,gf_rmWaveN(n2,gv_rmWaveMult3),kind);
    AIAttackWaveAddUnits(4,gf_rmWaveN(n3,gv_rmWaveMult4),kind);
    AIAttackWaveAddUnits(5,gf_rmWaveN(n4,gv_rmWaveMult5),kind);
    for (d=6;d<=10;d+=1) { AIAttackWaveAddUnits(d,gf_rmWaveN(n4,gv_rmEliteWaveMult),kind); }
}
''' % ((ELITE_WAVE_MULT,) + WAVE_SLOT_MULT)


def func_span(t, name):
    m = re.search(r'^bool %s \(bool testConds, bool runActions\) \{\n' % re.escape(name), t, re.M)
    assert m, name
    end = t.index('\n}\n', m.end()) + 3
    return m.start(), end


def edit(m, t):
    notes = []
    # 1. damage: dealt = 100 + ATK, taken = 100 (defense % removed)
    t, nd = DEALT.subn(lambda x: x.group(1) + '100+' + ATK + x.group(3), t)
    t, nt = TAKEN.subn(lambda x: x.group(1) + '100' + x.group(3), t)
    assert nd >= 1 and nd == nt, (m, nd, nt)
    notes.append(f'damage lines {nd}')
    # 2. timed enemy upgrades
    for name in UPGRADE_TRIGGERS.get(m, ()):
        a, b = func_span(t, name)
        body = t[a:b]
        body, nw = re.subn(r'Wait\((\d+\.\d+), c_timeAI\)', lambda x: f'Wait({x.group(1)}*{UPT}, c_timeAI)', body)
        assert nw >= 1 and 'TechTreeUpgradeAddLevel' in body, (m, name)
        t = t[:a] + body + t[b:]
        notes.append(f'{name} waits {nw}')
    # 3. waves
    if 'gf_rmWave4(' in t:
        assert t.count(WAVE_OLD_HEAD) == 1 and t.count(WAVE_OLD) == 1, m
        t = t.replace(WAVE_OLD_HEAD, WAVE_NEW_HEAD).replace(WAVE_OLD, WAVE_NEW)
        assert 'AIAttackWaveAddUnits4(' not in t, m
        notes.append(f'wave calls {t.count("gf_rmWave4(") - 1}')
    return t, notes


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
            t, notes = edit(m, raw.replace('\r\n', '\n'))
            p.write_bytes(t.replace('\n', nl).encode('utf-8'))
            changed.add(f'{m}.SC2Map/mapscript.galaxy')
            print(m, '; '.join(notes))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
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
