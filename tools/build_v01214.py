#!/usr/bin/env python3
"""0.12.13 -> 0.12.14: 피닉스 용사 탈리스 멈춤 (사용자 2026-11-27 "탈리스 안움직이는 버그 그대로").

0.9.6에서 정의 없는 전술 AI 함수를 지웠지만 그대로였다. 다음 후보(코덱스 0.9.6 의견): 자동 시전 '튕기는 공격'.
FenixTalisAdeptBounceShot은 공격 명령에 붙는 CAbilAugment이고, 첫 탄(FenixTalisAdeptBounceShotLM1)에
'대상까지 길 거리 6.1 미만'(Pathing=1) 검사가 있다. 절벽·건물 너머 적처럼 길 거리가 멀면 이 검사가 실패하고
증강된 공격 명령이 취소돼 탈리스가 멈출 수 있다 (게임 확인 필요).

maps 3~9·11·12 (탈리스가 있는 맵):
  - 탈리스 능력 목록에서 증강 능력을 빼고, 명령 카드 (2,1) 버튼은 같은 아이콘의 패시브 표시로.
  - 대신 무기 효과를 묶음(RM14_TalisAttackSet)으로: 원래 탄(FenixTalisAdeptLM) + 튕기는 탄.
    튕기는 탄은 숨은 5초 대기 행동(RM14_TalisBounceCD)이 없을 때만 나가고 나가면 대기를 건다 = 원래 재사용 대기 5초.
  - 튕기는 첫 탄은 길 거리 검사 없는 복사본(RM14_TalisBounceLM1, 무기 사거리 4 안이라 필요 없음).
피해·튕김 수·대상은 원작 그대로. Game not run.

Usage: python3 tools/build_v01214.py <0.12.13 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.12.13', b'version=0.12.14'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
G = '.SC2Map/base.sc2data/gamedata/'

EFFECTS = '''    <CEffectSet id="RM14_TalisAttackSet">
        <EditorCategories value="Race:Protoss" />
        <EffectArray value="FenixTalisAdeptLM" />
        <EffectArray value="RM14_TalisBounceSet" />
    </CEffectSet>
    <CEffectSet id="RM14_TalisBounceSet">
        <EditorCategories value="Race:Protoss" />
        <ValidatorArray value="RM14_TalisBounceReady" />
        <EffectArray value="RM14_TalisBounceCDAB" />
        <EffectArray value="RM14_TalisBounceLM1" />
    </CEffectSet>
    <CEffectApplyBehavior id="RM14_TalisBounceCDAB">
        <EditorCategories value="Race:Protoss" />
        <WhichUnit Value="Caster" />
        <Behavior value="RM14_TalisBounceCD" />
    </CEffectApplyBehavior>
    <CEffectLaunchMissile id="RM14_TalisBounceLM1">
        <EditorCategories value="Race:Protoss" />
        <ImpactEffect value="FenixTalisAdeptBounceShotSet1" />
    </CEffectLaunchMissile>
'''
BEHAVIOR = '''    <CBehaviorBuff id="RM14_TalisBounceCD">
        <EditorCategories value="Race:Protoss" />
        <InfoFlags index="Hidden" value="1" />
        <Duration value="5" />
    </CBehaviorBuff>
'''
VALIDATOR = '''    <CValidatorUnitCompareBehaviorCount id="RM14_TalisBounceReady">
        <WhichUnit Value="Caster" />
        <Behavior value="RM14_TalisBounceCD" />
        <Compare value="EQ" />
        <Value value="0" />
    </CValidatorUnitCompareBehaviorCount>
'''


def one(t, tag, i):
    m = list(re.finditer(r'<%s id="%s"[^>]*>.*?</%s>' % (tag, i, tag), t, re.S)); assert len(m) == 1, (tag, i, len(m))
    return m[0]


def append(t, block):
    k = t.rindex('</Catalog>'); return t[:k] + block + t[k:]


def p_unit(t, m):
    e = one(t, 'CUnit', 'FenixTalisAdept'); b = e.group(0)
    a = '\n        <AbilArray Link="FenixTalisAdeptBounceShot" />'; assert b.count(a) == 1, m
    c = '<LayoutButtons Face="FenixTalisAdeptBounceShot" Type="AbilCmd" AbilCmd="FenixTalisAdeptBounceShot,Execute" Row="2" Column="1" />'
    assert b.count(c) == 1, m
    b = b.replace(a, '').replace(c, '<LayoutButtons Face="FenixTalisAdeptBounceShot" Type="Passive" Row="2" Column="1" />')
    return t[:e.start()] + b + t[e.end():]


def p_weapon(t, m):
    e = one(t, 'CWeaponLegacy', 'FenixTalisAdept'); b = e.group(0)
    a = '<Effect value="FenixTalisAdeptLM" />'; assert b.count(a) == 1, m
    return t[:e.start()] + b.replace(a, '<Effect value="RM14_TalisAttackSet" />') + t[e.end():]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            for f, fn in (('unitdata.xml', p_unit), ('weapondata.xml', p_weapon),
                          ('effectdata.xml', lambda t, m: append(t, EFFECTS)),
                          ('behaviordata.xml', lambda t, m: append(t, BEHAVIOR)),
                          ('validatordata.xml', lambda t, m: append(t, VALIDATOR))):
                k = m + G + f; t = files[k].decode('utf-8')
                assert 'RM14_Talis' not in t or f in ('unitdata.xml', 'weapondata.xml'), (m, f)
                t = fn(t, m); E.fromstring(t.encode('utf-8'))
                files[k] = t.encode('utf-8'); changed.add(k)
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
