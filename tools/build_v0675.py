#!/usr/bin/env python3
"""0.6.74 -> 0.6.75 (user 2026-11-22 "플토 저그 연구 5단계잖음 1단계마다 유닛 2개 추가로", "1단계 연구 적용 안 되는 것 같은데 확인좀").

Ally support tiers (Hyperion lab research bought: Protoss -> Purifier, Zerg -> Primal Zerg, 0-5), maps 3-7:
- Each tier now adds 2 light (low-supply) units instead of 1 heavy one, so more units arrive under the 120 cap
  (zergling tiers: 4). Maps 4-7: Purifier Fenix Adept / Instigator / Adept / Instigator / Adept; Primal Zerg
  zergling / Ravasaur / Roach / Hydralisk / zergling. Map 3 keeps its own light list (Legionnaire, Adept, zergling,
  Ravasaur, Roach, Hydralisk). Free, trial.
- Check result: the tier count (libCamp research state Purchased, Protoss/Zerg category) matches the original lab
  code in all five maps; it was counted once when the support buttons were set up. It is now also recounted every
  time a support group is filled, so the group always uses the current lab state. No code bug found for tier 1.
- Free tier units counted toward the 120 army cap, so a big group could make the whole call fail (and with 2 per
  tier, more often). Now only the paid part must fit; free units fill the room that is left.
Game not run.

Usage: python3 tools/build_v0675.py <0.6.74 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.74', b'version=0.6.75'
P = ['ColossusPurifier', 'TempestPurifier']
TIERS = {
    'TRaynor03': ('m3c', 10, ['ZealotPurifier', 'AdeptFenix', 'ZealotPurifier', 'AdeptFenix', 'ZealotPurifier'],
                  ['DehakaZerglingLevel2', 'DehakaRavasaur', 'DehakaRoachLevel2', 'DehakaHydraliskLevel2', 'DehakaRavasaur']),
}
for m, pre in (('TTychus01', 'm4'), ('TTosh01', 'm5'), ('THanson01', 'm6'), ('TTosh02', 'm7')):
    # user 2026-11-22 "5단계마다 더 많은 유닛 나오지 않음, 적절한 경유닛을 넣어": light (low-supply) units only.
    TIERS[m] = (pre, 8, ['AdeptFenix', 'StalkerPurifier', 'AdeptFenix', 'StalkerPurifier', 'AdeptFenix'],
                ['DehakaZerglingLevel2', 'DehakaRavasaur', 'DehakaRoachLevel2', 'DehakaHydraliskLevel2', 'DehakaZerglingLevel2'])


def patch(s, pre, prot, zerg):
    tl = re.compile(r'^( *)if \(gv_%s_tier\[p\]>=([1-5])\) \{ (?:gf_%s_SupAdd\(p,"\w+"\); ?)+\}\n' % (pre, pre), re.M)
    lines = tl.findall(s)
    assert len(lines) == 10, (pre, len(lines))
    seen = {'p': 0}
    def rep(mt):
        ind, n = mt.group(1), int(mt.group(2))
        zergside = seen['p'] >= 5; seen['p'] += 1
        kind = (zerg if zergside else prot)[n - 1]
        cnt = 4 if kind == 'DehakaZerglingLevel2' else 2
        adds = ' '.join(f'gf_{pre}_SupAdd(p,"{kind}");' for _ in range(cnt))
        return f'{ind}if (gv_{pre}_tier[p]>={n}) {{ {adds} }}\n'
    s = tl.sub(rep, s)
    head = f'    gv_{pre}_supN[p]=0;\n'
    i = s.index(f'void gf_{pre}_SupFill (int p) {{')
    j = s.index(head, i); assert j - i < 200
    s = s[:j] + head + f'    gv_{pre}_tier[p]=gf_{pre}_Tier(p);  // 0.6.75: recount each group\n' + s[j + len(head):]
    assert s.index(f'int gf_{pre}_Tier (int p)') < i  # declared before use
    return s


def cap_free(s, pre):
    # Free tier units counted toward the 120 cap and could make the whole call fail; now only the paid group
    # must fit, and free units fill the room that is left (the rest are dropped for that call).
    fpre = 'm3' if pre == 'm3c' else pre
    kind = f'gv_{pre}_supKind[p][i]'
    old = (f'        food+=gf_{fpre}_UnitFood({kind});\n    }}\n'
           f'    if (gf_{fpre}_Food(p)+food>120.0 || ')
    new = (f'        if (i<gv_{pre}_supPaid[p]) {{ food+=gf_{fpre}_UnitFood({kind}); }}\n    }}\n'
           f'    if (gf_{fpre}_Food(p)+food>120.0 || ')
    assert s.count(old) == 1, pre; s = s.replace(old, new)
    pay = f'    PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);\n    return true;\n}}\n'
    i = s.index(f'bool gf_{pre}_CallPay (int p) {{'); j = s.index(pay, i); assert j - i < 1500
    fill = (f'    PlayerModifyPropertyInt(p,c_playerPropVespene,c_playerPropOperSubtract,g);\n'
            f'    // 0.6.75: free tier units only fill the room left under the cap.\n'
            f'    for (i=gv_{pre}_supPaid[p];i<gv_{pre}_supN[p];i+=1) {{\n'
            f'        if (gf_{fpre}_Food(p)+food+gf_{fpre}_UnitFood({kind})>120.0) {{ gv_{pre}_supN[p]=i; break; }}\n'
            f'        food+=gf_{fpre}_UnitFood({kind});\n    }}\n    return true;\n}}\n')
    return s[:j] + fill + s[j + len(pay):]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m, (pre, _, prot, zerg) in TIERS.items():
            k = f'{m}.SC2Map/mapscript.galaxy'
            t = files[k].decode('utf-8'); crlf = '\r\n' in t
            t = cap_free(patch(t.replace('\r\n', '\n'), pre, prot, zerg), pre)
            files[k] = (t.replace('\n', '\r\n') if crlf else t).encode('utf-8'); changed.add(k)
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist():
                z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
