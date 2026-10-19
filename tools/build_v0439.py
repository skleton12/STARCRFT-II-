#!/usr/bin/env python3
"""Build CCM 0.4.39 from 0.4.38: 무기고에서 안 산 불곰 기술을 미션 안에서 연구 (4번, 망치 경호대만).

사용자 지시 (2026-10-19): 히페리온 무기고에서 사지 않은 것은 미션 안에서 연구되게. 불곰(용병 망치 경호대)만.
  자날 무기고 불곰 항목 두 개:
  - 충격탄 (JackhammerConcussionGrenades): 이미 기술실 충격탄 연구가 있고, 샀으면 완료로 친다 (0.4.13, 0.4.36).
  - 동역학 충격완화복 (MarauderLifeBoost, 망치 경호대 생명력 +25): 이번에 기술실 연구로 추가한다.
    연구를 끝내면 무기고 구매와 같은 업그레이드를 켠다. 샀으면 버튼이 안 나온다. 100/100·60초 (시험값).

Usage: python3 tools/build_v0439.py <0.4.38 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.38', b'version=0.4.39'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
ICON = r'Assets\Textures\btn-techupgrade-terran-kineticfoam.dds'
STR = {
    'Button/Name/RM4_KineticFoam': '동역학 충격완화복 /// Kinetic Foam',
    'Button/Tooltip/RM4_KineticFoam': '<c val="ffff8a">망치 경호대</c>의 생명력이 25 증가합니다. 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다. /// '
                                      '<c val="ffff8a">Hammer Security</c> gain +25 life. Researched in the mission when not bought at the Hyperion Armory.',
}
SCRIPT_OLD = '    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",8),true);\n'
SCRIPT_NEW = SCRIPT_OLD + ('    // Armory items not bought are researched in the mission (user 2026-10-19): Kinetic Foam.\n'
                           '    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",9),true);\n'
                           '    TechTreeUpgradeAllow(1,"MarauderLifeBoost",true);\n')


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
    assert 'RM4_KineticFoam' not in t
    return (t.rstrip('\r\n') + nl + 'Button/Hotkey/RM4_KineticFoam=F' + nl).encode('utf-8-sig' if d.startswith(b'\xef\xbb\xbf') else 'utf-8')


FIX = {
    'metadata.txt': lambda d: d.replace(OLD, NEW),
    M4 + 'mapscript.galaxy': rep(SCRIPT_OLD, SCRIPT_NEW),
    GD + 'abildata.xml': rep('Requirements="RM4_ShrapnelLearn" /></InfoArray></CAbilResearch>',
                             'Requirements="RM4_ShrapnelLearn" /></InfoArray><InfoArray index="Research10" Time="60" Upgrade="MarauderLifeBoost">'
                             '<Resource index="Minerals" value="100" /><Resource index="Vespene" value="100" />'
                             '<Button DefaultButtonFace="RM4_KineticFoam" State="Available" Requirements="RM4_KineticFoamLearn" /></InfoArray></CAbilResearch>'),
    GD + 'unitdata.xml': rep('<LayoutButtons Face="RM4_Shrapnel" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research9" Row="1" Column="2" />',
                             '<LayoutButtons Face="RM4_Shrapnel" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research9" Row="1" Column="2" />'
                             '<LayoutButtons Face="RM4_KineticFoam" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research10" Row="1" Column="3" />'),
    GD + 'buttondata.xml': append(f'<CButton id="RM4_KineticFoam"><Icon value="{ICON}" /><Name value="Button/Name/RM4_KineticFoam" />'
                                  '<Tooltip value="Button/Tooltip/RM4_KineticFoam" /><TooltipFlags index="ShowLevel" value="0" /></CButton>'),
    GD + 'requirementdata.xml': append('<CRequirement id="RM4_KineticFoamLearn"><NodeArray index="Show" Link="RM4_KineticFoamShow" /></CRequirement>'),
    GD + 'requirementnodedata.xml': append(
        '<CRequirementCountUpgrade id="RM4_KineticFoamQueued"><Count Link="MarauderLifeBoost" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
        '<CRequirementNot id="RM4_KineticFoamNotQueued"><OperandArray value="RM4_KineticFoamQueued" /></CRequirementNot>'
        '<CRequirementAnd id="RM4_KineticFoamShow"><OperandArray index="0" value="RM4_KineticFoamNotQueued" />'
        '<OperandArray index="1" value="RM4_HaveHammer" /></CRequirementAnd>'),
    KO: strings,
}


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        V35.gate('kokr', files[KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M4}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[KO])
        for loc in ['kokr'] + V35.OTHER_LOCALES:
            files[f'{M4}{loc}.sc2data/localizeddata/gamehotkeys.txt'] = hotkeys(files[f'{M4}{loc}.sc2data/localizeddata/gamehotkeys.txt'])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if not n.startswith(M4) and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
