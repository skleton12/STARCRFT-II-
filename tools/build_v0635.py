#!/usr/bin/env python3
"""0.6.34 -> 0.6.35: 피닉스 초상화 얼굴, 적 공세 물량이 시간에 따라 커지게 (사용자 2026-11-15).

1) 피닉스(3번) 초상화 (사용자 "초상화도 몸만 보이는듯"):
   액터의 PortraitActor FenixEx2Portrait는 CompositePortrait라 'FenixEx2PortraitAddition' 액터(얼굴 모델)를 만들어야
   얼굴이 나온다. 맵에 Addition 액터·모델과 초상화 조명(CLight FenixEx2Portrait)이 없어 빈 초상화(몸 모델)만 보였다.
   공허 캠페인 원본 정의 그대로 옮긴다 (모델 SMX2_Fenix.m3, 표정 SMX2_Fenix.fxa).
   대사는 데이터상 연결이 맞으므로(협동전 FenixDragoon_*, 부모 ProtossAck_Void는 자날 층에 있음) 바꾸지 않는다.
   소리 파일이 자날 맵에서 안 읽히는지는 게임 확인 필요.
2) 공세 물량 시간 비례 (사용자 "물량은 초반에 적고 후반에 많아야지 그냥 무턱대고 오는거 같음"):
   2~6번 맵 gf_rmWaveN 배율에 임무 시간 배수를 곱한다: 0분 0.7 -> 24분 1.4 (직선, 그 뒤 1.4 유지, 시험값).
   공세 수를 정할 때(공세 트리거가 gf_rmWave4를 부를 때)의 임무 시간을 쓴다. 난이도 칸별 배율은 그대로.
게임 미실행.

Usage: python3 tools/build_v0635.py <0.6.34 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
from build_v062 import add_xml, GD

OLD, NEW = b'version=0.6.34', b'version=0.6.35'
WAVE_MAPS = ('TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
RAMP_START, RAMP_END, RAMP_MIN = '0.7', '1.4', '24.0'
VOID = ROOT / 'source/void.sc2campaign' / GD

WAVE_OLD = '''int gf_rmWaveN (int n, fixed mult) {
    if (n<=0) { return 0; }
    return CeilingI(IntToFixed(n)*mult);
}
'''
WAVE_NEW = f'''// 0.6.35 (user 2026-11-15): few early, many late - wave size also scales with mission time (trial).
const fixed gv_rmRampStart = {RAMP_START};
const fixed gv_rmRampEnd = {RAMP_END};
const fixed gv_rmRampMinutes = {RAMP_MIN};
fixed gf_rmWaveRamp () {{
    fixed m = GameGetMissionTime() / 60.0;
    if (m > gv_rmRampMinutes) {{ m = gv_rmRampMinutes; }}
    return gv_rmRampStart + (gv_rmRampEnd - gv_rmRampStart) * m / gv_rmRampMinutes;
}}
int gf_rmWaveN (int n, fixed mult) {{
    if (n<=0) {{ return 0; }}
    return CeilingI(IntToFixed(n)*mult*gf_rmWaveRamp());
}}
'''


def rec(path, tag, rid):
    t = path.read_text('utf-8')
    s = t.index(f'<{tag} id="{rid}"')
    gt = t.index('>', s)
    if t[gt - 1] == '/':
        return t[s:gt + 1]
    e = t.index(f'</{tag}>', s) + len(tag) + 3
    return t[s:e]


def portrait(d):
    g = d / GD
    add_xml(g / 'actordata.xml', rec(VOID / 'actordata.xml', 'CActorModel', 'FenixEx2PortraitAddition'))
    add_xml(g / 'modeldata.xml', rec(VOID / 'modeldata.xml', 'CModel', 'FenixEx2PortraitAddition'))
    light = rec(VOID / 'lightdata.xml', 'CLight', 'FenixEx2Portrait')
    lp = g / 'lightdata.xml'
    assert not lp.exists()
    lp.write_text('<?xml version="1.0" encoding="utf-8"?>\n<Catalog>\n    ' + light + '\n</Catalog>\n', 'utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        portrait(root / 'TRaynor03.SC2Map')
        for m in WAVE_MAPS:
            p = root / f'{m}.SC2Map/mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            assert t.count(WAVE_OLD) == 1, m
            p.write_bytes(t.replace(WAVE_OLD, WAVE_NEW).replace('\n', nl).encode('utf-8'))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        new = 'TRaynor03.SC2Map/base.sc2data/gamedata/lightdata.xml'
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                out.write(root / new, new)
            changed = tuple(f'{m}.SC2Map/' for m in WAVE_MAPS)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names + [new]
                for n in names:
                    if not n.startswith(changed) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
