#!/usr/bin/env python3
"""Build CCM 0.4.60 from 0.4.59: 정화자 동맹 탐사정을 프로비우스로 (4번, 사용자 지시 2026-10-21 "프로브 프로비우스로 바꿔줘").

협동전 피닉스 방식 그대로: 탐사정에 숨김 행동 FenixProbiusProbe(이름 '프로비우스')를 붙이고 액터 메시지
'Create FenixProbiusProbe'로 프로비우스 액터를 씌운다 (원래 탐사정 액터는 그 액터가 지움). 프로비우스 액터는
협동전 원본(초상화 FenixProbiusPortrait, 챔피언 광택 GlazeFenixChampionUnit, 챔피언 와이어프레임)에서 옮기고,
모델만 우리 동맹 외형과 같은 Probe_Purifier_Collection 으로 둔다 (협동전은 피닉스 스킨이 Probe 를 바꿔 줌).
대상: 정화자(8) 소유 탐사정 전부. 능력·채취·건설·스크립트의 'Probe' 판정은 그대로 (유닛 종류는 안 바뀜).
3번 맵은 그대로 (요청 확인 후).

Usage: python3 tools/build_v0460.py <0.4.59 zip> <probius actors xml> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.59', b'version=0.4.60'
M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
KO = M4 + 'kokr.sc2data/localizeddata/gamestrings.txt'
UNIT = ('<CUnit id="FenixProbiusProbe"><Race value="Prot" /><EditorFlags index="NoPlacement" value="1" />'
        '<SubgroupPriority value="103" /></CUnit>')
BEHAVIOR = ('<CBehaviorBuff id="FenixProbiusProbe"><InfoFlags index="Hidden" value="1" /><InfoFlags index="AlwaysUseGameText" value="1" />'
            '<EditorCategories value="AbilityorEffectType:Units" /><Modification UnitNameOverride="Unit/Name/FenixProbiusProbe" />'
            '</CBehaviorBuff>')
MODELS = ('<CModel id="FenixProbiusPortrait" parent="Portrait" Race="Protoss">'
          '<Model value="Assets\\Portraits\\Protoss\\Probe_Purifier_Collection_Probius_Portrait\\Probe_Purifier_Collection_Probius_Portrait.m3" />'
          '<Image value="Assets\\Textures\\Probe_Purifier_Collection_Probius_Portrait_Static.dds" /></CModel>'
          '<CModel id="GlazeFenixChampion" parent="PersistentSpellFX">'
          '<Model value="Assets\\Effects\\Glaze\\Glaze_Fenix_AI_Champion\\Glaze_Fenix_AI_Champion.m3" /></CModel>')
NAME = 'Unit/Name/FenixProbiusProbe=프로비우스 /// Probius'
SKIN_OLD = '        if (!UnitHasBehavior2(u,"RM3_AllySkin")) { UnitBehaviorAdd(u,"RM3_AllySkin",u,1); }\n'
SKIN_NEW = SKIN_OLD + ('        // Purifier probes become Probius (co-op Fenix: name behavior + actor, 0.4.60).\n'
                       '        if (p==8 && UnitGetType(u)=="Probe" && !UnitHasBehavior2(u,"FenixProbiusProbe")) {\n'
                       '            UnitBehaviorAdd(u,"FenixProbiusProbe",u,1);\n'
                       '            libNtve_gf_SendActorMessageToUnit(u,"Create FenixProbiusProbe");\n'
                       '        }\n')


def append(extra):
    def fn(d):
        t = d.decode('utf-8')
        assert 'FenixProbius' not in t or 'GlazeFenixChampion' in extra and 'id="GlazeFenixChampion' not in t
        i = t.rindex('</Catalog>')
        return (t[:i] + extra + t[i:]).encode('utf-8')
    return fn


def script(d):
    t = d.decode('utf-8')
    assert t.count(SKIN_OLD) == 1 and 'FenixProbiusProbe' not in t
    return t.replace(SKIN_OLD, SKIN_NEW).encode('utf-8')


def strings(d):
    t = d.decode('utf-8')
    assert 'Unit/Name/FenixProbiusProbe=' not in t
    return (t.rstrip('\r\n') + '\n' + NAME + '\n').encode('utf-8')


def build(source, actors, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    act = actors.read_text(encoding='utf-8')
    assert 'id="FenixProbiusProbe"' in act and 'Probe_Purifier_Collection' in act
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for name, extra in (('unitdata.xml', UNIT), ('behaviordata.xml', BEHAVIOR), ('modeldata.xml', MODELS), ('actordata.xml', act)):
            files[GD + name] = append(extra)(files[GD + name])
        files[M4 + 'mapscript.galaxy'] = script(files[M4 + 'mapscript.galaxy'])
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
    p.add_argument('source', type=Path); p.add_argument('actors', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.actors, a.output)
