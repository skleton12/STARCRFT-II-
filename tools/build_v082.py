#!/usr/bin/env python3
"""0.8.1 -> 0.8.2: 울트라 축전기·바나듐 장갑 (사용자 2026-11-23).

사용자: "플토 업글도 되있는 가정도 해야되니 ... 공격력 업글하면 공속 증가되는거랑 방어업하면 체력 늘어나는 업그레이드 그것도 넣을거지",
        "축전기-바나듐 업그레이드 공학 연구소에서 연구할수 있음? 근데 그거 하나는 이미 적용되 있어야함 그리고 저거 연구 되면
         적용되는거고 이미 예시로 1/1이라고 치면 1업했으니 그거에도 적용되는걸로".
히페리온 연구실 1단계(프로토스 연구)는 울트라 축전기(UltraCapacitors: 무기 업그레이드 단계마다 공격 속도 +5%)와
바나듐 장갑(VanadiumPlating: 장갑 업그레이드 단계마다 생명력 +5%) 중 하나를 고른다. 원작은 고른 쪽을 사면 공학 연구소·무기고의
공방업 연구가 별도 업그레이드(...UltraCapacitorsLevelN / ...VanadiumPlatingLevelN)로 바뀐다.

maps 3~8 (TRaynor03, TTychus01, TTosh01, THanson01, TTosh02, THorner01):
  1. 바뀐 업그레이드에 모드 용병이 빠져 있던 것을 채운다: 맵이 평소 공방업(TerranXWeapons/ArmorsLevelN과 부모)에 붙인 줄 중
     바뀐 업그레이드에 없는 줄(코랄의 후예·이지스·프로메테우스·죽음의 우두머리·B-2 등)을 같은 단계에 붙이고, 그 용병 무기의
     공격 속도 +5%(RateMultiplier 0.05)·유닛 생명력 ×1.05(LifeMax·LifeStart)도 원작 용병과 같은 값으로 붙인다.
  2. 공학 연구소 첫 화면: 연구실에서 바나듐 장갑을 골랐으면 [울트라 축전기](0,4, 단축키 C), 울트라 축전기를 골랐으면
     [바나듐 장갑](1,4, 단축키 V)을 연구할 수 있다 ("하나는 이미 적용돼 있어야 함"). 둘 다 안 골랐으면 버튼 없음.
     모드에서 재설계한 미션 내 연구, 150/150·90초 시험값, 한 번만.
  3. 연구가 끝나면 이미 끝낸 공방업 단계에도 거슬러 적용 (1/1이면 바로 1단계분): 1초마다 스크립트가 보병·차량·함선 줄마다
     끝낸 단계 N(평소판 또는 바뀐판)에 숨은 업그레이드 RM8_UC_<줄>N / RM8_VP_<줄>N을 한 번 준다. 숨은 업그레이드 내용은
     바뀐 업그레이드 N단계의 공격 속도·생명력 줄 그대로(원작 유닛 + 1의 용병). 원작 UltraCapacitors 업그레이드 자체는 주지
     않으므로 공학 연구소·무기고는 평소판 연구 그대로다 (단계 연구를 두 번 시키지 않음).
새 업그레이드는 모두 UpgradeCheat 0 (원작 연구실 업그레이드와 같음, 코덱스 검토). 레이너(플레이어 1) 업그레이드라 적·동맹에는 영향 없음. 한국어 이름 '울트라 축전기'·'바나듐 장갑' 공식 번역 미확인. 게임 미실행.

Usage: python3 tools/build_v082.py <0.8.1 zip> <new output zip>
"""
import argparse, copy, re, zipfile, xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.8.1', b'version=0.8.2'
MS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01']
LANGS = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
G = '.SC2Map/base.sc2data/gamedata/'
BASE = [HERE.parent / f'source/{p}/base.sc2data/gamedata/upgradedata.xml'
        for p in ('liberty.sc2mod', 'liberty.sc2campaign', 'libertystory.sc2campaign')]
