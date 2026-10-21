#!/usr/bin/env python3
"""Build CCM 0.4.58 from 0.4.57: 이지스 근위대 진급·코랄의 후예 인구 (사용자 지시 2026-10-21).

1. 이지스 근위대(MarauderMengsk, 4번 고용소)는 0.4.28 이식 때 '진급은 코랄의 후예에만' 규칙으로 계급을 빼고 넣었다.
   사용자: "이지스 근위대 … 레벨이 사라졌음" → 코랄의 후예와 같은 방식(처치 경험치, 3계급)으로 진급을 붙인다.
   계급 효과는 협동전 원본 MengskVeterancyMarauderMengsk 값(공격력 +25%·방어력 +1·생명력 +75, 계급마다).
   필요 경험치 1200/2400/3600 (시험값, 코랄의 후예 600/1200/1800의 두 배). 협동전 계급 능력(2계급 파편)은
   0.4.43에서 기본으로 주므로 따로 붙이지 않는다. 근위대 통치력·마스터 힘·사령관 레벨은 넣지 않는다.
2. 코랄의 후예(RMK_MarineMengsk) 인구 2 → 1 (사용자 "인구수가 큼 줄여줘", 해병과 같게; 1~4번 맵).

Usage: python3 tools/build_v0458.py <0.4.57 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.57', b'version=0.4.58'
MAPS = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
RANK = ('<Modification><DamageDealtFraction index="Melee" value="0.25" /><DamageDealtFraction index="Ranged" value="0.25" />'
        '<DamageDealtFraction index="Splash" value="0.25" /><LifeArmorBonus value="1" /><VitalMaxArray index="Life" value="75" /></Modification>')
VET = ('<CBehaviorVeterancy id="RMK_MengskVeterancyMarauderMengsk"><BehaviorFlags index="Permanent" value="1" />'
       '<BehaviorFlags index="EnabledWhileDead" value="1" /><EditorCategories value="AbilityorEffectType:Units,Race:Terran" />'
       '<XPFraction index="Kills" value="1" />'
       '<VeterancyLevelArray RankNameSchema="Behavior/RankName/RMK_KorhalRank0" />'
       f'<VeterancyLevelArray MinVeterancyXP="1200" RankNameSchema="Behavior/RankName/RMK_KorhalRank1">{RANK}</VeterancyLevelArray>'
       f'<VeterancyLevelArray MinVeterancyXP="2400" RankNameSchema="Behavior/RankName/RMK_KorhalRank2">{RANK}</VeterancyLevelArray>'
       f'<VeterancyLevelArray MinVeterancyXP="3600" RankNameSchema="Behavior/RankName/RMK_KorhalRank3">{RANK}</VeterancyLevelArray>'
       '</CBehaviorVeterancy>')
NAME = 'Behavior/Name/RMK_MengskVeterancyMarauderMengsk=이지스 근위대 계급 /// Aegis Guard Rank'


def food(d):
    t = d.decode('utf-8')
    m = re.search(r'<CUnit id="RMK_MarineMengsk">.*?</CUnit>', t, re.S)
    b = m.group(0)
    assert b.count('<Food value="-2" />') == 1
    return (t[:m.start()] + b.replace('<Food value="-2" />', '<Food value="-1" />') + t[m.end():]).encode('utf-8')


def units4(d):
    t = food(d).decode('utf-8')
    head = '<CUnit id="MarauderMengsk">'
    assert t.count(head) == 1 and 'RMK_MengskVeterancyMarauderMengsk' not in t
    t = t.replace(head, head + '\n        <BehaviorArray Link="RMK_MengskVeterancyMarauderMengsk" />')
    return t.encode('utf-8')


def behaviors(d):
    t = d.decode('utf-8')
    i = t.rindex('</Catalog>')
    return (t[:i] + VET + t[i:]).encode('utf-8')


def strings(d):
    t = d.decode('utf-8')
    assert 'RMK_MengskVeterancyMarauderMengsk' not in t
    return (t.rstrip('\r\n') + '\n' + NAME + '\n').encode('utf-8')


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m in MAPS[:3]:
            n = f'{m}.SC2Map/base.sc2data/gamedata/unitdata.xml'
            files[n] = food(files[n])
        files[GD + 'unitdata.xml'] = units4(files[GD + 'unitdata.xml'])
        files[GD + 'behaviordata.xml'] = behaviors(files[GD + 'behaviordata.xml'])
        files[KO] = strings(files[KO])
        V35.gate('kokr', files[KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M4}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[KO])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
