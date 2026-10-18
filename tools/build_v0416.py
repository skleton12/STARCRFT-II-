#!/usr/bin/env python3
"""Build CCM 0.4.16 from 0.4.15: 불곰 연구 중 충격탄 하나만 보임 (사용자 보고 2026-10-18: 파편탄·자기가속 없음).

보인 충격탄은 자날 원래 연구(BarracksTechLabResearch Research3)로 본다 — 0.4.13 업그레이드 허용으로 같이 열렸다.
  - 원래 충격탄 연구를 숨긴다 (Research1·2 원래 자극제·방패처럼 Suppressed).
  - 모드 불곰 연구 네 개의 스크립트 여닫기(TechTreeAbilityAllow)를 지우고, 3번 자극제 줄처럼 데이터 조건으로만 보이게 한다:
    망치 경호대를 한 기 이상 가지고 있을 때 (RM4_HaveHammer). 비선형 규칙(불곰이 없으면 안 보임)은 이 조건으로 지킨다.

Usage: python3 tools/build_v0416.py <0.4.15 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.15', b'version=0.4.16'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
FACES = ('RM4_Concussive', 'RM4_Suppression', 'RM4_Magrail', 'RM4_Shrapnel')


def abil(d):
    old = b'<CAbilResearch id="BarracksTechLabResearch">'
    assert d.count(old) == 1
    return d.replace(old, old + b'<InfoArray index="Research3"><Button State="Suppressed" /></InfoArray>')


def nodes(d):
    n = 0
    for f in FACES:
        a = f'<CRequirementAnd id="{f}Show">'.encode()
        assert d.count(a) == 1
        i = d.index(a); j = d.index(b'</CRequirementAnd>', i)
        body = d[i:j]
        k = len(re.findall(rb'<OperandArray', body))
        d = d[:j] + f'<OperandArray index="{k}" value="RM4_HaveHammer" />'.encode() + d[j:]; n += 1
    end = d.rindex(b'</Catalog>')
    return d[:end] + b'<CRequirementCountUnit id="RM4_HaveHammer"><Count Link="HammerSecurity" State="CompleteOnly" /></CRequirementCountUnit>' + d[end:]


GATE = re.compile(r'\n    // Hammer Security research needs the original Marauder unlock \(nonlinear rule\)\.\n(?:    TechTreeAbilityAllow\(1,AbilityCommand\("RM3_TechResearch",[5-8]\),[^\n]*\n){4}')


def patch(t):
    t, n = GATE.subn('\n', t)
    assert n == 1, n
    return t


def script(d):
    crlf = b'\r\n' in d
    t = patch(d.decode('utf-8').replace('\r\n', '\n'))
    return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    fix = {GD + 'abildata.xml': abil, GD + 'requirementnodedata.xml': nodes, M4 + 'mapscript.galaxy': script,
           'metadata.txt': lambda d: d.replace(OLD, NEW)}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), fix[info.filename](d) if info.filename in fix else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in fix: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    sup = HERE / 'data/mission04_support.galaxy'
    t = sup.read_text()
    if GATE.search(t): sup.write_text(patch(t))
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
