#!/usr/bin/env python3
"""0.8.9 -> 0.8.10: 연구실 저그 2단계 행성 요새·화염 포탑, 기술실 동시 연구 2개 (사용자 2026-11-24
"저그 10단계가 되었어 화염포탑이랑 행성요새가 해금되어야됨", "기술실 연구 2개로 늘릴수 있니").

1. maps 3~8: 히페리온 연구실 저그 2단계(10점)는 행성 요새(ResearchZ2_1, 사령부 → 행성 요새 변신 명령)와 화염 포탑
   (ResearchZ2_2, SCV 건설 TerranBuild 19) 중 하나만 고르고, 캠페인 스크립트가 고르지 않은 쪽 명령을 막는다.
   0.8.9 강화 벙커처럼 공학 연구소 첫 화면 (1,3)에 고르지 않은 쪽 [행성 요새 연구](P) 또는 [화염 포탑 연구](T)가 나온다
   (둘 다 안 골랐으면 없음, 한 번에 하나만 보이므로 같은 칸). 1초마다 스크립트가 연구실 상태를 보고 숨은 표시 업그레이드
   RM9_CanPF / RM9_CanPerd를 한 번 준다(캠페인 데이터가 늦게 불러와져도 됨, 코덱스 검토). 연구가 끝나면 1초마다 그 명령을 허용한다(캠페인이 다시 막아도 되살림).
   모드에서 재설계한 미션 내 연구, 150/150·90초 시험값, 한 번만.
2. maps 2~8: 레이너의 병영·군수 공장·우주공항 기술실이 연구를 동시에 2개 진행한다 (원작 반응로와 같은 QueueCount +1
   숨은 행동 RM9_TechLab2, 2초마다 스크립트가 플레이어 1 기술실에만 붙임 — 적 기술실은 그대로). 시험값.
Game not run.

Usage: python3 tools/build_v0810.py <0.8.9 zip> <new output zip>
"""
import argparse, copy, re, zipfile, xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.8.9', b'version=0.8.10'
BAY = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01']
LAB2 = ['TRaynor02'] + BAY
LANGS = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
G = '.SC2Map/base.sc2data/gamedata/'
IT = {  # key: (upgrade, show-flag upgrade, research index, hotkey, icon, ko, en, abil cmd)
    'PF': ('RM9_PFUnlock', 'RM9_CanPF', 'Research23', 'P', r'Assets\Textures\btn-building-terran-planetaryfortress.dds',
           '행성 요새', 'Planetary Fortress', 'AbilityCommand("UpgradeToPlanetaryFortress", 0)', '화염 포탑'),
    'PT': ('RM9_PerdUnlock', 'RM9_CanPerd', 'Research24', 'T', r'Assets\Textures\btn-unit-terran-perditionturret.dds',
           '화염 포탑', 'Perdition Turret', 'AbilityCommand("TerranBuild", 19)', '행성 요새'),
}
EN_OTHER = {'PF': 'Perdition Turret', 'PT': 'Planetary Fortress'}
ROW, COL = 1, 3


def upg_xml():
    o = ''
    for k, (u, c, r, hk, ic, ko, en, ac, oth) in IT.items():
        o += (f'    <CUpgrade id="{u}"><Race value="Terr" /><MaxLevel value="1" /><Alert value="ResearchComplete" /><Icon value="{ic}" />'
              f'<Flags index="UpgradeCheat" value="0" /></CUpgrade>\n'
              f'    <CUpgrade id="{c}"><Race value="Terr" /><MaxLevel value="1" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>\n')
    return o


def node_xml():
    o = ''
    for k, (u, c, *_) in IT.items():
        o += (f'    <CRequirementCountUpgrade id="{u}Can"><Count Link="{c}" State="CompleteOnly" /></CRequirementCountUpgrade>\n'
              f'    <CRequirementCountUpgrade id="{u}Queued"><Count Link="{u}" State="QueuedOrBetter" /></CRequirementCountUpgrade>\n'
              f'    <CRequirementNot id="{u}NotQueued"><OperandArray index="0" value="{u}Queued" /></CRequirementNot>\n'
              f'    <CRequirementAnd id="{u}Show"><OperandArray value="{u}Can" /><OperandArray value="{u}NotQueued" /></CRequirementAnd>\n')
    return o


