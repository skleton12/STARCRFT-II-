#!/usr/bin/env python3
"""Build CCM 0.3.23 from 0.3.22: 원시저그 건물을 협동전 데하카처럼 '건설'한다 (3번 미션).

사용자 보고 (2026-10-17): "구 없애라고", "왜 협동전처럼 안 만듦".
원인 (데이터 검토):
  - 0.3.12부터 원시 건물은 스크립트가 고치 모델을 땅에 따로 띄웠다가(TriggerModel) 시간이 되면 지우고
    완성 건물을 만들었다. 협동전 방식이 아니다.
  - 협동전은 일벌레가 건물을 '건설 중' 상태로 만들고(건설 능력 PrimalBuildInProgress),
    건물 액터가 건설 시작 때 고치 액터(DehakaHatcheryBuild/DehakaBarracksBuild)를 붙여
    진행도에 따라 고치 애니메이션(Build A~D)을 돌린 뒤 완성 때 지운다.
  - 0.3.4 이식에서 이 연결이 빠졌다: 건설 능력 PrimalBuildInProgress, 고치 액터 틀 PrimalZergBuildingBuild,
    진행 액터 PrimalZergConstructionAttached, 방향 PrimalZergBuildingFacing, DehakaHatcheryBuild 액터,
    원시 군락 액터의 '건설 시작 → 고치 생성' 이벤트. (원시 감시자 고치 액터는 부모가 없는 상태였다.)
수정:
  - 위 레코드를 협동전 원본(starcoop) 그대로 이식 (건설 단계 소리 2개 포함, 둘 다 자날에 있는 소리).
  - 원시 군락·원시 감시자에 PrimalBuildInProgress 능력 추가 → 일반 건설 상태 생성 가능.
  - 스크립트: 땅에 띄우던 고치 모델(CreateModelAtPoint) 전부 삭제. 일벌레가 터에 도착하면 사라지고
    건물이 '건설 중'으로 생겨 진행도를 원작 건설 시간(군락 100·감시자 60)에 맞춰 올린다 (정화자 건물과 같은 방식).
  - 활동 문구(UI/Summoning)는 자날 문자열에 없어 넣지 않는다 (기본 '건설 중' 표시).
건설 시간·순서·비용·위치는 그대로.

Usage: python3 tools/build_v0323.py <0.3.22 zip> <new output zip>
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.3.22', b'version=0.3.23'
M3 = 'TRaynor03.SC2Map/'
GD = M3 + 'base.sc2data/gamedata/'

# starcoop.sc2mod actordata/abildata, copied as-is.
ACTORS = (
    '<CActorSiteOpRotationExplicit id="PrimalZergBuildingFacing"><Forward value="-1.000000,-7.000000,0.000000" /></CActorSiteOpRotationExplicit>'
    '<CActorModel default="1" id="PrimalZergBuildingBuild" parent="ModelConstruction">'
    '<Aliases value="_PrimalZergBuildModel" /><HostSiteOps Ops="SOpShadow PrimalZergBuildingFacing" />'
    '<On Terms="ActorCreation" Send="Create PrimalZergConstructionAttached" />'
    '<On Terms="UnitConstruction.*.Finish" Send="AnimClear ::Progress" /></CActorModel>'
    '<CActorProgress id="PrimalZergConstructionAttached">'
    '<On Terms="AbilMorph.*.Cancel" Send="Destroy" /><On Terms="AbilMorph.*.Finish" Send="Destroy" />'
    '<StageArray AnimProps="Build,A,Start" BlendTime="0.000000" /><StageArray AnimProps="Build,A,Stand" />'
    '<StageArray AnimProps="Build,B,Start" /><StageArray AnimProps="Build,B,Stand" />'
    '<StageArray AnimProps="Build,C,Start" /><StageArray AnimProps="Build,C,Stand" />'
    '<StageArray AnimProps="Build,D" /><Supporter Subject="_PrimalZergBuildModel" /></CActorProgress>'
    '<CActorSound id="PrimalZergConstructionSoundLevel2" parent="ProgressSound"><Sound value="Zerg_BuildingMorphStages" />'
    '<On Terms="ProgressLevel.PrimalZergConstructionAttached.Start; Level 2" Send="Create" /></CActorSound>'
    '<CActorSound id="PrimalZergConstructionSoundLevel4" parent="ProgressSound"><Sound value="Zerg_BuildingMorphStages" />'
    '<On Terms="ProgressLevel.PrimalZergConstructionAttached.Start; Level 4" Send="Create" /></CActorSound>'
    '<CActorModel id="DehakaHatcheryBuild" parent="PrimalZergBuildingBuild" />')
ABIL = '<CAbilBuildable id="PrimalBuildInProgress" />'
HATCH_EVENT = '<On Terms="UnitConstruction.DehakaHatchery.Start" Send="Create DehakaHatcheryBuild" />'

BUILD_OLD = '''    actor cocoon;
    // Primal buildings: the drone becomes a cocoon, the building appears when the time is up (Dehaka style).
    if (kind=="DehakaHatchery" || kind=="DehakaBarracks") {
        cocoon=libNtve_gf_CreateModelAtPoint(kind+"Build",at);
        for (elapsed=0;elapsed<seconds;elapsed+=1) {
            if (gv_gameOver) { ActorSend(cocoon,"Destroy"); return false; }
            Wait(1.0,c_timeGame);
        }
        ActorSend(cocoon,"Destroy");
        UnitCreate(1,kind,0,p,at,270.0);
        if (kind=="DehakaHatchery") { gv_m3_hatchery=UnitLastCreated(); }
        return UnitIsAlive(UnitLastCreated());
    }
'''
BUILD_NEW = '    // Primal buildings use co-op construction too (PrimalBuildInProgress; the actor shows the cocoon).\n'

HIVE_OLD = '''    // Primal Hive: the drone becomes a cocoon; the hive appears when the time is up.
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,450);
    UnitRemove(UnitGroupUnit(drones,1));
    fx[1]=libNtve_gf_CreateModelAtPoint("DehakaHatcheryBuild",site[1]);
'''
HIVE_NEW = '''    // Primal Hive: the drone is consumed and the hive starts as a co-op construction (cocoon on the actor).
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,450);
    UnitRemove(UnitGroupUnit(drones,1));
    b[1]=gf_m3_Begin("DehakaHatchery",11,site[1]);
'''
LOOP_OLD = '''            if (i==1 || i==2) {
                if (GameGetMissionTime()-st[i]>=dur[i]) {
                    ActorSend(fx[i],"Destroy");
                    if (i==1) {
                        UnitCreate(1,"DehakaHatchery",0,11,site[1],270.0);
                        gv_m3_hatchery=UnitLastCreated();
                    }
                    else { UnitCreate(1,"DehakaBarracks",0,11,site[2],270.0); }
                    b[i]=UnitLastCreated();
                    done[i]=true;
                }
                continue;
            }
'''
WARDEN_OLD = '''        // Primal Hive done: the waiting drone becomes the Primal Warden cocoon.
        if (done[1] && !started[2]) {
            PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,250);
            UnitRemove(UnitGroupUnit(drones,2));
            fx[2]=libNtve_gf_CreateModelAtPoint("DehakaBarracksBuild",site[2]);
'''
WARDEN_NEW = '''        // Primal Hive done: the waiting drone starts the Primal Warden (co-op construction).
        if (done[1] && !started[2]) {
            PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,250);
            UnitRemove(UnitGroupUnit(drones,2));
            b[2]=gf_m3_Begin("DehakaBarracks",11,site[2]);
'''


def script(data):
    text = data.decode('utf-8')
    for old, new in [(BUILD_OLD, BUILD_NEW), (HIVE_OLD, HIVE_NEW), (LOOP_OLD, ''), (WARDEN_OLD, WARDEN_NEW)]:
        assert text.count(old) == 1, old[:60]
        text = text.replace(old, new, 1)
    assert 'Build",site' not in text and 'kind+"Build"' not in text and 'actor cocoon' not in text
    return text.encode('utf-8')


def units(data):
    root = E.fromstring(data)
    for uid in ('DehakaHatchery', 'DehakaBarracks'):
        el = [e for e in root if e.tag == 'CUnit' and e.get('id') == uid]
        assert len(el) == 1, uid
        assert not any(a.get('Link') == 'PrimalBuildInProgress' for a in el[0].findall('AbilArray'))
        E.SubElement(el[0], 'AbilArray', Link='PrimalBuildInProgress')
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def append(xml, absent):
    def f(data):
        text = data.decode('utf-8')
        for a in absent: assert f'id="{a}"' not in text, a
        out = text.replace('</Catalog>', xml + '</Catalog>', 1).encode('utf-8')
        E.fromstring(out)
        return out
    return f


def actors(data):
    root = E.fromstring(append(ACTORS, ['PrimalZergBuildingBuild', 'PrimalZergConstructionAttached', 'PrimalZergBuildingFacing',
                                         'DehakaHatcheryBuild', 'PrimalZergConstructionSoundLevel2', 'PrimalZergConstructionSoundLevel4'])(data))
    el = [e for e in root if e.tag == 'CActorUnit' and e.get('id') == 'DehakaHatchery']
    assert len(el) == 1
    assert not any(o.get('Send') == 'Create DehakaHatcheryBuild' for o in el[0].findall('On'))
    el[0].insert(4, E.fromstring(HATCH_EVENT))
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


FIX = {M3 + 'mapscript.galaxy': script, GD + 'unitdata.xml': units, GD + 'actordata.xml': actors,
       GD + 'abildata.xml': append(ABIL, ['PrimalBuildInProgress']),
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX: data = FIX[info.filename](data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
