#!/usr/bin/env python3
"""Build CCM 0.4.2 from 0.4.1: 망치 경호대(불곰) 병영 기술실 연구 (4번 TTychus01, 공통 묶음).

사용자 결정 (2026-10-18, docs/missions/nonlinear_design.md 7장): "셋 다, 단 무기고 업그레이드 제외", "충격탄 → 강화로 한 줄".
  같은 칸 한 줄: 충격탄 (자날 PunisherGrenades, 100/100·80초) → 억제탄 (협동전 NovaConcussiveShells, 100/100·60초)
  별도: 자기가속 탄약 (협동전 MarauderMagrailMunitions, 150/150·90초) — 자동 시전 보조 미사일 능력
  별도: 무력화탄 (멩스크 협동전 MarauderMengskSlow, 100/100·60초, 원래 유령 사관학교 → 기술실, 모드 변경)
효과 연결 (망치 경호대의 HammerSecuritySet):
  - 충격탄: 원래부터 PunisherGrenadesSlow가 들어 있다 (연구하면 켜짐).
  - 무력화탄: 대상 감속을 멩스크 감속으로 '바꾼다' (스위치). 충격탄 감속과 겹치지 않는다 (5장 중첩 금지).
  - 억제탄: 협동전처럼 대상 주변 반경 1의 적에게도 감속 (Marauder_BlackOpsSlowAOE).
연구 버튼은 원작 불곰이 해금됐을 때만 쓸 수 있다 (스크립트, 비선형 규칙).

Usage: python3 tools/build_v042.py <0.4.1 zip> <new output zip>
"""
import argparse
import copy
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.1', b'version=0.4.2'
M4 = 'TTychus01.SC2Map'
GD = M4 + '/base.sc2data/gamedata/'
PORT = ('MarauderMagrailMunitions', 'HaveMarauderMagrailMunitions')
DROP = r'Mastery|Prestige|Nova|Dehaka|Kerrigan|Mengsk'
# (index, upgrade, time, minerals, gas, button, icon, row, col)
RESEARCH = [
    ('Research6', 'PunisherGrenades', 80, 100, 100, 'RM4_Concussive', r'Assets\Textures\btn-ability-terran-punishergrenade-color.dds', 0, 1),
    ('Research7', 'RM4_Suppression', 60, 100, 100, 'RM4_Suppression', r'Assets\Textures\btn-ability-terran-superconcussive.dds', 0, 1),
    ('Research8', 'MarauderMagrailMunitions', 90, 150, 150, 'RM4_Magrail', r'Assets\Textures\btn-upgrade-terran-magrailmunitions.dds', 0, 2),
    ('Research9', 'RM4_Incapacitator', 60, 100, 100, 'RM4_Incapacitator', r'Assets\Textures\btn-ability-mengsk-marauder-superconcussiveshells.dds', 0, 3),
]
PREV = {'RM4_Suppression': 'PunisherGrenades'}
KO = {
    'Button/Name/RM4_Concussive': '충격탄 /// Concussive Shells',
    'Button/Tooltip/RM4_Concussive': '<c val="ffff8a">망치 경호대</c>의 공격에 맞은 적의 이동 속도가 잠시 느려집니다. /// Units hit by <c val="ffff8a">Hammer Securities</c> are briefly slowed.',
    'Button/Name/RM4_Suppression': '억제탄 /// Suppression Shells',
    'Button/Tooltip/RM4_Suppression': '충격탄을 강화합니다. <c val="ffff8a">망치 경호대</c>에게 맞은 대상 주변의 적도 느려집니다. 거대 유닛은 면역입니다. /// Improves Concussive Shells. Enemies around the target hit by <c val="ffff8a">Hammer Securities</c> are also slowed. Massive units are immune.',
    'Button/Name/RM4_Magrail': '자기가속 탄약 /// Magrail Munitions',
    'Button/Tooltip/RM4_Magrail': '<c val="ffff8a">망치 경호대</c>가 30초마다 자동으로 추가 미사일을 발사합니다. /// <c val="ffff8a">Hammer Securities</c> automatically fire an extra missile every 30 seconds.',
    'Button/Name/RM4_Incapacitator': '무력화탄 /// Incapacitator Shells',
    'Button/Tooltip/RM4_Incapacitator': '<c val="ffff8a">망치 경호대</c>의 감속이 더 강한 무력화 감속으로 바뀝니다. 충격탄 감속과 겹치지 않습니다. 거대 유닛은 면역입니다. /// <c val="ffff8a">Hammer Securities</c> apply a stronger incapacitating slow instead of the concussive slow. Massive units are immune.',
    'Upgrade/Name/PunisherGrenades': '충격탄 /// Concussive Shells',
    'Upgrade/Name/RM4_Suppression': '억제탄 /// Suppression Shells',
    'Upgrade/Name/MarauderMagrailMunitions': '자기가속 탄약 /// Magrail Munitions',
    'Upgrade/Name/RM4_Incapacitator': '무력화탄 /// Incapacitator Shells',
    'Abil/Name/MarauderMagrailMunitions': '자기가속 탄약 /// Magrail Munitions',
    'Behavior/Name/RM4_IncapSlow': '무력화탄 /// Incapacitator Shells',
    'Behavior/Tooltip/RM4_IncapSlow': '이동 속도가 느려졌습니다. /// Movement speed is reduced.',
    'Behavior/Name/MagrailStun1Sec': '기절 /// Stunned',
    'Behavior/Name/AutomatedAssimilatorBeam': '자동 융화소 광선 /// Automated Assimilator Beam',
    'Behavior/Name/HotSHunterTimedLife': '시간제 생명 /// Timed Life',
    'Unit/Name/MagrailMunitionMissile': '자기가속 탄약 미사일 /// Magrail Munitions Missile',
}
SCRIPT_OLD = '    TechTreeUnitAllow(1,"DevilDog",TechTreeUnitIsAllowed(1,"Firebat"));\n'
SCRIPT_NEW = SCRIPT_OLD + '''    // Hammer Security research needs the original Marauder unlock (nonlinear rule).
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",5),TechTreeUnitIsAllowed(1,"Marauder"));
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",6),TechTreeUnitIsAllowed(1,"Marauder"));
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",7),TechTreeUnitIsAllowed(1,"Marauder"));
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",8),TechTreeUnitIsAllowed(1,"Marauder"));
'''


