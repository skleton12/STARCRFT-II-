#!/usr/bin/env python3
"""0.6.74 -> 0.6.75 (user 2026-11-22 "플토 저그 연구 5단계잖음 1단계마다 유닛 2개 추가로", "1단계 연구 적용 안 되는 것 같은데 확인좀").

Ally support tiers (Hyperion lab research bought: Protoss -> Purifier, Zerg -> Primal Zerg, 0-5), maps 3-7:
- Each tier now adds 2 units of its kind instead of 1 (zergling tier: 4 zerglings, they come in pairs). Free, trial.
- Check result: maps 4-7 counted the tier once when the support buttons were set up. Map 3 (TRaynor03) never set its
  tier at all (always 0). The tier is now recounted every time a support group is filled, in all five maps, so
  the group always uses the current lab state.
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
    TIERS[m] = (pre, 8, ['ZealotPurifier', 'StalkerPurifier', 'AdeptFenix', 'ColossusPurifier', 'TempestPurifier'],
                ['DehakaZerglingLevel2', 'DehakaRavasaur', 'DehakaRoachLevel3', 'DehakaUltraliskLevel2', 'DehakaUltraliskLevel3'])


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
        assert f'"{kind}"' in mt.group(0), (pre, n, kind)  # same kind as before, only the count changes
        adds = ' '.join(f'gf_{pre}_SupAdd(p,"{kind}");' for _ in range(cnt))
        return f'{ind}if (gv_{pre}_tier[p]>={n}) {{ {adds} }}\n'
    s = tl.sub(rep, s)
    head = f'    gv_{pre}_supN[p]=0;\n'
    i = s.index(f'void gf_{pre}_SupFill (int p) {{')
    j = s.index(head, i); assert j - i < 200
    s = s[:j] + head + f'    gv_{pre}_tier[p]=gf_{pre}_Tier(p);  // 0.6.75: recount each group (map 3 never set it)\n' + s[j + len(head):]
    assert s.index(f'int gf_{pre}_Tier (int p)') < i  # declared before use
    if pre == 'm3c':  # map 3 label showed the never-set tier: count it when the buttons are set up too
        a = '    gv_m3c_callAt[10]=MaxF(240.0,GameGetMissionTime());\n'
        assert s.count(a) == 1
        s = s.replace(a, '    gv_m3c_tier[10]=gf_m3c_Tier(10);\n    gv_m3c_tier[11]=gf_m3c_Tier(11);\n' + a)
    return s


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
            t = patch(t.replace('\r\n', '\n'), pre, prot, zerg)
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
