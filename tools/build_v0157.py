#!/usr/bin/env python3
"""0.15.6 -> 0.15.7: 충격 전차가 공성 -> 전차 모드로 바뀔 때 투명해지던 것 (사용자 2026-11-28).
원인: 공성 해제 전환 액터 SiegeTankMengskMorph(TankModeMorphModel, 모델 SiegeTank_Mengsk_COOP_Morph)가 이식 때 빠짐.
협동전 원본 그대로 10개 공장 맵 actordata에 넣는다(BlackOps 줄 제외, 0.15.6). 또 (사용자 "수송선에 나와야하는게 공성 파괴단", "충격전차는 용병고용소에서 고용되어야하는 용병", "용병 고용소에 왜 충격사단 없음"):
0.15.3의 스크립트 바꿈(군수 공장·수송선·주기 바꿈·해금 확인의 SiegeBreaker -> SiegeTankMengsk)을 되돌려 일반 공성 전차 = 공성 파괴단,
충격 전차는 고용소에서만. 고용소 충격 전차는 계약과 무관하게 공성 전차가 해금되면(RMA_TankUnlocked와 같은 1초 확인) 열린다.
Usage: build_v0157.py <0.15.6 zip> <out>"""
import copy, re, sys, zipfile
from pathlib import Path
OLD, NEW = b'version=0.15.6', b'version=0.15.7'
SRC = Path(__file__).resolve().parent.parent / 'source/starcoop/commanders/arcturusmengsk.sc2mod/base.sc2data/gamedata/actordata.xml'
import sys as _s; _s.path.insert(0, str(Path(__file__).resolve().parent))
import build_v035 as V35
from build_v062 import set_lines
STR = {'Button/Name/RM_SiegeBreaker': '공성 파괴단 /// Siege Breakers',
       'Button/Tooltip/RM_SiegeBreaker': '용병 공성 전차입니다. 공성 모드로 먼 거리의 지상 유닛을 공격합니다. /// Mercenary Siege Tank. Siege Mode attacks distant ground units.'}
HOOK = '        TechTreeUpgradeAddLevel(1, "RMA_TankUnlocked", 1);\n'
ADD = ('        // 0.15.7: Shock Division hire (mercenary compound) opens once siege tanks are unlocked.\n'
       '        TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",4),true);\n'
       '        if (TechTreeUpgradeCount(1,"RM15_ShockHireUnlocked",c_techCountQueuedOrBetter)==0) { TechTreeUpgradeAddLevel(1,"RM15_ShockHireUnlocked",1); }\n')
INIT = '    TechTreeUpgradeAllow(1, "RMA_TankUnlocked", true);\n'
INIT2 = INIT + '    TechTreeUnitAllow(1,"SiegeTankMengsk",true);\n    TechTreeUnitAllow(1,"SiegeTankMengskSieged",true);\n'
OLDCHK = '(TechTreeAbilityIsAllowed(1, AbilityCommand("FactoryTrain", 1))'


def script(s):
    nl = '\r\n' if '\r\n' in s else '\n'; s = s.replace('\r\n', '\n')
    s = s.replace('"SiegeTankMengskSieged"', '"SiegeBreakerSieged"').replace('"SiegeTankMengsk"', '"SiegeBreaker"')
    assert s.count(HOOK) == 1 and s.count(INIT) == 1 and 'SiegeTankMengsk' not in s
    s = s.replace(HOOK, '        if (TechTreeUpgradeCount(1, "RMA_TankUnlocked", c_techCountQueuedOrBetter) == 0) { TechTreeUpgradeAddLevel(1, "RMA_TankUnlocked", 1); }\n' + ADD).replace(INIT, INIT2)
    C = 'libCamp_gf_MercStatusCheck(libCamp_ge_StoryMercID_MercSiegeBreakers,libCamp_ge_StoryMercStatus_Purchased)'
    a = f'    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",4),{C});\n'
    b = f'    if ({C} && TechTreeUpgradeCount(1,"RM15_ShockHireUnlocked",c_techCountQueuedOrBetter)==0) {{\n        TechTreeUpgradeAddLevel(1,"RM15_ShockHireUnlocked",1);\n    }}\n'
    assert s.count(a) == 1 and s.count(b) == 1
    s = s.replace(a, '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",4),TechTreeUpgradeCount(1,"RM15_ShockHireUnlocked",c_techCountQueuedOrBetter)>0);\n').replace(b, '')
    R = 'bool gt_rm14Tank_Func (bool testConds, bool runActions) {\n    if (!runActions) { return true; }\n'
    assert s.count(R) == 1
    s = s.replace(R, R + '    if (TechTreeUpgradeCount(1,"RM15_ShockHireUnlocked",c_techCountQueuedOrBetter)>0) { TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",4),true); }\n')
    # the 1 s check stops once RMA_TankUnlocked is set: also run it while the hire is not yet unlocked
    s = s.replace('if (TechTreeUpgradeCount(1, "RMA_TankUnlocked", c_techCountQueuedOrBetter) == 0 && ' + OLDCHK,
                  'if ((TechTreeUpgradeCount(1, "RMA_TankUnlocked", c_techCountQueuedOrBetter) == 0 || TechTreeUpgradeCount(1, "RM15_ShockHireUnlocked", c_techCountQueuedOrBetter) == 0) && ' + OLDCHK)
    assert 'RM15_ShockHireUnlocked", c_techCountQueuedOrBetter) == 0) && ' in s
    return s.replace('\n', nl)


MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04', 'TTychus03', 'TTychus02']


def actor():
    m = re.search(r'    <CActorUnit id="SiegeTankMengskMorph" .*?</CActorUnit>\n', SRC.read_text('utf-8'), re.S)
    a = re.sub(r'^[ \t]*<On [^>]*BlackOps[^>]*/>\n', '', m.group(0), flags=re.M)
    assert 'BlackOps' not in a and 'SiegeTank_Mengsk_COOP_Morph' in a
    return a.replace('"/>', '" />')


def build(src, out):
    out = Path(out); assert not out.exists(); a = actor()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        for mp in MAPS:
            n = f'{mp}.SC2Map/base.sc2data/gamedata/actordata.xml'; t = z.read(n).decode('utf-8')
            assert 'id="SiegeTankMengskMorph"' not in t and 'id="SiegeTankMengskSieged"' in t, mp
            k = t.rindex('</Catalog>'); rep[n] = (t[:k] + a + t[k:]).encode('utf-8')
            sn = f'{mp}.SC2Map/mapscript.galaxy'; rep[sn] = script(z.read(sn).decode('utf-8')).encode('utf-8')
            kn = f'{mp}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'; ko = set_lines(z.read(kn), STR); V35.gate('kokr', ko); rep[kn] = ko
            for loc in V35.OTHER_LOCALES: rep[f'{mp}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(ko)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__': build(*sys.argv[1:])
