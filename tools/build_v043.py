#!/usr/bin/env python3
"""Build CCM 0.4.3 from 0.4.2: 무력화탄 → 파편탄 (4번 TTychus01).

사용자 지시 (2026-10-18): 무력화탄 대신 이지스 근위대 2등급 능력(파편)을 연구로 넣는다.
  원본: 멩스크 협동전 진급 2등급 MarauderMengskShrapnel — 공격 시 대상 뒤 부채꼴(반경 3, 60도)의 적에게 피해 4(장갑 +4).
  진급 능력이었으므로 이 모드에서는 '모드에서 재설계한 연구'다 (CLAUDE.md 4장). 연구 칸·비용·시간은 무력화탄 자리 그대로 (100/100·60초).
  망치 경호대 대상 감속은 원래 충격탄 감속으로 되돌린다 (무력화 감속 스위치 제거).

Usage: python3 tools/build_v043.py <0.4.2 zip> <new output zip>
"""
import argparse
import copy
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.2', b'version=0.4.3'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
ICON = r'Assets\Textures\btn-techupgrade-terran-clusterwarheads.dds'
STRINGS = {
    'Button/Name/RM4_Shrapnel': '파편탄 /// Shrapnel Shells',
    'Button/Tooltip/RM4_Shrapnel': '<c val="ffff8a">망치 경호대</c>의 공격이 대상 뒤 부채꼴 범위에 파편을 흩뿌려 적에게 4(장갑 +4)의 피해를 줍니다. 이지스 근위대 2등급 능력을 연구로 바꾼 것입니다. /// <c val="ffff8a">Hammer Security</c> attacks spray shrapnel in a cone behind the target, dealing 4 (+4 vs Armored) damage. The Aegis Guard rank 2 ability, made a research.',
    'Upgrade/Name/RM4_Shrapnel': '파편탄 /// Shrapnel Shells',
    'Effect/Name/RM4_ShrapnelDamage': '파편탄 /// Shrapnel Shells',
}
DROP_KEYS = ('RM4_Incapacitator', 'RM4_IncapSlow')
NEW_EFFECTS = ('<CEffectDamage id="RM4_ShrapnelDamage" parent="DU_WEAP"><AttributeBonus index="Armored" value="4" /><Kind value="Ranged" />'
               '<KindSplash value="Splash" /><Amount value="4" /><Death value="Eviscerate" /></CEffectDamage>'
               '<CEffectEnumArea id="RM4_ShrapnelSearch"><LaunchLocation Value="CasterUnit" /><ImpactLocation Value="TargetUnit" />'
               '<ExcludeArray Value="Target" /><SearchFilters value="Ground;Self,Player,Ally,Missile,Stasis,Dead,Hidden,Invulnerable" />'
               '<AreaArray Arc="59.9963" Radius="3" Effect="RM4_ShrapnelDamage" /><ValidatorArray value="RM4_HaveShrapnel" /></CEffectEnumArea>')


def ren(data):
    return data.replace(b'RM4_Incapacitator', b'RM4_Shrapnel')


def effects(data):
    root = E.fromstring(ren(data))
    drop = {'RM4_HammerSlowSwitch', 'RM4_IncapSlowAB'}
    for e in [e for e in root if e.get('id') in drop]: root.remove(e)
    for e in root:
        if e.get('id') == 'RM4_SuppressAOE':
            e.find('AreaArray').set('Effect', 'PunisherGrenadesSlow')
        if e.tag == 'CEffectSet' and e.get('id') == 'HammerSecuritySet' and e.find('EffectArray[@index="0"]') is not None:
            e.remove(e.find('EffectArray[@index="0"]'))
            E.SubElement(e, 'EffectArray', value='RM4_ShrapnelSearch')
    for el in E.fromstring('<C>' + NEW_EFFECTS + '</C>'): root.append(el)
    out = E.tostring(root, encoding='utf-8', xml_declaration=True)
    assert b'RM4_HammerSlowSwitch' not in out and b'RM4_IncapSlow' not in out
    return out


def behaviors(data):
    root = E.fromstring(data)
    for e in [e for e in root if e.get('id') == 'RM4_IncapSlow']: root.remove(e)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def icons(data):
    root = E.fromstring(ren(data))
    for e in root:
        if e.get('id') == 'RM4_Shrapnel': e.find('Icon').set('value', ICON)
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def strings(data):
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    lines = [l for l in text.split(nl) if not any(k in l.split('=', 1)[0] for k in DROP_KEYS)]
    while lines and lines[-1] == '': lines.pop()
    lines += [f'{k}={v}' for k, v in STRINGS.items()] + ['']
    return nl.join(lines).encode('utf-8')


FIX = {GD + 'effectdata.xml': effects, GD + 'behaviordata.xml': behaviors, GD + 'buttondata.xml': icons,
       GD + 'upgradedata.xml': icons, GD + 'abildata.xml': ren, GD + 'unitdata.xml': ren, GD + 'validatordata.xml': ren,
       GD + 'requirementdata.xml': ren, GD + 'requirementnodedata.xml': ren, KO: strings,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for name, fn in FIX.items(): files[name] = fn(files[name])
        V35.gate('kokr', files[KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M4}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[KO])
        assert not any(b'RM4_Incap' in d for n, d in files.items() if n.startswith(M4) and not n.lower().startswith(M4.lower() + 'assets'))
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
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
