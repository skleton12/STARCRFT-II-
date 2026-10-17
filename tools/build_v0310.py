#!/usr/bin/env python3
"""Build CCM 0.3.10 from 0.3.9: 동맹 건설 순서를 본진부터 (3번 미션).

사용자 지시 (2026-10-17): "연결체와 원시 군락부터 지어야지".
  정화자: 탐사정이 연결체(40초)부터 → 완성 후 수정탑(16)·관문(30) 동시 → 관문 완성 시 첫 소환.
  원시저그: 원시 일벌레가 원시 군락(40)부터 변태 → 완성 후 다른 일벌레가 원시 감시자(30)로 변태 → 감시자 완성 시 첫 투하.
  건설비·시간·위치는 0.3.9 시험값 그대로.

Usage: python3 tools/build_v0310.py <0.3.9 zip> <new output zip>
"""
import argparse
import copy
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v039 as V39  # noqa: E402

OLD, NEW = b'version=0.3.9', b'version=0.3.10'
M3 = 'TRaynor03.SC2Map/'

OLD_START = '''    UnitIssueOrder(UnitGroupUnit(probes,1),OrderTargetingPoint(AbilityCommand("move",0),site[0]),c_orderQueueReplace);
    UnitIssueOrder(UnitGroupUnit(drones,1),OrderTargetingPoint(AbilityCommand("move",0),site[1]),c_orderQueueReplace);
    UnitIssueOrder(UnitGroupUnit(drones,2),OrderTargetingPoint(AbilityCommand("move",0),site[2]),c_orderQueueReplace);
    Wait(3.0,c_timeGame);
    if (gv_gameOver) { return true; }
    dur[0]=16.0;
    dur[1]=40.0;
    dur[2]=30.0;
    dur[3]=40.0;
    dur[4]=30.0;
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,100);
    b[0]=gf_m3_Begin("Pylon",10,site[0]);
    st[0]=GameGetMissionTime();
    // Primal drones morph into the buildings (Dehaka style: the drone is used up).
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,700);
    UnitRemove(UnitGroupUnit(drones,2));
    UnitRemove(UnitGroupUnit(drones,1));
    b[1]=gf_m3_Begin("DehakaHatchery",11,site[1]);
    st[1]=GameGetMissionTime();
    b[2]=gf_m3_Begin("DehakaBarracks",11,site[2]);
    st[2]=GameGetMissionTime();
    started[0]=true;
    started[1]=true;
    started[2]=true;
'''
NEW_START = '''    // Town halls first: a probe builds the Nexus, a primal drone morphs into the Primal Hive.
    UnitIssueOrder(UnitGroupUnit(probes,1),OrderTargetingPoint(AbilityCommand("move",0),site[3]),c_orderQueueReplace);
    UnitIssueOrder(UnitGroupUnit(drones,1),OrderTargetingPoint(AbilityCommand("move",0),site[1]),c_orderQueueReplace);
    Wait(3.0,c_timeGame);
    if (gv_gameOver) { return true; }
    dur[0]=16.0;
    dur[1]=40.0;
    dur[2]=30.0;
    dur[3]=40.0;
    dur[4]=30.0;
    PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,400);
    b[3]=gf_m3_Begin("Nexus",10,site[3]);
    st[3]=GameGetMissionTime();
    PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,450);
    UnitRemove(UnitGroupUnit(drones,1));
    b[1]=gf_m3_Begin("DehakaHatchery",11,site[1]);
    st[1]=GameGetMissionTime();
    started[3]=true;
    started[1]=true;
'''
OLD_NEXT = '''        // Pylon done: two probes build the Nexus and Gateway.
        if (done[0] && !started[3]) {
            UnitIssueOrder(UnitGroupUnit(probes,2),OrderTargetingPoint(AbilityCommand("move",0),site[3]),c_orderQueueReplace);
            UnitIssueOrder(UnitGroupUnit(probes,3),OrderTargetingPoint(AbilityCommand("move",0),site[4]),c_orderQueueReplace);
            PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,550);
            b[3]=gf_m3_Begin("Nexus",10,site[3]);
            st[3]=GameGetMissionTime();
            b[4]=gf_m3_Begin("Gateway",10,site[4]);
            st[4]=GameGetMissionTime();
            started[3]=true;
            started[4]=true;
        }
'''
NEW_NEXT = '''        // Nexus done: two probes build the Pylon and Gateway.
        if (done[3] && !started[0]) {
            UnitIssueOrder(UnitGroupUnit(probes,2),OrderTargetingPoint(AbilityCommand("move",0),site[0]),c_orderQueueReplace);
            UnitIssueOrder(UnitGroupUnit(probes,3),OrderTargetingPoint(AbilityCommand("move",0),site[4]),c_orderQueueReplace);
            PlayerModifyPropertyInt(10,c_playerPropMinerals,c_playerPropOperSubtract,250);
            b[0]=gf_m3_Begin("Pylon",10,site[0]);
            st[0]=GameGetMissionTime();
            b[4]=gf_m3_Begin("Gateway",10,site[4]);
            st[4]=GameGetMissionTime();
            started[0]=true;
            started[4]=true;
        }
        // Primal Hive done: another primal drone morphs into the Primal Warden.
        if (done[1] && !started[2]) {
            PlayerModifyPropertyInt(11,c_playerPropMinerals,c_playerPropOperSubtract,250);
            UnitRemove(UnitGroupUnit(drones,2));
            b[2]=gf_m3_Begin("DehakaBarracks",11,site[2]);
            st[2]=GameGetMissionTime();
            started[2]=true;
        }
'''
OLD_WARP = '        if (done[4] && !warped && UnitIsAlive(b[4])) {'
NEW_WARP = '        if (done[4] && done[0] && !warped && UnitIsAlive(b[4]) && UnitIsAlive(b[0])) {'
OLD_LOOP = '    for (k=0;k<200;k+=1) {\n        if (gv_gameOver) { return true; }\n        for (i=0;i<5;i+=1) {'
NEW_LOOP = '    for (k=0;k<240;k+=1) {\n        if (gv_gameOver) { return true; }\n        for (i=0;i<5;i+=1) {'
# Walk the drone to the Warden spot early so it is there when the Hive finishes.
OLD_DRONE = '    UnitIssueOrder(UnitGroupUnit(drones,1),OrderTargetingPoint(AbilityCommand("move",0),site[1]),c_orderQueueReplace);\n    Wait(3.0,c_timeGame);'
NEW_DRONE = ('    UnitIssueOrder(UnitGroupUnit(drones,1),OrderTargetingPoint(AbilityCommand("move",0),site[1]),c_orderQueueReplace);\n'
             '    UnitIssueOrder(UnitGroupUnit(drones,2),OrderTargetingPoint(AbilityCommand("move",0),site[2]),c_orderQueueReplace);\n'
             '    Wait(3.0,c_timeGame);')


def script(data):
    text = data.decode('utf-8')
    for old, new in [(OLD_START, NEW_START), (OLD_NEXT, NEW_NEXT), (OLD_WARP, NEW_WARP), (OLD_LOOP, NEW_LOOP), (OLD_DRONE, NEW_DRONE)]:
        assert text.count(old) == 1, old[:70]
        text = text.replace(old, new, 1)
    return text.encode('utf-8')


FIX = {M3 + 'mapscript.galaxy': script, 'metadata.txt': lambda d: d.replace(OLD, NEW)}


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
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path)
    a.add_argument('output', type=Path)
    x = a.parse_args(); build(x.source, x.output)
