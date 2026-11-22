#!/usr/bin/env python3
"""0.6.77 -> 0.6.78 (user 2026-11-22 "울트라 나오긴 하는데 업글 적용이 안 되네 차량 쪽도 바이오닉 쪽도").

Allies get Raynor's infantry levels as Protoss ground/air weapons/armor/shields and Primal attack/carapace levels
(CLAUDE.md 3장). The map copies of those upgrades were short versions ported early (Primal: zergling, roach,
hydralisk, Ravasaur only), so Primal Ultralisks/Tyrannozor/Igniters/Swarm Hosts/Mutalisks and the 0.6.77 Fenix
champions got nothing. Maps 3-7: every EffectArray / AffectedUnitArray line of the co-op (starcoop) version of these
30 upgrades (levels 1-3) is added to the map version when it is missing there (same Reference + Operation) and its
unit/weapon/effect/behavior is a ported one (defined in the map, not in the base data - so standard units, which
enemies use too, are not touched). Nothing already there changes, so nothing counts twice.
Game not run.

Usage: python3 tools/build_v0678.py <0.6.77 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import port_units as P

OLD, NEW = b'version=0.6.77', b'version=0.6.78'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02']
LINES = ['ProtossGroundWeapons', 'ProtossGroundArmors', 'ProtossShields', 'ProtossAirWeapons', 'ProtossAirArmors',
         'DehakaPrimalWeapons', 'DehakaPrimalArmor']
UPS = [f'{l}Level{n}' for l in LINES for n in (1, 2, 3)]
SKIP = {'FenixWarbringerColossusThermalLancesFriendlyDamage',  # inherits Amount from its parent: would count twice
        'FenixAltarOfPsiStorms', 'FenixAltarOfPsiStormsBroken'}  # only a button of that name is in the maps (Codex)
SRC = (HERE.parent / 'source/starcoop/starcoop.sc2mod/base.sc2data/gamedata/upgradedata.xml').read_text('utf-8')


def base_ids():
    P.BASE_LAYERS.append(P.gd('liberty.sc2mod'))
    return {i for p in P.BASE_LAYERS for (_, i) in P.load_layer(p)}


def ref_id(line):
    m = re.search(r'Reference="\w+,(\w+)', line) or re.search(r'<AffectedUnitArray value="(\w+)"', line)
    return m.group(1) if m else None


def key(line):
    r = re.search(r'Reference="([^"]+)"', line); o = re.search(r'Operation="(\w+)"', line)
    a = re.search(r'<AffectedUnitArray value="(\w+)"', line)
    return ('A', a.group(1)) if a else (r.group(1) if r else line, o.group(1) if o else 'Add')


def patch(up_text, have, base):
    added = 0
    for u in UPS:
        sm = re.search(r'<CUpgrade id="%s"[^>]*>(.*?)</CUpgrade>' % u, SRC, re.S)
        if not sm: continue
        lines = [l.strip() for l in sm.group(1).splitlines() if l.strip().startswith(('<EffectArray', '<AffectedUnitArray'))
                 and l.strip().endswith('/>')]
        mm = re.search(r'(<CUpgrade id="%s"[^>]*>)(.*?)(\n\s*</CUpgrade>)' % u, up_text, re.S)
        if not mm: continue
        cur = {key(l.strip()) for l in mm.group(2).splitlines() if l.strip()}
        new = []
        for l in lines:
            i = ref_id(l)
            # only ported units/weapons (defined in the map, not in base data): base units already get the base upgrade
            if not i or i in SKIP or i not in have or i in base or key(l) in cur: continue
            cur.add(key(l)); new.append(l)
        if new:
            body = mm.group(2) + ''.join('\n        ' + l for l in new)
            up_text = up_text[:mm.start()] + mm.group(1) + body + mm.group(3) + up_text[mm.end():]
            added += len(new)
    return up_text, added


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    base = base_ids()
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            gd = f'{m}.SC2Map/base.sc2data/gamedata/'
            have = set()
            for k in files:
                if k.startswith(gd) and k.endswith('.xml'):
                    have |= set(re.findall(r' id="(\w+)"', files[k].decode('utf-8', 'ignore')))
            k = gd + 'upgradedata.xml'
            raw = files[k].decode('utf-8'); crlf = '\r\n' in raw
            t, n = patch(raw.replace('\r\n', '\n'), have, base)
            E.fromstring(t)
            files[k] = (t.replace('\n', '\r\n') if crlf else t).encode('utf-8'); changed.add(k)
            print(m, 'lines added', n)
            assert n > 0
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist():
                z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
