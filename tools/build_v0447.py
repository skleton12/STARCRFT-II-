#!/usr/bin/env python3
"""Build CCM 0.4.47 from 0.4.46: 숨겨 둔 기술실 연구 네 개를 다시 보이게 한다 (4번, 사용자 지시 2026-10-20).

사용자: "불곰 나오는 맵에서는 저거 필요한데 … 고쳐봐 일단 나오게" — 숨겨져 있던 연구 전부.
  - 억제탄(Research7)·파편탄(Research9): 0.4.37·0.4.45 합치기를 되돌린다. 0.4.35 사용자 지정 자리대로
    첫째 줄 3번 칸(0,2)은 충격탄 → 억제탄, 4번 칸(0,3)은 파편탄.
    효과도 다시 나눈다 (0.4.46의 '업그레이드가 반경을 바꾸는' 방식은 유지):
      충격탄 PunisherGrenades = 원작 감속만 (맵 재정의 삭제),
      억제탄 RM4_Suppression = 대상 주변 감속 반경 +1,
      파편탄 RM4_Shrapnel = 대상 뒤 부채꼴 파편 반경 +3 (피해 4·장갑 +4만, 0.4.37에서 붙인 감속은 뗌).
  - 자날판 전투 안정제(Research11, 1,4)·철인 장갑(Research14, 2,2): 0.4.45 선택 C로 숨겼던 버튼을 되살린다.
    협동전판과 효과가 겹치지 않게 둘 중 하나를 연구(또는 무기고 구매)하면 다른 쪽 버튼이 사라진다.
수치·비용·시간은 그대로 (시험값). 4번 맵만.

Usage: python3 tools/build_v0447.py <0.4.46 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.46', b'version=0.4.47'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
# (button face, research index, row, col)
SHOW = [('RM4_Suppression', 7, 0, 2), ('RM4_Shrapnel', 9, 0, 3),
        ('RMA_StabilizerMedPacks', 11, 1, 4), ('RMA_FirebatJuggernautPlating', 14, 2, 2)]
TIPS = {
    'RM4_Concussive': '<c val="ffff8a">망치 경호대</c>의 공격에 맞은 적의 이동 속도가 잠시 느려집니다. /// '
                      'Units hit by <c val="ffff8a">Hammer Securities</c> are briefly slowed.',
    'RM4_Shrapnel': '<c val="ffff8a">망치 경호대</c>의 공격이 대상 뒤 부채꼴 범위에 파편을 흩뿌려 적에게 4(장갑 +4)의 피해를 줍니다. /// '
                    '<c val="ffff8a">Hammer Security</c> attacks spray shrapnel in a cone behind the target, dealing 4 (+4 vs Armored) damage.',
}


def rep(t, a, b):
    assert t.count(a) == 1, a
    return t.replace(a, b)


def abil(d):
    t = d.decode('utf-8')
    for face, *_ in SHOW:
        t = rep(t, f'<Button DefaultButtonFace="{face}" State="Suppressed" Requirements="{face}Learn" />',
                f'<Button DefaultButtonFace="{face}" State="Available" Requirements="{face}Learn" />')
    return t.encode('utf-8')


def units(d):
    t = d.decode('utf-8')
    anchor = '<LayoutButtons Face="RM4_Concussive" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research6" Row="0" Column="2" />'
    add = ''.join(f'<LayoutButtons Face="{f}" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research{i}" Row="{r}" Column="{c}" />'
                  for f, i, r, c in SHOW)
    for f, *_ in SHOW:
        assert f'Face="{f}"' not in t, f
    return rep(t, anchor, anchor + add).encode('utf-8')


def effects(d):
    t = d.decode('utf-8')
    t = rep(t, '<AreaArray Arc="59.9963" Radius="0" Effect="RM4_ShrapnelHitSet" />',
            '<AreaArray Arc="59.9963" Radius="0" Effect="RM4_ShrapnelDamage" />')
    t, n = re.subn(r'\s*<CEffectSet id="RM4_ShrapnelHitSet">.*?</CEffectSet>', '', t, flags=re.S)
    assert n == 1 and 'RM4_ShrapnelHitSet' not in t
    return t.encode('utf-8')


def upgrades(d):
    t = d.decode('utf-8')
    t = rep(t, '<CUpgrade id="PunisherGrenades"><EffectArray Reference="Effect,RM4_ShrapnelSearch,AreaArray[0].Radius" Value="3" />'
               '<EffectArray Reference="Effect,RM4_SuppressAOE,AreaArray[0].Radius" Value="1" /></CUpgrade>', '')
    for up, eff, v in (('RM4_Suppression', 'RM4_SuppressAOE', 1), ('RM4_Shrapnel', 'RM4_ShrapnelSearch', 3)):
        t, n = re.subn(rf'(<CUpgrade id="{up}">.*?)(\s*</CUpgrade>)',
                       rf'\1<EffectArray Reference="Effect,{eff},AreaArray[0].Radius" Value="{v}" />\2', t, count=1, flags=re.S)
        assert n == 1, up
    return t.encode('utf-8')


def validators(d):
    t = d.decode('utf-8')
    t, n = re.subn(r'(<CValidatorPlayerRequirement id="RM4_HaveShrapnel">\s*<Value value=")RM4_ConcussiveUse(")', r'\1RM4_ShrapnelUse\2', t)
    assert n == 1
    return t.encode('utf-8')


def reqs(d):
    t = d.decode('utf-8')
    return rep(t, '<NodeArray index="Show" Link="RMA_StabilizerMedPacksNotQueued" />',
               '<NodeArray index="Show" Link="RMA_StabilizerMedPacksShow" />').encode('utf-8')


def nodes(d):
    t = d.decode('utf-8')
    # 자날판 버튼은 협동전판이 연구 중이거나 끝났으면 숨긴다 (협동전판은 0.4.45부터 반대 조건을 가짐).
    t, n = re.subn(r'(<CRequirementAnd id="RMA_FirebatJuggernautPlatingShow">.*?)(\s*</CRequirementAnd>)',
                   r'\1<OperandArray index="2" value="RMC_JuggernautCoopNotQueued" />\2', t, count=1, flags=re.S)
    assert n == 1
    assert 'id="RMA_StabilizerMedPacksShow"' not in t
    i = t.rindex('</Catalog>')
    t = t[:i] + ('<CRequirementAnd id="RMA_StabilizerMedPacksShow"><OperandArray index="0" value="RMA_StabilizerMedPacksNotQueued" />'
                 '<OperandArray index="1" value="RMC_StabilizerCoopNotQueued" /></CRequirementAnd>') + t[i:]
    return t.encode('utf-8')


def strings(d):
    t = d.decode('utf-8')
    for k, v in TIPS.items():
        t, n = re.subn(rf'Button/Tooltip/{k}=[^\r\n]*', lambda m: f'Button/Tooltip/{k}={v}', t)
        assert n == 1, k
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'abildata.xml': abil, GD + 'unitdata.xml': units,
       GD + 'effectdata.xml': effects, GD + 'upgradedata.xml': upgrades, GD + 'validatordata.xml': validators,
       GD + 'requirementdata.xml': reqs, GD + 'requirementnodedata.xml': nodes, KO: strings}


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
