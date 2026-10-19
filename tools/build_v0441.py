#!/usr/bin/env python3
"""Build CCM 0.4.41 from 0.4.40: 협동전 연구를 2페이지로 (4번, 사용자 지시 2026-10-19 "2페이지를 만들던가").

병영 기술실·공학 연구소 첫 화면 = 자날·무기고 연구, '협동전 연구' 버튼을 누르면 2페이지.
  병영 기술실 2페이지: 레이저 조준(노바), 파편탄(멩스크, 옮김), 전투 안정제(레이너 협동전판), 철인 장갑(레이너 협동전판).
  공학 연구소 2페이지: 신소재 강화 장갑·조준 지원 총안(멩스크, 옮김), KMC 자동장전기(스완), 정밀 보안 자동추적.
  - 협동전판은 자날 무기고판과 같은 ID라 따로 만든다 (RMC_…). 마스터 힘·사령관 체계 부분(레이너 의무관 피해 감소 마스터 힘)은 넣지 않는다.
    전투 안정제(협동전): 용병 의무관 치료 속도 +3·소모 -0.08. 철인 장갑(협동전): 화염방사병·악마의 개 생명력 +100.
    KMC 자동장전기: 미사일 포탑 공격 속도 +25% (기본·우박 미사일 무기). 정밀 보안 자동추적: 원작 HiSecAutoTracking(포탑 사거리 +1).
  - 비용 모두 100/100·60초 (시험값). 철인 장갑(협동전)은 악마의 개 해금 때만.

Usage: python3 tools/build_v0441.py <0.4.40 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.40', b'version=0.4.41'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
MENU = 'RMC_CoopMenu'
# new research: (button, upgrade, ability, index, icon, hotkey, gate, name, tooltip)
NEW_R = [
    ('RMC_StabilizerCoop', 'RMC_StabilizerCoop', 'RM3_TechResearch', 15, r'Assets\Textures\btn-upgrade-raynor-stabilizermedpacks.dds', 'M', None,
     '전투 안정제 (협동전) /// Stabilizer Medpacks (Co-op)',
     '용병 의무관의 치료 속도가 빨라지고 에너지 소모가 줄어듭니다. 레이너 협동전 연구입니다. /// Mercenary Medics heal faster and use less energy. Raynor co-op research.'),
    ('RMC_JuggernautCoop', 'RMC_JuggernautCoop', 'RM3_TechResearch', 16, r'Assets\Textures\btn-upgrade-raynor-juggernautplating.dds', 'J', 'RMA_DevilDogUnlocked',
     '철인 장갑 (협동전) /// Juggernaut Plating (Co-op)',
     '화염방사병의 생명력이 100 증가합니다. 레이너 협동전 연구입니다. /// Firebats gain +100 life. Raynor co-op research.'),
    ('RMC_TurretSpeed', 'RMC_TurretSpeed', 'RM3_BayResearch', 18, r'Assets\Textures\btn-upgrade-swann-kmcautoloaders.dds', 'K', None,
     'KMC 자동장전기 /// KMC Auto-Loaders',
     '미사일 포탑의 공격 속도가 25% 증가합니다. 스완 협동전 연구입니다. /// Missile Turrets attack 25% faster. Swann co-op research.'),
    ('RMC_HiSec', 'HiSecAutoTracking', 'RM3_BayResearch', 19, r'Assets\Textures\BTN-Upgrade-Terran-hisecautotracking.dds', 'H', None,
     '정밀 보안 자동추적 /// Hi-Sec Auto Tracking',
     '미사일 포탑의 사거리가 1 증가합니다. 스완 협동전 연구입니다. /// Missile Turrets gain +1 range. Swann co-op research.'),
]
# page 2 layout: unit -> [(face, abilcmd, row, col)]; existing buttons are moved here from page 1
PAGE2 = {
    'BarracksTechLab': [('RM3_Laser', 'RM3_TechResearch,Research5', 0, 0), ('RM4_Shrapnel', 'RM3_TechResearch,Research9', 0, 1),
                        ('RMC_StabilizerCoop', 'RM3_TechResearch,Research15', 0, 2), ('RMC_JuggernautCoop', 'RM3_TechResearch,Research16', 0, 3)],
    'EngineeringBay': [('StructureArmorMengskResearch', 'RM3_BayResearch,Research8', 0, 0), ('BunkerDepotMengskRangeResearch', 'RM3_BayResearch,Research9', 0, 1),
                       ('RMC_TurretSpeed', 'RM3_BayResearch,Research18', 0, 2), ('RMC_HiSec', 'RM3_BayResearch,Research19', 0, 3)],
}
MENU_SLOT = {'BarracksTechLab': (2, 3), 'EngineeringBay': (0, 2)}
UPGRADES = ('<CUpgrade id="RMC_StabilizerCoop"><Race value="Terr" /><Alert value="ResearchComplete" />'
            '<EffectArray Operation="Subtract" Reference="Effect,MercMedicHeal,DrainVitalCostFactor" Value="0.08" />'
            '<EffectArray Reference="Effect,MercMedicHeal,RechargeVitalRate" Value="3" /></CUpgrade>'
            '<CUpgrade id="RMC_JuggernautCoop"><Race value="Terr" /><Alert value="ResearchComplete" />'
            '<AffectedUnitArray value="DevilDog" /><AffectedUnitArray value="Firebat" />'
            '<EffectArray Reference="Unit,DevilDog,LifeMax" Value="100" /><EffectArray Reference="Unit,DevilDog,LifeStart" Value="100" />'
            '<EffectArray Reference="Unit,Firebat,LifeMax" Value="100" /><EffectArray Reference="Unit,Firebat,LifeStart" Value="100" /></CUpgrade>'
            '<CUpgrade id="RMC_TurretSpeed"><Race value="Terr" /><Alert value="ResearchComplete" /><AffectedUnitArray value="MissileTurret" />'
            '<EffectArray Reference="Weapon,LongboltMissile,RateMultiplier" Value="0.25" />'
            '<EffectArray Reference="Weapon,HailstormMissilePods,RateMultiplier" Value="0.25" /></CUpgrade>')
SCRIPT_OLD = '    TechTreeUpgradeAllow(1,"RMA_DevilDogUnlocked",true);\n'
SCRIPT_NEW = SCRIPT_OLD + '    // Co-op research page (0.4.41).\n' + ''.join(
    f'    TechTreeAbilityAllow(1,AbilityCommand("{a}",{n - 1}),true);\n    TechTreeUpgradeAllow(1,"{up}",true);\n'
    for bid, up, a, n, *_ in NEW_R)


def rep(a, b):
    def fn(d):
        t = d.decode('utf-8')
        assert t.count(a) == 1, a
        return t.replace(a, b).encode('utf-8')
    return fn


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
                      f'Requirements="{bid}Learn" /></InfoArray>' for bid, up, a, n, *_ in NEW_R if a == ab)
        t = t[:m.start()] + m.group(0).replace('</CAbilResearch>', add + '</CAbilResearch>') + t[m.end():]
    return t.encode('utf-8')


def units(d):
    t = d.decode('utf-8')
    for unit, rows in PAGE2.items():
        m = re.search(r'<CUnit id="' + unit + r'">.*?</CUnit>', t, re.S)
        u = m.group(0)
        for face, cmd, *_ in rows:  # move existing page-1 buttons
            u, n = re.subn(r'<LayoutButtons Face="' + face + r'" Type="AbilCmd" AbilCmd="' + re.escape(cmd) + r'" Row="\d" Column="\d" />', '', u)
            assert n <= 1, face
        r, c = MENU_SLOT[unit]
        u = re.sub(r'(<CardLayouts index="0">)', r'\1' + f'<LayoutButtons Face="{MENU}" Type="Submenu" SubmenuCardId="RMC1" Row="{r}" Column="{c}" />', u, count=1)
        page = ''.join(f'<LayoutButtons Face="{f}" Type="AbilCmd" AbilCmd="{cmd}" Row="{rr}" Column="{cc}" />' for f, cmd, rr, cc in rows)
        page += '<LayoutButtons Face="Cancel" Type="CancelSubmenu" Row="2" Column="4" />'
        u = u.replace('</CUnit>', f'<CardLayouts CardId="RMC1">{page}</CardLayouts></CUnit>')
        t = t[:m.start()] + u + t[m.end():]
    return t.encode('utf-8')


def reqs():
    r, n = '', ''
    for bid, up, a, idx, icon, hk, gate, *_ in NEW_R:
        r += f'<CRequirement id="{bid}Learn"><NodeArray index="Show" Link="{bid}Show" /></CRequirement>'
        n += (f'<CRequirementCountUpgrade id="{bid}Queued"><Count Link="{up}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
              f'<CRequirementNot id="{bid}NotQueued"><OperandArray value="{bid}Queued" /></CRequirementNot>')
        ops = f'<OperandArray index="0" value="{bid}NotQueued" />'
        if gate:
            n += f'<CRequirementCountUpgrade id="{bid}Gate"><Count Link="{gate}" State="CompleteOnly" /></CRequirementCountUpgrade>'
            ops += f'<OperandArray index="1" value="{bid}Gate" />'
        n += f'<CRequirementAnd id="{bid}Show">{ops}</CRequirementAnd>'
    return r, n


def buttons():
    b = (f'<CButton id="{MENU}"><Icon value="Assets\\Textures\\btn-command-terran-buildadvancedstructure.dds" />'
         f'<Name value="Button/Name/{MENU}" /><Tooltip value="Button/Tooltip/{MENU}" /></CButton>')
    for bid, up, a, n, icon, *_ in NEW_R:
        b += (f'<CButton id="{bid}"><Icon value="{icon}" /><Name value="Button/Name/{bid}" />'
              f'<Tooltip value="Button/Tooltip/{bid}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>')
    return b


STR = {f'Button/Name/{MENU}': '협동전 연구 /// Co-op Research',
       f'Button/Tooltip/{MENU}': '협동전 사령관의 연구를 엽니다. /// Opens co-op commander research.'}
for bid, up, a, n, icon, hk, gate, name, tip in NEW_R:
    STR[f'Button/Name/{bid}'] = name
    STR[f'Button/Tooltip/{bid}'] = tip
    STR[f'Upgrade/Name/{up}'] = name
del STR['Upgrade/Name/HiSecAutoTracking']


def strings(d):
    t = d.decode('utf-8')
    nl = '\r\n' if '\r\n' in t else '\n'
    lines = t.split(nl)
    while lines and lines[-1] == '': lines.pop()
    assert not any(l.split('=', 1)[0] in STR for l in lines)
    return nl.join(lines + [f'{k}={v}' for k, v in STR.items()] + ['']).encode('utf-8')


def hotkeys(d):
    t = d.decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in t else '\n'
    add = [f'Button/Hotkey/{MENU}=X'] + [f'Button/Hotkey/{bid}={hk}' for bid, up, a, n, icon, hk, *_ in NEW_R]
    return (t.rstrip('\r\n') + nl + nl.join(add) + nl).encode('utf-8-sig' if d.startswith(b'\xef\xbb\xbf') else 'utf-8')


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    r, n = reqs()
    fix = {'metadata.txt': lambda d: d.replace(OLD, NEW), M4 + 'mapscript.galaxy': rep(SCRIPT_OLD, SCRIPT_NEW),
           GD + 'abildata.xml': abil, GD + 'unitdata.xml': units, GD + 'buttondata.xml': append(buttons()),
           GD + 'requirementdata.xml': append(r), GD + 'requirementnodedata.xml': append(n),
           GD + 'upgradedata.xml': append(UPGRADES), KO: strings}
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