LINES = ['Infantry', 'Vehicle', 'Ship']
COST, TIME = (150, 150), 90          # trial
SLOT = {'UC': (0, 4), 'VP': (1, 4)}
INFO = {'UC': 'Research27', 'VP': 'Research28'}
ICON = {'UC': r'Assets\Textures\btn-research-terran-ultracapacitors.dds', 'VP': r'Assets\Textures\btn-research-terran-vanadiumplating.dds'}
UPG = {'UC': 'RM8_UltraCap', 'VP': 'RM8_Vanadium'}
LAB = {'UC': 'UltraCapacitors', 'VP': 'VanadiumPlating'}
HOTKEY = {'UC': 'C', 'VP': 'V'}
NAME = {'UC': ('울트라 축전기', 'Ultra-Capacitors'), 'VP': ('바나듐 장갑', 'Vanadium Plating')}
TIP = {'UC': ('보병·차량·함선 무기 업그레이드 단계마다 레이너 병력의 공격 속도가 5% 빨라집니다. 이미 끝낸 단계에도 적용됩니다. 연구실에서 바나듐 장갑을 골랐을 때만 연구할 수 있습니다.',
              'Each infantry, vehicle and ship weapon upgrade level also increases the attack speed of Raynor\'s forces by 5%. Applies to levels already researched. Available only if Vanadium Plating was chosen in the lab.'),
       'VP': ('보병·차량·함선 장갑 업그레이드 단계마다 레이너 병력의 생명력이 5% 늘어납니다. 이미 끝낸 단계에도 적용됩니다. 연구실에서 울트라 축전기를 골랐을 때만 연구할 수 있습니다.',
              'Each infantry, vehicle and ship armor upgrade level also increases the life of Raynor\'s forces by 5%. Applies to levels already researched. Available only if Ultra-Capacitors was chosen in the lab.')}


def blocks(text):
    """id -> list of (attrs, body) for every CUpgrade block."""
    out = {}
    for m in re.finditer(r'<CUpgrade\b([^>]*?)(/>|>(.*?)</CUpgrade>)', text, re.S):
        i = re.search(r'\bid="([^"]+)"', m.group(1))
        if i: out.setdefault(i.group(1), []).append((m.group(1), m.group(3) or ''))
    return out


def entries(body):
    res = []
    for m in re.finditer(r'<EffectArray\b([^>]*)/>', body):
        a = dict(re.findall(r'(\w+)="([^"]*)"', m.group(1)))
        if 'Reference' in a: res.append((a.get('Operation', 'Add'), a['Reference'], a.get('Value', '')))
    return res


def effective(layers, uid):
    """Entries of an upgrade with its parent chain, across layers (later layers add)."""
    got, parent = [], None
    for lay in layers:
        for attrs, body in lay.get(uid, []):
            p = re.search(r'\bparent="([^"]+)"', attrs)
            if p: parent = p.group(1)
            got += entries(body)
    if parent: got = effective(layers, parent) + got
    return got


def own(layer, uid):
    """Entries the map itself gives an upgrade and its parent chain (map layer only)."""
    got = []
    for attrs, body in layer.get(uid, []):
        got += entries(body)
    return got


def keyset(es):
    return {(o, r) for o, r, v in es}


def xml_entry(o, r, v):
    op = '' if o == 'Add' else f'Operation="{o}" '
    return f'        <EffectArray {op}Reference="{r}" Value="{v}" />'


