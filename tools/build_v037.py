#!/usr/bin/env python3
"""Build CCM 0.3.7 from 0.3.6 (3번 미션).

사용자 지시 (2026-10-17):
1. "빔이 내려오면서 그 지역을 정화" — 0.3.6은 0.25초마다 모델을 지웠다 새로 만들어 깜빡였다.
   원작 아둔의 창 정화 광선처럼 광선 하나가 하늘에서 내려와(Birth) 이어진 채로 기지를 천천히 훑는다.
   원작 구조(SOAPurifierBeamUnit: 보이지 않는 비행 유닛에 SOAPurifierBeam 모델을 붙여 이동)를 모드 ID로 단순 재현.
   피해는 광선 위치 반경 3(원작 값)의 적 2~5번만. 경로·속도·피해량은 시험값.
2. 용병 고용소를 미리 지어 두지 않고 SCV로 건설 (0.3.1부터 있던 건설 버튼 사용).
3. "자원 위치로 재분배" — 0.3.1에서 추가한 동쪽 광물 8개(절벽 위·칸 어긋남)와 가스 2곳(관문 자리·적 부화장 겹침, 절벽 끝)을
   지우고, 지형(2단계 평지)·적 배치와 겹치지 않는 자리에 다시 놓는다.
   - 정화자 연결체(28.5,29.5): 원본 광물 8 그대로, 가스는 원래 적 추출장 자리(21.5,29.5)에 풍부한 가스 (적 추출장 1개 삭제).
   - 원시 군락(42.5,29.5): 북쪽에 광물 8(군락과 3칸 간격), 가스는 서쪽 (35.5,28.5).
   - 원시 감시자·추가 감시자는 광물 길을 막지 않게 군락 남쪽으로.
   - 정화자 AI 융화소 목표 2 → 1 (정화자 가스 1곳).
   매장량은 0.3.1 시험값(광물 1800·가스 3000) 그대로.

Usage: python3 tools/build_v037.py <0.3.6 zip> <new output zip>
"""
import argparse
import copy
import sys
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v035 as V35  # noqa: E402  (other_locale, gate)
import build_v036 as V36  # noqa: E402  (0.3.6 beam loop text)

OLD, NEW = b'version=0.3.6', b'version=0.3.7'
M3 = 'TRaynor03.SC2Map/'
GD = M3 + 'base.sc2data/gamedata/'

HIVE_MINERALS = [(39, 35.5), (47, 35.5), (39, 36.5), (41, 36.5), (43, 36.5), (45, 36.5), (40, 37.5), (45, 37.5)]
PURIFIER_GAS = (21.5, 29.5)
PRIMAL_GAS = (35.5, 28.5)
REMOVE_IDS = {str(i) for i in range(30000, 30010)} | {'54'}   # 0.3.1 east minerals/geysers, enemy extractor on the gas spot

UNIT = ('<CUnit id="RM3_PurifierBeamUnit"><Race value="Prot" /><FlagArray index="Turnable" value="0" />'
        '<FlagArray index="Untargetable" value="1" /><FlagArray index="Invulnerable" value="1" />'
        '<FlagArray index="Unselectable" value="1" /><FlagArray index="NoPortraitTalk" value="1" />'
        '<FlagArray index="Unstoppable" value="1" /><PlaneArray index="Air" value="1" /><Mover value="Fly" />'
        '<Speed value="4" /><Acceleration value="1000" /><Sight value="11" />'
        '<AbilArray Link="stop" /><AbilArray Link="move" /><Radius value="1" /><MinimapRadius value="0" />'
        '<Name value="Unit/Name/RM3_PurifierBeamUnit" /></CUnit>')
ACTORS = ('<CActorUnit id="RM3_PurifierBeamUnit" parent="GenericUnitBase" unitName="RM3_PurifierBeamUnit">'
          '<Model value="Invisible" /><On Terms="ActorCreation" Send="Create RM3_PurifierBeam" />'
          '<StatusBarFlags index="Shields" value="0" /><StatusBarFlags index="Life" value="0" />'
          '<StatusBarFlags index="Energy" value="0" /><UnitFlags index="ShowBlobShadow" value="0" /></CActorUnit>'
          '<CActorModel id="RM3_PurifierBeam" parent="ModelAnimationStyleContinuous"><Host Subject="_Unit" />'
          '<HostSiteOps Ops="SOpAttachOrigin SOpShadowSyncGround" /><ModelFlags index="AutomateGlobalLoops" value="1" />'
          '</CActorModel>')
STRING = 'Unit/Name/RM3_PurifierBeamUnit=정화 광선 /// Purifier Beam'

