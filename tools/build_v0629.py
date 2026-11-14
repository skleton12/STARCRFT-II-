#!/usr/bin/env python3
"""0.6.28 -> 0.6.29: 적 공격 강화를 곱하기에서 더하기로 (사용자 2026-11-14).

사용자: "야 왜 적 마린 공격력이 공업2 인데 12냐", "곱하기를 왜해 더하기를 해야지 너무 쎄잖아".
0.6.27은 '1 + 0.5'를 모든 적 피해 x1.5로 넣어 공업 2 해병이 (6+2)x1.5 = 12였다.
사용자 뜻은 업그레이드 1단계 = 원래 증가량 + 50% (해병 +1 -> +1.5), 그러니 공업 2 해병은 6 + 3 = 9.

- 적 주는 피해 %는 100으로 되돌린다 (받는 피해 100, 0.6.27 그대로).
- 무기 업그레이드 줄마다 적 전용 숨은 업그레이드 RM_EH_<줄> (MaxLevel 3)을 만든다. 효과는 원작 그 줄의
  '피해량(Effect,...,Amount / AttributeBonus)' 증가분 x 0.5 (EH_FRACTION, 시험값). 레이너·동맹은 이 업그레이드를
  받지 않으므로 영향이 없다.
- 스크립트: 피해 % 를 설정하던 적 플레이어마다 2초에 한 번 그 줄의 완료 단계 수만큼 RM_EH_<줄> 단계를 맞춘다
  (올리기만 함, 최대 3).
- 1번 맵 (사용자 "1번맵 왜 애들 공방이 방 1 공2지 방1만 해"): 적(자치령) 업그레이드를 모든 난이도에서
  보병 방어 1만. 공격 업그레이드는 0 (7-1 최소 공격 1·원본 아주 어려움 공격 1·아주 어려움 +1 공격 줄 제거),
  방어는 최소 1 (원본은 어려움·아주 어려움에서만 1). 7-1 최소 업그레이드의 1번 예외.
업그레이드 속도(0.6.27)·공세 수·AI 칸은 그대로. 게임 미실행.

Usage: python3 tools/build_v0629.py <0.6.28 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD, NEW = b'version=0.6.28', b'version=0.6.29'
MAPS = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
LAYERS = ['core.sc2mod', 'liberty.sc2mod', 'liberty.sc2campaign', 'libertystory.sc2campaign']
LINES = ['TerranInfantryWeapons', 'TerranVehicleWeapons', 'TerranShipWeapons',
         'ZergMeleeWeapons', 'ZergMissileWeapons', 'ZergFlyerWeapons',
         'ProtossGroundWeapons', 'ProtossAirWeapons']
EH_FRACTION = 0.5          # +50% of each upgrade level's damage step (trial)
EH_PERIOD = 2.0
NAME = '적 공격 강화 /// Enemy Attack Bonus'

DEALT = re.compile(r'( *)PlayerModifyPropertyInt\(\s*([^,]+?),\s*c_playerPropDamageDealtPercent,\s*c_playerPropOperSetTo,\s*100\+libNtve_gf_DifficultyValueInt\(50,50,50,50\)\);\n')


def damage_refs(map_gd):
    """Per line: {reference: value} of additive damage steps, merged over layers then the map."""
    out = {l: {} for l in LINES}
    files = [ROOT / 'source' / L / 'base.sc2data/gamedata/upgradedata.xml' for L in LAYERS] + [map_gd / 'upgradedata.xml']
    for f in files:
        if not f.exists(): continue
        for e in E.parse(f).getroot():
            if e.tag != 'CUpgrade' or e.get('id') not in out: continue
            for a in e.findall('EffectArray'):
                ref, val, op = a.get('Reference', ''), a.get('Value'), a.get('Operation', 'Add')
                if op != 'Add' or not ref.startswith('Effect,') or val is None: continue
                if not (ref.endswith(',Amount') or ',AttributeBonus[' in ref): continue
                out[e.get('id')][ref] = float(val)
    return out


def upgrades_xml(refs):
    parts = []
    for line in LINES:
        if not refs[line]: continue
        race = 'Terr' if line.startswith('Terran') else 'Zerg' if line.startswith('Zerg') else 'Prot'
        eff = ''.join(f'<EffectArray Reference="{r}" Value="{v * EH_FRACTION:g}" />' for r, v in sorted(refs[line].items()))
        parts.append(f'<CUpgrade id="RM_EH_{line}"><Race value="{race}" /><MaxLevel value="3" />'
                     f'<EditorCategories value="Race:{ {"Terr": "Terran", "Zerg": "Zerg", "Prot": "Protoss"}[race] },UpgradeType:AttackBonus" />'
                     f'{eff}</CUpgrade>')
    return ''.join(parts)


def script_block(lines):
    sets = ''.join(f'    gf_rmEHSync(p,"{l}");\n' for l in lines)
    return f'''
// 0.6.29 (user 2026-11-14): enemy weapon upgrades give +{int(EH_FRACTION*100)}% more per level (added, not multiplied).
// RM_EH_<line> mirrors the line's damage steps x {EH_FRACTION}; synced to the enemy's completed levels.
bool[16] gv_rmEHOn;
trigger gt_rmEH;
void gf_rmEHSync (int p, string line) {{
    int n;
    int want = 0;
    int have;
    for (n=1;n<=3;n+=1) {{
        if (TechTreeUpgradeCount(p,line+"Level"+IntToString(n),c_techCountCompleteOnly)>0) {{ want=n; }}
    }}
    have=TechTreeUpgradeCount(p,"RM_EH_"+line,c_techCountCompleteOnly);
    if (want>have) {{ TechTreeUpgradeAddLevel(p,"RM_EH_"+line,want-have); }}
}}
bool gt_rmEH_Func (bool testConds, bool runActions) {{
    int p;
    if (!runActions) {{ return true; }}
    for (p=0;p<=15;p+=1) {{
        if (gv_rmEHOn[p]) {{
{sets.replace("    gf_", "            gf_")}        }}
    }}
    return true;
}}
void gf_rmEHStart (int p) {{
    gv_rmEHOn[p]=true;
    if (gt_rmEH==null) {{
        gt_rmEH=TriggerCreate("gt_rmEH_Func");
        TriggerAddEventTimePeriodic(gt_rmEH,{EH_PERIOD},c_timeGame);
    }}
}}
'''


M1_EDITS = [
    ('    if (TechTreeUpgradeCount(gv_p2_DOMINION_RED, "TerranInfantryWeaponsLevel1", c_techCountCompleteOnly) < 1) {\n'
     '        TechTreeUpgradeAddLevel(gv_p2_DOMINION_RED, "TerranInfantryWeaponsLevel1", 1 - TechTreeUpgradeCount(gv_p2_DOMINION_RED, "TerranInfantryWeaponsLevel1", c_techCountCompleteOnly));\n',
     '    // 0.6.29 (user 2026-11-14): mission 1 enemies get infantry armor 1 only, no weapon upgrade.\n'
     '    if (TechTreeUpgradeCount(gv_p2_DOMINION_RED, "TerranInfantryArmorsLevel1", c_techCountCompleteOnly) < 1) {\n'
     '        TechTreeUpgradeAddLevel(gv_p2_DOMINION_RED, "TerranInfantryArmorsLevel1", 1 - TechTreeUpgradeCount(gv_p2_DOMINION_RED, "TerranInfantryArmorsLevel1", c_techCountCompleteOnly));\n'),
    ('    TechTreeUpgradeAddLevel(gv_p2_DOMINION_RED, "TerranInfantryWeaponsLevel1", libNtve_gf_DifficultyValueInt(0, 0, 0, 1));\n',
     '    TechTreeUpgradeAddLevel(gv_p2_DOMINION_RED, "TerranInfantryWeaponsLevel1", libNtve_gf_DifficultyValueInt(0, 0, 0, 0));\n'),
    ('void gf_rmVHTerran (int p) {\n    gf_rmAIUp(p);\n    gf_rmVHAdd(p,"TerranInfantryWeaponsLevel");\n'
     '    gf_rmVHAdd(p,"TerranVehicleWeaponsLevel");\n    gf_rmVHAdd(p,"TerranVehicleArmorsLevel");\n',
     'void gf_rmVHTerran (int p) {\n    gf_rmAIUp(p);\n'),
]


def edit_script(m, t, lines):
    if m == 'TRaynor01':
        for a, b in M1_EDITS:
            assert t.count(a) == 1, a[:70]
            t = t.replace(a, b)
    t, n = DEALT.subn(lambda x: (f'{x.group(1)}PlayerModifyPropertyInt({x.group(2)}, c_playerPropDamageDealtPercent, c_playerPropOperSetTo, 100);\n'
                                 f'{x.group(1)}gf_rmEHStart({x.group(2)});\n'), t)
    assert n >= 1, m
    inc = list(re.finditer(r'^include "[^"]+"\n', t, re.M))
    assert inc, m
    at = inc[-1].end()
    t = t[:at] + script_block(lines) + t[at:]
    return t, n


def add_strings(path, ids):
    raw = path.read_bytes().decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in raw else '\n'
    have = {l.split('=', 1)[0] for l in raw.splitlines() if '=' in l}
    add = [f'Upgrade/Name/{i}={NAME}' for i in ids if f'Upgrade/Name/{i}' not in have]
    if add: raw = raw.rstrip('\r\n') + nl + nl.join(add) + nl
    path.write_bytes(raw.encode('utf-8'))


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            mp = root / f'{m}.SC2Map'
            gd = mp / 'base.sc2data/gamedata'
            refs = damage_refs(gd)
            lines = [l for l in LINES if refs[l]]
            up = gd / 'upgradedata.xml'
            if up.exists():
                ut = up.read_text('utf-8')
                assert ut.count('</Catalog>') == 1
                up.write_text(ut.replace('</Catalog>', upgrades_xml(refs) + '</Catalog>'), 'utf-8')
            else:
                up.write_text('<?xml version="1.0" encoding="utf-8"?>\n<Catalog>' + upgrades_xml(refs) + '</Catalog>\n', 'utf-8')
            sp = mp / 'mapscript.galaxy'
            raw = sp.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t, n = edit_script(m, raw.replace('\r\n', '\n'), lines)
            sp.write_bytes(t.replace('\n', nl).encode('utf-8'))
            ko = mp / 'kokr.sc2data/localizeddata/gamestrings.txt'
            add_strings(ko, [f'RM_EH_{l}' for l in lines])
            V35.gate('kokr', ko.read_bytes())
            for loc in V35.OTHER_LOCALES:
                (mp / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
            print(m, 'enemy players', n, {l: len(refs[l]) for l in lines})
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra: out.writestr(f, (root / f).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, 'new files:', extra)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