def req_xml():
    return ''.join(f'    <CRequirement id="{u}Learn"><NodeArray index="Show" Link="{u}Show" /><NodeArray index="Use" Link="{u}Show" /></CRequirement>\n'
                   for u, *_ in IT.values())


def btn_xml():
    return ''.join(f'    <CButton id="{u}"><Icon value="{ic}" /><Name value="Button/Name/{u}" /><Tooltip value="Button/Tooltip/{u}" />'
                   f'<TooltipFlags index="ShowLevel" value="0" /></CButton>\n' for u, c, r, hk, ic, *_ in IT.values())


BEH = ('    <CBehaviorBuff id="RM9_TechLab2"><BehaviorFlags index="Permanent" value="1" /><InfoFlags index="Hidden" value="1" />'
       '<Modification QueueCount="1" /></CBehaviorBuff>\n')

SCRIPT_BAY = '''// 0.8.10 (user 2026-11-24): lab Zerg tier 2 - research the unpicked Planetary Fortress / Perdition Turret in the Engineering Bay.
trigger gt_rm9Z2;

bool gt_rm9Z2_Func (bool testConds, bool runActions) {
    bool pf;
    bool pt;
    if (!runActions) { return true; }
    // checked every tick: campaign research state may load after map init (Codex review)
    pf = libCamp_gf_StoryResearchStateCheck(libCamp_ge_StoryResearchID_ResearchZ21PlanetaryFortress, libCamp_ge_StoryResearchState_ResearchStatePurchased);
    pt = libCamp_gf_StoryResearchStateCheck(libCamp_ge_StoryResearchID_ResearchZ22PerditionTurret, libCamp_ge_StoryResearchState_ResearchStatePurchased);
    if (pt && !pf && TechTreeUpgradeCount(1, "RM9_CanPF", c_techCountCompleteOnly) == 0) { TechTreeUpgradeAddLevel(1, "RM9_CanPF", 1); }
    if (pf && !pt && TechTreeUpgradeCount(1, "RM9_CanPerd", c_techCountCompleteOnly) == 0) { TechTreeUpgradeAddLevel(1, "RM9_CanPerd", 1); }
    if (TechTreeUpgradeCount(1, "RM9_PFUnlock", c_techCountCompleteOnly) > 0) { TechTreeAbilityAllow(1, AbilityCommand("UpgradeToPlanetaryFortress", 0), true); }
    if (TechTreeUpgradeCount(1, "RM9_PerdUnlock", c_techCountCompleteOnly) > 0) { TechTreeAbilityAllow(1, AbilityCommand("TerranBuild", 19), true); }
    return true;
}

void gf_rm9Z2Init () {
    if (gt_rm9Z2 != null) { return; }
    TechTreeAbilityAllow(1, AbilityCommand("RM3_BayResearch", 22), true);
    TechTreeAbilityAllow(1, AbilityCommand("RM3_BayResearch", 23), true);
    gt_rm9Z2 = TriggerCreate("gt_rm9Z2_Func");
    TriggerAddEventTimePeriodic(gt_rm9Z2, 1.0, c_timeGame);
}

'''

SCRIPT_LAB = '''// 0.8.10 (user 2026-11-24): Raynor's tech labs research two things at once (reactor-style QueueCount +1).
trigger gt_rm9Lab2;

bool gt_rm9Lab2_Func (bool testConds, bool runActions) {
    unitgroup g;
    unit u;
    int i;
    if (!runActions) { return true; }
    g = UnitGroup("BarracksTechLab", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0);
    UnitGroupAddUnitGroup(g, UnitGroup("FactoryTechLab", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0));
    UnitGroupAddUnitGroup(g, UnitGroup("StarportTechLab", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0));
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {
        u = UnitGroupUnit(g, i);
        if (UnitBehaviorCount(u, "RM9_TechLab2") == 0) { UnitBehaviorAdd(u, "RM9_TechLab2", u, 1); }
    }
    return true;
}

void gf_rm9Lab2Init () {
    if (gt_rm9Lab2 != null) { return; }
    gt_rm9Lab2 = TriggerCreate("gt_rm9Lab2_Func");
    TriggerAddEventTimePeriodic(gt_rm9Lab2, 2.0, c_timeGame);
}

'''


def end_insert(data, add, what):
    i = data.rindex(b'</Catalog>'); assert data[i:].strip() == b'</Catalog>', what
    return data[:i] + add.encode() + data[i:]


