#!/usr/bin/env python3
"""0.5.19 -> 0.5.20: 레드스톤 저그 기지 지원을 번갈아 투하 (사용자 2026-10-28 "초반에 너무 많음" → "번갈아 투하").

0.5.19는 120초마다 살아 있는 저그 기지 6곳이 한꺼번에 투하했다 (어려움 4분: 저글링 24·히드라 6).
이제 한 번에 살아 있는 기지 가운데 2곳만 (살아 있는 기지가 3곳 이하면 1곳) 돌아가며 보낸다 (시험값).
부대 구성·4분 시작·120초 간격·목적지·기지 파괴 시 중지는 그대로.

Usage: python3 tools/build_v0520.py <0.5.19 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.19', b'version=0.5.20'
S = 'TTosh01.SC2Map/mapscript.galaxy'

SCRIPT = [
    ('int gv_m5_zWave;\n', 'int gv_m5_zWave;\nint gv_m5_zTurn;\n'),
    ('    int b;\n    int sent;\n    unit hall;\n',
     '    int b;\n    int k;\n    int live;\n    int want;\n    int sent;\n    unit hall;\n'),
    ('    sent=0;\n    for (b=0;b<gv_m5_zBaseN;b+=1) {\n        hall=gv_m5_zBase[b];\n        if (!UnitIsAlive(hall)) { continue; }\n',
     '    sent=0;\n'
     '    // 0.5.20 (user 2026-10-28): bases take turns, 2 per wave (1 when 3 or fewer are left), trial.\n'
     '    live=0;\n'
     '    for (b=0;b<gv_m5_zBaseN;b+=1) { if (UnitIsAlive(gv_m5_zBase[b])) { live+=1; } }\n'
     '    want=2;\n'
     '    if (live<=3) { want=1; }\n'
     '    for (k=0;k<gv_m5_zBaseN && sent<want;k+=1) {\n'
     '        b=ModI(gv_m5_zTurn+k,gv_m5_zBaseN);\n'
     '        hall=gv_m5_zBase[b];\n'
     '        if (!UnitIsAlive(hall)) { continue; }\n'),
    ('    if (sent==0 || gv_m5_zN==0) { return; }\n',
     '    gv_m5_zTurn=ModI(b+1,gv_m5_zBaseN);\n    if (sent==0 || gv_m5_zN==0) { return; }\n'),
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[S].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = sub(t.replace('\r\n', '\n'), SCRIPT)
        files[S] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (S, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
