#!/usr/bin/env python3
"""0.9.6 -> 0.9.7 (사용자 2026-11-24 "플토 저그 연구 해금되면 걍 자동으로 선택한거 제외 업그레이드 나오게").

3~9번: 히페리온 연구실(프로토스·저그)에서 둘 중 하나를 고르면, 고르지 않은 쪽을 공학 연구소에서 연구할 수 있다.
이미 만든 것(0.8.2 울트라 축전기·바나듐 장갑, 0.8.9 강화 벙커, 0.8.10 행성 요새·화염 포탑)은 그대로 두고 나머지 15개:
P2 궤도 보급고·미세 여과, P3 자동 정제소·사령부 반응로, P4 밤까마귀·과학선, P5 기술 반응로·궤도 폭격,
Z1 까치날개 포탑(강화 벙커를 골랐을 때), Z3 약탈자·헤라클레스, Z4 세포 반응로·재생성 생체강철, Z5 군락 정신 모방기·사이오닉 방해기.
- 공학 연구소 첫 화면 (0,3)(3번은 (1,2))의 [연구실 연구](L) 하위 메뉴 RML1에 단계마다 한 칸(짝 중 고르지 않은 쪽만 보임).
- 새 연구 능력 RML_Research(공학 연구소 AbilArray에 추가), 150/150·90초 시험값, 한 번만. 표시 조건은 0.8.10과 같은 방식.
- 1초마다 스크립트: 연구실 상태를 보고 표시 업그레이드 RML_Can<k>를 주고, 연구를 끝낸 항목은 캠페인과 똑같이 그 연구의
  보상(캠페인 대화 상태 'LabResearch'의 Upgrade 1·2, Ability Command 1·2)을 플레이어 1에게 적용한다(명령 허용은 매초 되살림).
  적용 중에는 매초 캠페인 애드온 갱신(libCamp_gf_TS_UpdateTechAddons)도 부른다(기술 반응로, 캠페인 갱신 뒤 복구).
  세포 반응로는 처음 적용할 때 캠페인처럼 이미 있는 유닛 에너지 +100.
  알려진 한계(연구실에서 직접 골라도 같은 원작 한계): 자동 정제소는 풍부한 정제소엔 안 붙고, 세포 반응로 원작 업그레이드는 용병 의무관이 아닌 Medic 대상.
모드에서 재설계한 미션 내 연구. 한국어 이름 공식 번역 미확인. Game not run.

Usage: python3 tools/build_v097.py <0.9.6 zip> <new output zip>
"""
import argparse, copy, re, zipfile, xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.9.6', b'version=0.9.7'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02']
LANGS = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
G = '.SC2Map/base.sc2data/gamedata/'
T = 'Assets\\Textures\\'
# key, research id const, partner id const, row, col, hotkey, icon, ko, en, ko desc, en desc
ITEMS = [
    ('P21', 'ResearchP21OrbitalDepots', 'ResearchP22MicroFiltering', 0, 0, 'D', 'btn-research-terran-orbitaldepots.dds', '궤도 보급고', 'Orbital Depots', '보급고를 즉시 지을 수 있습니다.', 'Supply Depots can be built instantaneously.'),
    ('P22', 'ResearchP22MicroFiltering', 'ResearchP21OrbitalDepots', 0, 0, 'D', 'btn-research-terran-microfiltering.dds', '미세 여과', 'Micro-Filtering', '정제소와 자동 정제소의 가스 채취가 25% 빨라집니다.', 'Refineries and Automated Refineries produce vespene gas 25% faster.'),
    ('P31', 'ResearchP31AutomatedRefinery', 'ResearchP32CommandCenterReactor', 0, 1, 'R', 'btn-research-terran-automatedrefinery.dds', '자동 정제소', 'Automated Refinery', '정제소가 SCV 없이 가스를 채취합니다.', 'Refinery no longer requires SCVs to harvest vespene gas.'),
    ('P32', 'ResearchP32CommandCenterReactor', 'ResearchP31AutomatedRefinery', 0, 1, 'R', 'btn-research-terran-commandcenterreactor.dds', '사령부 반응로', 'Command Center Reactor', 'SCV 두 기를 동시에 훈련합니다.', 'Allows two SCVs to be trained simultaneously.'),
    ('P41', 'ResearchP41Raven', 'ResearchP42ScienceVessel', 0, 2, 'V', 'btn-research-terran-raven.dds', '밤까마귀', 'Raven', '지원 유닛 밤까마귀를 생산할 수 있습니다.', 'Allows the Raven support unit.'),
    ('P42', 'ResearchP42ScienceVessel', 'ResearchP41Raven', 0, 2, 'V', 'btn-research-terran-sciencevessel.dds', '과학선', 'Science Vessel', '지원 유닛 과학선을 생산할 수 있습니다.', 'Allows the Science Vessel support unit.'),
    ('P51', 'ResearchP51TechReactor', 'ResearchP52OrbitalStrike', 0, 3, 'S', 'btn-research-terran-techreactor.dds', '기술 반응로', 'Tech Reactor', '기술실과 반응로 기능을 함께 가진 부착물을 씁니다.', 'Combines the functionality of a Tech Lab and a Reactor in a single add-on.'),
    ('P52', 'ResearchP52OrbitalStrike', 'ResearchP51TechReactor', 0, 3, 'S', 'btn-research-terran-orbitalstrikerally.dds', '궤도 폭격', 'Orbital Strike', '병영 유닛이 투하 캡슐로 병영 집결지에 내려옵니다.', "Barracks units arrive by Drop-Pod at the Barracks' rally point."),
    ('Z11', 'ResearchZ11ShrikeTurret', 'ResearchZ12FortifiedBunker', 1, 0, 'T', 'btn-research-zerg-shriketurret.dds', '까치날개 포탑', 'Shrike Turret', '모든 벙커에 자동 포탑이 달립니다.', 'Outfits all Bunkers with an automated turret.'),
    ('Z31', 'ResearchZ31Predator', 'ResearchZ32Hercules', 1, 1, 'P', 'btn-research-zerg-predator.dds', '약탈자', 'Predator', '대보병 특화 유닛 약탈자를 생산할 수 있습니다.', 'Allows the Predator anti-infantry unit.'),
    ('Z32', 'ResearchZ32Hercules', 'ResearchZ31Predator', 1, 1, 'P', 'btn-research-zerg-hercules.dds', '헤라클레스', 'Hercules', '대형 수송선 헤라클레스를 생산할 수 있습니다.', 'Allows the Hercules transport.'),
    ('Z41', 'ResearchZ41CellularReactors', 'ResearchZ42RegenerativeBioSteel', 1, 2, 'C', 'btn-research-zerg-cellularreactor.dds', '세포 반응로', 'Cellular Reactor', '특수 유닛의 시작·최대 에너지가 100 늘어납니다.', 'Specialist units gain +100 starting energy and +100 maximum energy.'),
    ('Z42', 'ResearchZ42RegenerativeBioSteel', 'ResearchZ41CellularReactors', 1, 2, 'C', 'btn-research-zerg-regenerativebio-steel.dds', '재생성 생체강철', 'Regenerative Bio-Steel', '함선과 차량이 생명력을 천천히 회복합니다.', 'Ships and vehicles slowly regenerate life.'),
    ('Z51', 'ResearchZ51HiveMindEmulator', 'ResearchZ52SigmaProjector', 1, 3, 'H', 'btn-research-zerg-hivemindemulator.dds', '군락 정신 모방기', 'Hive Mind Emulator', '저그 유닛을 영구히 정신 지배하는 방어 건물을 지을 수 있습니다.', 'Allows a defensive structure that permanently Mind Controls Zerg units.'),
    ('Z52', 'ResearchZ52SigmaProjector', 'ResearchZ51HiveMindEmulator', 1, 3, 'H', 'btn-research-zerg-psidisruptor.dds', '사이오닉 방해기', 'Psi Disrupter', '주변 저그 유닛을 느리게 하는 방어 건물을 지을 수 있습니다.', 'Allows a defensive structure that slows all nearby Zerg units.'),
]
MENU = 'RML_Menu'
# 3번은 (0,3)에 멩스크 조준 지원 총안이 있어 원작 건물 장갑 칸(캠페인에서 숨김)을 쓴다 — 게임 확인 필요
MENU_CELL = {'TRaynor03': (1, 2)}


