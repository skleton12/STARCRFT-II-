#!/usr/bin/env python3
"""Build CCM 0.4.36 from 0.4.35: 기술실 충격탄을 연구해도 감속이 안 걸리던 것 (4번).

원인: 자날 스토리 층(libertystory)이 검증기 PunisherGrenadesResearched를 '히페리온 무기고 충격탄 구매
(JackhammerConcussionGrenadesResearched)'로 바꿔 둔다. 그래서 망치 경호대의 감속(PunisherGrenadesSlow)과
주변 감속(MarauderSlowAOE)은 무기고에서 샀을 때만 켜지고, 기술실 연구 PunisherGrenades는 무시됐다.
억제탄(RM4_SuppressAOE)도 같은 감속 효과를 써서 함께 죽어 있었다.
수정: 맵에서 이 검증기를 '충격탄 업그레이드 완료'로 바꾼다. 무기고 구매는 0.4.13부터 충격탄 업그레이드를
주므로 구매 효과는 그대로 유지된다.

Usage: python3 tools/build_v0436.py <0.4.35 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.35', b'version=0.4.36'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'


def add(xml, guard):
    def fn(d):
        assert guard.encode() not in d, guard
        i = d.rindex(b'</Catalog>')
        return d[:i] + xml.encode('utf-8') + d[i:]
    return fn


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW),
       GD + 'validatordata.xml': add('<CValidatorPlayerRequirement id="PunisherGrenadesResearched"><Value value="RM4_ConcussiveUse" />'
                                     '</CValidatorPlayerRequirement>', 'id="PunisherGrenadesResearched"'),
       GD + 'requirementdata.xml': add('<CRequirement id="RM4_ConcussiveUse"><NodeArray index="Use" Link="RM4_PunisherGrenadesDone" />'
                                       '</CRequirement>', 'id="RM4_ConcussiveUse"')}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert b'id="RM4_PunisherGrenadesDone"' in prev.read(GD + 'requirementnodedata.xml')
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), FIX[info.filename](d) if info.filename in FIX else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