def plan(map_upg, base_layers):
    """Per map: lines to add to the variant upgrades, and the hidden RM8_UC/VP upgrades' content."""
    mp = blocks(map_upg)
    layers = base_layers + [mp]
    add, hidden = {}, {}
    for line in LINES:
        for n in (1, 2, 3):
            for kind, plain_p, plain, var, keep in (
                    ('UC', f'Terran{line}Weapons', f'Terran{line}WeaponsLevel{n}', f'Terran{line}WeaponsUltraCapacitorsLevel{n}', 'RateMultiplier'),
                    ('VP', f'Terran{line}Armors', f'Terran{line}ArmorsLevel{n}', f'Terran{line}ArmorsVanadiumPlatingLevel{n}', 'Life')):
                var_es = effective(layers, var)
                have = keyset(var_es)
                mod = own(mp, plain_p) + own(mp, plain)
                new = []
                for o, r, v in mod:
                    if (o, r) not in have and (o, r) not in keyset(new): new.append((o, r, v))
                # merc attack speed / life on top, same values as the original variant
                for o, r, v in mod:
                    p = r.split(',')
                    if kind == 'UC' and p[0] == 'Weapon' and p[-1] == 'Level':
                        e = ('Add', f'Weapon,{p[1]},RateMultiplier', '0.05')
                    elif kind == 'VP' and p[0] == 'Unit' and p[-1] == 'LifeArmor':
                        for f in ('LifeMax', 'LifeStart'):
                            e = ('Multiply', f'Unit,{p[1]},{f}', '1.05')
                            if (e[0], e[1]) not in have and (e[0], e[1]) not in keyset(new): new.append(e)
                        continue
                    else:
                        continue
                    if (e[0], e[1]) not in have and (e[0], e[1]) not in keyset(new): new.append(e)
                add[var] = new
                full = var_es + new
                if kind == 'UC':
                    h = [(o, r, v) for o, r, v in full if r.endswith(',RateMultiplier')]
                else:
                    h = [(o, r, v) for o, r, v in full if r.split(',')[-1] in ('LifeMax', 'LifeStart')]
                dedup, seen = [], set()
                for e in h:
                    if (e[0], e[1]) not in seen: seen.add((e[0], e[1])); dedup.append(e)
                assert dedup, (var, 'no bonus lines')
                hidden[f'RM8_{kind}_{line}{n}'] = dedup
    return add, hidden


def upg_xml(add, hidden):
    out = []
    for var, es in add.items():
        if es:
            out.append(f'    <CUpgrade id="{var}">\n' + '\n'.join(xml_entry(*e) for e in es) + '\n    </CUpgrade>')
    for k in ('UC', 'VP'):
        out.append(f'    <CUpgrade id="{UPG[k]}">\n        <Race value="Terr" />\n        <MaxLevel value="1" />\n'
                   f'        <Alert value="ResearchComplete" />\n        <Icon value="{ICON[k]}" />\n        <Flags index="UpgradeCheat" value="0" />\n    </CUpgrade>')
    for uid, es in hidden.items():
        out.append(f'    <CUpgrade id="{uid}">\n        <Race value="Terr" />\n        <MaxLevel value="1" />\n'
                   '        <EditorCategories value="Race:Terran,UpgradeType:Talents" />\n        <Flags index="UpgradeCheat" value="0" />\n'
                   + '\n'.join(xml_entry(*e) for e in es) + '\n    </CUpgrade>')
    return '\n'.join(out) + '\n'