def xml_parts():
    up = node = req = btn = info = lay = ''
    for i, (k, rid, pid, r, c, hk, ic, ko, en, dko, den) in enumerate(ITEMS, 1):
        u, can = f'RML_{k}', f'RML_Can{k}'
        up += (f'    <CUpgrade id="{u}"><Race value="Terr" /><MaxLevel value="1" /><Alert value="ResearchComplete" /><Icon value="{T}{ic}" />'
               f'<Flags index="UpgradeCheat" value="0" /></CUpgrade>\n'
               f'    <CUpgrade id="{can}"><Race value="Terr" /><MaxLevel value="1" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>\n')
        node += (f'    <CRequirementCountUpgrade id="{u}Can"><Count Link="{can}" State="CompleteOnly" /></CRequirementCountUpgrade>\n'
                 f'    <CRequirementCountUpgrade id="{u}Queued"><Count Link="{u}" State="QueuedOrBetter" /></CRequirementCountUpgrade>\n'
                 f'    <CRequirementNot id="{u}NotQueued"><OperandArray index="0" value="{u}Queued" /></CRequirementNot>\n'
                 f'    <CRequirementAnd id="{u}Show"><OperandArray value="{u}Can" /><OperandArray value="{u}NotQueued" /></CRequirementAnd>\n')
        req += f'    <CRequirement id="{u}Learn"><NodeArray index="Show" Link="{u}Show" /><NodeArray index="Use" Link="{u}Show" /></CRequirement>\n'
        btn += (f'    <CButton id="{u}"><Icon value="{T}{ic}" /><Name value="Button/Name/{u}" /><Tooltip value="Button/Tooltip/{u}" />'
                f'<Hotkey value="Button/Hotkey/{u}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>\n')
        info += (f'        <InfoArray index="Research{i}" Time="90" Upgrade="{u}"><Resource index="Minerals" value="150" />'
                 f'<Resource index="Vespene" value="150" /><Button DefaultButtonFace="{u}" State="Available" Requirements="{u}Learn" /></InfoArray>\n')
        lay += f'            <LayoutButtons Face="{u}" Type="AbilCmd" AbilCmd="RML_Research,Research{i}" Row="{r}" Column="{c}" />\n'
    btn += (f'    <CButton id="{MENU}"><Icon value="{T}btn-research-terran-techreactor.dds" /><Name value="Button/Name/{MENU}" />'
            f'<Tooltip value="Button/Tooltip/{MENU}" /><Hotkey value="Button/Hotkey/{MENU}" /></CButton>\n')
    abil = f'    <CAbilResearch id="RML_Research">\n{info}    </CAbilResearch>\n'
    page = f'        <CardLayouts CardId="RML1">\n{lay}            <LayoutButtons Face="Cancel" Type="CancelSubmenu" Row="2" Column="4" />\n        </CardLayouts>\n'
    return up, node, req, btn, abil, page


