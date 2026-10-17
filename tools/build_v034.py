#!/usr/bin/env python3
"""Build CCM 0.3.4 from 0.3.3 following docs/research/coop_buildings.md.

Mission 3 only (1·2번은 문자열 번역만):
  - 원시저그: 일반 Hatchery/SpawningPool/Drone 외형 바꾸기 대신 데하카 협동전 실제 유닛
    DehakaHatchery(원시 군락)·DehakaBarracks(원시 감시자)·DehakaDrone(원시 일벌레)를 이식해 사용.
    알 생산·뿌리 들기·굴 건설·연구는 이식하지 않는다 (기준표: 자동 추가 금지). 일벌레는 스크립트가 보충(시험값).
  - 정화자: 협동전이 아닌 선동자(StalkerPurifier) 대신 피닉스 사도(AdeptFenix). 수는 그대로 2.
  - 추출장은 공유 ID Extractor 그대로, 0.3.3의 원시 추출장 외형 유지.
  - 배포 전 검사: 세 맵 kokr의 표시 문자열에 한글 없는 값이 남으면 실패 (CLAUDE.md 3-1).

Usage: python3 tools/build_v034.py <0.3.3 zip> <new output zip>
"""
import argparse
import copy
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import port_units as P  # noqa: E402

OLD, NEW = b'version=0.3.3', b'version=0.3.4'
M3 = 'TRaynor03.SC2Map/'
SEEDS = ['DehakaHatchery', 'DehakaBarracks', 'DehakaDrone', 'AdeptFenix']
DROP = ('^(DehakaDroneMorph|BurrowDehakaDroneDown|DroneCarcassHarvest|DehakaHatcheryUproot|DehakaBarracksUproot|'
        'DehakaHatcheryTrainEgg|DehakaBarracksTrainEgg|DehakaHatcheryBuild|DehakaHatcheryResearch|FenixTalisAdeptMorph|'
        'FenixSuppressAvengingProtocol|PrimalBuildInProgress|Drag|Yoink|HaveFenixCommander|MapObjectInteract|'
        'ChronoBoostTarget|KD8CasterKnockingBack|NotBeingAbducted)$|Dakrun|Glevig|Murvar|ReaperKD8|FuelCellPickup|'
        'SwarmHost|FenixTalis|NydusDestroyer|SOAMapWideChrono|Talis_|Merge$|InPlay$')

# Script edits (exact text from 0.3.3 mission 3).
SCRIPT = [
    ('t=="StalkerPurifier"', 't=="AdeptFenix"'),
    ('UnitCreate(1,"StalkerPurifier",0,10,at[k],0.0);', 'UnitCreate(1,"AdeptFenix",0,10,at[k],0.0);'),
    ('    if (kind=="Hatchery") { gv_m3_hatchery=b; }\n', '    if (kind=="DehakaHatchery") { gv_m3_hatchery=b; }\n'),
    ('    UnitCreate(6,"Drone",0,11,Point(43.0,35.0),270.0);\n', '    UnitCreate(6,"DehakaDrone",0,11,Point(43.0,35.0),270.0);\n'),
    ('gf_m3_Build("Hatchery",11,Point(42.5,29.5),40)', 'gf_m3_Build("DehakaHatchery",11,Point(42.5,29.5),40)'),
    ('gf_m3_Build("SpawningPool",11,Point(46.5,33.5),30)', 'gf_m3_Build("DehakaBarracks",11,Point(46.5,33.5),30)'),
    # Normal Zerg AI stock would build a normal Hatchery/Pool/Drone/Overlord: primal economy is scripted.
    ('    AISetStockUnitNext(11,12,"Drone",false);\n    AISetStock(11,1,"Hatchery");\n    AISetStock(11,1,"SpawningPool");\n    AISetStockFarms(11,"Overlord",true);\n',
     '    gf_m3_PrimalWorkers();\n'),
]
PRIMAL_WORKERS = '''void gf_m3_PrimalWorkers () {
    unitgroup g;
    unitgroup ore;
    unit u;
    int i;
    point home;
    // Trial: keep 12 primal drones (free, one per tick) and send idle ones to the nearest minerals.
    if (!UnitIsAlive(gv_m3_hatchery)) { return; }
    home=UnitGetPosition(gv_m3_hatchery);
    g=UnitGroup("DehakaDrone",11,RegionEntireMap(),UnitFilter(0,0,0,0),0);
    if (UnitGroupCount(g,c_unitCountAlive)<12) {
        UnitCreate(1,"DehakaDrone",0,11,home,270.0);
        UnitGroupAdd(g,UnitLastCreated());
    }
    ore=UnitGroup(null,0,RegionCircle(home,12.0),UnitFilter((1 << c_targetFilterRawResource),0,0,0),0);
    if (UnitGroupCount(ore,c_unitCountAll)==0) { return; }
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (UnitIsAlive(u) && UnitTestState(u,c_unitStateIdle)) {
            UnitIssueOrder(u,OrderTargetingUnit(AbilityCommand("DroneHarvest",0),UnitGroupClosestToPoint(ore,UnitGetPosition(u))),c_orderQueueReplace);
        }
    }
}

bool gt_m3_Tick_Func (bool testConds,bool runActions) {'''

