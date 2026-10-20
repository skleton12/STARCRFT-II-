#!/usr/bin/env python3
"""Build CCM 0.4.45 from 0.4.44: 전투 안정제·철인 장갑은 자날판 대신 협동전판 (4번, 사용자 선택 C 2026-10-20).

사용자 지적: 1페이지 자날 무기고판과 2페이지 협동전판이 같은 기능을 두 번 연구하는 중첩이다.
선택 C: 히페리온 무기고에서 안 샀으면 협동전판만 미션 안에서 연구한다. 샀으면 무기고(자날) 효과만 있고 협동전판은 안 나온다.
  - 1페이지 RMA_StabilizerMedPacks·RMA_FirebatJuggernautPlating 버튼을 없애고 연구 칸을 숨긴다.
  - 2페이지 RMC_StabilizerCoop·RMC_JuggernautCoop 은 '무기고판을 사지 않았을 때'만 보인다 (기존 조건에 더함).
파편탄을 충격탄에 합침 (사용자 2026-10-20 "산탄을 충격탄과 합하는게 나을듯"): 파편탄 연구 버튼을 없애고, 충격탄 연구 하나로
  감속 + 파편(부채꼴 피해·감속)을 준다. 망치 경호대만. 이지스 근위대는 원래대로 기본 파편.

Usage: python3 tools/build_v0445.py <0.4.44 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.44', b'version=0.4.45'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'


def rep(t, a, b):
    assert t.count(a) == 1, a
    return t.replace(a, b)


def units(d):
    t = d.decode('utf-8')
    t = rep(t, '<LayoutButtons Face="RMA_StabilizerMedPacks" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research11" Row="1" Column="4" />', '')
    t = rep(t, '<LayoutButtons Face="RMA_FirebatJuggernautPlating" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research14" Row="2" Column="2" />', '')
    t = rep(t, '<LayoutButtons Face="RM4_Shrapnel" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research9" Row="0" Column="1" />', '')
    return t.encode('utf-8')


def abil(d):
    t = d.decode('utf-8')
    for b in ('RMA_StabilizerMedPacks', 'RMA_FirebatJuggernautPlating', 'RM4_Shrapnel'):
        t = rep(t, f'<Button DefaultButtonFace="{b}" State="Available" Requirements="{b}Learn" />',
                f'<Button DefaultButtonFace="{b}" State="Suppressed" Requirements="{b}Learn" />')
    return t.encode('utf-8')


def reqs(d):
    t = d.decode('utf-8')
    return rep(t, '<NodeArray index="Show" Link="RMC_StabilizerCoopNotQueued" />',
               '<NodeArray index="Show" Link="RMC_StabilizerCoopShow" />').encode('utf-8')


def nodes(d):
    t = d.decode('utf-8')
    # RMA_*NotQueued = the WoL armory upgrade is neither bought nor being researched.
    t, n = re.subn(r'(<CRequirementAnd id="RMC_JuggernautCoopShow">.*?)(\s*</CRequirementAnd>)',
                   r'\1<OperandArray index="2" value="RMA_FirebatJuggernautPlatingNotQueued" />\2', t, count=1, flags=re.S)
    assert n == 1
    assert 'id="RMC_StabilizerCoopShow"' not in t
    i = t.rindex('</Catalog>')
    t = t[:i] + ('<CRequirementAnd id="RMC_StabilizerCoopShow"><OperandArray index="0" value="RMC_StabilizerCoopNotQueued" />'
                 '<OperandArray index="1" value="RMA_StabilizerMedPacksNotQueued" /></CRequirementAnd>') + t[i:]
    return t.encode('utf-8')


def validators(d):
    t = d.decode('utf-8')
    t, n = re.subn(r'(<CValidatorPlayerRequirement id="RM4_HaveShrapnel">\s*<Value value=")RM4_ShrapnelUse(")', r'\1RM4_ConcussiveUse\2', t)
    assert n == 1
    return t.encode('utf-8')


TIP = ('Button/Tooltip/RM4_Concussive=<c val="ffff8a">망치 경호대</c>의 공격에 맞은 적의 이동 속도가 잠시 느려지고, 대상 뒤 부채꼴 범위에 '
       '파편을 흩뿌려 적에게 4(장갑 +4)의 피해를 주고 느리게 합니다. 파편탄을 합친 연구입니다. /// Units hit by <c val="ffff8a">Hammer Securities</c> '
       'are briefly slowed, and shrapnel sprays in a cone behind the target, dealing 4 (+4 vs Armored) damage and slowing. Includes Shrapnel Shells.')


def strings(d):
    t = d.decode('utf-8')
    t, n = re.subn(r'Button/Tooltip/RM4_Concussive=[^\r\n]*', lambda m: TIP, t)
    assert n == 1
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'unitdata.xml': units, GD + 'abildata.xml': abil,
       GD + 'requirementdata.xml': reqs, GD + 'requirementnodedata.xml': nodes, GD + 'validatordata.xml': validators,
       'TTychus01.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt': strings}


def build(source, output):
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        ko = files['TTychus01.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt']
        V35.gate('kokr', ko)
        for loc in V35.OTHER_LOCALES:
            files[f'TTychus01.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(ko)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if not n.startswith('TTychus01.SC2Map/') and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
