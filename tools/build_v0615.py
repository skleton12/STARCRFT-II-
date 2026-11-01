#!/usr/bin/env python3
"""0.6.13 -> 0.6.15: 1·2번 미션 적 공방업 1단계 너프 (사용자 2026-11-01 "적군 공방업 1 너프, 첫번째는 방어력").

0.6.14(레이너 업그레이드 +1)는 지시를 잘못 읽은 것이라 철회한다 — 0.6.13 ZIP에서 다시 만든다.
적(자치령)에게 모드가 준 단계만 뺀다. 원본 미션이 난이도별로 주는 업그레이드는 그대로 둔다.
- 1번(TRaynor01): 방어만 — 7-1 최소 보병 방어 1단계와 아주 어려움 +1(보병 방어)을 뺀다. 공격은 그대로.
- 2번(TRaynor02): 공격·방어 — 7-1 최소 보병 공격·방어 1단계와 아주 어려움 +1(보병 공격·방어)을 뺀다.
결과: 쉬움·보통은 1단계 낮아진다. 어려움 방어처럼 원본이 이미 주는 단계는 그대로다.
아주 어려움은 원본 단계(+1 없음)가 된다. 피해 %는 0.6.13 그대로다.

Usage: python3 tools/build_v0615.py <0.6.13 zip> <new output zip>
"""
import argparse, copy, re, tempfile, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.13', b'version=0.6.15'
VH = '    gf_rmVHAdd(p,"TerranInfantry{}Level");\n'


def block(player, kind):
    return re.compile(r'    if \(TechTreeUpgradeCount\(' + player + r', "TerranInfantry' + kind +
                      r'Level1", c_techCountCompleteOnly\) < 1\) \{\n[^\n]*\n    \}\n')


def edit(m, t):
    if m == 'TRaynor01':
        t, n = block('gv_p2_DOMINION_RED', 'Armors').subn('', t); assert n == 1
        assert t.count(VH.format('Armors')) == 1; t = t.replace(VH.format('Armors'), '')
    else:
        call = '    gf_rm_EnemyMinUpgrades();\n'
        assert t.count(call) == 1
        t = t.replace(call, '    // 0.6.15: no 7-1 minimum upgrades in this mission (user 2026-11-01).\n')
        for k in ('Weapons', 'Armors'):
            assert t.count(VH.format(k)) == 1; t = t.replace(VH.format(k), '')
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        changed = {'metadata.txt'}
        for m in ('TRaynor01', 'TRaynor02'):
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