# 플레이어에게 보일 수 있는 문자열 범주 (편집기 전용 Actor/Model/Effect/Footprint 이름 등 제외)
VISIBLE = ('Unit/Name/', 'Button/Name/', 'Button/Tooltip/', 'Abil/Name/', 'Behavior/Name/', 'Behavior/Tooltip/',
           'Weapon/Name/', 'Upgrade/Name/', 'Card/Name/', 'RequirementNode/Tooltip/', 'Requirement/Tooltip/',
           'Behavior/RankName/', 'MapInfo/Player')
KO = {
    'Behavior/Name/AdeptPhaseShiftCancelDummy': '사이오닉 이동 취소',
    'Behavior/Name/AdeptPhaseShiftCaster': '사이오닉 이동',
    'Abil/Name/FenixKaldalisZealotMorph': '칼달리스 변신',
    'Behavior/Name/AutomatedAssimilatorBeam': '자동 융화소',
    'Behavior/Name/COOPHeroJustRevive': '부활 직후',
    'Behavior/Name/DehakaConsume': '섭취',
    'Behavior/Name/HotSHunterTimedLife': '시한부 생명',
    'Behavior/Name/KerriganVoidCoopCrushingGripWaveStun': '죄어드는 손아귀 기절',
    'Behavior/Name/NovaArmorBlinkSuit': '노바 순간이동 슈트',
    'Behavior/Name/NovaCombatSuit': '노바 전투복',
    'Behavior/Name/NovaGadgetBoombots': '노바 폭탄 로봇',
    'Behavior/Name/NovaWeaponBlazefireBladeShadowFuryController': '노바 그림자 격노',
    'Behavior/Name/NovaWeaponCanisterRifleSnipe': '노바 저격',
    'Behavior/Name/NovaWeaponPlasmaRifle': '노바 플라스마 소총',
    'Behavior/Name/NovaWeaponPsiRifle': '노바 사이 소총',
    'Upgrade/Name/DehakaCoopStage2': '데하카 2단계',
    'Upgrade/Name/NovaArmorBlinkSuit': '노바 순간이동 슈트',
    'Upgrade/Name/NovaWeaponBlazefireBlade': '노바 화염검',
}


def korean_gate(name, data):
    bad = []
    for line in data.decode('utf-8-sig').splitlines():
        k, _, v = line.partition('=')
        if k.startswith(VISIBLE) and v.strip() and not re.search('[가-힣]', v) \
                and re.search('[A-Za-z]{2,}', v.split('///')[0]):
            bad.append(k)
    if bad: raise SystemExit(f'{name}: 영어로 남은 표시 문자열 {len(bad)}개 {bad[:8]}')


def strings(data):
    text = data.decode('utf-8-sig')
    for key, value in KO.items():
        text = re.sub(r'^' + re.escape(key) + r'=[^\r\n]*', lambda _: key + '=' + value, text, flags=re.M)
    return text.encode('utf-8')


