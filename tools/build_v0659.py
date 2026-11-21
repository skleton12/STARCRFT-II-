#!/usr/bin/env python3
"""0.6.58 -> 0.6.59: 4번 어부지리(TTychus01) 동맹 = 5·6번 지원 버튼 방식 (사용자 2026-11-21).

사용자: "불곰미션 왜 소환 그거 사라지고 일꾼이 나옴 이거 고쳐줘". 4번은 0.4.x의 '동맹 일꾼이 내려와 플레이어가 짓는'
방식이 남아 있었다 (0.6.16 기록의 '4~6번처럼'은 틀린 설명이었다). 5번(TTosh01) 지원 모듈을 그대로 옮긴다:
- 동맹 탐사정·원시 일벌레를 내려보내지 않는다. 동맹 자원·원시저그 보급 설정은 그대로.
- 화면 위 [정화자 지원]·[원시저그 지원] 버튼(Ctrl+V·Ctrl+B) → 다음 지도 왼쪽 클릭 위치에 소환·투하 (오른쪽 클릭 취소).
  첫 사용 임무 4분, 재사용 120초, 그 동맹 자원·인구 120 (5번과 같은 시험값), 연구실 단계 무료 추가분, 도착 수 자막.
- 5번 모듈 중 레드스톤 전용(용암·높은 곳, 30초 자동 지원 SupSpots/Sup/Support, 저그 기지 지원)은 옮기지 않는다.
- 5번 데이터 RM5_AllyCaster(보이지 않는 시전 유닛)·RM5_AllySupport/PrimalSupport/CallPurifier/CallPrimal·버튼·효과와
  문자열·단축키를 함께 옮긴다. 동맹 자동 전투·핑·업그레이드 연동·생산(건물이 없어 쉼)은 그대로.
게임 미실행.

Usage: python3 tools/build_v0659.py <0.6.58 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import add_xml, set_lines, LOCS, KO, GD

OLD, NEW = b'version=0.6.58', b'version=0.6.59'
M4, M5 = 'TTychus01.SC2Map', 'TTosh01.SC2Map'
DATA = {'abildata.xml': ['RM5_AllySupport', 'RM5_PrimalSupport', 'RM5_CallPurifier', 'RM5_CallPrimal'],
        'actordata.xml': ['RM5_AllyCaster'], 'buttondata.xml': ['RM5_AllySupport', 'RM5_PrimalSupport'],
        'effectdata.xml': ['RM5_AllySupportSet', 'RM5_AllySupportSearch'], 'unitdata.xml': ['RM5_AllyCaster']}
KEYS = ['rm5/AdjSup', 'rm5/CallReady', 'rm5/CallWait', 'rm5/CallAim', 'rm5/CallBad', 'rm5/CallNoMoney', 'rm5/CallWaitMsg',
        'rm5/CallKeyP', 'rm5/CallKeyZ', 'rm5/CallTier', 'rmSupport/PurifierCount', 'rmSupport/PrimalCount',
        'rmSupport/CountEnd', 'Unit/Name/RM5_AllyCaster', 'Button/Name/RM5_AllySupport', 'Button/Tooltip/RM5_AllySupport',
        'Button/Name/RM5_PrimalSupport', 'Button/Tooltip/RM5_PrimalSupport']
HOTKEYS = ['Button/Hotkey/RM5_AllySupport', 'Button/Hotkey/RM5_PrimalSupport']
DROP_FUNCS = ('void gf_m5_SupSpots (int p) {', 'bool gt_m5_Sup_Func (bool testConds,bool runActions) {', 'void gf_m5_Support () {')

ARRIVE_OLD = '''    fx=libNtve_gf_CreateModelAtPoint("ProtossUnitBirth",Point(64.0,26.0));
    ActorSend(fx,"AnimPlay Warp Birth NonLooping");
    pod=libNtve_gf_CreateModelAtPoint("ZergDropPod",Point(67.0,27.0));
    ActorSend(pod,"AnimPlay Drop Birth NonLooping");
    Wait(3.0,c_timeGame);
    ActorSend(fx,"Destroy");
    ActorSend(pod,"Destroy");
    if (gv_gameOver) { return true; }
    UnitCreate(1,"Probe",0,8,Point(64.0,26.0),270.0);
    for (i=0;i<4;i+=1) { UnitCreate(1,"DehakaDrone",0,9,Point(66.0+1.0*i,27.0),270.0); }
    gv_m4_ready=true;
    TriggerQueueEnter();
    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm4/AdjName"),StringExternal("rm4/Adj1"),7.0,c_transmissionDurationSet,true);
    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm4/AdjName"),StringExternal("rm4/Adj2"),7.0,c_transmissionDurationSet,true);
    TriggerQueueExit();
'''
ARRIVE_NEW = '''    // 0.6.59 (user 2026-11-21): no ally workers on mission 4 either - the top support buttons (from mission 5).
    gv_m4_ready=true;
    gf_m4_CallUI();
    TriggerQueueEnter();
    TransmissionSend(PlayerGroupAll(),TransmissionSourceFromModel("AdjutantPortrait"),PortraitGetGame(),"Talk",null,StringExternal("rm4/AdjName"),StringExternal("rm5/AdjSup"),7.0,c_transmissionDurationSet,true);
    TriggerQueueExit();
'''
TICK_OLD = '    gf_m4_Workers();\n'
TICK_NEW = '    gf_m4_CallTick();\n'
INIT_ANCHOR = '    gv_m4_eggUnit[4]="DehakaTrainEggUltralisk";\n'


def norm(b):
    t = b.decode('utf-8'); nl = '\r\n' if '\r\n' in t else '\n'
    return t.replace('\r\n', '\n'), nl


def m5_module(src5):
    t = src5
    s = t.index('string[9] gv_m5_supWarp;\n')
    e = t.index('void gf_m5_CallTick () {\n')
    e = t.index('\n}\n', e) + 3
    mod = t[s:e]
    for head in DROP_FUNCS:
        a = mod.index(head)
        b = mod.index('\n}\n', a) + 3
        mod = mod[:a] + mod[b:]
    init = ''.join(l + '\n' for l in t.splitlines() if l.startswith('    gv_m5_supWarp['))
    assert init.count('\n') == 9
    ren = lambda x: re.sub(r'\b(g[vft])_m5_', r'\1_m4_', x)
    mod, init = ren(mod), ren(init)
    assert '_m5_' not in mod and 'HighGround' not in mod and 'gf_m4_Support' not in mod
    return '// 0.6.59: mission 4 support buttons, moved from mission 5 (TTosh01) unchanged except names.\n' + mod + '\n', init


def lines_of(raw, keys):
    out = {}
    for l in raw.decode('utf-8-sig').splitlines():
        k, _, v = l.partition('=')
        if k in keys: out[k] = v
    assert set(out) == set(keys), set(keys) - set(out)
    return out


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        d4, d5 = root / M4, root / M5
        for fn, ids in DATA.items():
            recs = {e.get('id'): e for e in E.parse(d5 / GD / fn).getroot()}
            have = {e.get('id') for e in E.parse(d4 / GD / fn).getroot()}
            xml = ''
            for i in ids:
                assert i in recs and i not in have, (fn, i)
                el = copy.deepcopy(recs[i]); el.tail = None
                xml += E.tostring(el, encoding='unicode')
            add_xml(d4 / GD / fn, xml)
        p = d4 / 'mapscript.galaxy'
        t, nl = norm(p.read_bytes())
        t5, _ = norm((d5 / 'mapscript.galaxy').read_bytes())
        mod, init = m5_module(t5)
        for a, b in ((ARRIVE_OLD, ARRIVE_NEW), (TICK_OLD, TICK_NEW), (INIT_ANCHOR, INIT_ANCHOR + init)):
            assert t.count(a) == 1, a[:50]
            t = t.replace(a, b)
        anchor = 'bool gt_m4_Tick_Func (bool testConds,bool runActions) {\n'
        assert t.count(anchor) == 1 and 'gf_m4_CallUI' in t
        t = t.replace(anchor, mod + anchor)
        p.write_bytes(t.replace('\n', nl).encode('utf-8'))
        strs = lines_of((d5 / KO).read_bytes(), KEYS)
        ko = set_lines((d4 / KO).read_bytes(), strs)
        (d4 / KO).write_bytes(ko)
        V35.gate('kokr', ko)
        for loc in V35.OTHER_LOCALES:
            (d4 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
        for loc in LOCS:
            h5 = lines_of((d5 / f'{loc}.sc2data/localizeddata/gamehotkeys.txt').read_bytes(), HOTKEYS)
            h = d4 / f'{loc}.sc2data/localizeddata/gamehotkeys.txt'
            h.write_bytes(set_lines(h.read_bytes(), h5))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in d4.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not n.startswith(M4 + '/') and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