SCRIPT = '''// 0.8.2 (user 2026-11-23): Ultra-Capacitors / Vanadium Plating researched in the Engineering Bay (RM8_UltraCap /
// RM8_Vanadium) also cover weapon/armor levels already done: each finished level N (normal or lab version) gets the
// hidden RM8_UC_<line>N / RM8_VP_<line>N once (+5% attack speed / +5% life per level). Player 1 only.
trigger gt_rm8Lab;

bool gt_rm8Lab_Func (bool testConds, bool runActions) {
    int i;
    int n;
    string l;
    string s;
    bool uc;
    bool vp;
    if (!runActions) { return true; }
    uc = TechTreeUpgradeCount(1, "RM8_UltraCap", c_techCountCompleteOnly) > 0;
    vp = TechTreeUpgradeCount(1, "RM8_Vanadium", c_techCountCompleteOnly) > 0;
    if (!uc && !vp) { return true; }
    for (i = 0; i < 3; i += 1) {
        if (i == 0) { l = "Infantry"; } else if (i == 1) { l = "Vehicle"; } else { l = "Ship"; }
        for (n = 1; n <= 3; n += 1) {
            s = IntToString(n);
            if (uc && TechTreeUpgradeCount(1, "RM8_UC_" + l + s, c_techCountCompleteOnly) == 0
                && TechTreeUpgradeCount(1, "Terran" + l + "WeaponsLevel" + s, c_techCountCompleteOnly) + TechTreeUpgradeCount(1, "Terran" + l + "WeaponsUltraCapacitorsLevel" + s, c_techCountCompleteOnly) > 0) {
                TechTreeUpgradeAddLevel(1, "RM8_UC_" + l + s, 1);
            }
            if (vp && TechTreeUpgradeCount(1, "RM8_VP_" + l + s, c_techCountCompleteOnly) == 0
                && TechTreeUpgradeCount(1, "Terran" + l + "ArmorsLevel" + s, c_techCountCompleteOnly) + TechTreeUpgradeCount(1, "Terran" + l + "ArmorsVanadiumPlatingLevel" + s, c_techCountCompleteOnly) > 0) {
                TechTreeUpgradeAddLevel(1, "RM8_VP_" + l + s, 1);
            }
        }
    }
    return true;
}

void gf_rm8LabInit () {
    if (gt_rm8Lab != null) { return; }
    gt_rm8Lab = TriggerCreate("gt_rm8Lab_Func");
    TriggerAddEventTimePeriodic(gt_rm8Lab, 1.0, c_timeGame);
}

'''


def req_xml():
    req, node = [], []
    for k, other in (('UC', 'VP'), ('VP', 'UC')):
        u = UPG[k]
        node.append(f'    <CRequirementCountUpgrade id="{u}LabOther"><Count Link="{LAB[other]}" State="CompleteOnly" /></CRequirementCountUpgrade>')
        node.append(f'    <CRequirementCountUpgrade id="{u}LabSame"><Count Link="{LAB[k]}" State="CompleteOnly" /></CRequirementCountUpgrade>')
        node.append(f'    <CRequirementCountUpgrade id="{u}Queued"><Count Link="{u}" State="QueuedOrBetter" /></CRequirementCountUpgrade>')
        node.append(f'    <CRequirementNot id="{u}NotLabSame"><OperandArray index="0" value="{u}LabSame" /></CRequirementNot>')
        node.append(f'    <CRequirementNot id="{u}NotQueued"><OperandArray index="0" value="{u}Queued" /></CRequirementNot>')
        node.append(f'    <CRequirementAnd id="{u}Show"><OperandArray value="{u}LabOther" /><OperandArray value="{u}NotLabSame" />'
                    f'<OperandArray value="{u}NotQueued" /></CRequirementAnd>')
        req.append(f'    <CRequirement id="{u}Learn"><NodeArray index="Show" Link="{u}Show" /></CRequirement>')
    return '\n'.join(req) + '\n', '\n'.join(node) + '\n'


def end_insert(data, add, what):
    i = data.rindex(b'</Catalog>')
    assert data[i:].strip() == b'</Catalog>', what
    return data[:i] + add.encode() + data[i:]