NEW_LOOP = '''    // Spear of Adun Purifier Beam: one beam descends, then sweeps the base in three rows (trial path/speed).
    UnitCreate(1,"RM3_PurifierBeamUnit",0,10,Point(19.0,24.0),0.0);
    beamUnit=UnitLastCreated();
    Wait(2.5,c_timeGame);
    UnitIssueOrder(beamUnit,OrderTargetingPoint(AbilityCommand("move",0),Point(48.0,24.0)),c_orderQueueReplace);
    UnitIssueOrder(beamUnit,OrderTargetingPoint(AbilityCommand("move",0),Point(48.0,31.0)),c_orderQueueAddToEnd);
    UnitIssueOrder(beamUnit,OrderTargetingPoint(AbilityCommand("move",0),Point(19.0,31.0)),c_orderQueueAddToEnd);
    UnitIssueOrder(beamUnit,OrderTargetingPoint(AbilityCommand("move",0),Point(19.0,38.0)),c_orderQueueAddToEnd);
    UnitIssueOrder(beamUnit,OrderTargetingPoint(AbilityCommand("move",0),Point(48.0,38.0)),c_orderQueueAddToEnd);
    for (pulse=0;pulse<160;pulse+=1) {
        if (gv_gameOver || UnitOrderCount(beamUnit)==0) { break; }
        at=UnitGetPosition(beamUnit);
        for (p=2;p<=5;p+=1) {
            targets=UnitGroup(null,p,RegionCircle(at,3.0),UnitFilter(0,0,0,0),0);
            i=UnitGroupCount(targets,c_unitCountAll);
            for (;i>0;i-=1) {
                u=UnitGroupUnit(targets,i);
                if (UnitIsAlive(u)) { UnitDamage(source,"RM3_SolarDamage",u,0.0); }
            }
        }
        Wait(0.25,c_timeGame);
    }
    UnitRemove(beamUnit);
    if (gv_gameOver) { UnitRemove(source); return true; }
'''
SCRIPT = [
    ('    actor beam;\n    actor prev;\n    point at;\n', '    unit beamUnit;\n    point at;\n'),
    ('    UnitCreate(1,"MercCompound",0,1,Point(93.5,35.5),270.0);\n', ''),
    ('    AISetStock(10,2,"Assimilator");\n', '    AISetStock(10,1,"Assimilator");\n'),
    ('gf_m3_Build("DehakaBarracks",11,Point(46.5,33.5),30)', 'gf_m3_Build("DehakaBarracks",11,Point(38.5,26.5),30)'),
    ('gf_m3_Build("Extractor",11,Point(48.5,29.5),20)', 'gf_m3_Build("Extractor",11,Point(35.5,28.5),20)'),
    ('UnitGroup("Extractor",11,RegionCircle(Point(48.5,29.5),2.0)', 'UnitGroup("Extractor",11,RegionCircle(Point(35.5,28.5),2.0)'),
    ('gf_m3_Build("DehakaBarracks",11,Point(38.5,33.5),30)', 'gf_m3_Build("DehakaBarracks",11,Point(44.5,25.5),30)'),
]


def script(data):
    text = data.decode('utf-8')
    old_loop = V36.NEW_LOOP
    assert text.count(old_loop) == 1
    text = text.replace(old_loop, NEW_LOOP, 1)
    for old, new in SCRIPT:
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    assert '"MercCompound",0,1' not in text and 'RM3_PurifierBeam"' not in text.replace('RM3_PurifierBeamUnit"', '')
    return text.encode('utf-8')


def objects(data):
    root = E.fromstring(data)
    gone = [el for el in root if el.get('Id') in REMOVE_IDS]
    assert len(gone) == len(REMOVE_IDS), [el.get('Id') for el in gone]
    for el in gone: root.remove(el)
    oid = 30000
    for x, y in HIVE_MINERALS:
        E.SubElement(root, 'ObjectUnit', Id=str(oid), Position=f'{x},{y},0', Scale='1,1,1', UnitType='RichMineralField', Resources='1800'); oid += 1
    for x, y in (PURIFIER_GAS, PRIMAL_GAS):
        E.SubElement(root, 'ObjectUnit', Id=str(oid), Position=f'{x},{y},0', Scale='1,1,1', UnitType='RichVespeneGeyser', Resources='3000'); oid += 1
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def append(xml):
    def f(data):
        text = data.decode('utf-8')
        out = text.replace('</Catalog>', xml + '</Catalog>', 1).encode('utf-8')
        E.fromstring(out)
        return out
    return f


def kokr(data):
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    assert 'Unit/Name/RM3_PurifierBeamUnit=' not in text
    out = (text.rstrip('\r\n') + nl + STRING + nl).encode('utf-8')
    V35.gate('kokr', out)
    return out


FIX = {M3 + 'mapscript.galaxy': script, M3 + 'objects': objects,
       GD + 'unitdata.xml': append(UNIT), GD + 'actordata.xml': append(ACTORS),
       M3 + 'kokr.sc2data/localizeddata/gamestrings.txt': kokr,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for name, fn in FIX.items(): files[name] = fn(files[name])
        ko = files[M3 + 'kokr.sc2data/localizeddata/gamestrings.txt']
        for loc in V35.OTHER_LOCALES:
            files[f'{M3}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(ko)
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
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
