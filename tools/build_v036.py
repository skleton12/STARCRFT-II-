#!/usr/bin/env python3
"""Build CCM 0.3.6 from 0.3.5: 3번 진입 연출을 아둔의 창 '정화 광선'(SOAPurifierBeam)으로.

사용자 확정 (2026-10-17): 진입 '태양 광선' = 아둔의 창에서 나오는 정화 광선.
- 모델: 원작 정화 광선 SOA_PurifierBeam.m3 (공허 캠페인·협동전 카락스 공용).
- 연출: 광선이 남서쪽 적 기지를 3줄로 왕복하며 지나가고, 광선 주변(반경 3, 원작과 같음)의 적 2~5번만 피해.
  이전 0.3.1은 광선 위치와 상관없이 반경 20 전체에 피해를 줬다.
- 경로·속도·피해량(0.25초마다 RM3_SolarDamage 250)은 시험값.
- 인수인계(docs/HANDOFF_mission03_solar_lance.md) 2번 보완: 광선 뒤 남은 적을 무시하고 바로 본진을 짓지 않는다.
  첫 소환·투하 병력이 기지 터(35.5,31 반경 14)의 남은 적을 먼저 공격하고, 적이 없어지거나
  최대 60초(시험값)가 지나면 본진·생산 건물 건설로 넘어간다. 무한 대기·광선 반복·무적은 추가하지 않는다.

Usage: python3 tools/build_v036.py <0.3.5 zip> <new output zip>
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.3.5', b'version=0.3.6'
M3 = 'TRaynor03.SC2Map/'
MODEL = (r'<CModel id="RM3_PurifierBeam" parent="Unit" Race="Protoss">'
         r'<Model value="Assets\Effects\Protoss\SOA_PurifierBeam\SOA_PurifierBeam.m3" />'
         r'<Radius value="3.000000" /><SelectionRadius value="3.000000" /></CModel>')

OLD_DECL = '    actor beam;\n    int i;\n    int pulse;\n    int p;\n'
NEW_DECL = '    actor beam;\n    actor prev;\n    point at;\n    int i;\n    int pulse;\n    int p;\n'
OLD_LOOP = '''    for (pulse=0;pulse<12;pulse+=1) {
        if (gv_gameOver) { UnitRemove(source); return true; }
        beam=libNtve_gf_CreateModelAtPoint("RM3_SolarLance",Point(20.0+pulse*2.5,30.0));
        ActorSend(beam,"AnimPlay Attack Attack NonLooping");
        for (p=2;p<=5;p+=1) {
            targets=UnitGroup(null,p,RegionCircle(Point(35.0,31.0),20.0),UnitFilter(0,0,0,0),0);
            i=UnitGroupCount(targets,c_unitCountAll);
            for (;i>0;i-=1) {
                u=UnitGroupUnit(targets,i);
                if (UnitIsAlive(u)) { UnitDamage(source,"RM3_SolarDamage",u,0.0); }
            }
        }
        Wait(0.5,c_timeGame);
        ActorSend(beam,"Destroy");
    }
'''
NEW_LOOP = '''    // Spear of Adun Purifier Beam: sweeps three rows (y 24/31/38, x 18..52) and burns only around itself.
    beam=null;
    for (pulse=0;pulse<54;pulse+=1) {
        if (gv_gameOver) { break; }
        if (ModI(pulse/18,2)==0) { at=Point(18.0+2.0*ModI(pulse,18),24.0+7.0*(pulse/18)); }
        else { at=Point(52.0-2.0*ModI(pulse,18),24.0+7.0*(pulse/18)); }
        prev=beam;
        beam=libNtve_gf_CreateModelAtPoint("RM3_PurifierBeam",at);
        if (prev!=null) { ActorSend(prev,"Destroy"); }
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
    if (beam!=null) { ActorSend(beam,"Destroy"); }
    if (gv_gameOver) { UnitRemove(source); return true; }
'''


CLEAR_GLOBAL_OLD = 'unitgroup gv_m3_pending;\n'
CLEAR_GLOBAL_NEW = '''unitgroup gv_m3_pending;
bool gv_m3_clearing;

bool gf_m3_EnemyAtSite () {
    int p;
    for (p=2;p<=5;p+=1) {
        if (UnitGroupCount(UnitGroup(null,p,RegionCircle(Point(35.5,31.0),14.0),UnitFilter(0,0,0,0),0),c_unitCountAlive)>0) { return true; }
    }
    return false;
}
'''
TARGET_OLD = '    target=Point(65.0,47.0);\n'
TARGET_NEW = '    target=Point(65.0,47.0);\n    if (gv_m3_clearing) { target=Point(35.5,31.0); }\n'
BUILD_OLD = '    TriggerExecute(gt_m3_drop,false,false);\n    if (!gf_m3_Build("Nexus",10,Point(28.5,29.5),40)) { return true; }\n'
BUILD_NEW = '''    TriggerExecute(gt_m3_drop,false,false);
    // First troops clear what the beam left at the site; build after it is clear or 60 s (trial).
    gv_m3_clearing=true;
    for (i=0;i<30 && gf_m3_EnemyAtSite();i+=1) {
        if (gv_gameOver) { gv_m3_clearing=false; return true; }
        UnitGroupIssueOrder(gf_m3_Army(10),OrderTargetingPoint(AbilityCommand("attack",0),Point(35.5,31.0)),c_orderQueueReplace);
        UnitGroupIssueOrder(gf_m3_Army(11),OrderTargetingPoint(AbilityCommand("attack",0),Point(35.5,31.0)),c_orderQueueReplace);
        Wait(2.0,c_timeGame);
    }
    gv_m3_clearing=false;
    if (!gf_m3_Build("Nexus",10,Point(28.5,29.5),40)) { return true; }
'''


def script(data):
    text = data.decode('utf-8')
    for old in (OLD_DECL, OLD_LOOP, CLEAR_GLOBAL_OLD, TARGET_OLD, BUILD_OLD):
        assert text.count(old) == 1, old[:40]
    text = text.replace(OLD_DECL, NEW_DECL, 1).replace(OLD_LOOP, NEW_LOOP, 1)
    text = text.replace(CLEAR_GLOBAL_OLD, CLEAR_GLOBAL_NEW, 1).replace(TARGET_OLD, TARGET_NEW, 1).replace(BUILD_OLD, BUILD_NEW, 1)
    return text.encode('utf-8')


def models(data):
    text = data.decode('utf-8')
    assert 'id="RM3_PurifierBeam"' not in text
    out = text.replace('</Catalog>', MODEL + '</Catalog>', 1).encode('utf-8')
    E.fromstring(out)
    return out


FIX = {M3 + 'mapscript.galaxy': script, M3 + 'base.sc2data/gamedata/modeldata.xml': models,
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
