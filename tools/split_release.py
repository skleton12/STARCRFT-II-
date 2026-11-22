#!/usr/bin/env python3
"""Store the release ZIP in GitHub as parts (user 2026-11-22: GitHub refuses files over 100 MiB).

The full ZIP stays local (releases/RaynorMercs_WoL_CCM.zip, git-ignored) and is what the user gets.
GitHub keeps releases/parts/RaynorMercs_WoL_CCM.zip.001, .002, ... (each at most 45 MiB) and a SHA-256 list.

  python3 tools/split_release.py            # split the local full ZIP into releases/parts/
  python3 tools/split_release.py --join     # rebuild the full ZIP from the parts and verify it
"""
import argparse, hashlib, shutil, tempfile, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FULL = ROOT / 'releases' / 'RaynorMercs_WoL_CCM.zip'
PARTS = ROOT / 'releases' / 'parts'
NAME = FULL.name
CHUNK = 45 * 1024 * 1024
SUMS = PARTS / 'SHA256SUMS.txt'


def sha(b): return hashlib.sha256(b).hexdigest()


def check(ok, msg):
    if not ok: raise SystemExit('error: ' + msg)


def split():
    check(FULL.is_file() and zipfile.is_zipfile(FULL), f'{FULL} is not a ZIP')
    data = FULL.read_bytes()
    check(0 < len(data) <= CHUNK * 999, 'bad size')
    PARTS.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=PARTS.parent) as tmp:  # stage, then swap: never leave a half-written set
        tmp = Path(tmp); lines = []
        for i in range(0, len(data), CHUNK):
            n = f'{NAME}.{i // CHUNK + 1:03d}'
            (tmp / n).write_bytes(data[i:i + CHUNK]); lines.append(f'{sha(data[i:i + CHUNK])}  {n}')
        lines.append(f'{sha(data)}  {NAME}')
        (tmp / SUMS.name).write_text('\n'.join(lines) + '\n')
        for old in list(PARTS.glob(NAME + '.*')) + [SUMS]: old.unlink(missing_ok=True)
        for f in tmp.iterdir(): shutil.move(str(f), PARTS / f.name)
    print(f'{len(lines) - 1} parts, {len(data)} bytes')


def join():
    sums = dict(reversed(l.split('  ')) for l in SUMS.read_text().split('\n') if l)
    parts = sorted(PARTS.glob(NAME + '.[0-9][0-9][0-9]'))
    want = sorted(k for k in sums if k != NAME)
    check(NAME in sums and want and [p.name for p in parts] == want, 'parts do not match SHA256SUMS.txt')
    data = b''
    for p in parts:
        b = p.read_bytes(); check(sha(b) == sums[p.name], 'bad hash: ' + p.name); data += b
    check(sha(data) == sums[NAME], 'joined ZIP hash mismatch')
    tmp = FULL.with_suffix('.zip.tmp'); tmp.write_bytes(data); tmp.replace(FULL); print(FULL, len(data))


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__); a.add_argument('--join', action='store_true')
    join() if a.parse_args().join else split()
