#!/usr/bin/env python3
"""Build CCM 0.3.18 from 0.3.17: 3번 맵에서 빠진 에셋 경로 복구 (원시저그 건물 '오류 구').

사용자 보고 (2026-10-17): "원시저그 건물 생성할 때 오류 구가 생김".
원인: 3번 맵 데이터의 일부 항목에서 모델·그림·소리 파일 경로 줄이 빠져 있었다. 모델 파일이 없으면 게임이
      빨간 오류 구를 그린다. 원시 건물 고치(DehakaHatcheryBuild/DehakaBarracksBuild → 부모 PrimalZergBuildingBuild)가 대표.
  - 0.3.4 build_v034.clean_dangling이 파일 경로 안의 이름(예: Primal_Zerg_Spit)을 끊긴 ID로 오인해 경로 줄을 지움.
  - 고치 부모 PrimalZergBuildingBuild·생산 침 Primal_Zerg_Spit 등은 그 전 이식부터 경로가 비어 있었다.
수정: 3번 맵의 이식 항목(원본 협동전·군단·공허 층에 있고 기본 층에 없는 ID)마다 원본 정의와 비교해,
      파일 경로 값(\\ 또는 .m3/.m3a/.dds/.ogg/.wav/.tga)을 가진 줄이 맵에 없으면 원본 줄을 되붙인다.
      ID 연결(효과·검증기·소리 링크 등)은 건드리지 않는다 (0.2.23~0.2.24에 일부러 지운 링크 보존).
2번 맵도 같은 검사에서 드롭포드 착지 소리 파일 4줄이 빠져 있어 함께 복구 (1번은 0개).

Usage: python3 tools/build_v0318.py <0.3.17 zip> <new output zip>
"""
import argparse
import copy
import re
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import port_units as P  # noqa: E402

OLD, NEW = b'version=0.3.17', b'version=0.3.18'
GDS = ('TRaynor02.SC2Map/base.sc2data/gamedata/', 'TRaynor03.SC2Map/base.sc2data/gamedata/')
PATH = re.compile(r'\\|/|\.(m3|m3a|dds|ogg|wav|tga)$', re.I)


def leaf_keys(el):
    """Leaf children keyed with their parent tag (an Image under GroupIcon is not the one under Wireframe)."""
    out = set()
    for pa in el.iter():
        for x in pa:
            if not len(x): out.add(key(x, pa if pa is not el else None))
    return out


def key(x, pa):
    return (pa.tag if pa is not None else '') + '/' + x.tag + repr(sorted(x.attrib.items()))


def source_defs():
    P.BASE_LAYERS.append(P.gd('liberty.sc2mod'))
    base = set()
    for p in P.BASE_LAYERS:
        base |= {k for k in P.load_layer(p)}
    out = {}
    for _, p in P.COPY_LAYERS:
        for k, els in P.load_layer(p).items():
            if k in base: continue
            out.setdefault(k, []).extend(els)
    return out


def repair(fn, data, src, report):
    root = E.fromstring(data)
    added = 0
    for el in root:
        k = (fn, el.get('id'))
        if k not in src: continue
        have = leaf_keys(el)
        for s in src[k]:
            if s.tag != el.tag: continue  # same ID can exist as different actor/model types
            parent = {c: pa for pa in s.iter() for c in pa}
            for x in s.iter():
                if x is s or len(x) or not any(PATH.search(v or '') for v in x.attrib.values()): continue
                pa = parent[x]
                kx = key(x, pa if pa is not s else None)
                if kx in have: continue
                # keep the original nesting (e.g. <Wireframe><Image/></Wireframe>), one level deep at most
                if pa is s: dest = el
                else:
                    assert parent[pa] is s, (k, x.tag)
                    dest = next((c for c in el if c.tag == pa.tag and c.attrib == pa.attrib), None)
                    if dest is None: dest = E.SubElement(el, pa.tag, pa.attrib)
                dest.append(copy.deepcopy(x)); have.add(kx); added += 1
                report.append(f'{fn}:{el.get("id")} {x.tag} {list(x.attrib.values())[0]}')
    if not added: return data
    out = E.tostring(root, encoding='utf-8', xml_declaration=True)
    E.fromstring(out)
    return out


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    src = source_defs()
    report = []
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename == 'metadata.txt': data = data.replace(OLD, NEW)
                    elif info.filename.startswith(GDS) and info.filename.endswith('.xml'):
                        data = repair(info.filename.rsplit('/', 1)[1], data, src, report)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(len(report), 'paths restored')
    for r in report: print('  ', r)
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path)
    a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
