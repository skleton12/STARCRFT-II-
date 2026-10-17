#!/usr/bin/env python3
"""Build CCM 0.3.28 from 0.3.27 (2·3번 미션).

사용자 지시 (2026-10-17):
1. 드래그 선택 문제를 고친 판. 유력한 원인: 2·3번 미션이 플레이어 1의 유닛 데이터 연결 전체를
   '해병→전쟁광', '의무관→용병 의무관'으로 바꿨다(CatalogLinkReplace). 그런데 전쟁광·용병 의무관의
   선택 묶음(SelectAlias)은 '해병'·'의무관'을 가리킨다. 멜리와 모드 1번(바꿈 없음)에서는 드래그가 정상이다.
   수정:
     - 유닛 연결 바꿈을 지운다.
     - 대신 병영 생산 데이터만 플레이어 1 전용으로 바꾼다 (CatalogFieldValueSet):
       훈련 1번 유닛 Marine→WarPig, 훈련 5번 Medic→MercMedic.
     - 플레이어 1이 보는 병영 해병·의무관 버튼의 그림·이름·설명을 전쟁광·스키비의 천사로 바꾼다.
     - 혹시 해병·의무관이 나오면 완성 순간 용병으로 바꾸는 보조 장치를 둔다 (2번에는 이미 있음, 3번에 추가).
     - 전쟁광·용병 의무관·코랄의 후예의 선택 묶음을 자기 자신으로 둔다.
   게임 미확인: 드래그 해결 여부, 플레이어별 버튼 변경 표시.
2. 방어 건물 (동맹 일꾼이 짓는다, 3번):
     - 정화자 탐사정: 광자포 (원래 필요한 융화로 조건은 정화자에게만 없앰. 수정탑 동력 필요).
       협동전 정화자 외형(PhotonCannon_Purifier_COOP)으로 바꾼다.
     - 원시 일벌레: 협동전 데하카 원시 벌레(DehakaNydusDestroyer, 40초, 일벌레 소모).
       공격·탐지만 넣고 깊은 땅굴 이동·레벨 잠금 광선은 넣지 않는다.
       원본은 '글레빅의 굴' 조건이 있지만 여기서는 없앤다.
3. 원시 일벌레 보충 (3번): 원시 일벌레가 2기 미만이면 30초마다 투하 포드로 2기까지 채운다 (무료, 시험값).
   탐사정이 모두 죽으면 같은 주기로 1기 소환한다.
4. 부관 안내 (사용자 의견): 동맹 일꾼이 도착하면 부관 초상화 통신으로 설명한다.
   '동맹 일꾼을 움직여 건설할 수 있다', '탐사정: 수정탑·광자포 / 원시 일벌레: 원시 감시자·원시 벌레'.
   원본 미션 통신과 겹치지 않게 같은 통신 대기열(TriggerQueue)을 쓴다. 음성은 없고 자막만 7초씩 나온다.

Usage: python3 tools/build_v0328.py <0.3.27 zip> <new output zip>
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
sys.path.insert(0, str(HERE))
import build_v035 as V35  # noqa: E402

OLD, NEW = b'version=0.3.27', b'version=0.3.28'
M2, M3 = 'TRaynor02.SC2Map', 'TRaynor03.SC2Map'
WURM_DROP = r'NydusDestroyerDeepTunnel|^Drag$|Brutalisk|NydusDestroyerBeam|DehakaLevel'

# Player-1-only barracks data and button look (replaces the unit-wide CatalogLinkReplace).
MERC_LINES = '''    // Raynor's barracks train mercenaries (player 1 only data). No unit-wide link replace: it broke box selection.
    CatalogFieldValueSet(c_gameCatalogAbil,"BarracksTrain","InfoArray[Train1].Unit[0]",PLAYER,"WarPig");
    CatalogFieldValueSet(c_gameCatalogAbil,"BarracksTrain","InfoArray[Train5].Unit[0]",PLAYER,"MercMedic");
    CatalogFieldValueSet(c_gameCatalogButton,"Marine","Icon",PLAYER,"Assets\\\\Textures\\\\BTN-Unit-Terran-MarineMercenary.dds");
    CatalogFieldValueSet(c_gameCatalogButton,"Marine","Name",PLAYER,"Button/Name/RM_WarPig");
    CatalogFieldValueSet(c_gameCatalogButton,"Marine","Tooltip",PLAYER,"Button/Tooltip/RM_WarPig");
    CatalogFieldValueSet(c_gameCatalogButton,"Medic","Icon",PLAYER,"Assets\\\\Textures\\\\btn-unit-terran-medicelite.dds");
    CatalogFieldValueSet(c_gameCatalogButton,"Medic","Name",PLAYER,"Button/Name/MercMedic");
    CatalogFieldValueSet(c_gameCatalogButton,"Medic","Tooltip",PLAYER,"Button/Tooltip/RM_MercMedic");
'''
M2_OLD = ('    CatalogLinkReplace(gv_pLAYER_01_USER, c_gameCatalogUnit, "Marine", "WarPig");\n',
          '    CatalogLinkReplace(gv_pLAYER_01_USER, c_gameCatalogUnit, "Medic", "MercMedic");\n')
M3_OLD = '    CatalogLinkReplace(1,c_gameCatalogUnit,"Marine","WarPig");\n    CatalogLinkReplace(1,c_gameCatalogUnit,"Medic","MercMedic");\n'
M3_TRAIN = '''bool gt_m3_TrainMerc_Func (bool testConds,bool runActions) {
    unit u;
    if (!runActions) { return true; }
    // Safety net: a Marine/Medic that still comes out for player 1 becomes the mercenary.
    u=EventUnitProgressUnit();
    if (u==null || UnitGetOwner(u)!=1) { return true; }
    if (UnitGetType(u)=="Marine") { libNtve_gf_ReplaceUnit(u,"WarPig",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }
    else if (UnitGetType(u)=="Medic") { libNtve_gf_ReplaceUnit(u,"MercMedic",libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }
    return true;
}

fixed gv_m3_nextWorkers;

void gf_m3_Workers () {
    int have;
    int i;
    actor pod;
    // Primal Drones are used up by morphing: keep at least 2 (free drop every 30 s, trial). Re-warp the Probe if it died.
    if (GameGetMissionTime()<gv_m3_nextWorkers) { return; }
    have=UnitGroupCount(UnitGroup("DehakaDrone",11,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive);
    if (have<2) {
        pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(100.0,44.0));
        ActorSend(pod,"AnimPlay Drop Birth NonLooping");
        for (i=have;i<2;i+=1) { UnitCreate(1,"DehakaDrone",0,11,Point(99.0+1.0*i,44.0),270.0); }
        gv_m3_nextWorkers=GameGetMissionTime()+30.0;
    }
    if (UnitGroupCount(UnitGroup("Probe",10,RegionEntireMap(),UnitFilter(0,0,0,0),0),c_unitCountAlive)==0) {
        UnitCreate(1,"Probe",0,10,Point(93.0,44.0),270.0);
        gv_m3_nextWorkers=GameGetMissionTime()+30.0;
    }
}

'''
M3_TICK_OLD = '    gf_m3_Produce();\n'
M3_TICK_NEW = '    gf_m3_Produce();\n    gf_m3_Workers();\n'
M3_INIT_ADD = '''    // Ally defenses (user 2026-10-17): Purifier Photon Cannon without the Forge requirement.
    TechTreeUnitAllow(10,"PhotonCannon",true);
    CatalogFieldValueSet(c_gameCatalogAbil,"ProtossBuild","InfoArray[Build8].Button.Requirements",10,"");
    t=TriggerCreate("gt_m3_TrainMerc_Func");
    TriggerAddEventUnitTrainProgress(t,null,c_unitProgressStageComplete);
'''

ADJ_OLD = '    UIDisplayMessage(PlayerGroupAll(),c_messageAreaSubtitle,StringExternal("rm3/Ready"));\n'
ADJ_NEW = '''    // Adjutant explains the allied workers (user 2026-10-17). Subtitles only, queued with the mission's transmissions.
    TriggerQueueEnter();
    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm3/AdjName"),StringExternal("rm3/Adj1"),7.0,c_transmissionDurationSet,true);
    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm3/AdjName"),StringExternal("rm3/Adj2"),7.0,c_transmissionDurationSet,true);
    TriggerQueueExit();
'''

STRINGS3 = {
    'rm3/AdjName': '부관 /// Adjutant',
    'rm3/Adj1': '정화자와 원시저그가 일꾼을 보냈습니다. 동맹 일꾼을 직접 움직여 동맹 건물을 지을 수 있습니다. /// The Purifiers and Primal Zerg have sent workers. You can move the allied workers and build allied structures.',
    'rm3/Adj2': '탐사정은 수정탑과 광자포를, 원시 일벌레는 원시 감시자와 원시 벌레를 짓습니다. 동맹은 그 건물에서 자기 자원으로 병력을 보냅니다. /// The Probe builds Pylons and Photon Cannons; Primal Drones build Primal Wardens and Primal Wurms. The allies send forces from them with their own resources.',
}

STRINGS = {
    'Button/Name/RM_WarPig': '전쟁광 훈련 /// Train War Pig',
    'Button/Tooltip/RM_WarPig': '용병 전쟁광을 훈련합니다. /// Trains a War Pig mercenary.',
    'Button/Tooltip/RM_MercMedic': '용병 의무관 스키비의 천사를 훈련합니다. 주변 생체 유닛을 치료합니다. /// Trains Skibi\'s Angel, a mercenary medic that heals nearby biological units.',
}

CANNON_MODELS = (r'<CModel id="PhotonCannon_Purifier_COOP" parent="Building" Race="Protoss"><Model value="Assets\Buildings\Protoss\PhotonCannon_Purifier_COOP\PhotonCannon_Purifier_COOP.m3" /></CModel>')
CANNON_SWAP = '<On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap PhotonCannon_Purifier_COOP" />'
DRONE_WURM = ('<InfoArray index="Build2" Unit="DehakaNydusDestroyer" Time="40"><Button DefaultButtonFace="DehakaNydusDestroyer" /></InfoArray>')
DRONE_WURM_BUTTON = '<LayoutButtons Face="DehakaNydusDestroyer" Type="AbilCmd" AbilCmd="DehakaDroneMorph,Build2" Row="2" Column="1" />'


def sub_once(text, old, new):
    assert text.count(old) == 1, old[:60]
    return text.replace(old, new, 1)


def rewrite(path, fn):
    p = Path(path)
    p.write_bytes(fn(p.read_bytes()))


def xml_edit(fn):
    def f(data):
        root = E.fromstring(data)
        fn(root)
        return E.tostring(root, encoding='utf-8', xml_declaration=True)
    return f


def find(root, tag, i):
    r = [e for e in root if e.tag == tag and e.get('id') == i]
    return r[0] if r else None


def self_alias(root):
    for uid in ('WarPig', 'MercMedic', 'RMK_MarineMengsk'):
        u = find(root, 'CUnit', uid)
        if u is None:
            u = E.SubElement(root, 'CUnit', id=uid)
        for s in u.findall('SelectAlias'):
            u.remove(s)
        E.SubElement(u, 'SelectAlias', value=uid)


def add_strings(data, extra=None):
    text = data.decode('utf-8')
    strings = dict(STRINGS, **(extra or {}))
    nl = '\r\n' if '\r\n' in text else '\n'
    for k in strings: assert f'{nl}{k}=' not in text, k
    out = (text.rstrip('\r\n') + nl + nl.join(f'{k}={v}' for k, v in strings.items()) + nl).encode('utf-8')
    V35.gate('kokr', out)
    return out


def m2_script(data):
    text = data.decode('utf-8')
    text = sub_once(text, M2_OLD[0], MERC_LINES.replace('PLAYER', 'gv_pLAYER_01_USER'))
    text = sub_once(text, M2_OLD[1], '')
    assert 'CatalogLinkReplace(gv_pLAYER_01_USER' not in text
    return text.encode('utf-8')


def m3_script(data):
    text = data.decode('utf-8')
    text = sub_once(text, M3_OLD, MERC_LINES.replace('PLAYER', '1'))
    text = sub_once(text, 'void gf_m3_Start () {', M3_TRAIN + 'void gf_m3_Start () {')
    text = sub_once(text, M3_TICK_OLD, M3_TICK_NEW)
    text = sub_once(text, 'bool gt_m3_Tick_Func (bool testConds,bool runActions) {',
                    'void gf_m3_Workers ();\n\nbool gt_m3_Tick_Func (bool testConds,bool runActions) {')
    text = sub_once(text, ADJ_OLD, ADJ_NEW)
    anchor = '    gt_m3_zbuild=TriggerCreate("gt_m3_ZBuild_Func");\n'
    text = sub_once(text, anchor, anchor + M3_INIT_ADD)
    # gf_m3_Init needs a local trigger variable for the new trigger.
    text = sub_once(text, 'void gf_m3_Init () {\n    int p;\n', 'void gf_m3_Init () {\n    trigger t;\n    int p;\n')
    assert 'CatalogLinkReplace(1,c_gameCatalogUnit' not in text
    return text.encode('utf-8')


def m3_data(gd):
    def units(root):
        self_alias(root)
        d = find(root, 'CUnit', 'DehakaDrone')
        d.find('CardLayouts').append(E.fromstring(DRONE_WURM_BUTTON))
    rewrite(gd / 'unitdata.xml', xml_edit(units))

    def abils(root):
        a = find(root, 'CAbilBuild', 'DehakaDroneMorph')
        a.append(E.fromstring(DRONE_WURM))
    rewrite(gd / 'abildata.xml', xml_edit(abils))

    def models(root):
        assert find(root, 'CModel', 'PhotonCannon_Purifier_COOP') is None
        root.append(E.fromstring(CANNON_MODELS))
    rewrite(gd / 'modeldata.xml', xml_edit(models))

    def actors(root):
        c = find(root, 'CActorUnit', 'PhotonCannon')
        if c is None:
            c = E.SubElement(root, 'CActorUnit', id='PhotonCannon')
        c.append(E.fromstring(CANNON_SWAP))
    rewrite(gd / 'actordata.xml', xml_edit(actors))


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names = prev.namelist()
        infos = prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        # Primal Wurm from co-op data (attack + detection only).
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(root / M3), '--liberty-base', '--skip-existing',
                        f'--drop={WURM_DROP}', 'DehakaNydusDestroyer'], check=True)
        (root / M3 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        m3_data(root / M3 / 'base.sc2data' / 'gamedata')
        rewrite(root / M2 / 'base.sc2data/gamedata/unitdata.xml', xml_edit(self_alias))
        rewrite(root / M2 / 'mapscript.galaxy', m2_script)
        rewrite(root / M3 / 'mapscript.galaxy', m3_script)
        for m in (M2, M3):
            ko = root / m / 'kokr.sc2data/localizeddata/gamestrings.txt'
            rewrite(ko, lambda d, m=m: add_strings(d, STRINGS3 if m == M3 else None))
            for loc in V35.OTHER_LOCALES:
                (root / m / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        rewrite(root / 'metadata.txt', lambda d: d.replace(OLD, NEW))
        extra = {str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file()} - set(names)
        assert not extra, sorted(extra)[:5]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n.startswith('TRaynor01.SC2Map/'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
