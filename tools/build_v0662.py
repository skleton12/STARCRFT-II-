#!/usr/bin/env python3
"""0.6.61 -> 0.6.62 (user 2026-11-21, 4번 어부지리 "근처로 하라니까 왜 멀리 보내누").

Why 0.6.61 still put the ally research buildings far away (mission 4): Raynor's starting War Pigs, medic and SCVs
stand right beside the Command Center, and UnitTypePlacementFromPoint treats them as blockers. Also each building
searched its whole preferred side (out to 16) before trying the other side, and geysers had the same 5-cell
keep-out as minerals, which closed the spots beside the CC.
Fix (maps 4-6):
- Placement: full test first; if it fails, UnitTypePlacementTestsFromPoint with cliff test + ignore blockers (units step aside),
  then an explicit no-overlap check against the CC box and nearby structures (Codex review), so the
  starting units no longer push the buildings out; the building is created exactly there (ignore placement).
- Each distance ring (5..16) tries both sides before stepping out; angles 5-90 degrees off the away-from-minerals line.
- Smaller buildings (user "크기를 줄여"): Purifier Conclave 4x4 -> 3x3 (model 0.75), Dehaka's Den 3x3 -> 2x2
  (model 0.67). Rings start at 4 (CC half 2.5 + 3x3 half 1.5).
- Keep-out: minerals 5 (unchanged), geysers 4. Away-side re-check (>= 2) unchanged.
Game not run.

Usage: python3 tools/build_v0662.py <0.6.61 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.61', b'version=0.6.62'
MAPS = ['TTychus01', 'TTosh01', 'THanson01']
SUBS = [
    (re.compile(rb'point gf_rm7Spot \(string kind, point c, fixed ang, fixed side\) \{.*?\r?\n\}\r?\n', re.S),
     b'''bool gf_rm7Clear (point q, point c, fixed h, bool scan) {
    // No overlap with the Command Center (5x5) or any other structure's centre near the footprint.
    unitgroup g;
    unit u;
    int i;
    if (AbsF(PointGetX(q) - PointGetX(c)) < 2.5 + h && AbsF(PointGetY(q) - PointGetY(c)) < 2.5 + h) { return false; }
    if (!scan) { return true; }
    // Fallback only. Margin h + 2.5 catches any structure up to 5x5 whose footprint would touch ours (the CC is checked above).
    g = UnitGroup(null, c_playerAny, RegionRect(PointGetX(q) - h - 2.5, PointGetY(q) - h - 2.5, PointGetX(q) + h + 2.5, PointGetY(q) + h + 2.5),
        UnitFilter((1 << c_targetFilterStructure), 0, 0, 0), 0);
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {
        u = UnitGroupUnit(g, i);
        if (DistanceBetweenPoints(UnitGetPosition(u), c) > 0.1) { return false; }
    }
    return true;
}
point gf_rm7Spot (string kind, point c, fixed ang, fixed side) {
    // 0.6.62: right next to the Command Center; each ring tries both sides before stepping out.
    // Full placement test first; only if that fails, ignore movable units (starting mercs, SCVs step aside),
    // then re-check overlap with the Command Center and other structures.
    fixed[7] off;
    point p;
    point q;
    fixed d;
    fixed s;
    fixed h = 1.0;
    int k;
    int j;
    int t;
    if (kind == "RM7_Conclave") { h = 1.5; }
    off[0] = 30.0; off[1] = 45.0; off[2] = 15.0; off[3] = 60.0; off[4] = 5.0; off[5] = 75.0; off[6] = 90.0;
    for (d = 4.0; d <= 16.0; d += 1.0) {
        // Pass 0: full placement test on every sample of this ring. Pass 1: ignore movable units.
        for (t = 0; t < 2; t += 1) {
            for (k = 0; k < 7; k += 1) {
                for (j = 0; j < 2; j += 1) {
                    s = side;
                    if (j == 1) { s = -side; }
                    p = PointWithOffsetPolar(c, d, ang + s * off[k]);
                    if (t == 0) { q = UnitTypePlacementFromPoint(kind, 1, p, 1.0); }
                    else { q = UnitTypePlacementTestsFromPoint(kind, 1, p, 1.0, c_placementTestCliffMask | c_placementTestIgnoreBlockersMask); }
                    if (q != null && !gf_rm7NearMineral(q) && gf_rm7Clear(q, c, h, t == 1)
                        && (PointGetX(q) - PointGetX(c)) * Cos(ang) + (PointGetY(q) - PointGetY(c)) * Sin(ang) >= 2.0) {
                        return q;
                    }
                }
            }
        }
    }
    return null;
}
'''),
    (re.compile(rb'    s = gf_rm7Spot\(kind, c, ang, side\);\r?\n    if \(s == null\) \{ s = gf_rm7Spot\(kind, c, ang, -side\); \}\r?\n'),
     b'    s = gf_rm7Spot(kind, c, ang, side);\n'),
    (re.compile(rb'    UnitCreate\(1, kind, 0, 1, s, 270\.0\);'),
     b'    UnitCreate(1, kind, c_unitCreateIgnorePlacement, 1, s, 270.0);'),
    (re.compile(rb'        if \(StringFind\(UnitGetType\(UnitGroupUnit\(g, i\)\), "Geyser", c_stringNoCase\) != c_stringNotFound\) \{ return true; \}'),
     b'        if (StringFind(UnitGetType(UnitGroupUnit(g, i)), "Geyser", c_stringNoCase) != c_stringNotFound\n'
     b'            && DistanceBetweenPoints(q, UnitGetPosition(UnitGroupUnit(g, i))) < 4.0) { return true; }'),
]


DATA = [
    ('unitdata.xml', b'<Footprint value="Footprint4x4Contour" /><PlacementFootprint value="Footprint4x4" /><Radius value="1.75" /><SeparationRadius value="1.75" />',
     b'<Footprint value="Footprint3x3Contour" /><PlacementFootprint value="Footprint3x3" /><Radius value="1.25" /><SeparationRadius value="1.25" />'),
    ('actordata.xml', b'<UnitIcon value="Assets\\Textures\\btn-unit-protoss-fenix-purifier-conclave.dds" /><Aliases value="_UnitHuge" />',
     b'<UnitIcon value="Assets\\Textures\\btn-unit-protoss-fenix-purifier-conclave.dds" /><Aliases value="_UnitLarge" /><On Terms="ActorCreation" Send="SetScale 0.75" />'),
    ('actordata.xml', b'<UnitIcon value="Assets\\Textures\\btn-building-dehaka-dehakanest.dds" /><Aliases value="_UnitMedium" />',
     b'<UnitIcon value="Assets\\Textures\\btn-building-dehaka-dehakanest.dds" /><Aliases value="_UnitMedium" /><On Terms="ActorCreation" Send="SetScale 0.67" />'),
]
DEN_OLD = b'<Footprint value="Footprint3x3Contour" /><PlacementFootprint value="Footprint3x3" /><Radius value="1.25" /><SeparationRadius value="1.25" />'
DEN_NEW = b'<Footprint value="Footprint2x2Contour" /><PlacementFootprint value="Footprint2x2" /><Radius value="0.875" /><SeparationRadius value="0.875" />'


def shrink(u):
    """Den first (its 3x3 text also appears elsewhere), then the Conclave."""
    a = u.index(b'<CUnit id="RM7_DehakaDen">'); e = u.index(b'</CUnit>', a)
    seg = u[a:e]; assert seg.count(DEN_OLD) == 1
    u = u[:a] + seg.replace(DEN_OLD, DEN_NEW) + u[e:]
    a = u.index(b'<CUnit id="RM7_Conclave">'); e = u.index(b'</CUnit>', a)
    seg = u[a:e]; old, new = DATA[0][1], DATA[0][2]; assert seg.count(old) == 1
    return u[:a] + seg.replace(old, new) + u[e:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            k = f'{m}.SC2Map/mapscript.galaxy'
            s = files[k]
            nl = b'\r\n' if b'\r\n' in s else b'\n'
            for pat, rep in SUBS:
                s, n = pat.subn(rep.replace(b'\n', nl), s, count=1)
                assert n == 1, (m, pat.pattern[:40])
            files[k] = s; changed.add(k)
            g = f'{m}.SC2Map/base.sc2data/gamedata/'
            files[g + 'unitdata.xml'] = shrink(files[g + 'unitdata.xml']); changed.add(g + 'unitdata.xml')
            ad = files[g + 'actordata.xml']
            for _, old, new in DATA[1:]:
                assert ad.count(old) == 1, (m, old[:40]); ad = ad.replace(old, new)
            files[g + 'actordata.xml'] = ad; changed.add(g + 'actordata.xml')
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
