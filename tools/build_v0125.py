#!/usr/bin/env python3
"""0.12.4 -> 0.12.5: 연구실 저그 3단계 = 열화탄 / 나노탄환 (사용자 2026-11-27).

사용자: 연구실 유닛 칸(약탈자·헤라클레스)을 업그레이드로 — "A 열화탄 보병 공격이 적에 방어력 -1(중첩3회)",
"B 나노탄환 적피해 데미지에서 10%를 회복함", "위에것들도 업그레이드로 적용되게 해야됨 … 유령 연구소나 차량연구소에서
연구 가능하게 하삼", "적용하라고". 모드에서 재설계한 캠페인 연구실 항목 (4장).

maps 3~9·11·12:
  - 히페리온에서 Z31(원작 약탈자)을 골랐거나 단계가 열렸는데 안 골라 자동 첫째(0.12.4)면 열화탄(RMZL_Shred),
    Z32(원작 헤라클레스)를 골랐으면 나노탄환(RMZL_Nano)을 켠다. 약탈자(FactoryTrain 9)·헤라클레스(StarportTrain 5)
    생산 명령은 레이너에게 막는다(1초마다, 캠페인이 다시 허용해도).
  - 고르지 않은 쪽은 0.9.7 연구실 연구(RML_Research Research10/11)를 공학 연구소 연구실 메뉴에서 빼고
    열화탄 → 유령 사관학교 (0,2) D, 나노탄환 → 무기고 (0,2) N 에서 연구 (150/150·90초 그대로, 시험값).
    연구가 끝나면 0.9.7 처리(gf_rmLabApply)가 원작 보상 대신 이 업그레이드를 켠다.
  - 열화탄: 레이너의 생체·지상 비건물 유닛이 적에게 피해를 주면 대상에 RMZL_ShredBuff(방어력 -1, 최대 3중첩, 5초 시험값).
  - 나노탄환: 레이너의 기계 비건물 유닛(차량·함선)이 적에게 준 피해의 10%만큼 자기 생명력 회복.
    (기계 칸으로 논의한 것에 맞춤 — 사용자 확인 전 시험값.)
  두 효과 모두 스크립트 피해 이벤트로 처리해 용병·원본 유닛 무기에 상관없이 닿는다.
  - 히페리온 허브(TStory01) 연구실 화면 이름·설명·확인 문구를 열화탄·나노탄환으로 (아이콘·영상은 원작 그대로 — 대화 상태
    데이터 덮어쓰기는 배열이 덧붙어 위험해 이번에 안 함).
Game not run. Codex review not run (no codex CLI in this container) — 코덱스 검토 대기.

Usage: python3 tools/build_v0125.py <0.12.4 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, LOCS

OLD, NEW = b'version=0.12.4', b'version=0.12.5'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
HUB = 'TStory01'
G = '.SC2Map/base.sc2data/gamedata/'
R = 'libCamp_ge_StoryResearchID_Research'
T = 'Assets\\Textures\\'
SHRED_ICON = T + 'btn-techupgrade-terran-u238rounds.dds'
NANO_ICON = T + 'btn-techupgrade-terran-nano-botinjectors.dds'
SHRED_DUR = '5'  # 시험값
NANO_FRAC = '0.1'  # 사용자 지정 10%

SHRED_KO = '보병 공격이 적의 방어력을 1 낮춥니다(최대 3번 중첩, 5초).'
SHRED_EN = "Infantry attacks reduce the target's armor by 1 (stacks up to 3 times, 5 seconds)."
NANO_KO = '차량·함선이 적에게 준 피해의 10%만큼 생명력을 회복합니다.'
NANO_EN = 'Vehicles and ships regain life equal to 10% of the damage they deal to enemies.'
COND_KO = ' 연구실에서 다른 쪽을 골랐거나, 단계가 열렸는데 아무것도 고르지 않아 다른 쪽이 자동 적용됐을 때 연구할 수 있습니다.'
COND_EN = ' Available if the other option was chosen in the lab, or was applied automatically because the tier is unlocked with nothing chosen.'


def strings():
    return {
        'Button/Name/RML_Z31': '열화탄 연구 /// Research Depleted Rounds',
        'Button/Tooltip/RML_Z31': f'{SHRED_KO}{COND_KO} /// {SHRED_EN}{COND_EN}',
        'Upgrade/Name/RML_Z31': '열화탄 /// Depleted Rounds',
        'Button/Name/RML_Z32': '나노탄환 연구 /// Research Nano Rounds',
        'Button/Tooltip/RML_Z32': f'{NANO_KO}{COND_KO} /// {NANO_EN}{COND_EN}',
        'Upgrade/Name/RML_Z32': '나노탄환 /// Nano Rounds',
        'Upgrade/Name/RMZL_Shred': '열화탄 /// Depleted Rounds',
        'Upgrade/Name/RMZL_Nano': '나노탄환 /// Nano Rounds',
        'Behavior/Name/RMZL_ShredBuff': '열화탄 /// Depleted Rounds',
        'Behavior/Tooltip/RMZL_ShredBuff': '방어력이 1 낮아졌습니다(최대 3번 중첩). /// Armor reduced by 1 (stacks up to 3 times).',
    }


def hub_strings():
    p = 'ConversationState/LabResearch/'
    return {
        p + 'ResearchZ3_1': '열화탄 /// Depleted Rounds',
        p + 'ResearchZ3_1/Info/Description': f'{SHRED_KO} /// {SHRED_EN}',
        p + 'ResearchZ3_1/Info/Tooltip': f'{SHRED_KO} /// {SHRED_EN}',
        p + 'ResearchZ3_1/Info/Confirmation': '열화탄을 연구하시겠습니까? 헤라클레스 자리의 나노탄환은 미션 안 무기고에서 연구해야 합니다. /// Research Depleted Rounds? Nano Rounds must then be researched in the mission at the Armory.',
        p + 'ResearchZ3_2': '나노탄환 /// Nano Rounds',
        p + 'ResearchZ3_2/Info/Description': f'{NANO_KO} /// {NANO_EN}',
        p + 'ResearchZ3_2/Info/Tooltip': f'{NANO_KO} /// {NANO_EN}',
        p + 'ResearchZ3_2/Info/Confirmation': '나노탄환을 연구하시겠습니까? 열화탄은 미션 안 유령 사관학교에서 연구해야 합니다. /// Research Nano Rounds? Depleted Rounds must then be researched in the mission at the Ghost Academy.',
    }


XML = {
    'upgradedata.xml': ('    <CUpgrade id="RMZL_Shred"><Race value="Terr" /><MaxLevel value="1" /><Icon value="%s" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>\n'
                        '    <CUpgrade id="RMZL_Nano"><Race value="Terr" /><MaxLevel value="1" /><Icon value="%s" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>\n'
                        % (SHRED_ICON, NANO_ICON)),
    'behaviordata.xml': ('    <CBehaviorBuff id="RMZL_ShredBuff">\n        <Alignment value="Negative" />\n'
                         f'        <InfoIcon value="{SHRED_ICON}" />\n        <MaxStackCount value="3" />\n        <Duration value="{SHRED_DUR}" />\n'
                         '        <Modification>\n            <LifeArmorBonus value="-1" />\n        </Modification>\n    </CBehaviorBuff>\n'),
    'unitdata.xml': ('    <CUnit id="GhostAcademy">\n        <AbilArray Link="RML_Research" />\n        <CardLayouts index="0">\n'
                     '            <LayoutButtons Face="RML_Z31" Type="AbilCmd" AbilCmd="RML_Research,Research10" Row="0" Column="2" />\n'
                     '        </CardLayouts>\n    </CUnit>\n'
                     '    <CUnit id="Armory">\n        <AbilArray Link="RML_Research" />\n        <CardLayouts index="0">\n'
                     '            <LayoutButtons Face="RML_Z32" Type="AbilCmd" AbilCmd="RML_Research,Research11" Row="0" Column="2" />\n'
                     '        </CardLayouts>\n    </CUnit>\n'),
}

SCRIPT = f'''// 0.12.5 (user 2026-11-27): lab Zerg tier 3 = Depleted Rounds (Z31 slot) / Nano Rounds (Z32 slot) instead of Predator / Hercules.
trigger gt_rmZ3Hit;

void gf_rmZ3Set (string upg) {{
    if (TechTreeUpgradeCount(1, upg, c_techCountCompleteOnly) == 0) {{ libNtve_gf_SetUpgradeLevelForPlayer(1, upg, 1); }}
}}

void gf_rmZ3Tick () {{
    // the campaign allows the Predator / Hercules for a purchased lab pick: those units are not in this mod
    TechTreeAbilityAllow(1, AbilityCommand("FactoryTrain", 9), false);
    TechTreeAbilityAllow(1, AbilityCommand("StarportTrain", 5), false);
    if (gf_rmLabBought({R}Z31Predator)) {{ gf_rmZ3Set("RMZL_Shred"); }}
    if (gf_rmLabBought({R}Z32Hercules)) {{ gf_rmZ3Set("RMZL_Nano"); }}
}}

bool gt_rmZ3Hit_Func (bool testConds, bool runActions) {{
    unit s = EventUnitDamageSourceUnit();
    unit v = EventUnit();
    string st;
    fixed amt;
    if (!runActions) {{ return true; }}
    if (s == null || v == null) {{ return true; }}
    if (UnitGetOwner(s) != 1) {{ return true; }}
    if (!UnitFilterMatch(v, 1, UnitFilter((1 << c_targetFilterEnemy), 0, 0, 0))) {{ return true; }}
    st = UnitGetType(s);
    if (UnitTypeTestAttribute(st, c_unitAttributeStructure)) {{ return true; }}
    // Depleted Rounds: infantry (biological, ground) shreds 1 armor, up to 3 stacks
    if (TechTreeUpgradeCount(1, "RMZL_Shred", c_techCountCompleteOnly) > 0 && UnitTypeTestAttribute(st, c_unitAttributeBiological)
        && !UnitTestPlane(s, c_planeAir) && UnitIsAlive(v)) {{
        UnitBehaviorAdd(v, "RMZL_ShredBuff", s, 1);
    }}
    // Nano Rounds: vehicles and ships (mechanical) regain 10% of the damage dealt
    if (TechTreeUpgradeCount(1, "RMZL_Nano", c_techCountCompleteOnly) > 0 && UnitTypeTestAttribute(st, c_unitAttributeMechanical) && UnitIsAlive(s)) {{
        amt = EventUnitDamageAmount() * {NANO_FRAC};
        if (amt > 0.0) {{ UnitSetPropertyFixed(s, c_unitPropLife, UnitGetPropertyFixed(s, c_unitPropLife, c_unitPropCurrent) + amt); }}
    }}
    return true;
}}

void gf_rmZ3Init () {{
    if (gt_rmZ3Hit != null) {{ return; }}
    gt_rmZ3Hit = TriggerCreate("gt_rmZ3Hit_Func");
    TriggerAddEventUnitDamaged(gt_rmZ3Hit, null, c_unitDamageTypeAny, c_unitDamageEither, null);
}}

'''


def patch_script(t):
    def rep(a, b):
        nonlocal t
        assert t.count(a) == 1, a[:90]
        t = t.replace(a, b)
    # new functions after the 0.12.4 helpers (gf_rmLabBought) and before gf_rmLabApply uses them
    a = '// 0.8.10 (user 2026-11-24): lab Zerg tier 2'
    rep(a, SCRIPT + a)
    # gf_rmLabApply: the Z31 / Z32 rewards become the new upgrades
    a = '    if (u1 != null && TechTreeUpgradeCount(1, u1, c_techCountCompleteOnly) == 0) { libNtve_gf_SetUpgradeLevelForPlayer(1, u1, 1); }\n'
    rep(a, f'    // 0.12.5: lab Zerg tier 3 rewards are upgrades in this mod\n'
           f'    if (id == {R}Z31Predator) {{ gf_rmZ3Set("RMZL_Shred"); return; }}\n'
           f'    if (id == {R}Z32Hercules) {{ gf_rmZ3Set("RMZL_Nano"); return; }}\n' + a)
    a = '    gf_rmLabAutoApply('
    i = t.index(a)
    t = t[:i] + '    gf_rmZ3Tick();\n' + t[i:]
    rep('    gf_rmLabInit();\n', '    gf_rmLabInit();\n    gf_rmZ3Init();\n')
    return t


def end_insert(t, add):
    k = t.rindex('</Catalog>')
    return t[:k] + add + t[k:]


def patch_bay(t, m):
    e = list(re.finditer(r'<CUnit id="EngineeringBay"[^>]*>.*?</CUnit>', t, re.S)); assert len(e) == 1, m
    body = e[0].group(0)
    n0 = len(body)
    body = re.sub(r'\s*<LayoutButtons Face="RML_Z3[12]" Type="AbilCmd" AbilCmd="RML_Research,Research1[01]"[^>]*/>', '', body)
    assert len(body) < n0 and 'RML_Z31' not in body and 'RML_Z32' not in body, m
    return t[:e[0].start()] + body + t[e[0].end():]


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
            for f, add in XML.items():
                t = files[P(f)].decode('utf-8')
                assert 'RMZL_' not in t and '<CUnit id="GhostAcademy"' not in t and '<CUnit id="Armory"' not in t, (m, f)
                if f == 'unitdata.xml': t = patch_bay(t, m)
                files[P(f)] = end_insert(t, add).encode('utf-8')
            # button icons of the relocated research
            t = files[P('buttondata.xml')].decode('utf-8')
            for b, ic in (('RML_Z31', SHRED_ICON), ('RML_Z32', NANO_ICON)):
                mm = list(re.finditer(r'<CButton id="%s">.*?</CButton>' % b, t, re.S)); assert len(mm) == 1, (m, b)
                nb = re.sub(r'<Icon value="[^"]*" />', lambda _m, ic=ic: f'<Icon value="{ic}" />', mm[0].group(0), count=1)
                t = t[:mm[0].start()] + nb + t[mm[0].end():]
            files[P('buttondata.xml')] = t.encode('utf-8')
            t = files[P('upgradedata.xml')].decode('utf-8')
            for u, ic in (('RML_Z31', SHRED_ICON), ('RML_Z32', NANO_ICON)):
                mm = list(re.finditer(r'<CUpgrade id="%s">.*?</CUpgrade>' % u, t, re.S)); assert len(mm) == 1, (m, u)
                nb = re.sub(r'<Icon value="[^"]*" />', lambda _m, ic=ic: f'<Icon value="{ic}" />', mm[0].group(0), count=1)
                t = t[:mm[0].start()] + nb + t[mm[0].end():]
            files[P('upgradedata.xml')] = t.encode('utf-8')
            for f in ('upgradedata.xml', 'behaviordata.xml', 'unitdata.xml', 'buttondata.xml'):
                E.fromstring(files[P(f)]); changed.add(P(f))
            k = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
            files[k] = patch_script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], strs); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
            for loc in LOCS:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'
                files[q] = set_lines(files[q], {'Button/Hotkey/RML_Z31': 'D', 'Button/Hotkey/RML_Z32': 'N'}); changed.add(q)
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
