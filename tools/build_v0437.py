#!/usr/bin/env python3
"""Build CCM 0.4.37 from 0.4.36: 억제탄을 파편탄에 합친다 (4번, 사용자 지시 2026-10-19).

사용자: "억제탄이랑 파편탄을 융합, 업그레이드는 파편탄이지만 효과는 둘 다".
  - 기술실 억제탄 버튼(Research7)을 없앤다 (업그레이드 데이터는 남김).
  - 파편탄 하나로: 부채꼴 파편 피해 4(장갑 +4) + 파편 맞은 적 감속 + 대상 주변 반경 1 감속.
  - 감속은 원작 Slow(1.5초, 이동 50%)를 쓰되 충격탄 검사 없이 파편탄만 보고 건다. 거대·건물 제외.
불곰 미션(4번)은 히페리온 무기고 불곰 항목이 열리기 전이라 구매 효과와 겹칠 일이 없다 (사용자).

Usage: python3 tools/build_v0437.py <0.4.36 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.36', b'version=0.4.37'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
TIP = ('Button/Tooltip/RM4_Shrapnel=<c val="ffff8a">망치 경호대</c>의 공격이 대상 뒤 부채꼴 범위에 파편을 흩뿌려 적에게 4(장갑 +4)의 피해를 주고, '
       '파편에 맞은 적과 대상 주변의 적을 느리게 합니다. 거대 유닛은 감속되지 않습니다. 억제탄을 합친 모드 연구입니다. /// '
       '<c val="ffff8a">Hammer Security</c> attacks spray shrapnel in a cone behind the target, dealing 4 (+4 vs Armored) damage, '
       'and slow enemies hit by shrapnel and around the target. Massive units are not slowed. Merges Suppression Shells (mod research).')
SLOW = ('<CEffectApplyBehavior id="RM4_ShrapnelSlow"><Behavior value="Slow" /><ValidatorArray value="PunisherGrenadesSlowTargetFilters" />'
        '<ValidatorArray value="NotStructure" /><ValidatorArray value="NotFrenzied" /></CEffectApplyBehavior>'
        '<CEffectSet id="RM4_ShrapnelHitSet"><EffectArray value="RM4_ShrapnelDamage" /><EffectArray value="RM4_ShrapnelSlow" /></CEffectSet>')


def sub1(t, a, b):
    assert t.count(a) == 1, a
    return t.replace(a, b)


def effects(d):
    t = d.decode('utf-8')
    m = re.search(r'<CEffectEnumArea id="RM4_SuppressAOE">.*?</CEffectEnumArea>', t, re.S)
    s = m.group(0)
    s = sub1(s, 'Effect="PunisherGrenadesSlow"', 'Effect="RM4_ShrapnelSlow"')
    s = sub1(s, 'value="RM4_HaveSuppression"', 'value="RM4_HaveShrapnel"')
    t = t[:m.start()] + s + t[m.end():]
    m = re.search(r'<CEffectEnumArea id="RM4_ShrapnelSearch">.*?</CEffectEnumArea>', t, re.S)
    t = t[:m.start()] + sub1(m.group(0), 'Effect="RM4_ShrapnelDamage"', 'Effect="RM4_ShrapnelHitSet"') + t[m.end():]
    t = t.replace('</Catalog>', SLOW + '</Catalog>')
    return t.encode('utf-8')


def abil(d):
    t = d.decode('utf-8')
    return sub1(t, '<Button DefaultButtonFace="RM4_Suppression" State="Available" Requirements="RM4_SuppressionLearn" />',
                '<Button DefaultButtonFace="RM4_Suppression" State="Suppressed" Requirements="RM4_SuppressionLearn" />').encode('utf-8')


def units(d):
    t = d.decode('utf-8')
    return sub1(t, '<LayoutButtons Face="RM4_Suppression" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research7" Row="0" Column="2" />', '').encode('utf-8')


def strings(d):
    t = d.decode('utf-8')
    t, n = re.subn(r'Button/Tooltip/RM4_Shrapnel=[^\r\n]*', lambda m: TIP, t)
    assert n == 1
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'effectdata.xml': effects,
       GD + 'abildata.xml': abil, GD + 'unitdata.xml': units, KO: strings}


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
