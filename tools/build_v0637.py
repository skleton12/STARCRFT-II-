#!/usr/bin/env python3
"""0.6.36 -> 0.6.37: full release ZIP only, no game changes (user 2026-11-21: "not the overwrite version").

0.6.36 was handed out as a partial ZIP to be dropped into the existing ZIP in Windows Explorer; Explorer then stalled
and desktop files could not be dragged. 0.6.37 is a complete ZIP to unpack fresh. Content is byte-identical to 0.6.36
except metadata.txt. Every entry gets normal file permissions (0644; 681 entries had 0600) and a plain stored name.

Usage: python3 tools/build_v0637.py <0.6.36 zip> <new output zip>
"""
import argparse, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.36', b'version=0.6.37'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names = prev.namelist()
        assert len(names) == len({n.lower() for n in names}) and not any(n.endswith('/') for n in names)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    data = prev.read(info)
                    if info.filename == 'metadata.txt': data = data.replace(OLD, NEW)
                    zi = zipfile.ZipInfo(info.filename, info.date_time)
                    zi.compress_type = zipfile.ZIP_DEFLATED
                    zi.create_system = 0
                    zi.external_attr = (0o644 << 16) | 0x20  # regular file, archive bit
                    z.writestr(zi, data)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == names
                for n in names:
                    if n != 'metadata.txt': assert z.read(n) == prev.read(n), n
                assert NEW in z.read('metadata.txt').splitlines()
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
