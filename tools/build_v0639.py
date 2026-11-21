#!/usr/bin/env python3
"""0.6.38 -> 0.6.39: more co-op Terran research, adapted (user 2026-11-21 "사신 대공 제외하고 나머지 연구 일부 개조해서 넣고
대부분 업그레이드도 개조해서 넣어줘"; list: docs/research/coop_terran_missing_2026-11-21.md).

Maps 4·5·6 (TTychus01, TTosh01, THanson01), Barracks Tech Lab co-op page (RMC1). All mod-redesigned, trial values,
100/100·60초 like the other co-op page items. Effects are upgrades that change data values (0.4.46 style).
- ITC-E 방아쇠 (Tychus) → 용병 사신 권총·폭탄 공격 속도 약 +25% (주기 1.1→0.88, 1.8→1.44). Maps 5·6, 사신 해금 때만.
- LE9 집속탄 (Han & Horner, 개조) → 용병 사신 D-8 폭탄 피해 +20. Maps 5·6, 사신 해금 때만.
  (사신 제트 추진기 과부하=대공·비행은 사용자 지시로 제외)
- 지구력 보충제 (Tychus) → 악마의 개·프로메테우스 중대·망치 경호대·이지스 근위대 최대 생명력 약 +25%.
- 프로키온 혈청 (Tychus 장비, 개조) → 용병 의무관 치료 속도 +6 (12→18, 전투 안정제와 합산).
Existing upgrades widened:
- 철인 장갑 (협동전) RMC_JuggernautCoop → 프로메테우스 중대도 생명력 +100.
- 신소재 강화 장갑 MengskStructureArmor → 미사일 포탑·대지파괴 포도 생명력 +200·방어력 +2 (멩스크 원본 대상).
Not done (need new abilities/behaviors): 사신 비행, 도약 추진 공격, 궤도 투하, 의무관 탐지·피해 감소·이중 치료.

Usage: python3 tools/build_v0639.py <0.6.38 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.6.38', b'version=0.6.39'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
REAPER_MAPS = ('TTosh01', 'THanson01')
# (button/upgrade id, research index, icon, hotkey, gate, row, col, reaper_only, name, tooltip)
NEW_R = [
    ('RMC_ReaperTriggers', 21, r'Assets\Textures\btn-upgrade-nova-equipment-gunblade_gun.dds', 'T', 'RMR_ReaperUnlocked', 1, 2, True,
     'ITC-E 방아쇠 /// ITC-E Triggers',
     '용병 사신의 권총과 D-8 폭탄 공격 속도가 약 25% 빨라집니다. 타이커스 협동전 연구를 고쳐 넣은 것입니다. /// Mercenary Reapers attack about 25% faster with pistols and D-8 charges. Adapted Tychus co-op research.'),
    ('RMC_ClusterCharges', 22, r'Assets\Textures\btn-upgrade-nova-btn-upgrade-nova-pulsegrenade.dds', 'C', 'RMR_ReaperUnlocked', 1, 3, True,
     'LE9 집속탄 /// LE9 Cluster Charges',
     '용병 사신의 D-8 폭탄 피해가 20 증가합니다. 한과 호너 협동전 연구를 고쳐 넣은 것입니다. /// Mercenary Reaper D-8 charges deal +20 damage. Adapted Han and Horner co-op research.'),
    ('RMC_Endurance', 23, r'Assets\Textures\btn-upgrade-mengsk-veterancy.dds', 'E', None, 1, 4, False,
     '지구력 보충제 /// Endurance Supplements',
     '악마의 개, 프로메테우스 중대, 망치 경호대, 이지스 근위대의 최대 생명력이 약 25% 증가합니다. 타이커스 협동전 연구입니다. /// Devil Dogs, Prometheus Company, Hammer Securities and Aegis Guards gain about 25% maximum life. Tychus co-op research.'),
    ('RMC_MedicSerum', 24, r'Assets\Textures\btn-unit-terran-medicelite.dds', 'P', None, 2, 0, False,
     '프로키온 혈청 /// Procyon Serum',
     '용병 의무관의 치료 속도가 초당 6 증가합니다. 타이커스 협동전 장비를 연구로 고쳐 넣은 것입니다. /// Mercenary Medics heal 6 more life per second. Tychus co-op gear adapted as research.'),
]
UPG = {
    'RMC_ReaperTriggers': '<AffectedUnitArray value="MercReaper" />'
        '<EffectArray Reference="Weapon,MercReaperP38ScytheGuassPistol,Period" Value="-0.22" />'
        '<EffectArray Reference="Weapon,MercReaperD8Charge,Period" Value="-0.36" />',
    'RMC_ClusterCharges': '<AffectedUnitArray value="MercReaper" /><EffectArray Reference="Effect,MercReaperD8ChargeDamage,Amount" Value="20" />',
    'RMC_Endurance': ''.join(f'<AffectedUnitArray value="{u}" />' for u, _ in (('DevilDog', 0), ('RM6_Prometheus', 0), ('HammerSecurity', 0), ('MarauderMengsk', 0)))
        + ''.join(f'<EffectArray Reference="Unit,{u},LifeMax" Value="{v}" /><EffectArray Reference="Unit,{u},LifeStart" Value="{v}" />'
                  for u, v in (('DevilDog', 40), ('RM6_Prometheus', 140), ('HammerSecurity', 30), ('MarauderMengsk', 130))),
    'RMC_MedicSerum': '<AffectedUnitArray value="MercMedic" /><EffectArray Reference="Effect,MercMedicHeal,RechargeVitalRate" Value="6" />'
        '<EffectArray Reference="Effect,MercMedicHealExtra,RechargeVitalRate" Value="6" />',
}
JUGG_OLD = '<EffectArray Reference="Unit,Firebat,LifeStart" Value="100" />'
JUGG_ADD = ('<AffectedUnitArray value="RM6_Prometheus" /><EffectArray Reference="Unit,RM6_Prometheus,LifeMax" Value="100" />'
            '<EffectArray Reference="Unit,RM6_Prometheus,LifeStart" Value="100" />')
ARMOR_OLD = '<AffectedUnitArray value="BunkerDepotMengsk" />'
ARMOR_ADD = ''.join(f'<AffectedUnitArray value="{u}" /><EffectArray Reference="Unit,{u},LifeMax" Value="200" />'
                    f'<EffectArray Reference="Unit,{u},LifeStart" Value="200" /><EffectArray Reference="Unit,{u},LifeArmor" Value="2" />'
                    for u in ('MissileTurret', 'ArtilleryMengsk'))
STR_FIX = {
    'Button/Tooltip/RMC_JuggernautCoop': '화염방사병, 악마의 개, 프로메테우스 중대의 생명력이 100 증가합니다. 레이너 협동전 연구입니다. /// Firebats, Devil Dogs and the Prometheus Company gain +100 life. Raynor co-op research.',
    'Button/Tooltip/StructureArmorMengskResearch': '<c val="ffff8a">보급 벙커, 미사일 포탑, 대지파괴 포</c>의 생명력이 200, 방어력이 2 증가합니다. /// Increases the life of <c val="ffff8a">Supply Bunkers, Missile Turrets and Earthsplitter Artillery</c> by 200 and their armor by 2.',
}
ANCHOR = '    TechTreeUpgradeAllow(1,"RMA_DevilDogUnlocked",true);\n'


def items(m):
    return [r for r in NEW_R if m in REAPER_MAPS or not r[7]]


def once(t, a, b):
    assert t.count(a) == 1, a[:80]
    return t.replace(a, b)


def edit(m, files):
    gd = f'{m}.SC2Map/base.sc2data/gamedata/'
    its = items(m)
    t = files[gd + 'abildata.xml'].decode('utf-8')
    mm = re.search(r'<CAbilResearch id="RM3_TechResearch">.*?</CAbilResearch>', t, re.S)
    assert not any(f'index="Research{r[1]}"' in mm.group(0) for r in its)
    add = ''.join(f'<InfoArray index="Research{n}" Time="60" Upgrade="{b}"><Resource index="Minerals" value="100" />'
                  f'<Resource index="Vespene" value="100" /><Button DefaultButtonFace="{b}" State="Available" Requirements="{b}Learn" /></InfoArray>'
                  for b, n, *_ in its)
    t = t[:mm.start()] + mm.group(0).replace('</CAbilResearch>', add + '</CAbilResearch>') + t[mm.end():]
    files[gd + 'abildata.xml'] = t.encode('utf-8')

    t = files[gd + 'unitdata.xml'].decode('utf-8')
    mm = re.search(r'<CUnit id="BarracksTechLab">.*?</CUnit>', t, re.S)
    u = mm.group(0)
    cm = re.search(r'<CardLayouts CardId="RMC1">(.*?)</CardLayouts>', u, re.S)
    used = set(re.findall(r'Row="(\d)" Column="(\d)"', cm.group(1)))
    btns = ''
    for b, n, icon, hk, gate, r, c, *_ in its:
        assert (str(r), str(c)) not in used, (m, b, r, c)
        btns += f'<LayoutButtons Face="{b}" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research{n}" Row="{r}" Column="{c}" />'
    u = u[:cm.end(1)] + btns + u[cm.end(1):]
    files[gd + 'unitdata.xml'] = (t[:mm.start()] + u + t[mm.end():]).encode('utf-8')

    up = files[gd + 'upgradedata.xml'].decode('utf-8')
    up = once(up, JUGG_OLD, JUGG_OLD + JUGG_ADD)
    am = re.search(r'<CUpgrade id="MengskStructureArmor">.*?</CUpgrade>', up, re.S)
    blk = once(am.group(0), ARMOR_OLD, ARMOR_OLD + ARMOR_ADD)
    up = up[:am.start()] + blk + up[am.end():]
    i = up.rindex('</Catalog>')
    up = up[:i] + ''.join(f'<CUpgrade id="{b}"><Race value="Terr" /><Alert value="ResearchComplete" /><Icon value="{icon}" />'
                          f'<EditorCategories value="Race:Terran,UpgradeType:Talents" />{UPG[b]}</CUpgrade>'
                          for b, n, icon, *_ in its) + up[i:]
    files[gd + 'upgradedata.xml'] = up.encode('utf-8')

    def app(path, xml):
        d = files[path]; i = d.rindex(b'</Catalog>'); files[path] = d[:i] + xml.encode('utf-8') + d[i:]
    app(gd + 'buttondata.xml', ''.join(f'<CButton id="{b}"><Icon value="{icon}" /><Name value="Button/Name/{b}" />'
                                       f'<Tooltip value="Button/Tooltip/{b}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>'
                                       for b, n, icon, *_ in its))
    req, node = '', ''
    for b, n, icon, hk, gate, *_ in its:
        req += f'<CRequirement id="{b}Learn"><NodeArray index="Show" Link="{b}Show" /></CRequirement>'
        node += (f'<CRequirementCountUpgrade id="{b}Queued"><Count Link="{b}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
                 f'<CRequirementNot id="{b}NotQueued"><OperandArray index="0" value="{b}Queued" /></CRequirementNot>')
        ops = f'<OperandArray value="{b}NotQueued" />'
        if gate:
            node += f'<CRequirementCountUpgrade id="{b}Gate"><Count Link="{gate}" State="CompleteOnly" /></CRequirementCountUpgrade>'
            ops += f'<OperandArray value="{b}Gate" />'
        node += f'<CRequirementAnd id="{b}Show">{ops}</CRequirementAnd>'
    app(gd + 'requirementdata.xml', req)
    app(gd + 'requirementnodedata.xml', node)

    sp = f'{m}.SC2Map/mapscript.galaxy'
    s = files[sp].decode('utf-8')
    nl = '\r\n' if '\r\n' in s else '\n'
    s = s.replace('\r\n', '\n')
    s = once(s, ANCHOR, ANCHOR + '    // 0.6.39: adapted co-op research page items.\n' + ''.join(
        f'    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",{n - 1}),true);\n    TechTreeUpgradeAllow(1,"{b}",true);\n'
        for b, n, *_ in its))
    files[sp] = s.replace('\n', nl).encode('utf-8')

    strs = dict(STR_FIX)
    for b, n, icon, hk, gate, r, c, ro, name, tip in its:
        strs[f'Button/Name/{b}'] = name; strs[f'Button/Tooltip/{b}'] = tip; strs[f'Upgrade/Name/{b}'] = name
    return strs, {f'Button/Hotkey/{b}': hk for b, n, icon, hk, *_ in its}


def set_strings(d, strs):
    t = d.decode('utf-8'); nl = '\r\n' if '\r\n' in t else '\n'
    lines = [l for l in t.split(nl) if l != '']
    keys = [l.split('=', 1)[0] for l in lines]
    for k, v in strs.items():
        if k in keys:
            lines[keys.index(k)] = f'{k}={v}'
        else:
            lines.append(f'{k}={v}'); keys.append(k)
    return (nl.join(lines) + nl).encode('utf-8')


def hotkeys(d, hk):
    bom = d.startswith(b'\xef\xbb\xbf'); t = d.decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'
    assert not any(f'{k}=' in t for k in hk)
    return (t.rstrip('\r\n') + nl + nl.join(f'{k}={v}' for k, v in hk.items()) + nl).encode('utf-8-sig' if bom else 'utf-8')


def build(src, out):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS:
            strs, hk = edit(m, files)
            ko = f'{m}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'
            files[ko] = set_strings(files[ko], strs)
            V35.gate('kokr', files[ko])
            for loc in V35.OTHER_LOCALES:
                files[f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[ko])
            for loc in ['kokr'] + V35.OTHER_LOCALES:
                p = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'
                files[p] = hotkeys(files[p], hk)
        import xml.etree.ElementTree as E
        for k, v in files.items():
            if k.endswith('.xml'): E.fromstring(v)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if not any(k.startswith(m + '.SC2Map/') for m in MAPS) and k != 'metadata.txt':
                        assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
