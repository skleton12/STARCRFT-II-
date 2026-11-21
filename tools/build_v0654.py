#!/usr/bin/env python3
"""0.6.53 -> 0.6.54 (user 2026-11-21 "광물업은 중첩업글임", "중첩이면 3번까지로 해, 초당 광물은 너와 코덱스가 정해").

RM6_EternalRes (고갈되지 않는 자원, 공학 연구소, maps 3-6) had no button requirement and no MaxLevel, so it could be
bought forever (400/400 each) with no extra effect. Now a 3-level upgrade:
  - MaxLevel 3; button requirement RM6_EternalResLearn = (queued-or-better count) < 3 (Liberty const "3").
  - Regen per mineral field / Raynor refinery per second: L1 2, L2 3, L3 4 (Codex proposed 1/1.75/2.5; user asked
    for "2나 3" so more can be mined; trial ETERNAL_REGEN_QUARTERS 8/12/16, quarter units kept for later fractions).
  - Button name shows the next level, "(1단계)" -> "(2단계)" -> "(3단계)", and the upgrade name the finished level
    (user "옆에 1단계 이렇게 적어놔줘"): per-player CatalogFieldValueSet on Button/Upgrade Name when the level changes. Floor 100 and cap at the starting
    amount unchanged. Cost stays 400/400 per level (one research slot cannot price levels differently; trial).
  - Tooltip (12 languages) states the per-level regen.

Usage: python3 tools/build_v0654.py <0.6.53 zip> <new output zip>
"""
import argparse, copy, re, zipfile, xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.6.53', b'version=0.6.54'
MS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
LANGS = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
G = '.SC2Map/base.sc2data/gamedata/'
REQ = b'<CRequirement id="RM6_EternalResLearn"><NodeArray index="Show" Link="RM6_EternalResShow" /></CRequirement>'
NODES = (b'<CRequirementCountUpgrade id="RM6_EternalResQueued"><Count Link="RM6_EternalRes" State="QueuedOrBetter" />'
         b'</CRequirementCountUpgrade><CRequirementLT id="RM6_EternalResShow"><OperandArray index="0" '
         b'value="RM6_EternalResQueued" /><OperandArray index="1" value="3" /></CRequirementLT>')
EN = ('Each level: minerals near your Command Centers and vespene in your Refineries no longer run out and regenerate '
      'toward their starting amount. Regeneration per field per second: Level 1 2, Level 2 3, Level 3 4 (max 3 levels).')
KO = ('단계마다 사령부 근처 광물과 레이너 정제소 가스가 고갈되지 않고 처음 매장량까지 다시 찹니다. '
      '지대 하나당 초당 재생: 1단계 2, 2단계 3, 3단계 4 (최대 3단계).')
OLD_EN = 'Minerals and vespene near your Command Centers no longer run out and slowly regenerate to their starting amount.'
OLD_KO = '사령부 근처의 광물과 레이너 정제소의 가스가 더는 고갈되지 않고, 처음 매장량까지 천천히 다시 찹니다.'

S_FIELD_A = b'void gf_rmEternalField (unit u) {'
S_FIELD_B = (b'// 0.6.54: 3 levels, regen per field per second L1 2 / L2 3 / L3 4 (trial ETERNAL_REGEN_QUARTERS, in quarters).\n'
             b'int[4] gv_rmEternalQ;\nint gv_rmEternalStep = 1;\nint gv_rmEternalTick = 0;\nint gv_rmEternalShown = 0;\n'
             b'void gf_rmEternalField (unit u) {')
S_DECL_A = b'bool gt_rmEternal_Func (bool testConds, bool runActions) {\n    unitgroup halls;\n'
S_DECL_B = S_DECL_A + b'    int lv;\n'
S_ADD_A = b'else if (cur < top) { cur = MinI(top, cur + 1); }'
S_ADD_B = b'else if (cur < top) { cur = MinI(top, cur + gv_rmEternalStep); }'
S_LV_A = b'    if (TechTreeUpgradeCount(1, "RM6_EternalRes", c_techCountCompleteOnly) == 0) { return true; }\n'
S_LV_B = (b'    lv = MinI(3, TechTreeUpgradeCount(1, "RM6_EternalRes", c_techCountCompleteOnly));\n'
          b'    if (lv != gv_rmEternalShown) {\n'
          b'        gv_rmEternalShown = lv;\n'
          b'        if (lv < 3) { CatalogFieldValueSet(c_gameCatalogButton, "RM6_EternalRes", "Name", 1, "Button/Name/RM6_EternalRes" + IntToString(lv + 1)); }\n'
          b'        CatalogFieldValueSet(c_gameCatalogUpgrade, "RM6_EternalRes", "Name", 1, "Upgrade/Name/RM6_EternalRes" + IntToString(lv));\n'
          b'    }\n'
          b'    if (lv == 0) { return true; }\n'
          b'    gv_rmEternalQ[1] = 8; gv_rmEternalQ[2] = 12; gv_rmEternalQ[3] = 16;\n'
          b'    // whole units this second = floor((t+1)*q/4) - floor(t*q/4), so fractional rates also add up exactly\n'
          b'    gv_rmEternalStep = ((gv_rmEternalTick + 1) * gv_rmEternalQ[lv]) / 4 - (gv_rmEternalTick * gv_rmEternalQ[lv]) / 4;\n'
          b'    gv_rmEternalTick = (gv_rmEternalTick + 1) % 4;\n')


