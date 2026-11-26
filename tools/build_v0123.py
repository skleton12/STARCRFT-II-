#!/usr/bin/env python3
"""0.12.2 -> 0.12.3: 토르 무기고 연구를 군수 공장 기술실에서 (사용자 2026-11-26 "토르 연구도 있는거지").

규칙(4장 "무기고에서 안 산 기술은 미션 안에서 연구"), 0.9.2 벌처와 같은 방식. maps 4~9·11·12:
  - 330mm 탄막포(330mmBarrageCannons, 원작: 토르 330mm 탄막포 능력) (2,2) 단축키 B — 연구가 끝나면 능력 명령을 허용
  - 불멸 프로토콜(MechanicalRebirth, 원작: 파괴된 토르를 전장에서 다시 가동) (1,4) 단축키 I
  군수 공장 기술실·기술 반응로, FactoryTechLabResearch Research12/13, 100/100·60초(시험값). 원작 업그레이드라 히페리온에서
  샀으면 숨는다. 토르 해금(FactoryTrain 4 또는 토르 보유) 뒤에만 보인다(RMA_ThorUnlocked, 1초마다 확인 — 코랄은 임무 중 해금).
  토르는 용병판이 없어 원본. 첫 정의 안에 합친다. 한국어 이름 공식 번역 미확인. Game not run.

Usage: python3 tools/build_v0123.py <0.12.2 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD, LOCS

OLD, NEW = b'version=0.12.2', b'version=0.12.3'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
NOTE = (' 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다.', ' Researched in the mission when not bought at the Hyperion Armory.')
COST = '<Resource index="Minerals" value="100" /><Resource index="Vespene" value="100" />'
ITEMS = [
    ('RMA_Barrage', '330mmBarrageCannons', 12, 2, 2, 'B', 'Assets\\Textures\\btn-techupgrade-terran-330mmbarragecannon.dds',
     ('330mm 탄막포', '330mm Barrage Cannon'), ('토르가 330mm 탄막포 능력을 얻습니다. 지정한 지역에 강력한 포격을 퍼붓습니다.' + NOTE[0],
                                          'Thors gain the 330mm Barrage Cannon ability, bombarding a target area.' + NOTE[1])),
    ('RMA_Immortal', 'MechanicalRebirth', 13, 1, 4, 'I', 'Assets\\Textures\\btn-techupgrade-terran-immortalityprotocol.dds',
     ('불멸 프로토콜', 'Immortality Protocol'), ('파괴된 토르를 전장에서 다시 가동할 수 있습니다.' + NOTE[0],
                                              'Destroyed Thors can be rebuilt in the field.' + NOTE[1])),
]


def first(t, tag, i):
    m = list(re.finditer(r'<%s id="%s"[^>]*>.*?</%s>' % (tag, i, tag), t, re.S))
    assert len(m) == 1, (tag, i, len(m))
    return m[0]


def end_insert(t, add):
    k = t.rindex('</Catalog>')
    return t[:k] + add + t[k:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    strs, hk = {}, {}
    btn = abil = card = req = node = ''
    for bid, upg, n, r, c, key, icon, (nk, ne), (tk, te) in ITEMS:
        btn += (f'<CButton id="{bid}"><Icon value="{icon}" /><Name value="Button/Name/{bid}" /><Tooltip value="Button/Tooltip/{bid}" />'
                f'<Hotkey value="Button/Hotkey/{bid}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>')
        abil += (f'<InfoArray index="Research{n}" Time="60" Upgrade="{upg}">{COST}<Button DefaultButtonFace="{bid}" State="Available" '
                 f'Requirements="{bid}Learn" /></InfoArray>')
        card += f'<LayoutButtons Face="{bid}" Type="AbilCmd" AbilCmd="FactoryTechLabResearch,Research{n}" Row="{r}" Column="{c}" />'
        req += f'<CRequirement id="{bid}Learn"><NodeArray index="Show" Link="{bid}Show" /><NodeArray index="Use" Link="{bid}Show" /></CRequirement>'
        node += (f'<CRequirementCountUpgrade id="{bid}Queued"><Count Link="{upg}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
                 f'<CRequirementNot id="{bid}NotQueued"><OperandArray index="0" value="{bid}Queued" /></CRequirementNot>'
                 f'<CRequirementAnd id="{bid}Show"><OperandArray value="{bid}NotQueued" /><OperandArray value="RMA_ThorGate" /></CRequirementAnd>')
        strs[f'Button/Name/{bid}'] = f'{nk} 연구 /// Research {ne}'
        strs[f'Button/Tooltip/{bid}'] = f'{tk} /// {te}'
        hk[bid] = key
    node += '<CRequirementCountUpgrade id="RMA_ThorGate"><Count Link="RMA_ThorUnlocked" State="CompleteOnly" /></CRequirementCountUpgrade>'
    upg_xml = '<CUpgrade id="RMA_ThorUnlocked"><Race value="Terr" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>'
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            P = lambda f: f'{m}.SC2Map/{GD}{f}'
            # unit cards: into the first CardLayouts of the one definition
            t = files[P('unitdata.xml')].decode('utf-8')
            for u in ('FactoryTechLab', 'FactoryTechReactor'):
                b = first(t, 'CUnit', u)
                c0 = re.search(r'<CardLayouts index="0">(.*?)</CardLayouts>', b.group(0), re.S)
                assert 'Row="2" Column="2"' not in c0.group(1) and 'Row="1" Column="4"' not in c0.group(1), (m, u)
                p = b.start() + c0.end(1); t = t[:p] + card + t[p:]
            files[P('unitdata.xml')] = t.encode('utf-8')
            t = files[P('abildata.xml')].decode('utf-8')
            b = first(t, 'CAbilResearch', 'FactoryTechLabResearch')
            assert 'index="Research12"' not in b.group(0) and 'index="Research13"' not in b.group(0), m
            p = b.end() - len('</CAbilResearch>'); files[P('abildata.xml')] = (t[:p] + abil + t[p:]).encode('utf-8')
            for f, x in (('buttondata.xml', btn), ('requirementdata.xml', req), ('requirementnodedata.xml', node), ('upgradedata.xml', upg_xml)):
                t = files[P(f)].decode('utf-8'); assert 'RMA_Barrage' not in t and 'RMA_ThorUnlocked' not in t, (m, f)
                files[P(f)] = end_insert(t, x).encode('utf-8')
            for f in ('unitdata.xml', 'abildata.xml', 'buttondata.xml', 'requirementdata.xml', 'requirementnodedata.xml', 'upgradedata.xml'):
                E.fromstring(files[P(f)]); changed.add(P(f))
            k = f'{m}.SC2Map/mapscript.galaxy'; t = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
            a = '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",10),true);\n'
            assert t.count(a) == 1, m
            t = t.replace(a, a + (
                '    // 0.12.3: Thor armory tech not bought at the Hyperion (user 2026-11-26).\n'
                '    TechTreeUpgradeAllow(1,"RMA_ThorUnlocked",true);\n'
                '    if (TechTreeUpgradeCount(1,"RMA_ThorUnlocked",c_techCountQueuedOrBetter)==0 && TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",4))) {\n'
                '        TechTreeUpgradeAddLevel(1,"RMA_ThorUnlocked",1);\n    }\n'
                '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",11),true);\n'
                '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",12),true);\n'
                '    TechTreeUpgradeAllow(1,"330mmBarrageCannons",true);\n    TechTreeUpgradeAllow(1,"MechanicalRebirth",true);\n'))
            # Replenishable Magazine: the original armory purchase allows the mine-making command; do the same once researched.
            sc = ('// 0.12.3: 330mm Barrage Cannon researched in the mission allows the Thor ability command (as the armory purchase).\n'
                  'trigger gt_rm12Thor;\n\n'
                  'bool gt_rm12Thor_Func (bool testConds, bool runActions) {\n'
                  '    if (!runActions) { return true; }\n'
                  '    // Thors can be unlocked mid-mission (Media Blitz: Swann), so the gate is checked every second.\n'
                  '    if (TechTreeUpgradeCount(1, "RMA_ThorUnlocked", c_techCountQueuedOrBetter) == 0 && (TechTreeAbilityIsAllowed(1, AbilityCommand("FactoryTrain", 4))\n'
                  '        || UnitGroupCount(UnitGroup("Thor", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) > 0)) {\n'
                  '        TechTreeUpgradeAddLevel(1, "RMA_ThorUnlocked", 1);\n    }\n'
                  '    if (TechTreeUpgradeCount(1, "330mmBarrageCannons", c_techCountCompleteOnly) > 0) { TechTreeAbilityAllow(1, AbilityCommand("330mmBarrageCannons", 0), true); }\n'
                  '    return true;\n}\n\n'
                  'void gf_rm12ThorInit () {\n'
                  '    if (gt_rm12Thor != null) { return; }\n'
                  '    gt_rm12Thor = TriggerCreate("gt_rm12Thor_Func");\n'
                  '    TriggerAddEventTimePeriodic(gt_rm12Thor, 1.0, c_timeGame);\n}\n\n')
            a = 'void InitMap () {\n'; assert t.count(a) == 1; t = t.replace(a, sc + a)
            a = '    gf_rm9MinesInit();\n'; assert t.count(a) == 1; t = t.replace(a, a + '    gf_rm12ThorInit();\n')
            files[k] = t.replace('\n', nl).encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], strs); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
            for loc in LOCS:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'
                files[q] = set_lines(files[q], {f'Button/Hotkey/{b}': h for b, h in hk.items()}); changed.add(q)
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