def xml_edit(path, fn):
    root = E.parse(path).getroot()
    fn(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def add(root, text):
    for el in E.fromstring('<C>' + text + '</C>'):
        assert not any(e.tag == el.tag and e.get('id') == el.get('id') for e in root), el.get('id')
        root.append(el)


def edit(gd):
    def abils(root):
        a = [e for e in root if e.tag == 'CAbilResearch' and e.get('id') == 'RM3_TechResearch']
        assert len(a) == 1
        for idx, up, t, m, g, face, *_ in RESEARCH:
            a[0].append(E.fromstring(f'<InfoArray index="{idx}" Time="{t}" Upgrade="{up}"><Resource index="Minerals" value="{m}" />'
                                     f'<Resource index="Vespene" value="{g}" /><Button DefaultButtonFace="{face}" State="Available" Requirements="{face}Learn" /></InfoArray>'))
    xml_edit(gd / 'abildata.xml', abils)

    def buttons(root):
        add(root, ''.join(f'<CButton id="{face}"><Icon value="{icon}" /><Name value="Button/Name/{face}" /><Tooltip value="Button/Tooltip/{face}" />'
                          f'<TooltipFlags index="ShowLevel" value="0" /></CButton>' for _, _, _, _, _, face, icon, *_ in RESEARCH))
    xml_edit(gd / 'buttondata.xml', buttons)

    def reqs(root):
        out = ''
        for _, up, _, _, _, face, *_ in RESEARCH:
            use = f'<NodeArray index="Use" Link="RM4_{PREV[up]}Done" />' if up in PREV else ''
            out += f'<CRequirement id="{face}Learn">{use}<NodeArray index="Show" Link="{face}Show" /></CRequirement>'
        out += ''.join(f'<CRequirement id="RM4_{n}Use"><NodeArray index="Use" Link="RM4_{n}Done" /></CRequirement>' for n in ('Suppression', 'Incapacitator'))
        add(root, out)
    xml_edit(gd / 'requirementdata.xml', reqs)

    def nodes(root):
        out = ''.join(f'<CRequirementCountUpgrade id="RM4_{n}Done"><Count Link="{u}" State="CompleteOnly" /></CRequirementCountUpgrade>'
                      for n, u in (('PunisherGrenades', 'PunisherGrenades'), ('Suppression', 'RM4_Suppression'), ('Incapacitator', 'RM4_Incapacitator')))
        for _, up, _, _, _, face, *_ in RESEARCH:
            out += f'<CRequirementCountUpgrade id="{face}Queued"><Count Link="{up}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
            out += f'<CRequirementNot id="{face}NotQueued"><OperandArray value="{face}Queued" /></CRequirementNot>'
            if up in PREV:
                out += f'<CRequirementAnd id="{face}Show"><OperandArray index="0" value="RM4_{PREV[up]}Done" /><OperandArray index="1" value="{face}NotQueued" /></CRequirementAnd>'
            else:
                out += f'<CRequirementAnd id="{face}Show"><OperandArray index="0" value="{face}NotQueued" /></CRequirementAnd>'
        add(root, out)
    xml_edit(gd / 'requirementnodedata.xml', nodes)

    def effects(root):
        # Own small records instead of porting the co-op chains (those drag in Nova/Mengsk commander data).
        add(root, '<CEffectApplyBehavior id="RM4_IncapSlowAB"><ValidatorArray value="PunisherGrenadesSlowTargetFilters" />'
                  '<ValidatorArray value="NotStructure" /><ValidatorArray value="NotFrenzied" /><Behavior value="RM4_IncapSlow" /></CEffectApplyBehavior>'
                  '<CEffectSwitch id="RM4_HammerSlowSwitch"><CaseArray Validator="RM4_HaveIncapacitator" Effect="RM4_IncapSlowAB" />'
                  '<CaseDefault value="PunisherGrenadesSlow" /></CEffectSwitch>'
                  '<CEffectEnumArea id="RM4_SuppressAOE"><SearchFilters value="Ground;Player,Ally,Missile,Stasis,Dead,Hidden,Invulnerable" />'
                  '<AreaArray Radius="1" Effect="RM4_HammerSlowSwitch" /><ExcludeArray Value="Target" />'
                  '<ValidatorArray value="RM4_HaveSuppression" /></CEffectEnumArea>'
                  '<CEffectSet id="HammerSecuritySet"><EffectArray index="0" value="RM4_HammerSlowSwitch" /><EffectArray value="RM4_SuppressAOE" /></CEffectSet>')
    xml_edit(gd / 'effectdata.xml', effects)

    def behaviors(root):
        # Mengsk co-op incapacitator slow values (MarauderMengskShrapnelSlow): 3 s, move speed x0.4.
        add(root, r'<CBehaviorBuff id="RM4_IncapSlow"><Alignment value="Negative" /><Duration value="3" />'
                  r'<Modification MoveSpeedMultiplier="0.4" /><InfoIcon value="Assets\Textures\btn-ability-mengsk-marauder-superconcussiveshells.dds" />'
                  r'<Name value="Behavior/Name/RM4_IncapSlow" /><Tooltip value="Behavior/Tooltip/RM4_IncapSlow" /></CBehaviorBuff>')
    xml_edit(gd / 'behaviordata.xml', behaviors)

    def upgrades(root):
        add(root, ''.join(f'<CUpgrade id="{u}"><Race value="Terr" /><Alert value="ResearchComplete" /><Icon value="{icon}" /></CUpgrade>'
                          for _, u, _, _, _, _, icon, *_ in RESEARCH if u.startswith('RM4_')))
    xml_edit(gd / 'upgradedata.xml', upgrades)

    def validators(root):
        add(root, ''.join(f'<CValidatorPlayerRequirement id="RM4_Have{n}"><Value value="RM4_{n}Use" /></CValidatorPlayerRequirement>'
                          for n in ('Suppression', 'Incapacitator')))
    xml_edit(gd / 'validatordata.xml', validators)

    def units(root):
        lab = [e for e in root if e.tag == 'CUnit' and e.get('id') == 'BarracksTechLab'][-1].find('CardLayouts')
        for idx, _, _, _, _, face, _, row, col in RESEARCH:
            lab.append(E.fromstring(f'<LayoutButtons Face="{face}" Type="AbilCmd" AbilCmd="RM3_TechResearch,{idx}" Row="{row}" Column="{col}" />'))
        assert not any(e.tag == 'CUnit' and e.get('id') == 'HammerSecurity' for e in root)
        add(root, '<CUnit id="HammerSecurity"><AbilArray Link="MarauderMagrailMunitions" /><CardLayouts index="0">'
                  '<LayoutButtons Face="MarauderMagrailMunitions" Type="AbilCmd" AbilCmd="MarauderMagrailMunitions,Execute" Row="2" Column="2" />'
                  '</CardLayouts></CUnit>')
    xml_edit(gd / 'unitdata.xml', units)


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(root / M4), '--liberty-base', 
                        '--skip-existing', f'--drop={DROP}', *PORT], check=True)
        (root / M4 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        edit(root / GD)
        sp = root / M4 / 'mapscript.galaxy'
        t = sp.read_bytes().decode('utf-8')
        assert t.count(SCRIPT_OLD) == 1
        sp.write_bytes(t.replace(SCRIPT_OLD, SCRIPT_NEW).encode('utf-8'))
        ko = root / M4 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        text = ko.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        lines, done = text.split(nl), set()
        for i, line in enumerate(lines):
            k = line.split('=', 1)[0]
            if k in KO: lines[i] = f'{k}={KO[k]}'; done.add(k)
        while lines and lines[-1] == '': lines.pop()
        lines += [f'{k}={v}' for k, v in KO.items() if k not in done] + ['']
        ko.write_bytes(nl.join(lines).encode('utf-8'))
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])  # ported strings get their English half
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (root / M4 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra: out.writestr(f, (root / f).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if not n.startswith(M4 + '/') and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, 'new files:', extra)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