def lab(ko, k, e, n):
    return (k.format(n) + ' /// ' + e.format(n)) if ko else e.format(n)


def once(data, a, b, what):
    assert data.count(a) == 1, (what, a[:60], data.count(a))
    return data.replace(a, b)


def end_insert(data, add, what):
    i = data.rindex(b'</Catalog>')
    assert data[i:].strip() == b'</Catalog>', what
    return data[:i] + add + data[i:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MS:
            k = m + G + 'upgradedata.xml'; s = files[k]
            s2 = re.sub(rb'(<CUpgrade id="RM6_EternalRes">\s*<Race value="Terr" />)', rb'\1<MaxLevel value="3" />', s, count=1)
            assert s2 != s and b'MaxLevel' not in re.search(rb'<CUpgrade id="RM6_EternalRes">.*?</CUpgrade>', s, re.S).group(0), m
            files[k] = s2; changed.add(k)
            k = m + G + 'abildata.xml'
            files[k] = once(files[k], b'<Button DefaultButtonFace="RM6_EternalRes" State="Available" />',
                            b'<Button DefaultButtonFace="RM6_EternalRes" State="Available" Requirements="RM6_EternalResLearn" />', m)
            changed.add(k)
            k = m + G + 'requirementdata.xml'; files[k] = end_insert(files[k], REQ, m); changed.add(k)
            k = m + G + 'requirementnodedata.xml'; files[k] = end_insert(files[k], NODES, m); changed.add(k)
            k = m + '.SC2Map/mapscript.galaxy'; s = files[k]
            nl = b'\r\n' if b'\r\n' in s else b'\n'
            fx = lambda x: x.replace(b'\n', nl)
            s = once(s, fx(S_FIELD_A), fx(S_FIELD_B), m); s = once(s, S_ADD_A, S_ADD_B, m); s = once(s, fx(S_LV_A), fx(S_LV_B), m); s = once(s, fx(S_DECL_A), fx(S_DECL_B), m)
            files[k] = s; changed.add(k)
            for lang in LANGS:
                k = f'{m}.SC2Map/{lang}.sc2data/localizeddata/gamestrings.txt'
                old = (OLD_KO + ' /// ' + OLD_EN) if lang == 'kokr' else OLD_EN
                new = (KO + ' /// ' + EN) if lang == 'kokr' else EN
                files[k] = once(files[k], ('Button/Tooltip/RM6_EternalRes=' + old).encode(),
                                ('Button/Tooltip/RM6_EternalRes=' + new).encode(), k)
                d = files[k]; nl = b'\r\n' if b'\r\n' in d else b'\n'
                ko = lang == 'kokr'
                bn = ('고갈되지 않는 자원 연구 /// Research Inexhaustible Resources' if ko else 'Research Inexhaustible Resources')
                d = once(d, ('Button/Name/RM6_EternalRes=' + bn).encode(),
                         ('Button/Name/RM6_EternalRes=' + lab(ko, '고갈되지 않는 자원 연구 ({}단계)', 'Research Inexhaustible Resources (Level {})', 1)).encode(), k)
                extra = []
                for n in (1, 2, 3):
                    extra.append('Button/Name/RM6_EternalRes%d=' % n + lab(ko, '고갈되지 않는 자원 연구 ({}단계)', 'Research Inexhaustible Resources (Level {})', n))
                    extra.append('Upgrade/Name/RM6_EternalRes%d=' % n + lab(ko, '고갈되지 않는 자원 {}단계', 'Inexhaustible Resources Level {}', n))
                d = d.rstrip(b'\r\n') + nl + nl.join(x.encode() for x in extra) + nl
                files[k] = d
                changed.add(k)
        for k in changed:
            if k.endswith('.xml'): E.fromstring(files[k])
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
