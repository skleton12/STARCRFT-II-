#!/usr/bin/env python3
"""Build CCM 0.3.35 from 0.3.34: 원시저그 병력을 협동전처럼 원시 감시자에서 '생성' (3번 미션).

사용자 지시 (2026-10-17): "프로토스는 소환인데 원시저그는 생성으로 가야 할 듯, 그래서 감시자 준 거".
0.3.27~0.3.34는 원시저그 묶음도 감시자 옆에 그냥 나타났다 (정화자 소환과 같은 방식, 연출 없음).
협동전 데하카 원시 감시자의 실제 생산 능력 DehakaBarracksTrainEgg를 옮긴다:
  감시자가 알을 뱉고(투사체 DehakaTrainLM) → 알(DehakaTrainEgg…)이 땅에 떨어져 → 시간이 지나 부화한다
  (원시 저글링 15초, 원시 바퀴 24초, 원시 히드라리스크 26초 — 협동전 데이터).
  - 스크립트가 감시자에게 알 생산 명령을 내린다. 비용은 협동전 데이터대로 원시저그 자원에서 나간다.
    충전(종류마다 16초에 1개, 최대 5개 저장)과 첫 대기 20초도 협동전 데이터 그대로다.
  - 순서: 저글링 → 저글링 → 바퀴 → 히드라 반복 (시험값). 병력 인구 100 상한은 그대로.
  - 협동전에서 바퀴·히드라는 글레빅 진화 건물이 있어야 하는데, 이 모드에는 그 건물이 없어 조건을 뺐다 (모드 변경).
    군단 숙주·울트라리스크(무르바르·다크룬 진화)는 넣지 않는다.
  - 라바사우르스는 협동전에서 감시자 생산이 아니라 저글링 합체로 나와서, 3번 원시저그 생산에서는 뺀다.
  - 감시자 명령 칸에는 버튼을 넣지 않는다 (동맹 자동 생산, 플레이어가 대신 누르지 않음).
정화자(수정탑 소환)는 그대로다.

Usage: python3 tools/build_v0335.py <0.3.34 zip> <new output zip>
"""
import argparse
import copy
import re
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.3.34', b'version=0.3.35'
M3 = 'TRaynor03.SC2Map'
GD = M3 + '/base.sc2data/gamedata/'
EGG = 'DehakaBarracksTrainEgg'
DROP = r'SwarmHost|Ultralisk|Glevig|Murvar|Dakrun|DehakaLevel|Level3|Mastery'

OLD_SPAWN = '''            if (p==10) {
                gv_m3_fx[gv_m3_fxN]=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at);
                ActorSend(gv_m3_fx[gv_m3_fxN],"AnimPlay Warp Birth NonLooping");
                gv_m3_fxN+=1;
            }
            UnitCreate(1,kind[k],0,p,at,270.0);'''
NEW_SPAWN = '''            gv_m3_fx[gv_m3_fxN]=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",at);
            ActorSend(gv_m3_fx[gv_m3_fxN],"AnimPlay Warp Birth NonLooping");
            gv_m3_fxN+=1;
            UnitCreate(1,kind[k],0,p,at,270.0);'''
OLD_P11 = '''        else {
            if (GameGetMissionTime()<gv_m3_nextMake11) { continue; }
            posts=UnitGroup("DehakaBarracks",11,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
            for (k=0;k<4;k+=1) { kind[k]="DehakaZerglingLevel2"; }
            kind[4]="DehakaRoachLevel2";
            kind[5]="DehakaHydraliskLevel2";
            count=6;
            if (ModI(gv_m3_turn11,2)==1) { kind[6]="DehakaRavasaur"; count=7; }
        }'''
NEW_P11 = '''        else {
            // Primal Zerg hatch from Warden eggs like co-op (user 2026-10-17): see gf_m3_Hatch.
            gf_m3_Hatch();
            continue;
        }'''
