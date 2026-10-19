#!/usr/bin/env python3
"""Build CCM 0.4.40 from 0.4.39: 무기고에서 안 산 기술을 미션 안에서 연구 — 4번에 있는 유닛·건물 전부.

사용자 지시 (2026-10-19): "유닛들 전부 무기고에서 구매하지 않은 것들 다 기술실에서 업그레이드 가능하게".
  - 병영 기술실 (보병): 전투 안정제·고급 의무관 시설(의무관), 곰발톱 분사기·강철 장갑판(화염방사병).
  - 공학 연구소 (건물·SCV는 기술실이 없음): 신소재 강철 골조·탄환 가속기(벙커), 이중 융합 용접기·고급 건설(SCV),
    화재 진압 시스템·궤도 중계기(사령부), 강화 골조·우박 미사일 포드(미사일 포탑).
  - 연구를 끝내면 무기고 구매와 같은 업그레이드를 켠다. 샀거나 연구 중이면 버튼이 안 나온다.
  - 이미 있는 것: 해병 자극제·전투 방패, 불곰 충격탄·동역학 충격완화복. 사신(죽음의 우두머리)은 4번에 없어 뺀다.
    차량·비행선·유령 항목은 그 유닛이 나오는 임무를 만들 때 넣는다 (같은 표에 추가).
  - 전투 안정제는 원작이 일반 의무관 치료(heal)만 바꿔서 용병 의무관(MercMedicHeal)에는 안 들었다 → 같은 값으로 넓힌다
    (무기고에서 산 경우도 이제 용병 의무관에 적용).
  - 화염방사병 두 항목은 악마의 개 생산이 해금됐을 때만 보인다 (RMA_DevilDogUnlocked).
  - 비용: 모두 100/100·60초 (시험값).

Usage: python3 tools/build_v0440.py <0.4.39 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD, NEW = b'version=0.4.39', b'version=0.4.40'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
# (button id, upgrade, research ability, InfoArray index, row, col, hotkey, gate flag)
ITEMS = [
    ('RMA_StabilizerMedPacks', 'StabilizerMedPacks', 'RM3_TechResearch', 11, 1, 4, 'M', None),
    ('RMA_AdvancedMedicTraining', 'AdvancedMedicTraining', 'RM3_TechResearch', 12, 2, 0, 'V', None),
    ('RMA_BearclawNozzles', 'BearclawNozzles', 'RM3_TechResearch', 13, 2, 1, 'B', 'RMA_DevilDogUnlocked'),
    ('RMA_FirebatJuggernautPlating', 'FirebatJuggernautPlating', 'RM3_TechResearch', 14, 2, 2, 'J', 'RMA_DevilDogUnlocked'),
    ('RMA_NeoSteelFrame', 'NeoSteelFrame', 'RM3_BayResearch', 10, 1, 0, 'B', None),
    ('RMA_ProjectileAccelerators', 'ProjectileAccelerators', 'RM3_BayResearch', 11, 1, 1, 'P', None),
    ('RMA_DualFusionWelders', 'DualFusionWelders', 'RM3_BayResearch', 12, 1, 2, 'W', None),
    ('RMA_AdvancedConstruction', 'AdvancedConstruction', 'RM3_BayResearch', 13, 2, 2, 'C', None),
    ('RMA_FireSuppressionSystems', 'FireSuppressionSystems', 'RM3_BayResearch', 14, 0, 4, 'R', None),
    ('RMA_OrbitalRelay', 'OrbitalRelay', 'RM3_BayResearch', 15, 1, 4, 'O', None),
    ('RMA_ReinforcedSuperstructure', 'ReinforcedSuperstructure', 'RM3_BayResearch', 16, 1, 3, 'I', None),
    ('RMA_HailstormMissilePods', 'HailstormMissilePods', 'RM3_BayResearch', 17, 2, 3, 'H', None),
]
UNIT_OF = {'RM3_TechResearch': 'BarracksTechLab', 'RM3_BayResearch': 'EngineeringBay'}
NOTE = (' 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다.', ' Researched in the mission when not bought at the Hyperion Armory.')


def armory():
    """upgrade -> (icon, tooltip key) from the original armory screen data."""
    t = (ROOT / 'source/libertystory.sc2campaign/base.sc2data/gamedata/conversationstatedata.xml').read_text('utf-8')
    out = {}
    for b in re.findall(r'<Indices>(.*?)</Indices>', t, re.S):
        up = re.search(r'InfoUpgrade Id="\w+" Upgrade="([^"]+)"', b)
        if up:
            out[up.group(1)] = (re.search(r'<ImagePath value="([^"]+)"', b).group(1),
                                re.search(r'<InfoText Id="Tooltip" Text="([^"]+)"', b).group(1))
    return out


def strings_src():
    d = {}
    for x in ('liberty.sc2campaign', 'libertystory.sc2campaign'):
        for l in (ROOT / f'source/{x}/kokr.sc2data/localizeddata/gamestrings.txt').read_text('utf-8').splitlines():
            if '=' in l:
                k, v = l.split('=', 1); d[k] = v
    return d


def desc(v):
    """'<title>…<n/>desc /// …' -> (ko, en) description only."""
    ko, en = v.split(' /// ', 1)
    f = lambda s: re.sub(r'</?s(?: [^>]*)?>', '', re.sub(r'^<s val="TooltipTitle_Tech">.*?</s><n/>', '', s)).strip()  # keep <d ref> numbers
    return f(ko), f(en)


def build_texts():
    arm, src = armory(), strings_src()
    btn, strs = [], {}
    for bid, up, *_ in ITEMS:
        icon, tip = arm[up]
        name = src[f'Upgrade/Name/{up}']
        assert ' /// ' in name, up
        ko, en = desc(src[tip])
        strs[f'Button/Name/{bid}'] = name
        strs[f'Button/Tooltip/{bid}'] = f'{ko}{NOTE[0]} /// {en}{NOTE[1]}'
        btn.append(f'<CButton id="{bid}"><Icon value="{icon}" /><Name value="Button/Name/{bid}" />'
                   f'<Tooltip value="Button/Tooltip/{bid}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>')
    return ''.join(btn), strs


def append(xml):
    def fn(d):
        i = d.rindex(b'</Catalog>')
        return d[:i] + xml.encode('utf-8') + d[i:]
    return fn


def abil(d):
    t = d.decode('utf-8')
    for ab in ('RM3_TechResearch', 'RM3_BayResearch'):
        m = re.search(r'<CAbilResearch id="' + ab + r'">.*?</CAbilResearch>', t, re.S)
        add = ''.join(f'<InfoArray index="Research{n}" Time="60" Upgrade="{up}"><Resource index="Minerals" value="100" />'
                      f'<Resource index="Vespene" value="100" /><Button DefaultButtonFace="{bid}" State="Available" '
                      f'Requirements="{bid}Learn" /></InfoArray>' for bid, up, a, n, *_ in ITEMS if a == ab)
        for _, _, a, n, *_ in ITEMS:
            if a == ab: assert f'index="Research{n}"' not in m.group(0)
        s = m.group(0).replace('</CAbilResearch>', add + '</CAbilResearch>')
        t = t[:m.start()] + s + t[m.end():]
    return t.encode('utf-8')


def units(d):
    t = d.decode('utf-8')
    for ab, unit in UNIT_OF.items():
        m = re.search(r'<CUnit id="' + unit + r'">\s*<AbilArray[^>]*/>\s*<CardLayouts index="0">', t)
        add = ''.join(f'<LayoutButtons Face="{bid}" Type="AbilCmd" AbilCmd="{a},Research{n}" Row="{r}" Column="{c}" />'
                      for bid, up, a, n, r, c, *_ in ITEMS if a == ab)
        t = t[:m.end()] + add + t[m.end():]
    return t.encode('utf-8')


def reqs():
    r, n = '', ''
    for bid, up, a, idx, row, col, hk, gate in ITEMS:
        r += f'<CRequirement id="{bid}Learn"><NodeArray index="Show" Link="{bid}Show" /></CRequirement>'
        n += (f'<CRequirementCountUpgrade id="{bid}Queued"><Count Link="{up}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
              f'<CRequirementNot id="{bid}NotQueued"><OperandArray value="{bid}Queued" /></CRequirementNot>')
        if gate:
            n += (f'<CRequirementCountUpgrade id="{bid}Gate"><Count Link="{gate}" State="CompleteOnly" /></CRequirementCountUpgrade>'
                  f'<CRequirementAnd id="{bid}Show"><OperandArray index="0" value="{bid}NotQueued" /><OperandArray index="1" value="{bid}Gate" /></CRequirementAnd>')
        else:
            n += f'<CRequirementAnd id="{bid}Show"><OperandArray index="0" value="{bid}NotQueued" /></CRequirementAnd>'
    return r, n


MEDPACK = ('<CUpgrade id="StabilizerMedPacks"><EffectArray Operation="Set" Reference="Effect,MercMedicHeal,DrainVitalCostFactor" Value="0.25" />'
           '<EffectArray Reference="Effect,MercMedicHeal,RechargeVitalRate" Value="1.000000" /></CUpgrade>'
           '<CUpgrade id="RMA_DevilDogUnlocked"><Race value="Terr" /></CUpgrade>')
SCRIPT_OLD = '    TechTreeUpgradeAllow(1,"MarauderLifeBoost",true);\n'
SCRIPT_NEW = SCRIPT_OLD + ''.join(
    f'    TechTreeAbilityAllow(1,AbilityCommand("{a}",{n - 1}),true);\n    TechTreeUpgradeAllow(1,"{up}",true);\n'
    for bid, up, a, n, *_ in ITEMS) + (
    '    TechTreeUpgradeAllow(1,"RMA_DevilDogUnlocked",true);\n'
    '    if (TechTreeUpgradeCount(1,"RMA_DevilDogUnlocked",c_techCountQueuedOrBetter)==0 && TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",5))) {\n'
    '        TechTreeUpgradeAddLevel(1,"RMA_DevilDogUnlocked",1);\n'
    '    }\n')


def rep(a, b):
    def fn(d):
        t = d.decode('utf-8')
        assert t.count(a) == 1, a
        return t.replace(a, b).encode('utf-8')
    return fn


def strings(add):
    def fn(d):
        t = d.decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        lines = t.split(nl)
        while lines and lines[-1] == '': lines.pop()
        assert not any(l.split('=', 1)[0] in add for l in lines)
        return nl.join(lines + [f'{k}={v}' for k, v in add.items()] + ['']).encode('utf-8')
    return fn


def hotkeys(d):
    t = d.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in t else '\n'
    add = nl.join(f'Button/Hotkey/{bid}={hk}' for bid, up, a, n, r, c, hk, g in ITEMS)
    return (t.rstrip('\r\n') + nl + add + nl).encode('utf-8-sig' if d.startswith(b'\xef\xbb\xbf') else 'utf-8')


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    btn, strs = build_texts()
    r, n = reqs()
    fix = {'metadata.txt': lambda d: d.replace(OLD, NEW), M4 + 'mapscript.galaxy': rep(SCRIPT_OLD, SCRIPT_NEW),
           GD + 'abildata.xml': abil, GD + 'unitdata.xml': units, GD + 'buttondata.xml': append(btn),
           GD + 'requirementdata.xml': append(r), GD + 'requirementnodedata.xml': append(n),
           GD + 'upgradedata.xml': append(MEDPACK), KO: strings(strs)}
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        for k, fn in fix.items(): files[k] = fn(files[k])
        V35.gate('kokr', files[KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M4}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[KO])
        for loc in ['kokr'] + V35.OTHER_LOCALES:
            p = f'{M4}{loc}.sc2data/localizeddata/gamehotkeys.txt'
            files[p] = hotkeys(files[p])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for k in prev.namelist():
                    if not k.startswith(M4) and k != 'metadata.txt': assert out.read(k) == prev.read(k), k
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
