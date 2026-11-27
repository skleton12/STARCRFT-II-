#!/usr/bin/env python3
"""0.12.3 -> 0.12.4: 연구실 단계가 열렸는데 아무것도 안 골랐을 때 (사용자 2026-11-27).

사용자: "연구소는 연구소가 풀리면 전부다 적용되어야하는거긴함 이유인 즉슨 치트쓸경우도 대비해야되니",
선택 "고른 쪽 적용+나머지 연구" (지금 방식 유지 + 아무것도 안 골랐을 때 하나는 자동, 나머지는 연구).

maps 3~9·11·12 (연구실 연구가 있는 맵 전부):
  - 단계가 열렸다 = 그 연구의 히페리온 연구 점수(libCamp_gf_StoryResearchPoints(분류)) >= 원작 요구 점수
    (libCamp_gf_StoryResearchLevelRequirement, 원작 연구실 단계와 같은 값). 요구 점수를 못 읽으면(0) 아무것도 안 한다.
  - 열렸는데 짝 둘 다 안 골랐으면 짝의 첫째(P11 울트라 축전기·P21 궤도 보급고·P31 자동 정제소·P41 밤까마귀·P51 기술 반응로·
    Z11 까치날개 포탑·Z21 행성 요새·Z31 약탈자·Z41 세포 반응로·Z51 군락 정신 모방기)를 이 미션 안에서만 고른 것으로 친다:
    1초마다 캠페인과 같은 보상(0.9.7 gf_rmLabApply)을 적용한다. 캠페인 저장 상태는 바꾸지 않는다(히페리온에서 나중에 고를 수 있음).
  - 둘째는 기존 '고르지 않은 쪽' 연구로 공학 연구소에 나온다: 0.9.7 연구실 연구(gf_rmLabOne)·0.8.10 행성 요새/화염 포탑은
    상태 확인을 gf_rmLabHas로 바꿨고, 0.8.2 바나듐 장갑·0.8.9 강화 벙커는 첫째의 보상 업그레이드(UltraCapacitors·ShrikeTurret)를
    보고 나오므로 그대로 나온다.
  - 0.9.7 연구실 연구 툴팁의 조건 문구를 고침.
Game not run.

Usage: python3 tools/build_v0124.py <0.12.3 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO
from build_v097 import ITEMS as LAB_ITEMS

OLD, NEW = b'version=0.12.3', b'version=0.12.4'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
R = 'libCamp_ge_StoryResearchID_Research'
PAIRS = [('P11UltraCapacitors', 'P12VanadiumPlating'), ('P21OrbitalDepots', 'P22MicroFiltering'),
         ('P31AutomatedRefinery', 'P32CommandCenterReactor'), ('P41Raven', 'P42ScienceVessel'),
         ('P51TechReactor', 'P52OrbitalStrike'), ('Z11ShrikeTurret', 'Z12FortifiedBunker'),
         ('Z21PlanetaryFortress', 'Z22PerditionTurret'), ('Z31Predator', 'Z32Hercules'),
         ('Z41CellularReactors', 'Z42RegenerativeBioSteel'), ('Z51HiveMindEmulator', 'Z52SigmaProjector')]
BOUGHT = 'libCamp_ge_StoryResearchState_ResearchStatePurchased'


def helpers():
    s = ['// 0.12.4 (user 2026-11-27): a lab tier that is unlocked (research points) with neither option picked (e.g. cheats)',
         '// counts as its FIRST option picked, in this mission only (campaign state untouched); the other one is researchable.',
         'bool gf_rmLabBought (int id) {',
         f'    return libCamp_gf_StoryResearchStateCheck(id, {BOUGHT});',
         '}', '',
         'bool gf_rmLabAutoOn (int a, int b) {',
         '    int req = libCamp_gf_StoryResearchLevelRequirement(a);',
         '    if (req <= 0) { return false; }',
         '    if (libCamp_gf_StoryResearchPoints(libCamp_gf_StoryResearchCategory(a)) < req) { return false; }',
         '    return !gf_rmLabBought(a) && !gf_rmLabBought(b);',
         '}', '',
         'int gf_rmLabFirstPartner (int id) {']
    for a, b in PAIRS:
        s.append(f'    if (id == {R}{a}) {{ return {R}{b}; }}')
    s += [f'    return {R}None;', '}', '',
          'bool gf_rmLabHas (int id) {',
          '    int b = gf_rmLabFirstPartner(id);',
          '    if (gf_rmLabBought(id)) { return true; }',
          f'    if (b == {R}None) {{ return false; }}',
          '    return gf_rmLabAutoOn(id, b);',
          '}', '', '']
    return '\n'.join(s)


def auto_apply():
    s = ['// 0.12.4: unlocked tier with no pick -> the first option\'s campaign reward, re-applied every tick like 0.9.7.',
         'void gf_rmLabAutoApply (int a, int b, int n) {',
         '    if (gf_rmLabAutoOn(a, b)) { gf_rmLabApply(a, n); }',
         '}', '', '']
    return '\n'.join(s)


def calls():
    return ''.join(f'    gf_rmLabAutoApply({R}{a}, {R}{b}, {16 + i});\n' for i, (a, b) in enumerate(PAIRS))


def patch_script(t):
    def rep(a, b):
        nonlocal t
        assert t.count(a) == 1, a[:80]
        t = t.replace(a, b)
    rep('bool[16] gv_rmLabDone;', 'bool[32] gv_rmLabDone;')
    a = '// 0.8.10 (user 2026-11-24): lab Zerg tier 2'
    rep(a, helpers() + a)
    for x in ('pf', 'pt'):
        rid = 'Z21PlanetaryFortress' if x == 'pf' else 'Z22PerditionTurret'
        rep(f'    {x} = libCamp_gf_StoryResearchStateCheck({R}{rid}, {BOUGHT});', f'    {x} = gf_rmLabHas({R}{rid});')
    rep(f'    if (libCamp_gf_StoryResearchStateCheck(other, {BOUGHT})\n        && !libCamp_gf_StoryResearchStateCheck(id, {BOUGHT})',
        '    if (gf_rmLabHas(other)\n        && !gf_rmLabHas(id)')
    a = 'bool gt_rmLab_Func (bool testConds, bool runActions) {'
    rep(a, auto_apply() + a)
    a = f'    gf_rmLabOne({R}P21OrbitalDepots,'
    rep(a, calls() + a)
    return t


def strings():
    d = {}
    for k, rid, pid, r, c, hk, ic, ko, en, dko, den in LAB_ITEMS:
        tko = f'{dko} 연구실에서 다른 쪽을 골랐거나, 단계가 열렸는데 아무것도 고르지 않아 다른 쪽이 자동 적용됐을 때 연구할 수 있습니다.'
        ten = f'{den} Available if the other option was chosen in the lab, or was applied automatically because the tier is unlocked with nothing chosen.'
        d[f'Button/Tooltip/RML_{k}'] = f'{tko} /// {ten}'
    return d


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    strs = strings()
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            k = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
            files[k] = patch_script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], strs); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
