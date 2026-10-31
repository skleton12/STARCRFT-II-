#!/usr/bin/env python3
"""0.6.7 -> 0.6.8: 프로메테우스 중대 고용 가격 (사용자 2026-10-31 "가격 151가스인데 기분탓임?").

원인: 고용(SummonMercenaries)은 칸에 적힌 비용(원작 악마의 개 칸: 광물 100·가스 75)에 유닛 비용 × 기수를 더해 받는다.
0.6.4가 RM6_Prometheus 유닛 비용을 임의로 50/38로 적어 2기 = 100/76이 더해져 광물 200·가스 151이 됐다.
이지스가 원작 망치 경호대 유닛 비용(125/25)을 따른 것처럼, 원작 악마의 개 유닛 비용(광물 75·가스 0)으로 맞춘다.
→ 고용 가격 = 원작 악마의 개 고용과 같은 광물 250·가스 75. 4·5·6번.

Usage: python3 tools/build_v068.py <0.6.7 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_v062 import find, xml_edit, GD

OLD, NEW = b'version=0.6.7', b'version=0.6.8'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')


def edit(root):
    u = find(root, 'CUnit', 'RM6_Prometheus')
    cost = {c.get('index'): c for c in u.findall('CostResource')}
    assert cost['Minerals'].get('value') == '50' and cost['Vespene'].get('value') == '38'
    cost['Minerals'].set('value', '75')
    u.remove(cost['Vespene'])


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            xml_edit(root / f'{m}.SC2Map' / GD / 'unitdata.xml', edit)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n != 'metadata.txt' and not any(n == f'{m}.SC2Map/{GD}unitdata.xml' for m in MAPS):
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
