#!/usr/bin/env python3
"""0.12.5 -> 0.12.6: 연구실 프로토스 4단계 = 보병 공방업 4·5단계 / 무법자 장비 (사용자 2026-11-27).

사용자: 밤까마귀·과학선 칸을 업그레이드로 — "1번을 공업 5단계 2번을 더 좋은 용병 장비 뭐 이런식으로",
"유령 연구소나 차량연구소에서 연구 가능하게", "적용하라고". 모드에서 재설계한 캠페인 연구실 항목 (4장).

maps 3~9·11·12:
  - P41(원작 밤까마귀) → 보병 공방업 4·5단계 해금(RMPL_Inf45): 유령 사관학교 (1,0)에 보병 무기 4·5단계,
    (1,1)에 보병 장갑 4·5단계(3단계를 끝내면 나옴, 울트라 축전기·바나듐 장갑판 3단계도 인정; 공학 연구소 칸은 원작 버튼과 겹쳐서).
    4단계 325/325·250초, 5단계 400/400·280초 (시험값). 효과는 원작 3단계와 같은 증가량을 한 번 더
    (부모 TerranInfantryWeapons/Armors + 자날 스토리·맵 3단계의 증가 줄 복사). 울트라 축전기·바나듐 장갑의 추가 보너스와
    동맹 공방업 연동은 3단계까지 그대로(4·5단계에는 안 붙음).
  - P42(원작 과학선) → 무법자 장비(RMPL_Gear): 레이너의 생체·지상 비건물 유닛(보병 용병)에게 영구 효과
    '무법자 장비' — 최대 생명력 +20%, 주는 피해 +15% (시험값; 타이커스 협동전 무법자 장비 계열을 단순화한 모드 재설계,
    장비 하나하나 이식은 아님).
  - 골랐거나 0.12.4 자동 첫째면 켜고, 밤까마귀(StarportTrain 2)·과학선(StarportTrain 6) 생산은 막는다.
    동맹 해금표의 '과학선·밤까마귀' 칸(정화자 보전기·원시저그 관통촉수)은 이 두 업그레이드 중 하나가 있으면 열린다.
  - 고르지 않은 쪽은 공학 연구소 연구실 메뉴에서 빼고 유령 사관학교 (0,3) W(공방업 해금)·(0,4) G(무법자 장비)에서 연구
    (0.9.7 RML_Research Research5/6, 150/150·90초 그대로).
  - 히페리온 허브 연구실 화면 이름·설명·확인 문구.
Game not run. Codex review not run (no codex CLI in this container) — 코덱스 검토 대기.

Usage: python3 tools/build_v0126.py <0.12.5 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, LOCS

OLD, NEW = b'version=0.12.5', b'version=0.12.6'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
HUB = 'TStory01'
G = '.SC2Map/base.sc2data/gamedata/'
R = 'libCamp_ge_StoryResearchID_Research'
T = 'Assets\\Textures\\'
STORY_UP = ROOT / 'source/libertystory.sc2campaign/base.sc2data/gamedata/upgradedata.xml'
W_ICON = T + 'btn-upgrade-terran-infantryweaponslevel3.dds'
A_ICON = T + 'btn-upgrade-terran-infantryarmorlevel3.dds'
GEAR_ICON = T + 'btn-techupgrade-terran-combatshield-color.dds'
GEAR_LIFE, GEAR_DMG = '0.2', '0.15'  # 시험값

# key, kind(W/A), level, base, ultra/vanadium level 3, cost, time, row, col, hotkey
LV = [('W4', 'W', 4, 'TerranInfantryWeaponsLevel3', 'TerranInfantryWeaponsUltraCapacitorsLevel3', 325, 250, 1, 0, 'E'),
      ('W5', 'W', 5, None, None, 400, 280, 1, 0, 'E'),
      ('A4', 'A', 4, 'TerranInfantryArmorsLevel3', 'TerranInfantryArmorsVanadiumPlatingLevel3', 325, 250, 1, 1, 'A'),
      ('A5', 'A', 5, None, None, 400, 280, 1, 1, 'A')]

INF_KO, INF_EN = '유령 사관학교에서 보병 무기·장갑 4·5단계를 연구할 수 있습니다(3단계를 끝낸 뒤).', 'Infantry Weapons and Armor levels 4 and 5 can be researched at the Ghost Academy (after level 3).'
GEAR_KO, GEAR_EN = '보병 용병의 최대 생명력이 20%, 주는 피해가 15% 늘어납니다.', 'Infantry mercenaries gain 20% maximum life and deal 15% more damage.'
COND_KO = ' 연구실에서 다른 쪽을 골랐거나, 단계가 열렸는데 아무것도 고르지 않아 다른 쪽이 자동 적용됐을 때 연구할 수 있습니다.'
COND_EN = ' Available if the other option was chosen in the lab, or was applied automatically because the tier is unlocked with nothing chosen.'


def level3_lines(kind, map_up):
    u = 'TerranInfantryWeaponsLevel3' if kind == 'W' else 'TerranInfantryArmorsLevel3'
    out = []
    for t in (STORY_UP.read_text('utf-8'), map_up):
        for b in re.findall(r'<CUpgrade [^>]*id="%s"[^>]*>.*?</CUpgrade>' % u, t, re.S):
            for e in re.findall(r'<EffectArray [^>]*/>', b):
                if 'Operation="Set"' in e: continue
                e = re.sub(r'\s*/>$', ' />', e)
                if e not in out: out.append(e)
    assert len(out) > 10, (kind, len(out))
    return out


def xml_parts(map_up):
    up = ('    <CUpgrade id="RMPL_Inf45"><Race value="Terr" /><MaxLevel value="1" /><Icon value="%s" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>\n'
          '    <CUpgrade id="RMPL_Gear"><Race value="Terr" /><MaxLevel value="1" /><Icon value="%s" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>\n'
          % (W_ICON, GEAR_ICON))
    node = req = btn = info = lay = ''
    for i, (k, kind, lv, base, alt, cost, tm, r, c, hk) in enumerate(LV, 1):
        u = f'RMPL_Inf{k}'
        parent = 'TerranInfantryWeapons' if kind == 'W' else 'TerranInfantryArmors'
        ic = W_ICON if kind == 'W' else A_ICON
        lines = '\n'.join('        ' + e for e in level3_lines(kind, map_up))
        up += (f'    <CUpgrade id="{u}" parent="{parent}">\n        <Icon value="{ic}" />\n        <Alert value="ResearchComplete" />\n'
               f'        <Flags index="UpgradeCheat" value="0" />\n{lines}\n    </CUpgrade>\n')
        node += (f'    <CRequirementCountUpgrade id="{u}Queued"><Count Link="{u}" State="QueuedOrBetter" /></CRequirementCountUpgrade>\n'
                 f'    <CRequirementNot id="{u}NotQueued"><OperandArray index="0" value="{u}Queued" /></CRequirementNot>\n')
        if base:
            node += (f'    <CRequirementCountUpgrade id="{u}Base"><Count Link="{base}" State="CompleteOnly" /></CRequirementCountUpgrade>\n'
                     f'    <CRequirementCountUpgrade id="{u}Alt"><Count Link="{alt}" State="CompleteOnly" /></CRequirementCountUpgrade>\n'
                     f'    <CRequirementOr id="{u}Prev"><OperandArray value="{u}Base" /><OperandArray value="{u}Alt" /></CRequirementOr>\n'
                     f'    <CRequirementAnd id="{u}Show"><OperandArray value="RMPL_Inf45Have" /><OperandArray value="{u}Prev" /><OperandArray value="{u}NotQueued" /></CRequirementAnd>\n')
        else:
            prev = f'RMPL_Inf{kind}4'
            node += (f'    <CRequirementCountUpgrade id="{u}Prev"><Count Link="{prev}" State="CompleteOnly" /></CRequirementCountUpgrade>\n'
                     f'    <CRequirementAnd id="{u}Show"><OperandArray value="{u}Prev" /><OperandArray value="{u}NotQueued" /></CRequirementAnd>\n')
        req += f'    <CRequirement id="{u}Learn"><NodeArray index="Show" Link="{u}Show" /><NodeArray index="Use" Link="{u}Show" /></CRequirement>\n'
        btn += (f'    <CButton id="{u}"><Icon value="{ic}" /><Name value="Button/Name/{u}" /><Tooltip value="Button/Tooltip/{u}" />'
                f'<Hotkey value="Button/Hotkey/{u}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>\n')
        info += (f'        <InfoArray index="Research{i}" Time="{tm}" Upgrade="{u}"><Resource index="Minerals" value="{cost}" />'
                 f'<Resource index="Vespene" value="{cost}" /><Button DefaultButtonFace="{u}" State="Available" Requirements="{u}Learn" /></InfoArray>\n')
        lay += f'            <LayoutButtons Face="{u}" Type="AbilCmd" AbilCmd="RMPL_Research,Research{i}" Row="{r}" Column="{c}" />\n'
    node += '    <CRequirementCountUpgrade id="RMPL_Inf45Have"><Count Link="RMPL_Inf45" State="CompleteOnly" /></CRequirementCountUpgrade>\n'
    abil = f'    <CAbilResearch id="RMPL_Research">\n{info}    </CAbilResearch>\n'
    beh = ('    <CBehaviorBuff id="RMPL_GearBuff">\n'
           f'        <InfoIcon value="{GEAR_ICON}" />\n'
           '        <Modification>\n'
           f'            <VitalMaxFractionArray index="Life" value="{GEAR_LIFE}" />\n'
           f'            <DamageDealtFraction index="Melee" value="{GEAR_DMG}" />\n'
           f'            <DamageDealtFraction index="Ranged" value="{GEAR_DMG}" />\n'
           f'            <DamageDealtFraction index="Splash" value="{GEAR_DMG}" />\n'
           '        </Modification>\n    </CBehaviorBuff>\n')
    return up, node, req, btn, abil, lay, beh


def strings():
    d = {'Button/Name/RML_P41': '보병 공방업 4·5단계 연구 /// Research Infantry Upgrades 4-5',
         'Button/Tooltip/RML_P41': f'{INF_KO}{COND_KO} /// {INF_EN}{COND_EN}',
         'Upgrade/Name/RML_P41': '보병 공방업 4·5단계 /// Infantry Upgrades 4-5',
         'Button/Name/RML_P42': '무법자 장비 연구 /// Research Outlaw Gear',
         'Button/Tooltip/RML_P42': f'{GEAR_KO}{COND_KO} /// {GEAR_EN}{COND_EN}',
         'Upgrade/Name/RML_P42': '무법자 장비 /// Outlaw Gear',
         'Upgrade/Name/RMPL_Inf45': '보병 공방업 4·5단계 /// Infantry Upgrades 4-5',
         'Upgrade/Name/RMPL_Gear': '무법자 장비 /// Outlaw Gear',
         'Behavior/Name/RMPL_GearBuff': '무법자 장비 /// Outlaw Gear',
         'Behavior/Tooltip/RMPL_GearBuff': f'{GEAR_KO} /// {GEAR_EN}'}
    names = {'W': ('보병 무기', 'Infantry Weapons'), 'A': ('보병 장갑', 'Infantry Armor')}
    for k, kind, lv, base, alt, cost, tm, r, c, hk in LV:
        u = f'RMPL_Inf{k}'; nk, ne = names[kind]
        d[f'Button/Name/{u}'] = f'{nk} {lv}단계 연구 /// Research {ne} Level {lv}'
        d[f'Upgrade/Name/{u}'] = f'{nk} {lv}단계 /// {ne} Level {lv}'
        tk = '레이너 보병의 공격력이 3단계와 같은 만큼 더 오릅니다.' if kind == 'W' else '레이너 보병의 방어력이 3단계와 같은 만큼 더 오릅니다.'
        te = 'Raises infantry attack by the same amount as level 3 again.' if kind == 'W' else 'Raises infantry armor by the same amount as level 3 again.'
        d[f'Button/Tooltip/{u}'] = f'{tk} 연구실 보병 공방업 4·5단계가 필요합니다. /// {te} Requires the lab Infantry Upgrades 4-5.'
    return d


def hub_strings():
    p = 'ConversationState/LabResearch/'
    return {
        p + 'ResearchP4_1': '보병 공방업 4·5단계 /// Infantry Upgrades 4-5',
        p + 'ResearchP4_1/Info/Description': f'{INF_KO} /// {INF_EN}',
        p + 'ResearchP4_1/Info/Tooltip': f'{INF_KO} /// {INF_EN}',
        p + 'ResearchP4_1/Info/Confirmation': '보병 공방업 4·5단계를 연구하시겠습니까? 무법자 장비는 미션 안 유령 사관학교에서 연구해야 합니다. /// Research Infantry Upgrades 4-5? Outlaw Gear must then be researched in the mission at the Ghost Academy.',
        p + 'ResearchP4_2': '무법자 장비 /// Outlaw Gear',
        p + 'ResearchP4_2/Info/Description': f'{GEAR_KO} /// {GEAR_EN}',
        p + 'ResearchP4_2/Info/Tooltip': f'{GEAR_KO} /// {GEAR_EN}',
        p + 'ResearchP4_2/Info/Confirmation': '무법자 장비를 연구하시겠습니까? 보병 공방업 4·5단계는 미션 안 유령 사관학교에서 연구해야 합니다. /// Research Outlaw Gear? Infantry Upgrades 4-5 must then be researched in the mission at the Ghost Academy.',
    }


def patch_script(t):
    def rep(a, b):
        nonlocal t
        assert t.count(a) == 1, a[:90]
        t = t.replace(a, b)
    rep('    if (id == libCamp_ge_StoryResearchID_ResearchZ31Predator) { gf_rmZ3Set("RMZL_Shred"); return; }\n',
        f'    if (id == {R}P41Raven) {{ gf_rmZ3Set("RMPL_Inf45"); return; }}\n'
        f'    if (id == {R}P42ScienceVessel) {{ gf_rmZ3Set("RMPL_Gear"); return; }}\n'
        '    if (id == libCamp_ge_StoryResearchID_ResearchZ31Predator) { gf_rmZ3Set("RMZL_Shred"); return; }\n')
    rep('    TechTreeAbilityAllow(1, AbilityCommand("StarportTrain", 5), false);\n',
        '    TechTreeAbilityAllow(1, AbilityCommand("StarportTrain", 5), false);\n'
        '    // 0.12.6: lab Protoss tier 4 is an upgrade too (no Raven / Science Vessel)\n'
        '    TechTreeAbilityAllow(1, AbilityCommand("StarportTrain", 2), false);\n'
        '    TechTreeAbilityAllow(1, AbilityCommand("StarportTrain", 6), false);\n'
        f'    if (gf_rmLabBought({R}P41Raven)) {{ gf_rmZ3Set("RMPL_Inf45"); }}\n'
        f'    if (gf_rmLabBought({R}P42ScienceVessel)) {{ gf_rmZ3Set("RMPL_Gear"); }}\n'
        '    gf_rmGearTick();\n')
    gear = ('// 0.12.6: Outlaw Gear - permanent buff on Raynor\'s infantry (biological, ground, not structures)\n'
            'void gf_rmGearTick () {\n'
            '    unitgroup g;\n    unit u;\n    int i;\n'
            '    if (TechTreeUpgradeCount(1, "RMPL_Gear", c_techCountCompleteOnly) == 0) { return; }\n'
            '    g = UnitGroup(null, 1, RegionEntireMap(), UnitFilter((1 << c_targetFilterBiological) | (1 << c_targetFilterGround), 0, (1 << c_targetFilterStructure) | (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32))), 0);\n'
            '    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {\n'
            '        u = UnitGroupUnit(g, i);\n'
            '        if (UnitBehaviorCount(u, "RMPL_GearBuff") == 0) { UnitBehaviorAdd(u, "RMPL_GearBuff", u, 1); }\n'
            '    }\n}\n\n')
    rep('void gf_rmZ3Tick () {\n', gear + 'void gf_rmZ3Tick () {\n')
    rep('    gf_rmZ3Init();\n', '    gf_rmZ3Init();\n'
        '    TechTreeAbilityAllow(1, AbilityCommand("RMPL_Research", 0), true);\n    TechTreeAbilityAllow(1, AbilityCommand("RMPL_Research", 1), true);\n'
        '    TechTreeAbilityAllow(1, AbilityCommand("RMPL_Research", 2), true);\n    TechTreeAbilityAllow(1, AbilityCommand("RMPL_Research", 3), true);\n'
        '    TechTreeUpgradeAllow(1, "RMPL_InfW4", true);\n    TechTreeUpgradeAllow(1, "RMPL_InfW5", true);\n'
        '    TechTreeUpgradeAllow(1, "RMPL_InfA4", true);\n    TechTreeUpgradeAllow(1, "RMPL_InfA5", true);\n')
    # ally unlock table: the Science Vessel / Raven slot now follows either of the two upgrades
    # (mission 3 has no ally unlock table)
    a = 'return TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",6)) || TechTreeAbilityIsAllowed(1,AbilityCommand("StarportTrain",2));'
    assert t.count(a) <= 1
    t = t.replace(a, 'return TechTreeUpgradeCount(1,"RMPL_Inf45",c_techCountCompleteOnly) + TechTreeUpgradeCount(1,"RMPL_Gear",c_techCountCompleteOnly) > 0;')
    return t


def end_insert(t, add):
    k = t.rindex('</Catalog>')
    return t[:k] + add + t[k:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    strs = strings()
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            P = lambda f: f'{m}{G}{f}'
            map_up = files[P('upgradedata.xml')].decode('utf-8')
            up, node, req, btn, abil, lay, beh = xml_parts(map_up)
            for f, add in (('upgradedata.xml', up), ('requirementnodedata.xml', node), ('requirementdata.xml', req),
                           ('buttondata.xml', btn), ('abildata.xml', abil), ('behaviordata.xml', beh)):
                t = files[P(f)].decode('utf-8'); assert 'RMPL_' not in t, (m, f)
                files[P(f)] = end_insert(t, add).encode('utf-8'); changed.add(P(f))
            # unit cards
            t = files[P('unitdata.xml')].decode('utf-8')
            e = list(re.finditer(r'<CUnit id="EngineeringBay"[^>]*>.*?</CUnit>', t, re.S)); assert len(e) == 1, m
            body = e[0].group(0); n0 = len(body)
            body = re.sub(r'\s*<LayoutButtons Face="RML_P4[12]" Type="AbilCmd" AbilCmd="RML_Research,Research[56]"[^>]*/>', '', body)
            assert len(body) < n0 and 'RML_P41' not in body and 'RML_P42' not in body, m
            t = t[:e[0].start()] + body + t[e[0].end():]
            ga = list(re.finditer(r'<CUnit id="GhostAcademy">.*?</CUnit>', t, re.S)); assert len(ga) == 1, m
            a = '            <LayoutButtons Face="RML_Z31" Type="AbilCmd" AbilCmd="RML_Research,Research10" Row="0" Column="2" />\n'
            g = ga[0].group(0); assert g.count(a) == 1, m
            g = g.replace(a, a + '            <LayoutButtons Face="RML_P41" Type="AbilCmd" AbilCmd="RML_Research,Research5" Row="0" Column="3" />\n'
                              '            <LayoutButtons Face="RML_P42" Type="AbilCmd" AbilCmd="RML_Research,Research6" Row="0" Column="4" />\n' + lay)
            a2 = '        <AbilArray Link="RML_Research" />\n'; assert g.count(a2) == 1, m
            g = g.replace(a2, a2 + '        <AbilArray Link="RMPL_Research" />\n')
            t = t[:ga[0].start()] + g + t[ga[0].end():]
            files[P('unitdata.xml')] = t.encode('utf-8'); changed.add(P('unitdata.xml'))
            # relocated lab buttons: icons
            for f, tag in (('buttondata.xml', 'CButton'), ('upgradedata.xml', 'CUpgrade')):
                t = files[P(f)].decode('utf-8')
                for b, ic in (('RML_P41', W_ICON), ('RML_P42', GEAR_ICON)):
                    mm = list(re.finditer(r'<%s id="%s">.*?</%s>' % (tag, b, tag), t, re.S)); assert len(mm) == 1, (m, b)
                    nb = re.sub(r'<Icon value="[^"]*" />', lambda _m, ic=ic: f'<Icon value="{ic}" />', mm[0].group(0), count=1)
                    t = t[:mm[0].start()] + nb + t[mm[0].end():]
                files[P(f)] = t.encode('utf-8')
            for f in ('upgradedata.xml', 'requirementnodedata.xml', 'requirementdata.xml', 'buttondata.xml', 'abildata.xml', 'behaviordata.xml', 'unitdata.xml'):
                E.fromstring(files[P(f)])
            k = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
            files[k] = patch_script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], strs); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
            hk = {f'Button/Hotkey/RMPL_Inf{x[0]}': x[9] for x in LV}
            hk.update({'Button/Hotkey/RML_P41': 'W', 'Button/Hotkey/RML_P42': 'G'})
            for loc in LOCS:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'
                files[q] = set_lines(files[q], hk); changed.add(q)
        k = f'{HUB}.SC2Map/{KO}'
        ko = set_lines(files[k], hub_strings()); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
        for loc in V35.OTHER_LOCALES:
            q = f'{HUB}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
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
