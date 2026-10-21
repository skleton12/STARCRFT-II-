#!/usr/bin/env python3
"""Build CCM 0.4.54 from 0.4.53: 기술실 연구 숨김 원인 수정 — Not 노드 피연산자 번호 (4번).

진단 0.4.48~0.4.53 결론 (사용자 스크린샷 2026-10-21):
  - 시험 업그레이드로 만든 개수·Not[index 0]·And·Or 노드는 모두 정상 (0.4.53).
  - 그런데 And(우리 고급 의무관 Not) 은 거짓 (0.4.52). 우리 RM4_/RMA_/RMC_ Not 노드 21개는
    <OperandArray value=…> 처럼 번호가 없다. Not 은 피연산자 칸이 하나로 정해진 노드라 블리자드 원본 약 800개가
    모두 index="0" 을 쓴다. 번호가 없으면 피연산자가 비어 무효가 되고, 버튼 조건으로 혼자 쓰이면 통과(보임),
    And 안에서는 거짓(숨음)이 된다 → 파편탄·충격완화복·전투 안정제·화염 연구·우리 충격탄이 숨은 원인.
  - 보이던 G 는 원작 충격탄(BarracksTechLabResearch Research3)이다. State=Suppressed 는 '요구조건 못 채우면 숨김'이라
    기술실만 있으면 보인다. 망치 경호대 해금 조건을 건너뛰므로 항상 거짓인 Show 요구조건으로 숨긴다.
수정:
  1. 네 맵의 Not(및 Eq 등 고정 칸 노드) 중 번호 없는 OperandArray 에 index="0" 을 붙인다.
  2. 원작 충격탄 버튼 Requirements = RM4_HideOriginal (Show = RMZ_NeverNode, 항상 거짓).
  3. 0.4.48~0.4.53 진단 스크립트와 시험 데이터(RMT_…)를 모두 뺀다 (mapscript 는 0.4.49 것). 파편탄 아이콘(0.4.51)은 유지.
check_release 에 '고정 칸 노드 번호 필수' 검사를 넣는다.

Usage: python3 tools/build_v0454.py <0.4.53 zip> <0.4.49 zip (mapscript source)> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.53', b'version=0.4.54'
MAPS = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
SCRIPT = M4 + 'mapscript.galaxy'
FIXED = 'Not|Eq|NE|GT|LT|GTE|LTE|Div|Mod|Odd'


def strip_diag(t):
    t, n = re.subn(r'<(C\w+) id="RMT_[^"]*">.*?</\1>', '', t, flags=re.S)
    assert 'RMT_' not in t
    return t


def nodes(d):
    t = strip_diag(d.decode('utf-8'))
    def fix(m):
        return re.sub(r'<OperandArray (?!index=)', '<OperandArray index="0" ', m.group(0))
    t = re.sub(rf'<(CRequirement(?:{FIXED}))\s+id="[^"]+"[^>]*>.*?</\1>', fix, t, flags=re.S)
    return t.encode('utf-8')


def reqs(d):
    t = strip_diag(d.decode('utf-8'))
    assert 'id="RM4_HideOriginal"' not in t
    i = t.rindex('</Catalog>')
    t = t[:i] + '<CRequirement id="RM4_HideOriginal"><NodeArray index="Show" Link="RMZ_NeverNode" /></CRequirement>' + t[i:]
    return t.encode('utf-8')


def upgrades(d):
    return strip_diag(d.decode('utf-8')).encode('utf-8')


def abil(d):
    t = d.decode('utf-8')
    m = re.search(r'<CAbilResearch id="BarracksTechLabResearch">.*?</CAbilResearch>', t, re.S)
    b = m.group(0)
    old = '<InfoArray index="Research3">\n            <Button State="Suppressed" />'
    assert b.count(old) == 1, b
    b = b.replace(old, '<InfoArray index="Research3">\n            <Button State="Suppressed" Requirements="RM4_HideOriginal" />')
    return (t[:m.start()] + b + t[m.end():]).encode('utf-8')


def build(source, script_src, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(script_src) as base:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert b'version=0.4.49' in base.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        files[SCRIPT] = base.read(SCRIPT)
        assert b'gt_m4_Diag_Func' not in files[SCRIPT]
        files[GD + 'requirementdata.xml'] = reqs(files[GD + 'requirementdata.xml'])
        files[GD + 'upgradedata.xml'] = upgrades(files[GD + 'upgradedata.xml'])
        files[GD + 'abildata.xml'] = abil(files[GD + 'abildata.xml'])
        for m in MAPS:
            n = f'{m}.SC2Map/base.sc2data/gamedata/requirementnodedata.xml'
            files[n] = nodes(files[n])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('script_src', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.script_src, a.output)
