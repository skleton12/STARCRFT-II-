#!/usr/bin/env python3
"""0.9.1 -> 0.9.2: 벌처 무기고 연구를 군수 공장 기술실에서 (사용자 2026-11-24 "벌처 연구도 들어가있는 버젼이지?" → "당연히 넣어야지 빨리 넣어").

규칙(4장 "무기고에서 안 산 기술은 미션 안에서 연구"), 0.8.3 다이아몬드백과 같은 방식. maps 4~9:
  - 케르베로스 지뢰(CerberusMines, 원작: 거미 지뢰 폭발·감지 반경 +33%) (2,0) 단축키 C
  - 재충전 탄창(NanoConstructor, 원작 Replenishable Magazine: 벌처가 광물 15로 지뢰를 다시 만듦 — MakeVultureSpiderMines 명령) (2,1) 단축키 R
  군수 공장 기술실·기술 반응로, FactoryTechLabResearch Research10/11, 100/100·60초(시험값). 원작 업그레이드 그대로라 히페리온에서
  샀으면 버튼이 숨는다. 벌처 해금(FactoryTrain 8 또는 벌처 보유) 뒤에만 보인다(표시 업그레이드 RMA_VultureUnlocked, 1초마다 확인 — 임무 중 해금 대비, 코덱스 검토). 재충전 탄창은 연구가 끝나면
  스크립트가 지뢰 만들기 명령을 허용한다(원작 무기고 구매와 같은 명령, 버튼은 원작 요구조건 UseNanoConstructor). 벌처는 용병판이 없어 원본.
  첫 정의 안에 합친다(두 번 정의 금지, 0.8.5). 한국어 이름 공식 번역 미확인. Game not run.

Usage: python3 tools/build_v092.py <0.9.1 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD, LOCS

OLD, NEW = b'version=0.9.1', b'version=0.9.2'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02']
NOTE = (' 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다.', ' Researched in the mission when not bought at the Hyperion Armory.')
COST = '<Resource index="Minerals" value="100" /><Resource index="Vespene" value="100" />'
ITEMS = [
    ('RMA_Cerberus', 'CerberusMines', 10, 2, 0, 'C', 'Assets\\Textures\\btn-techupgrade-terran-cerberusmine.dds',
     ('케르베로스 지뢰', 'Cerberus Mine'), ('벌처 거미 지뢰의 폭발 반경과 감지 반경이 33% 늘어납니다.' + NOTE[0],
                                          'Increases spider mine blast and trigger radiuses by 33%.' + NOTE[1])),
    ('RMA_Replenish', 'NanoConstructor', 11, 2, 1, 'R', 'Assets\\Textures\\btn-techupgrade-terran-replenishablemagazine.dds',
     ('재충전 탄창', 'Replenishable Magazine'), ('벌처가 지뢰 하나당 광물 15를 써서 전장에서 거미 지뢰를 다시 만들 수 있습니다.' + NOTE[0],
                                              'Vultures can replenish mines in the field at a cost of 15 minerals per mine.' + NOTE[1])),
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
                 f'<CRequirementAnd id="{bid}Show"><OperandArray value="{bid}NotQueued" /><OperandArray value="RMA_VultureGate" /></CRequirementAnd>')
        strs[f'Button/Name/{bid}'] = f'{nk} 연구 /// Research {ne}'
        strs[f'Button/Tooltip/{bid}'] = f'{tk} /// {te}'
        hk[bid] = key
    node += '<CRequirementCountUpgrade id="RMA_VultureGate"><Count Link="RMA_VultureUnlocked" State="CompleteOnly" /></CRequirementCountUpgrade>'
    upg_xml = '<CUpgrade id="RMA_VultureUnlocked"><Race value="Terr" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>'
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
                assert 'Row="2" Column="0"' not in c0.group(1) and 'Row="2" Column="1"' not in c0.group(1), (m, u)
                p = b.start() + c0.end(1); t = t[:p] + card + t[p:]
            files[P('unitdata.xml')] = t.encode('utf-8')
            t = files[P('abildata.xml')].decode('utf-8')
            b = first(t, 'CAbilResearch', 'FactoryTechLabResearch')
            assert 'index="Research10"' not in b.group(0) and 'index="Research11"' not in b.group(0), m
            p = b.end() - len('</CAbilResearch>'); files[P('abildata.xml')] = (t[:p] + abil + t[p:]).encode('utf-8')
            for f, x in (('buttondata.xml', btn), ('requirementdata.xml', req), ('requirementnodedata.xml', node), ('upgradedata.xml', upg_xml)):
                t = files[P(f)].decode('utf-8'); assert 'RMA_Cerberus' not in t and 'RMA_VultureUnlocked' not in t, (m, f)
                files[P(f)] = end_insert(t, x).encode('utf-8')
            for f in ('unitdata.xml', 'abildata.xml', 'buttondata.xml', 'requirementdata.xml', 'requirementnodedata.xml', 'upgradedata.xml'):
                E.fromstring(files[P(f)]); changed.add(P(f))
            k = f'{m}.SC2Map/mapscript.galaxy'; t = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
            a = '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",8),true);\n'
            assert t.count(a) == 1, m
            t = t.replace(a, a + (
                '    // 0.9.2: Vulture armory tech not bought at the Hyperion (user 2026-11-24).\n'
                '    TechTreeUpgradeAllow(1,"RMA_VultureUnlocked",true);\n'
                '    if (TechTreeUpgradeCount(1,"RMA_VultureUnlocked",c_techCountQueuedOrBetter)==0 && TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",8))) {\n'
                '        TechTreeUpgradeAddLevel(1,"RMA_VultureUnlocked",1);\n    }\n'
                '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",9),true);\n'
                '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",10),true);\n'
                '    TechTreeUpgradeAllow(1,"CerberusMines",true);\n    TechTreeUpgradeAllow(1,"NanoConstructor",true);\n'))
            # Replenishable Magazine: the original armory purchase allows the mine-making command; do the same once researched.
            sc = ('// 0.9.2: Replenishable Magazine researched in the mission allows the Vulture mine-making command (as the armory purchase).\n'
                  'trigger gt_rm9Mines;\n\n'
                  'bool gt_rm9Mines_Func (bool testConds, bool runActions) {\n'
                  '    if (!runActions) { return true; }\n'
                  '    // Codex review: Vultures can be unlocked mid-mission (Cutthroat: Mira Han), so the gate is checked every second.\n'
                  '    if (TechTreeUpgradeCount(1, "RMA_VultureUnlocked", c_techCountQueuedOrBetter) == 0 && (TechTreeAbilityIsAllowed(1, AbilityCommand("FactoryTrain", 8))\n'
                  '        || UnitGroupCount(UnitGroup("Vulture", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) > 0)) {\n'
                  '        TechTreeUpgradeAddLevel(1, "RMA_VultureUnlocked", 1);\n    }\n'
                  '    if (TechTreeUpgradeCount(1, "NanoConstructor", c_techCountCompleteOnly) > 0) { TechTreeAbilityAllow(1, AbilityCommand("MakeVultureSpiderMines", 0), true); }\n'
                  '    return true;\n}\n\n'
                  'void gf_rm9MinesInit () {\n'
                  '    if (gt_rm9Mines != null) { return; }\n'
                  '    gt_rm9Mines = TriggerCreate("gt_rm9Mines_Func");\n'
                  '    TriggerAddEventTimePeriodic(gt_rm9Mines, 1.0, c_timeGame);\n}\n\n')
            a = 'void InitMap () {\n'; assert t.count(a) == 1; t = t.replace(a, sc + a)
            a = '    AchievementsDisable(1);\n'; assert t.count(a) == 1; t = t.replace(a, a + '    gf_rm9MinesInit();\n')
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
