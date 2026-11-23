#!/usr/bin/env python3
"""0.8.2 -> 0.8.3: 다이아몬드백(코브라) 무기고 연구를 군수 공장 기술실에서 (사용자 2026-11-23 "코브라 연구랑 이런거 적용된거지 그 열차 사냥하는거 갈거라서").

규칙(4장 "무기고에서 안 산 기술은 미션 안에서 연구", 차량은 그 유닛이 나오는 임무를 만들 때 추가). Maps 4-8, 0.6.71 골리앗과 같은 방식:
  - 성형 선체(ShapedHull, 원작: 다이아몬드백 생명력 +50) (1,2) 단축키 H
  - 3리튬 동력 전지(TriLithiumPowerCells, 원작: 다이아몬드백 사거리 +1) (1,3) 단축키 T
  군수 공장 기술실·기술 반응로, FactoryTechLabResearch Research8/9, 100/100·60초(시험값). 원작 업그레이드 그대로라 히페리온에서
  샀으면 버튼이 숨는다(QueuedOrBetter). 다이아몬드백 해금(군수 공장 생산 허용, FactoryTrain 7) 뒤에만 보이고,
  8번 대열차 강도(THorner01)는 임무 중에 버려진 다이아몬드백을 얻으므로 처음부터 보인다. 다이아몬드백은 용병판이 없어 원본 유닛.
그리고 (사용자 같은 날 "벙커 연구 업그레이드 중에 150 체력 ... 체력 자동재생 같은거 넣어줘") 1~8번: 연구실 강화 벙커
(FortifiedBunkerCarapace, 생명력 +150)에 체력 자동 재생을 더한다 - 일반 벙커·보급 벙커(BunkerDepotMengsk, 있는 맵), 피해를 받지 않고
REGEN_DELAY초 뒤 초당 REGEN_RATE (시험값 5초·초당 5). 연구실 업그레이드를 맵에서 넓힌 것(모드 변경).
Game not run.

Usage: python3 tools/build_v083.py <0.8.2 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD, LOCS

OLD, NEW = b'version=0.8.2', b'version=0.8.3'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01']
NOTE = (' 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다.', ' Researched in the mission when not bought at the Hyperion Armory.')
COST = '<Resource index="Minerals" value="100" /><Resource index="Vespene" value="100" />'
ITEMS = [
    ('RMA_ShapedHull', 'ShapedHull', 8, 1, 2, 'H', 'Assets\\Textures\\btn-techupgrade-terran-shapedhull.dds',
     ('성형 선체', 'Shaped Hull'), ('다이아몬드백의 생명력이 50 증가합니다.' + NOTE[0], 'Diamondbacks gain +50 life.' + NOTE[1])),
    ('RMA_TriLithium', 'TriLithiumPowerCells', 9, 1, 3, 'T', 'Assets\\Textures\\btn-techupgrade-terran-trilithiumpowercell.dds',
     ('3리튬 동력 전지', 'Tri-Lithium Power Cell'), ('다이아몬드백의 사거리가 1 증가합니다.' + NOTE[0], 'Diamondbacks gain +1 attack range.' + NOTE[1])),
]


def xml_parts():
    btn = abil = card = req = node = ''
    strs, hk = {}, {}
    for bid, upg, n, r, c, key, icon, (nk, ne), (tk, te) in ITEMS:
        btn += (f'<CButton id="{bid}"><Icon value="{icon}" /><Name value="Button/Name/{bid}" /><Tooltip value="Button/Tooltip/{bid}" />'
                f'<Hotkey value="Button/Hotkey/{bid}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>')
        abil += (f'<InfoArray index="Research{n}" Time="60" Upgrade="{upg}">{COST}<Button DefaultButtonFace="{bid}" State="Available" '
                 f'Requirements="{bid}Learn" /></InfoArray>')
        card += f'<LayoutButtons Face="{bid}" Type="AbilCmd" AbilCmd="FactoryTechLabResearch,Research{n}" Row="{r}" Column="{c}" />'
        req += f'<CRequirement id="{bid}Learn"><NodeArray index="Show" Link="{bid}Show" /></CRequirement>'
        node += (f'<CRequirementCountUpgrade id="{bid}Queued"><Count Link="{upg}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
                 f'<CRequirementNot id="{bid}NotQueued"><OperandArray index="0" value="{bid}Queued" /></CRequirementNot>'
                 f'<CRequirementAnd id="{bid}Show"><OperandArray value="{bid}NotQueued" /><OperandArray value="RMA_DiamondbackGate" /></CRequirementAnd>')
        strs[f'Button/Name/{bid}'] = f'{nk} 연구 /// Research {ne}'
        strs[f'Button/Tooltip/{bid}'] = f'{tk} /// {te}'
        hk[bid] = key
    node += '<CRequirementCountUpgrade id="RMA_DiamondbackGate"><Count Link="RMA_DiamondbackUnlocked" State="CompleteOnly" /></CRequirementCountUpgrade>'
    unit = ''.join(f'<CUnit id="{u}"><CardLayouts index="0">{card}</CardLayouts></CUnit>' for u in ('FactoryTechLab', 'FactoryTechReactor'))
    data = {'buttondata.xml': btn, 'abildata.xml': f'<CAbilResearch id="FactoryTechLabResearch">{abil}</CAbilResearch>',
            'unitdata.xml': unit, 'requirementdata.xml': req, 'requirementnodedata.xml': node,
            'upgradedata.xml': '<CUpgrade id="RMA_DiamondbackUnlocked"><Race value="Terr" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>'}
    return data, strs, hk


ALL = ['TRaynor01', 'TRaynor02', 'TRaynor03'] + MAPS
REGEN_RATE, REGEN_DELAY = 5, 5   # trial


def bunker(raw, units):
    t = raw.decode('utf-8')
    add = ''.join(f'<EffectArray Operation="Set" Reference="Unit,{u},LifeRegenRate" Value="{REGEN_RATE}" />'
                  f'<EffectArray Operation="Set" Reference="Unit,{u},LifeRegenDelay" Value="{REGEN_DELAY}" />' for u in units)
    assert 'LifeRegenRate' not in (re.search(r'<CUpgrade id="FortifiedBunkerCarapace">.*?</CUpgrade>', t, re.S) or re.match('', '')).group(0)
    if t.count('<CUpgrade id="FortifiedBunkerCarapace">') == 1:
        i = t.index('</CUpgrade>', t.index('<CUpgrade id="FortifiedBunkerCarapace">'))
        t = t[:i] + add + t[i:]
    else:
        assert 'id="FortifiedBunkerCarapace"' not in t
        k = t.rindex('</Catalog>'); t = t[:k] + f'<CUpgrade id="FortifiedBunkerCarapace">{add}</CUpgrade>' + t[k:]
    return t.encode('utf-8')


def script(m, raw):
    t = raw.decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
    a = '    TechTreeUpgradeAllow(1,"RM7_Lockdown",true);\n'
    assert t.count(a) == 1, m
    cond = 'true' if m == 'THorner01' else 'TechTreeAbilityIsAllowed(1,AbilityCommand("FactoryTrain",7))'
    b = ('    TechTreeUpgradeAllow(1,"RM7_Lockdown",true);\n'
         '    // 0.8.3: Diamondback armory tech not bought at the Hyperion (mission 8 hands Diamondbacks over mid-mission).\n'
         '    TechTreeUpgradeAllow(1,"RMA_DiamondbackUnlocked",true);\n'
         f'    if (TechTreeUpgradeCount(1,"RMA_DiamondbackUnlocked",c_techCountQueuedOrBetter)==0 && {cond}) {{\n'
         '        TechTreeUpgradeAddLevel(1,"RMA_DiamondbackUnlocked",1);\n    }\n'
         '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",7),true);\n'
         '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",8),true);\n'
         '    TechTreeUpgradeAllow(1,"ShapedHull",true);\n    TechTreeUpgradeAllow(1,"TriLithiumPowerCells",true);\n')
    t = t.replace(a, b)
    return t.replace('\n', nl).encode('utf-8')


def append(raw, xml, ids):
    t = raw.decode('utf-8')
    for i in ids:
        assert f'id="{i}"' not in t or i in ('FactoryTechLab', 'FactoryTechReactor', 'FactoryTechLabResearch'), i
    k = t.rindex('</Catalog>')
    return (t[:k] + xml + t[k:]).encode('utf-8')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    data, strs, hk = xml_parts()
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in ALL:
            p = f'{m}.SC2Map/{GD}upgradedata.xml'
            units = ['Bunker'] + (['BunkerDepotMengsk'] if b'id="BunkerDepotMengsk"' in files[f'{m}.SC2Map/{GD}unitdata.xml'] else [])
            files[p] = bunker(files[p], units); changed.add(p)
        for m in MAPS:
            u = files[f'{m}.SC2Map/{GD}unitdata.xml'].decode()
            for x in re.findall(r'<CUnit id="FactoryTech(?:Lab|Reactor)">(.*?)</CUnit>', u, re.S):
                assert 'Row="1" Column="2"' not in x and 'Row="1" Column="3"' not in x, m
            ab = files[f'{m}.SC2Map/{GD}abildata.xml'].decode()
            assert not re.search(r'<CAbilResearch id="FactoryTechLabResearch">(?:(?!</CAbilResearch>).)*index="Research[89]"', ab, re.S), m
            for f, xml in data.items():
                p = f'{m}.SC2Map/{GD}{f}'
                files[p] = append(files[p], xml, re.findall(r'id="([^"]+)"', xml)); changed.add(p)
            p = f'{m}.SC2Map/mapscript.galaxy'; files[p] = script(m, files[p]); changed.add(p)
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
