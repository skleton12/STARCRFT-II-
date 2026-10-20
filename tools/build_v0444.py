#!/usr/bin/env python3
"""Build CCM 0.4.44 from 0.4.43: 조건 없는 무기고·협동전 연구 버튼이 안 보이던 것 (4번).

사용자 스크린샷 (2026-10-20): 병영 기술실 2페이지에 레이저 조준만 보이고 전투 안정제(협동전)가 없다.
보이는 레이저 조준은 Show 요구조건이 곧바로 '연구 안 함(Not)' 노드다. 0.4.40·0.4.41에서 만든 조건 없는 항목은
피연산자 하나짜리 And 노드를 거친다 → 그 차이만 남는다. Show 를 레이저 조준과 같은 꼴(곧바로 NotQueued)로 바꾼다.
게이트가 있는 항목(화염방사병 해금 등, 피연산자 2개)은 그대로.

Usage: python3 tools/build_v0444.py <0.4.43 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.43', b'version=0.4.44'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'


def single_and_ids(nodes):
    out = []
    for m in re.finditer(r'<CRequirementAnd id="((?:RMA|RMC)_\w+)Show">(.*?)</CRequirementAnd>', nodes, re.S):
        if m.group(2).count('<OperandArray') == 1: out.append(m.group(1))
    return out


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        nodes = files[GD + 'requirementnodedata.xml'].decode('utf-8')
        ids = single_and_ids(nodes)
        assert ids, 'nothing to fix'
        req = files[GD + 'requirementdata.xml'].decode('utf-8')
        for b in ids:
            a = f'<NodeArray index="Show" Link="{b}Show" />'
            assert req.count(a) == 1, a
            req = req.replace(a, f'<NodeArray index="Show" Link="{b}NotQueued" />')
            nodes, n = re.subn(r'<CRequirementAnd id="' + b + r'Show">.*?</CRequirementAnd>', '', nodes, flags=re.S)
            assert n == 1
        files[GD + 'requirementdata.xml'] = req.encode('utf-8')
        files[GD + 'requirementnodedata.xml'] = nodes.encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        print('show = NotQueued:', ids)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