def clean_dangling(gd, before_ids):
    """새로 들어온 엔트리 안에서 맵·기본 층 어디에도 없는 ID를 가리키는 하위 항목을 지운다."""
    base = set()
    for p in P.BASE_LAYERS:
        base |= {i for _, i in P.load_layer(p)}
    copyids = set()
    for _, p in P.COPY_LAYERS:
        copyids |= {i for _, i in P.load_layer(p)}
    trees = {fn: E.parse(os.path.join(gd, fn)) for fn in os.listdir(gd) if fn.endswith('.xml')}
    have = {el.get('id') for t in trees.values() for el in t.getroot() if el.get('id')}
    missing = lambda node: any(t in copyids and t not in base and t not in have
                               for v in node.attrib.values() for t in P.TOKEN_RE.findall(v))
    removed = 0
    for fn, tree in trees.items():
        for el in tree.getroot():
            if el.get('id') in before_ids.get(fn, set()): continue
            for parent in list(el.iter()):
                for ch in list(parent):
                    if missing(ch) and not len(ch):
                        parent.remove(ch); removed += 1
        tree.write(os.path.join(gd, fn), encoding='utf-8', xml_declaration=True)
    return removed


def actors_drop_zerg_swaps(path):
    tree = E.parse(path)
    root = tree.getroot()
    for el in list(root):
        if el.tag == 'CActorUnit' and el.get('id') in ('Hatchery', 'SpawningPool', 'Drone'):
            for on in list(el):
                if on.get('Terms') == 'Behavior.RM3_AllySkin.On': el.remove(on)
            if not len(el) and not set(el.attrib) - {'id'}: root.remove(el)
    tree.write(path, encoding='utf-8', xml_declaration=True)


def mission3(work):
    gd = os.path.join(work, 'base.sc2data', 'gamedata')
    before = {fn: {el.get('id') for el in E.parse(os.path.join(gd, fn)).getroot()} for fn in os.listdir(gd)}
    subprocess.run([sys.executable, str(ROOT / 'tools/port_units.py'), '--liberty-base', '--skip-existing',
                    '--drop=' + DROP, work] + SEEDS, check=True)
    os.remove(os.path.join(work, 'ported_shared_refs.txt'))
    P.BASE_LAYERS.append(P.gd('liberty.sc2mod'))
    print('dangling children removed:', clean_dangling(gd, before))
    actors_drop_zerg_swaps(os.path.join(gd, 'actordata.xml'))
    sp = os.path.join(work, 'mapscript.galaxy')
    text = open(sp, encoding='utf-8').read()
    head = 'bool gt_m3_Tick_Func (bool testConds,bool runActions) {'
    assert text.count(head) == 1
    text = text.replace(head, PRIMAL_WORKERS, 1)
    for old, new in SCRIPT:
        assert text.count(old) == 1, old
        text = text.replace(old, new, 1)
    for gone in ('"StalkerPurifier"', '"Hatchery"', '"SpawningPool"', '"Drone"'):
        assert gone not in text[text.index('// Mission 03 support'):text.index('void InitGlobals () {')], gone
    open(sp, 'w', encoding='utf-8').write(text)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names = [n for n in prev.namelist() if n.startswith(M3)]
        prev.extractall(tmp, names)
        work = os.path.join(tmp, M3.rstrip('/'))
        mission3(work)
        new3 = {}
        for r, _, fs in os.walk(work):
            for f in fs:
                p = os.path.join(r, f)
                new3[M3 + os.path.relpath(p, work).replace(os.sep, '/')] = open(p, 'rb').read()
        assert set(names) <= set(new3), set(names) - set(new3)
        extra = sorted(set(new3) - set(names))
        print('new files:', extra)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = new3.get(info.filename, prev.read(info.filename))
                    if info.filename == 'metadata.txt': data = data.replace(OLD, NEW)
                    if info.filename.lower().endswith('kokr.sc2data/localizeddata/gamestrings.txt'):
                        data = strings(data); korean_gate(info.filename, data)
                    if info.filename.endswith('.xml'): E.fromstring(data)
                    out.writestr(copy.copy(info), data)
                for n in extra:
                    E.fromstring(new3[n]); out.writestr(n, new3[n])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist() + extra
                for n in prev.namelist():
                    if not n.startswith(M3) and 'gamestrings' not in n and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
