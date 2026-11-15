#!/usr/bin/env python3
"""0.6.30 -> 0.6.31: 비싼 연구 '고갈되지 않는 자원' (사용자 2026-11-15).

사용자: "좀 비싼업그레이드 추가 고갈되지 않는 자원 업그레이드시 광물과 가스가 고갈되지 않고 천천히 재생합니다".
모드에서 재설계한 미션 내 연구 (원작에 없음). 3·4·5·6번 맵 (공학 연구소 RM3_BayResearch가 있는 맵).
- 연구 RM6_EternalRes: 공학 연구소 첫 화면 2행 3열(멀티샷 옆), 단축키 G, 광물 400·가스 400·150초 (시험값, "좀 비싼").
- 효과 (스크립트, 1초마다): 레이너 사령부(사령부·궤도 사령부·행성 요새, 떠 있는 것 제외) 반경 12 안의 광물 덩어리(중립, 이름에 Mineral)와
  레이너의 모든 정제소(위치 무관)의 자원이 (빈 간헐천·다른 플레이어 정제소 제외, 사령부가 겹쳐도 한 번만, Codex 검토 반영)
    1) 바닥값 아래로 내려가지 않는다 (광물 100·가스 100, 시험값) -> 고갈되지 않음,
    2) 초당 1씩(시험값) 처음 매장량까지 천천히 다시 찬다.
  처음 매장량은 임무 시작 때 맵의 모든 자원에 기록한다 (유닛 사용자 값 7번 칸). 나중에 지은 정제소는 처음 본 값이 상한.
- 아이콘: 자날 스토리 층에 있는 '풍부한 광물' 안내 아이콘(btn-tips-richminerals, 자날 맵에서 불러올 수 있음, 다른 버튼에 안 씀).
게임 미실행.

Usage: python3 tools/build_v0631.py <0.6.30 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import find, xml_edit, add_xml, set_lines, LOCS, KO, GD

OLD, NEW = b'version=0.6.30', b'version=0.6.31'
MAPS = ('TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
UP = 'RM6_EternalRes'
COST, TIME = '400', '150'
FLOOR, REGEN, RADIUS = 100, 1, 12.0
CV = 7   # unit custom value slot holding the starting amount
ICON = 'Assets\\Textures\\btn-tips-richminerals.dds'

ADD = {
    'upgradedata.xml': f'<CUpgrade id="{UP}"><Race value="Terr" /><Alert value="ResearchComplete" /><Icon value="{ICON}" /></CUpgrade>',
    'buttondata.xml': f'<CButton id="{UP}"><Icon value="{ICON}" /><Name value="Button/Name/{UP}" />'
                      f'<Tooltip value="Button/Tooltip/{UP}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>',
}
STRINGS = {
    f'Upgrade/Name/{UP}': '고갈되지 않는 자원 /// Inexhaustible Resources',
    f'Button/Name/{UP}': '고갈되지 않는 자원 연구 /// Research Inexhaustible Resources',
    f'Button/Tooltip/{UP}': '사령부 근처의 광물과 레이너 정제소의 가스가 더는 고갈되지 않고, 처음 매장량까지 천천히 다시 찹니다. '
                            '/// Minerals and vespene near your Command Centers no longer run out and slowly regenerate to their starting amount.',
}
ALLOW_ANCHOR = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",0),true);\n'
SCRIPT = f'''
// 0.6.31 (user 2026-11-15): research RM6_EternalRes - resources near Raynor's town halls never run out and regrow.
trigger gt_rmEternal;
void gf_rmEternalField (unit u) {{
    int cur = UnitGetPropertyInt(u, c_unitPropResources, c_unitPropCurrent);
    int top = FixedToInt(UnitGetCustomValue(u, {CV}));
    if (cur <= 0 && top <= 0) {{ return; }}
    if (cur > top) {{ top = cur; UnitSetCustomValue(u, {CV}, IntToFixed(top)); }}
    if (cur < {FLOOR}) {{ cur = {FLOOR}; }}
    else if (cur < top) {{ cur = MinI(top, cur + {REGEN}); }}
    UnitSetPropertyInt(u, c_unitPropResources, cur);
}}
void gf_rmEternalAdd (unitgroup out, unit hall) {{
    unitgroup g;
    int i;
    unit u;
    if (!UnitIsAlive(hall)) {{ return; }}
    g = UnitGroup(null, 0, RegionCircle(UnitGetPosition(hall), {RADIUS}), UnitFilter(0, 0, 0, 0), 0);
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {{
        u = UnitGroupUnit(g, i);
        if (StringFind(UnitGetType(u), "Mineral", c_stringNoCase) != c_stringNotFound) {{ UnitGroupAdd(out, u); }}
    }}
}}
bool gt_rmEternal_Func (bool testConds, bool runActions) {{
    unitgroup halls;
    unitgroup fields;
    int i;
    if (!runActions) {{ return true; }}
    if (TechTreeUpgradeCount(1, "{UP}", c_techCountCompleteOnly) == 0) {{ return true; }}
    // Every Raynor refinery (anywhere) + mineral fields near Raynor's grounded town halls; a set, so overlap counts once.
    fields = UnitGroup("Refinery", 1, null, UnitFilter(0, 0, 0, 0), 0);
    UnitGroupAddUnitGroup(fields, UnitGroup("RefineryRich", 1, null, UnitFilter(0, 0, 0, 0), 0));
    halls = UnitGroup("CommandCenter", 1, null, UnitFilter(0, 0, 0, 0), 0);
    UnitGroupAddUnitGroup(halls, UnitGroup("OrbitalCommand", 1, null, UnitFilter(0, 0, 0, 0), 0));
    UnitGroupAddUnitGroup(halls, UnitGroup("PlanetaryFortress", 1, null, UnitFilter(0, 0, 0, 0), 0));
    for (i = UnitGroupCount(halls, c_unitCountAll); i > 0; i -= 1) {{ gf_rmEternalAdd(fields, UnitGroupUnit(halls, i)); }}
    for (i = UnitGroupCount(fields, c_unitCountAll); i > 0; i -= 1) {{ gf_rmEternalField(UnitGroupUnit(fields, i)); }}
    return true;
}}
void gf_rmEternalStart () {{
    unitgroup g = UnitGroup(null, 0, null, UnitFilter(0, 0, 0, 0), 0);
    int i;
    unit u;
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {{
        u = UnitGroupUnit(g, i);
        UnitSetCustomValue(u, {CV}, IntToFixed(UnitGetPropertyInt(u, c_unitPropResources, c_unitPropCurrent)));
    }}
    gt_rmEternal = TriggerCreate("gt_rmEternal_Func");
    TriggerAddEventTimePeriodic(gt_rmEternal, 1.0, c_timeGame);
}}
'''


def edit_map(d):
    g = d / GD
    for fn, xml in ADD.items():
        add_xml(g / fn, xml)

    def abils(root):
        r = find(root, 'CAbilResearch', 'RM3_BayResearch')
        assert not [i for i in r.findall('InfoArray') if i.get('index') == 'Research22']
        r.append(E.fromstring(f'<InfoArray index="Research22" Time="{TIME}" Upgrade="{UP}">'
                              f'<Resource index="Minerals" value="{COST}" /><Resource index="Vespene" value="{COST}" />'
                              f'<Button DefaultButtonFace="{UP}" State="Available" /></InfoArray>'))
    xml_edit(g / 'abildata.xml', abils)

    def units(root):
        bay = find(root, 'CUnit', 'EngineeringBay')
        page = [c for c in bay.findall('CardLayouts') if c.get('index') == '0']
        assert len(page) == 1 and not [b for b in page[0] if (b.get('Row'), b.get('Column')) == ('2', '3')]
        page[0].append(E.fromstring(f'<LayoutButtons Face="{UP}" Type="AbilCmd" AbilCmd="RM3_BayResearch,Research22" Row="2" Column="3" />'))
    xml_edit(g / 'unitdata.xml', units)

    p = d / 'mapscript.galaxy'
    raw = p.read_bytes().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    assert t.count(ALLOW_ANCHOR) == 1 and 'gt_rmEternal' not in t
    t = t.replace(ALLOW_ANCHOR, ALLOW_ANCHOR + '    // 0.6.31: Inexhaustible Resources research (Engineering Bay).\n'
                  '    TechTreeAbilityAllow(1,AbilityCommand("RM3_BayResearch",21),true);\n'
                  f'    TechTreeUpgradeAllow(1,"{UP}",true);\n'
                  '    gf_rmEternalStart();\n')
    inc = list(re.finditer(r'^include "[^"]+"\n', t, re.M))
    t = t[:inc[-1].end()] + SCRIPT + t[inc[-1].end():]
    p.write_bytes(t.replace('\n', nl).encode('utf-8'))


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            d = root / f'{m}.SC2Map'
            edit_map(d)
            ko = set_lines((d / KO).read_bytes(), STRINGS)
            (d / KO).write_bytes(ko)
            V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
            for loc in LOCS:
                h = d / f'{loc}.sc2data/localizeddata/gamehotkeys.txt'
                h.write_bytes(set_lines(h.read_bytes(), {f'Button/Hotkey/{UP}': 'G'}))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in MAPS) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