def strings(k):
    u, c, r, hk, ic, ko, en, ac, oth = IT[k]
    tko = f'{ko}을(를) 쓸 수 있게 됩니다. 연구실에서 {oth}을(를) 골랐을 때만 연구할 수 있습니다.'
    ten = f'Unlocks the {en}. Available only if {EN_OTHER[k]} was chosen in the lab.'
    return {f'Button/Name/{u}': (f'{ko} 연구 /// Research {en}', f'Research {en}'),
            f'Button/Tooltip/{u}': (f'{tko} /// {ten}', ten),
            f'Upgrade/Name/{u}': (f'{ko} /// {en}', en)}


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in LAB2:
            bay = m in BAY
            k = m + G + 'behaviordata.xml'; assert b'RM9_TechLab2' not in files[k]
            files[k] = end_insert(files[k], BEH, k); changed.add(k)
            k = m + '.SC2Map/mapscript.galaxy'; s = files[k]
            nl = '\r\n' if b'\r\n' in s else '\n'
            sc = SCRIPT_LAB + (SCRIPT_BAY if bay else '')
            a = b'void InitMap () {'; assert s.count(a) == 1 and b'gt_rm9Lab2' not in s, m
            s = s.replace(a, sc.replace('\n', nl).encode() + a)
            a = ('    AchievementsDisable(1);' + nl).encode(); assert s.count(a) == 1, m
            s = s.replace(a, a + ('    gf_rm9Lab2Init();' + nl + ('    gf_rm9Z2Init();' + nl if bay else '')).encode())
            files[k] = s; changed.add(k)
            if not bay: continue
            k = m + G + 'abildata.xml'; s = files[k]
            a = list(re.finditer(rb'<CAbilResearch id="RM3_BayResearch">.*?</CAbilResearch>', s, re.S))
            assert len(a) == 1 and b'"Research23"' not in a[0].group(0) and b'"Research24"' not in a[0].group(0), m
            ins = ''.join(f'        <InfoArray index="{r}" Time="90" Upgrade="{u}">\n            <Resource index="Minerals" value="150" />\n'
                          f'            <Resource index="Vespene" value="150" />\n            <Button DefaultButtonFace="{u}" State="Available" Requirements="{u}Learn" />\n'
                          f'        </InfoArray>\n' for u, c, r, *_ in IT.values()).encode() + b'    '
            j = a[0].end() - len(b'</CAbilResearch>'); files[k] = s[:j] + ins + s[j:]; changed.add(k)
            k = m + G + 'unitdata.xml'; s = files[k]
            e = list(re.finditer(rb'<CUnit id="EngineeringBay"[^>]*>.*?</CUnit>', s, re.S)); assert len(e) == 1, m
            c0 = re.search(rb'<CardLayouts index="0">(.*?)</CardLayouts>', e[0].group(0), re.S)
            assert f'Row="{ROW}" Column="{COL}"'.encode() not in c0.group(1), m
            p = e[0].start() + c0.end(1)
            files[k] = s[:p] + ''.join(f'            <LayoutButtons Face="{u}" Type="AbilCmd" AbilCmd="RM3_BayResearch,{r}" Row="{ROW}" Column="{COL}" />\n'
                                       for u, c, r, *_ in IT.values()).encode() + s[p:]; changed.add(k)
            for f, add in (('upgradedata.xml', upg_xml()), ('buttondata.xml', btn_xml()), ('requirementdata.xml', req_xml()),
                           ('requirementnodedata.xml', node_xml())):
                k = m + G + f; assert b'RM9_PFUnlock' not in files[k], k
                files[k] = end_insert(files[k], add, k); changed.add(k)
            for lang in LANGS:
                ko = lang == 'kokr'
                for fn, lines in (('gamestrings.txt', [f'{x}={v[0] if ko else v[1]}' for kk in IT for x, v in strings(kk).items()]),
                                  ('gamehotkeys.txt', [f'Button/Hotkey/{v[0]}={v[3]}' for v in IT.values()])):
                    k = f'{m}.SC2Map/{lang}.sc2data/localizeddata/{fn}'; d = files[k]
                    enl = b'\r\n' if b'\r\n' in d else b'\n'; assert b'RM9_PFUnlock' not in d, k
                    files[k] = d.rstrip(b'\r\n') + enl + enl.join(l.encode('utf-8') for l in lines) + enl; changed.add(k)
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
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