def script():
    s = ['// 0.9.7 (user 2026-11-24): research the lab option you did NOT pick in the Engineering Bay (Lab Research page).',
         'trigger gt_rmLab;', 'bool gv_rmLabDone[16];', '',
         'void gf_rmLabApply (int id, int n) {',
         '    string u1 = libCamp_gf_TS_StoryResearchRewardUpgrade1(id);',
         '    string u2 = libCamp_gf_TS_StoryResearchRewardUpgrade2(id);',
         '    abilcmd a1 = libCamp_gf_TS_StoryResearchRewardAC1(id);',
         '    abilcmd a2 = libCamp_gf_TS_StoryResearchRewardAC2(id);',
         '    unitgroup g;',
         '    unit u;',
         '    int i;',
         '    if (u1 != null && TechTreeUpgradeCount(1, u1, c_techCountCompleteOnly) == 0) { libNtve_gf_SetUpgradeLevelForPlayer(1, u1, 1); }',
         '    if (u2 != null && TechTreeUpgradeCount(1, u2, c_techCountCompleteOnly) == 0) { libNtve_gf_SetUpgradeLevelForPlayer(1, u2, 1); }',
         '    if (a1 != null) { TechTreeAbilityAllow(1, a1, true); }',
         '    if (a2 != null) { TechTreeAbilityAllow(1, a2, true); }',
         '    // campaign add-on permissions are recomputed every tick: a campaign refresh may have cleared them (Codex review)',
         '    libCamp_gf_TS_UpdateTechAddons(1);',
         '    if (!gv_rmLabDone[n]) {',
         '        gv_rmLabDone[n] = true;',
         '        // Cellular Reactor: like the campaign, +100 current energy for units that already exist',
         '        if (id == libCamp_ge_StoryResearchID_ResearchZ41CellularReactors) {',
         '            g = UnitGroup(null, 1, RegionEntireMap(), UnitFilter(0, 0, (1 << c_targetFilterStructure) | (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32))), 0);',
         '            for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) { u = UnitGroupUnit(g, i); UnitSetPropertyFixed(u, c_unitPropEnergy, UnitGetPropertyFixed(u, c_unitPropEnergy, c_unitPropCurrent) + 100.0); }',
         '        }',
         '    }',
         '}', '',
         'void gf_rmLabOne (int id, int other, string can, string upg, int n) {',
         '    // checked every tick: campaign research state may load after map init',
         '    if (libCamp_gf_StoryResearchStateCheck(other, libCamp_ge_StoryResearchState_ResearchStatePurchased)',
         '        && !libCamp_gf_StoryResearchStateCheck(id, libCamp_ge_StoryResearchState_ResearchStatePurchased)',
         '        && TechTreeUpgradeCount(1, can, c_techCountCompleteOnly) == 0) { TechTreeUpgradeAddLevel(1, can, 1); }',
         '    if (TechTreeUpgradeCount(1, upg, c_techCountCompleteOnly) > 0) { gf_rmLabApply(id, n); }',
         '}', '',
         'bool gt_rmLab_Func (bool testConds, bool runActions) {',
         '    if (!runActions) { return true; }']
    for i, (k, rid, pid, *_r) in enumerate(ITEMS, 1):
        s.append(f'    gf_rmLabOne(libCamp_ge_StoryResearchID_{rid}, libCamp_ge_StoryResearchID_{pid}, "RML_Can{k}", "RML_{k}", {i});')
    s += ['    return true;', '}', '', 'void gf_rmLabInit () {', '    int i;', '    if (gt_rmLab != null) { return; }',
          f'    for (i = 1; i <= {len(ITEMS)}; i += 1) {{ TechTreeAbilityAllow(1, AbilityCommand("RML_Research", i - 1), true); }}',
          '    gt_rmLab = TriggerCreate("gt_rmLab_Func");', '    TriggerAddEventTimePeriodic(gt_rmLab, 1.0, c_timeGame);', '}', '', '']
    return '\n'.join(s)