def once(data, a, b, what):
    assert data.count(a) == 1, (what, a[:70], data.count(a))
    return data.replace(a, b)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    base_layers = [blocks(p.read_text(encoding='utf-8')) for p in BASE]
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        req, node = req_xml()
        for m in MS:
            k = m + G + 'upgradedata.xml'
            assert b'RM8_' not in files[k], m
            add, hidden = plan(files[k].decode('utf-8'), base_layers)
            print(m, 'variant lines added:', sum(len(v) for v in add.values()),
                  'hidden UC/VP lines:', sum(len(v) for v in hidden.values()))
            files[k] = end_insert(files[k], upg_xml(add, hidden), m); changed.add(k)
            k = m + G + 'abildata.xml'; s = files[k]
            a = re.search(rb'<CAbilResearch id="RM3_BayResearch">.*?</CAbilResearch>', s, re.S)
            assert a and b'"Research27"' not in a.group(0) and b'"Research28"' not in a.group(0), m
            ins = ''.join(f'        <InfoArray index="{INFO[x]}" Time="{TIME}" Upgrade="{UPG[x]}">\n'
                          f'            <Resource index="Minerals" value="{COST[0]}" />\n            <Resource index="Vespene" value="{COST[1]}" />\n'
                          f'            <Button DefaultButtonFace="{UPG[x]}" State="Available" Requirements="{UPG[x]}Learn" />\n        </InfoArray>\n'
                          for x in ('UC', 'VP')).encode()
            j = a.end() - len(b'</CAbilResearch>')
            files[k] = s[:j] + ins + b'    ' + s[j:]; changed.add(k)
            k = m + G + 'unitdata.xml'; s = files[k]
            e = re.search(rb'<CUnit id="EngineeringBay"[^>]*>.*?</CUnit>', s, re.S)
            c0 = re.search(rb'<CardLayouts index="0">(.*?)</CardLayouts>', e.group(0), re.S)
            for x in ('UC', 'VP'):
                r, c = SLOT[x]
                assert f'Row="{r}" Column="{c}"'.encode() not in c0.group(1), (m, x)
            lay = ''.join(f'            <LayoutButtons Face="{UPG[x]}" Type="AbilCmd" AbilCmd="RM3_BayResearch,{INFO[x]}" Row="{SLOT[x][0]}" Column="{SLOT[x][1]}" />\n'
                          for x in ('UC', 'VP')).encode()
            p = e.start() + c0.end(1)
            files[k] = s[:p] + lay + s[p:]; changed.add(k)
            k = m + G + 'buttondata.xml'
            files[k] = end_insert(files[k], ''.join(
                f'    <CButton id="{UPG[x]}">\n        <Icon value="{ICON[x]}" />\n        <Name value="Button/Name/{UPG[x]}" />\n'
                f'        <Tooltip value="Button/Tooltip/{UPG[x]}" />\n        <TooltipFlags index="ShowLevel" value="0" />\n    </CButton>\n'
                for x in ('UC', 'VP')), m); changed.add(k)
            k = m + G + 'requirementdata.xml'; files[k] = end_insert(files[k], req, m); changed.add(k)
            k = m + G + 'requirementnodedata.xml'; files[k] = end_insert(files[k], node, m); changed.add(k)
            k = m + '.SC2Map/mapscript.galaxy'; s = files[k]
            nl = b'\r\n' if b'\r\n' in s else b'\n'
            assert b'gt_rm8Lab' not in s
            s = once(s, b'void InitMap () {', SCRIPT.replace('\n', nl.decode()).encode() + b'void InitMap () {', m)
            s = once(s, b'    AchievementsDisable(1);' + nl, b'    AchievementsDisable(1);' + nl + b'    gf_rm8LabInit();' + nl, m)
            files[k] = s; changed.add(k)
            for lang in LANGS:
                ko = lang == 'kokr'
                for fn, vals in (('gamestrings.txt', lambda x: [
                        f'Button/Name/{UPG[x]}=' + (f'{NAME[x][0]} 연구 /// Research {NAME[x][1]}' if ko else f'Research {NAME[x][1]}'),
                        f'Button/Tooltip/{UPG[x]}=' + (f'{TIP[x][0]} /// {TIP[x][1]}' if ko else TIP[x][1]),
                        f'Upgrade/Name/{UPG[x]}=' + (f'{NAME[x][0]} /// {NAME[x][1]}' if ko else NAME[x][1])]),
                                 ('gamehotkeys.txt', lambda x: [f'Button/Hotkey/{UPG[x]}={HOTKEY[x]}'])):
                    k = f'{m}.SC2Map/{lang}.sc2data/localizeddata/{fn}'
                    d = files[k]; enl = b'\r\n' if b'\r\n' in d else b'\n'
                    assert b'RM8_UltraCap' not in d, k
                    lines = [y for x in ('UC', 'VP') for y in vals(x)]
                    files[k] = d.rstrip(b'\r\n') + enl + enl.join(l.encode('utf-8') for l in lines) + enl
                    changed.add(k)
        for k in changed:
            if k.endswith('.xml'): E.fromstring(files[k])
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
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
