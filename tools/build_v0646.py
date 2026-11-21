#!/usr/bin/env python3
"""0.6.45 -> 0.6.46: mission 2 mercenary hire cooldown 300 -> 240 s (user 2026-11-21 "2번맵 용병 소환시간 살짝 줄여줘, 300 너무 길지 않음?").

TRaynor02 only. SummonMercenaries Train1 (Coral's Heirs) keeps the Liberty campaign charges/link and gets cooldown
TimeStart/TimeUse 240 (was 300 from the campaign data; trial value).

Usage: python3 tools/build_v0646.py <0.6.45 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.45', b'version=0.6.46'
P = 'TRaynor02.SC2Map/base.sc2data/gamedata/abildata.xml'
COOLDOWN = 240
A = b'<CAbilTrain id="SummonMercenaries"><InfoArray index="Train1"><Unit index="0" value="RMK_MarineMengsk" />'
B = (b'<CAbilTrain id="SummonMercenaries"><InfoArray index="Train1"><Cooldown><TimeStart value="%d" /><TimeUse value="%d" /></Cooldown>'
     b'<Unit index="0" value="RMK_MarineMengsk" />' % (COOLDOWN, COOLDOWN))


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        assert files[P].count(A) == 1
        files[P] = files[P].replace(A, B)
        import xml.etree.ElementTree as E
        E.fromstring(files[P])
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in ('metadata.txt', P): assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