def strings():
    d = {f'Button/Name/{MENU}': ('연구실 연구 /// Lab Research', 'Lab Research'),
         f'Button/Tooltip/{MENU}': ('히페리온 연구실에서 고르지 않은 쪽 기술을 연구합니다. /// Research the lab option you did not choose on the Hyperion.',
                                    'Research the lab option you did not choose on the Hyperion.')}
    for k, rid, pid, r, c, hk, ic, ko, en, dko, den in ITEMS:
        u = f'RML_{k}'
        tko = f'{dko} 연구실에서 다른 쪽을 골랐을 때만 연구할 수 있습니다.'
        ten = f'{den} Available only if the other option was chosen in the lab.'
        d[f'Button/Name/{u}'] = (f'{ko} 연구 /// Research {en}', f'Research {en}')
        d[f'Button/Tooltip/{u}'] = (f'{tko} /// {ten}', ten)
        d[f'Upgrade/Name/{u}'] = (f'{ko} /// {en}', en)
    return d


def end_insert(data, add, what):
    i = data.rindex(b'</Catalog>'); assert data[i:].strip() == b'</Catalog>', what
    return data[:i] + add.encode() + data[i:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    up, node, req, btn, abil, page = xml_parts()
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            k = m + '.SC2Map/mapscript.galaxy'; s = files[k]
            nl = '\r\n' if b'\r\n' in s else '\n'
            a = b'void InitMap () {'; assert s.count(a) == 1 and b'gt_rmLab' not in s, m
            s = s.replace(a, script().replace('\n', nl).encode() + a)
            a = ('    AchievementsDisable(1);' + nl).encode(); assert s.count(a) == 1, m
            files[k] = s.replace(a, a + ('    gf_rmLabInit();' + nl).encode()); changed.add(k)
            k = m + G + 'unitdata.xml'; s = files[k]
            e = list(re.finditer(rb'<CUnit id="EngineeringBay"[^>]*>.*?</CUnit>', s, re.S)); assert len(e) == 1, m
            body = e[0].group(0)
            c0 = re.search(rb'<CardLayouts index="0">(.*?)</CardLayouts>', body, re.S)
            mr, mc = MENU_CELL.get(m, (0, 3))
            assert f'Row="{mr}" Column="{mc}"'.encode() not in c0.group(1) and b'RML1' not in body, m
            body2 = (body[:c0.end(1)] + f'            <LayoutButtons Face="{MENU}" Type="Submenu" SubmenuCardId="RML1" Row="{mr}" Column="{mc}" />\n'.encode()
                     + body[c0.end(1):c0.end()] + b'\n' + page.encode() + body[c0.end():])
            ab = re.search(rb'<AbilArray Link="RM3_BayResearch" ?/>', body2); assert ab, m
            body2 = body2[:ab.end()] + b'\n        <AbilArray Link="RML_Research" />' + body2[ab.end():]
            files[k] = s[:e[0].start()] + body2 + s[e[0].end():]; changed.add(k)
            for f, add in (('upgradedata.xml', up), ('buttondata.xml', btn), ('requirementdata.xml', req),
                           ('requirementnodedata.xml', node), ('abildata.xml', abil)):
                k = m + G + f; assert b'RML_' not in files[k], k
                files[k] = end_insert(files[k], add, k); changed.add(k)
            st = strings()
            hot = [f'Button/Hotkey/RML_{x[0]}={x[5]}' for x in ITEMS] + [f'Button/Hotkey/{MENU}=L']
            for lang in LANGS:
                ko = lang == 'kokr'
                for fn, lines in (('gamestrings.txt', [f'{x}={v[0] if ko else v[1]}' for x, v in st.items()]), ('gamehotkeys.txt', hot)):
                    k = f'{m}.SC2Map/{lang}.sc2data/localizeddata/{fn}'; d = files[k]
                    enl = b'\r\n' if b'\r\n' in d else b'\n'; assert b'RML_' not in d, k
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
    print(out, len(changed))


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
