#!/usr/bin/env python3
"""0.6.5 -> 0.6.6: 이지스 근위대 고용 낙하 연출 (사용자 2026-10-31 "이지스는 왜 낙하로 안 내려옴").

원인: 고용소 고용(SummonMercenaries)은 원작 효과 MercGroundDrop으로 유닛에 같은 이름의 행동을 걸고,
원작 용병 액터는 그 행동이 생길 때 낙하 주머니 모델(…DropModel)을 만든다 (예: HammerSecurity → HammerSecurityDropModel).
협동전에서 옮긴 이지스 근위대(MarauderMengsk) 액터에는 이 연결이 없어, 유닛이 주머니 없이 1~3초 뒤 그냥 나타났다.
원작 망치 경호대와 같은 줄을 넣는다: MarauderMengsk → HammerSecurityDropModel (4·5·6번, 자날 캠페인 층의 원작 모델).
코랄의 후예(WarPigDropModel)·프로메테우스 중대(DevilDogDropModel)는 이미 연결돼 있다.

Usage: python3 tools/build_v066.py <0.6.5 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_v062 import find, xml_edit, GD

OLD, NEW = b'version=0.6.5', b'version=0.6.6'
DROPS = {'MarauderMengsk': 'HammerSecurityDropModel'}
MAPS = {m: list(DROPS) for m in ('TTychus01', 'TTosh01', 'THanson01')}
TERMS = 'Behavior.MercGroundDrop.Create'


def edit_map(d, actors):
    def go(root):
        for a in actors:
            act = find(root, 'CActorUnit', a)
            assert not [o for o in act.findall('On') if o.get('Terms') == TERMS], a
            act.insert(0, E.fromstring(f'<On Terms="{TERMS}" Send="Create {DROPS[a]}" />'))
    xml_edit(d / GD / 'actordata.xml', go)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m, actors in MAPS.items():
            edit_map(root / f'{m}.SC2Map', actors)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n not in ('metadata.txt',) and not any(n == f'{m}.SC2Map/{GD}actordata.xml' for m in MAPS):
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
