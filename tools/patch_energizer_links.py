#!/usr/bin/env python3
"""0.2.23 -> 0.2.24: remove an unrelated co-op actor validator event.

Repairs a confirmed unresolved reference; does not certify the reported crash.
"""
import argparse
import copy
from pathlib import Path
import xml.etree.ElementTree as ET
import zipfile
from patch_support_roster import update_entry

ACTORS = 'TRaynor02.SC2Map/base.sc2data/gamedata/actordata.xml'


def fix_impact(el):
    events = [n for n in el.findall('On')
              if n.get('Terms') == 'ActorCreation; ValidateUnit IsAssaultGalleon']
    if len(events) != 1:
        raise ValueError('Expected one unrelated assault galleon scale event')
    el.remove(events[0])


def build(source, output):
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Use a new output path')
    with zipfile.ZipFile(source) as src:
        if src.testzip() or len(src.namelist()) != len(set(src.namelist())):
            raise ValueError('Input integrity failed')
        meta = src.read('metadata.txt')
        if meta.splitlines().count(b'version=0.2.23') != 1:
            raise ValueError('Expected version 0.2.23')
        replacements = {
            'metadata.txt': meta.replace(b'version=0.2.23', b'version=0.2.24', 1),
            ACTORS: update_entry(src.read(ACTORS), 'RM21_SentryChronoBeamImpact', fix_impact),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        try:
            with zipfile.ZipFile(output, 'x') as out:
                for info in src.infolist():
                    out.writestr(copy.copy(info), replacements.get(info.filename, src.read(info.filename)))
            with zipfile.ZipFile(output) as out:
                if out.testzip():
                    raise ValueError('Output CRC failed')
                for name in out.namelist():
                    if name.endswith('.xml'):
                        ET.fromstring(out.read(name))
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    print(output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    build(args.source, args.output)
