#!/usr/bin/env python3
"""0.6.63 -> 0.6.64 (user 2026-11-21).

1) "기지 양옆에 가스 2개, 건물 없는 미션 제외": only mission 2 (TRaynor02) had one geyser at Raynor's base
   (3-6 already have two, mission 1 has no base). Add a RichVespeneGeyser on the other end of the mineral arc,
   mirrored from the existing one (86.5,22.5) across the CC->minerals axis and nudged onto flat ground: (84.5,37.5), same reserve 5369.
2) "광물이나 사령부에 왼쪽 위에 조그맣게 표시되는 거, 효과처럼" (maps 3-6): once Inexhaustible Resources
   (RM6_EternalRes) is researched, every field it keeps alive (mineral fields near Raynor's town halls, Raynor's
   refineries) and the town halls carry a visible buff icon "고갈되지 않는 자원 N단계" (CBehaviorBuff
   RM6_EternalShow1..3, permanent, icon btn-tips-richminerals). Only the current level is kept.
3) "방패 연구는 중첩인데 아이콘에는 따로 표기됨" -> one icon (maps 3-6, War Pig only): Combat Shield passive shows
   only until Combat Shield Level 2 is done; then the Level 2 passive takes the same slot with the combined text
   (+10 life, 20% less splash damage) and the same icon. B-2 passive moves one slot left.
Game not run.

Usage: python3 tools/build_v0664.py <0.6.63 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD

OLD, NEW = b'version=0.6.63', b'version=0.6.64'
M2 = 'TRaynor02'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01']
GEYSER_POS = '84.5,37.5,0'

BEHAV = ''.join(f'''<CBehaviorBuff id="RM6_EternalShow{n}"><Alignment value="Positive" /><BehaviorFlags index="Permanent" value="1" /><InfoIcon value="Assets\\Textures\\btn-tips-richminerals.dds" /></CBehaviorBuff>''' for n in (1, 2, 3))
RATE = {1: 2, 2: 3, 3: 4}
STR_EH = {}
for n in (1, 2, 3):
    STR_EH[f'Behavior/Name/RM6_EternalShow{n}'] = f'고갈되지 않는 자원 {n}단계 /// Inexhaustible Resources Level {n}'
    STR_EH[f'Behavior/Tooltip/RM6_EternalShow{n}'] = (f'이 근처 광물·가스는 고갈되지 않고 처음 매장량까지 초당 {RATE[n]}씩 다시 찹니다. '
                                                   f'/// Resources here never run out and regrow {RATE[n]} per second toward their starting amount.')
STR_SH = {'Button/Name/RMP_RM6_ShieldSplash': '전투 방패 2단계 /// Combat Shield Level 2',
          'Button/Tooltip/RMP_RM6_ShieldSplash': '최대 생명력 +10, 받는 범위 공격 피해 20% 감소. /// +10 maximum life, takes 20% less splash damage.'}

SCRIPT_FN = '''// 0.6.64: visible buff icon on the fields and town halls Inexhaustible Resources keeps alive (current level only).
unitgroup gv_rmEternalMarked;
void gf_rmEternalUnmark (unit u) {
    int k;
    for (k = 1; k <= 3; k += 1) {
        if (UnitHasBehavior2(u, "RM6_EternalShow" + IntToString(k))) { UnitBehaviorRemove(u, "RM6_EternalShow" + IntToString(k), 1); }
    }
}
void gf_rmEternalMark (unit u, int lv) {
    int k;
    for (k = 1; k <= 3; k += 1) {
        if (k != lv && UnitHasBehavior2(u, "RM6_EternalShow" + IntToString(k))) { UnitBehaviorRemove(u, "RM6_EternalShow" + IntToString(k), 1); }
    }
    if (!UnitHasBehavior2(u, "RM6_EternalShow" + IntToString(lv))) { UnitBehaviorAdd(u, "RM6_EternalShow" + IntToString(lv), u, 1); }
}
'''
FIELD_LOOP = '    for (i = UnitGroupCount(fields, c_unitCountAll); i > 0; i -= 1) { gf_rmEternalField(UnitGroupUnit(fields, i)); }\n'
FIELD_LOOP_NEW = ('    for (i = UnitGroupCount(fields, c_unitCountAll); i > 0; i -= 1) { gf_rmEternalField(UnitGroupUnit(fields, i)); }\n'
                  '    // 0.6.64: marked set = kept fields + grounded live halls; anything that dropped out loses its icon.\n'
                  '    for (i = UnitGroupCount(halls, c_unitCountAll); i > 0; i -= 1) { if (UnitIsAlive(UnitGroupUnit(halls, i))) { UnitGroupAdd(fields, UnitGroupUnit(halls, i)); } }\n'
                  '    if (gv_rmEternalMarked != null) {\n'
                  '        for (i = UnitGroupCount(gv_rmEternalMarked, c_unitCountAll); i > 0; i -= 1) {\n'
                  '            if (!UnitGroupHasUnit(fields, UnitGroupUnit(gv_rmEternalMarked, i))) { gf_rmEternalUnmark(UnitGroupUnit(gv_rmEternalMarked, i)); }\n'
                  '        }\n'
                  '    }\n'
                  '    for (i = UnitGroupCount(fields, c_unitCountAll); i > 0; i -= 1) { gf_rmEternalMark(UnitGroupUnit(fields, i), lv); }\n'
                  '    gv_rmEternalMarked = fields;\n')
FN_ANCHOR = 'bool gt_rmEternal_Func (bool testConds, bool runActions) {\n'

NODES = ('<CRequirementNot id="RMP_NotRM6_ShieldSplash"><OperandArray index="0" value="RMP_DoneRM6_ShieldSplash" /></CRequirementNot>'
         '<CRequirementAnd id="RMP_ShieldOnlyAnd"><OperandArray value="RMP_DoneRM3_Shield" /><OperandArray value="RMP_NotRM6_ShieldSplash" /></CRequirementAnd>')
REQ = '<CRequirement id="RMP_ShieldOnly"><NodeArray index="Show" Link="RMP_ShieldOnlyAnd" /></CRequirement>'


def add_cat(raw, xml):
    t = raw.decode('utf-8')
    i = t.rindex('</Catalog>')
    return (t[:i] + xml + '\n' + t[i:]).encode('utf-8')


def warpig(u):
    s = u.index('<CUnit id="WarPig"'); e = u.index('</CUnit>', s); seg = u[s:e]
    subs = [('<LayoutButtons Face="RMP_RM3_Shield" Type="Passive" Requirements="RMP_HaveRM3_Shield" Row="1" Column="0" />',
             '<LayoutButtons Face="RMP_RM3_Shield" Type="Passive" Requirements="RMP_ShieldOnly" Row="1" Column="0" />'),
            ('<LayoutButtons Face="RMP_RM6_ShieldSplash" Type="Passive" Requirements="RMP_HaveRM6_ShieldSplash" Row="1" Column="2" />',
             '<LayoutButtons Face="RMP_RM6_ShieldSplash" Type="Passive" Requirements="RMP_HaveRM6_ShieldSplash" Row="1" Column="0" />'),
            ('<LayoutButtons Face="RMP_RM6_B2LMG" Type="Passive" Requirements="RMP_HaveRM6_B2LMG" Row="1" Column="3" />',
             '<LayoutButtons Face="RMP_RM6_B2LMG" Type="Passive" Requirements="RMP_HaveRM6_B2LMG" Row="1" Column="2" />')]
    for a, b in subs:
        assert seg.count(a) == 1, a[:60]; seg = seg.replace(a, b)
    return u[:s] + seg + u[e:]


def geyser(raw):
    t = raw.decode('utf-8')
    m = re.search(r'    <ObjectUnit Id="28" Position="86.5,22.5,0"[^>]*UnitType="RichVespeneGeyser"[^>]*>.*?</ObjectUnit>\n', t, re.S)
    assert m and '84.5,37.5' not in t
    ids = [int(x) for x in re.findall(r' Id="(\d+)"', t)]
    new = m.group(0).replace('Id="28"', f'Id="{max(ids) + 1}"', 1).replace('Position="86.5,22.5,0"', f'Position="{GEYSER_POS}"', 1)
    return (t[:m.end()] + new + t[m.end():]).encode('utf-8')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        k = f'{M2}.SC2Map/objects'; files[k] = geyser(files[k]); changed.add(k)
        for m in MAPS:
            g = f'{m}.SC2Map/{GD}'
            for f, x in (('behaviordata.xml', BEHAV), ('requirementnodedata.xml', NODES), ('requirementdata.xml', REQ)):
                files[g + f] = add_cat(files[g + f], x); changed.add(g + f)
            files[g + 'unitdata.xml'] = warpig(files[g + 'unitdata.xml'].decode('utf-8')).encode('utf-8'); changed.add(g + 'unitdata.xml')
            b = files[g + 'buttondata.xml'].decode('utf-8')
            old = '<CButton id="RMP_RM6_ShieldSplash"><Icon value="Assets\\Textures\\btn-techupgrade-terran-combatshield.dds" />'
            assert b.count(old) == 1
            files[g + 'buttondata.xml'] = b.replace(old, old.replace('combatshield.dds', 'combatshield-color.dds')).encode('utf-8'); changed.add(g + 'buttondata.xml')
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'; t = raw.replace('\r\n', '\n')
            for a, bb in ((FIELD_LOOP, FIELD_LOOP_NEW), (FN_ANCHOR, SCRIPT_FN + FN_ANCHOR)):
                assert t.count(a) == 1, (m, a[:40]); t = t.replace(a, bb)
            files[p] = t.replace('\n', nl).encode('utf-8'); changed.add(p)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], {**STR_EH, **STR_SH}); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
        for k in changed:
            if k.endswith('.xml') or k.endswith('/objects'): E.fromstring(files[k])
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