HATCH = '''
void gf_m3_Hatch () {
    unitgroup posts;
    unit post;
    int i;
    int n;
    int c;
    int m;
    int g;
    // Each Warden spits an egg (co-op DehakaBarracksTrainEgg). Charges, cooldown, cost and hatch time are co-op data;
    // order zergling, zergling, roach, hydralisk (trial). Ally army supply stays under 100.
    posts=UnitGroup("DehakaBarracks",11,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    n=UnitGroupCount(posts,c_unitCountAll);
    for (i=1;i<=n;i+=1) {
        post=UnitGroupUnit(posts,i);
        c=ModI(gv_m3_turn11,4)-1;
        if (c<0) { c=0; }
        m=UnitTypeGetCost(gv_m3_eggUnit[c],c_unitCostMinerals);
        g=UnitTypeGetCost(gv_m3_eggUnit[c],c_unitCostVespene);
        if (gf_m3_Food(11)+2.0>100.0 || PlayerGetPropertyInt(11,c_playerPropMinerals)<m || PlayerGetPropertyInt(11,c_playerPropVespene)<g) { return; }
        if (UnitIssueOrder(post,Order(AbilityCommand("DehakaBarracksTrainEgg",c)),c_orderQueueReplace)) { gv_m3_turn11+=1; }
    }
}
'''
KO_FIX = {
    'Abil/Name/DehakaBarracksTrainEgg': '원시 알 생산 /// Primal Egg Training',
    'Behavior/Name/PreventKnockback': '밀려남 방지 /// Prevent Knockback',
}
EGG_UNITS = ('DehakaTrainEggZergling', 'DehakaTrainEggRoach', 'DehakaTrainEggHydralisk')


def xml_edit(path, fn):
    root = E.parse(path).getroot()
    fn(root)
    E.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)


def find(root, tag, i):
    r = [e for e in root if e.tag == tag and e.get('id') == i]
    assert len(r) == 1, (tag, i, len(r))
    return r[0]


def edit(gd):
    def abils(root):
        a = find(root, 'CAbilTrain', EGG)
        for info in list(a.findall('InfoArray')):
            if info.get('index') in ('Train4', 'Train5'):
                a.remove(info)
                continue
            b = info.find('Button')
            if b is not None and b.get('Requirements'):
                del b.attrib['Requirements']  # mod change: no Glevig evolution building in this mod
    xml_edit(gd / 'abildata.xml', abils)

    def units(root):
        w = [e for e in root if e.tag == 'CUnit' and e.get('id') == 'DehakaBarracks']
        assert len(w) == 1
        assert not any(a.get('Link') == EGG for a in w[0].findall('AbilArray'))
        E.SubElement(w[0], 'AbilArray', Link=EGG)
        for uid in EGG_UNITS + ('DehakaTrainEgg',):
            assert any(e.tag == 'CUnit' and e.get('id') == uid for e in root), uid
    xml_edit(gd / 'unitdata.xml', units)


def script(path):
    raw = path.read_bytes()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    t = raw.decode('utf-8').replace('\r\n', '\n')
    for a, b in ((OLD_SPAWN, NEW_SPAWN), (OLD_P11, NEW_P11)):
        assert t.count(a) == 1, a[:60]
        t = t.replace(a, b)
    decl = 'void gf_m3_Produce () {'
    assert t.count(decl) == 1
    t = t.replace(decl, HATCH.lstrip('\n') + '\n' + decl, 1)
    glob_anchor = 'point gv_m3_rally10;'
    assert t.count(glob_anchor) == 1
    t = t.replace(glob_anchor, 'string[4] gv_m3_eggUnit;\n' + glob_anchor, 1)
    start = 'void gf_m3_Start () {'
    assert t.count(start) == 1
    t = t.replace(start, start + '\n    gv_m3_eggUnit[0]="DehakaTrainEggZergling";\n    gv_m3_eggUnit[1]="DehakaTrainEggRoach";\n    gv_m3_eggUnit[2]="DehakaTrainEggHydralisk";', 1)
    path.write_bytes(t.replace('\n', nl).encode('utf-8'))


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(root / M3), '--liberty-base', '--skip-existing',
                        f'--drop={DROP}', *EGG_UNITS, 'DehakaTrainEgg', EGG], check=True)
        (root / M3 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        edit(root / GD)
        script(root / M3 / 'mapscript.galaxy')
        ko = root / M3 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        text = ko.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        lines = text.split(nl)
        for i, line in enumerate(lines):
            k = line.split('=', 1)[0]
            if k in KO_FIX: lines[i] = f'{k}={KO_FIX[k]}'
        ko.write_bytes(nl.join(lines).encode('utf-8'))
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (root / M3 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        assert [f for f in files if f not in names] == []
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not n.startswith(M3 + '/') and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
