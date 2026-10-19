#!/usr/bin/env python3
"""Build CCM 0.4.30 from 0.4.29: 이지스 근위대 고용 잠금 해제 + 불곰 연구가 '망치 경호대를 가지고 있을 때'만 보이던 것 (4번).

0.4.16의 조건 RM4_HaveHammer가 망치 경호대 유닛 수(1기 이상)를 봤다 → 불곰이 없으면 연구 버튼이 사라졌다.
원래 뜻은 '불곰 생산이 해금됐을 때'. 스크립트가 병영 불곰 생산(BarracksTrain 3) 허용을 확인하면
숨은 표시 업그레이드 RM4_HammerUnlocked를 켜고, RM4_HaveHammer는 그 표시를 본다 (사용자 확인 2026-10-19).

Usage: python3 tools/build_v0430.py <0.4.29 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.29', b'version=0.4.30'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'
TICK_OLD = '    gf_m4_Mercs();\n    gf_m4_Skin(8);'
TICK_NEW = ('    gf_m4_Mercs();\n'
            '    // Marauder research shows once Barracks may train Hammer Security (0.4.30), not only while one is alive.\n'
            '    if (TechTreeUpgradeCount(1,"RM4_HammerUnlocked",c_techCountQueuedOrBetter)==0 && TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",3))) {\n'
            '        TechTreeUpgradeAddLevel(1,"RM4_HammerUnlocked",1);\n'
            '    }\n'
            '    gf_m4_Skin(8);')
NODE_OLD = '<CRequirementCountUnit id="RM4_HaveHammer">\n        <Count Link="HammerSecurity" State="CompleteOnly" />\n    </CRequirementCountUnit>'
NODE_NEW = '<CRequirementCountUpgrade id="RM4_HaveHammer"><Count Link="RM4_HammerUnlocked" State="CompleteOnly" /></CRequirementCountUpgrade>'


def rep(a, b):
    def fn(d):
        t = d.decode('utf-8')
        assert t.count(a) == 1, a
        return t.replace(a, b).encode('utf-8')
    return fn


def upgrade(d):
    assert b'id="RM4_HammerUnlocked"' not in d
    i = d.rindex(b'</Catalog>')
    return d[:i] + b'<CUpgrade id="RM4_HammerUnlocked"><Race value="Terr" /></CUpgrade>' + d[i:]


HIRE_OLD = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",0),true);\n'
# 0.4.28 Aegis Guard hire (Train4) and its unit were still campaign-locked (no contract) -> allow them like Coral's Heirs.
HIRE_NEW = HIRE_OLD + ('    TechTreeUnitAllow(1,"MarauderMengsk",true);\n'
                       '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",3),true);\n')


def chain(*fns):
    def fn(d):
        for f in fns: d = f(d)
        return d
    return fn


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW),
       'TTychus01.SC2Map/mapscript.galaxy': chain(rep(HIRE_OLD, HIRE_NEW), rep('    gf_rmUpSync(8,9);\n    gf_m4_Skin(8);',
                                                TICK_NEW.replace('    gf_m4_Mercs();\n', '').replace('    gf_m4_Skin(8);', '    gf_rmUpSync(8,9);\n    gf_m4_Skin(8);'))),
       GD + 'requirementnodedata.xml': rep(NODE_OLD, NODE_NEW),
       GD + 'upgradedata.xml': upgrade}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), FIX[info.filename](d) if info.filename in FIX else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
