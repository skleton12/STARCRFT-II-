#!/usr/bin/env python3
"""Build CCM 0.4.7 from 0.4.6: 4번 레이너 본진 두 번째 가스도 풍부한 가스 +20%.

원본은 (81.5,13.5)에 레이너 정제소를 가스 오브젝트 없이 미리 배치했다. 0.4.4 자원 규칙이 이 가스를 놓쳤다.
  - 정제소 배치를 지우고 그 자리에 풍부한 가스(3000 = 기본 2500 +20%)를 놓는다.
  - 맵 초기화 때 그 가스 위에 레이너 정제소를 다시 세운다 (원작처럼 정제소가 있는 채로 시작).

Usage: python3 tools/build_v047.py <0.4.6 zip> <new output zip>
"""
import argparse, copy, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.4.6', b'version=0.4.7'
M4 = 'TTychus01.SC2Map/'
INIT = b'void gf_m4_Init () {'
ADD = (b'''
    // Raynor's starting Refinery stands on the rich geyser that replaced the original's geyser-less Refinery (0.4.7).
    UnitCreate(1,"Refinery",0,1,Point(81.5,13.5),270.0);''')


def objects(data):
    root = E.fromstring(data)
    ref = [e for e in root if e.tag == 'ObjectUnit' and e.get('UnitType') == 'Refinery' and e.get('Player') == '1']
    assert len(ref) == 1 and ref[0].get('Position') == '81.5,13.5,0'
    i = list(root).index(ref[0])
    root.remove(ref[0])
    root.insert(i, E.fromstring('<ObjectUnit Id="40" Position="81.5,13.5,0" Scale="1,1,1" UnitType="RichVespeneGeyser" Resources="3000" />'))
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def script(d):
    assert d.count(INIT) == 1
    j = d.index(b'\n', d.index(b'gv_m4_eggUnit[2]=', d.index(INIT))) 
    return d[:j] + ADD.replace(b'\n', b'\r\n' if b'\r\n' in d else b'\n') + d[j:]


FIX = {M4 + 'objects': objects, M4 + 'mapscript.galaxy': script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), FIX[info.filename](d) if info.filename in FIX else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
