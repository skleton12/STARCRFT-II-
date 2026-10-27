#!/usr/bin/env python3
"""0.5.8 -> 0.5.9: 레드스톤 상단 패널을 위로 올리고 정화자·원시저그 지원을 따로 (사용자 2026-10-27).

사용자: "패널 생기긴 했는데 좀 더 위로 올려 봐. 그리고 원시저그랑 정화자랑 분리시켜 줘."
- 패널 위치: 화면 위에서 64 → 4 (대화 상자), 패널 안 여백 8 → 0 (시험값).
- 능력 두 개, 각각 재사용 대기 30초·첫 사용 약 1분 뒤 (시험값):
  정화자 지원 RM5_AllySupport (기존 ID 유지, 차원 증원 아이콘, 단축키 V) → 정화자 묶음만 차원 소환.
  원시저그 지원 RM5_PrimalSupport (새 ID, 케리건 낙하 주머니 아이콘, 단축키 B) → 원시저그 묶음만 낙하 주머니.
- 사용자 보고 "선택만 되고 위치 어디다 둘지도 안 나옴": 위쪽 버튼은 즉시 능력(RM5_CallPurifier/RM5_CallPrimal)이고,
  누르면 스크립트가 협동전처럼 UISetTargetingOrder로 실제 지점 지정 능력의 커서를 연다 (starcoop LibCOMI 방식).
  버튼과 실제 능력은 재사용 대기(RM5_CD8/RM5_CD9)를 같이 쓴다.
- 각 능력은 자기 동맹 자원만 쓴다.
- 임무 목표 이름 "또는: 저그 기지 모두 파괴" → "저그 기지 파괴" (사용자 "그거 클리어하면 임무 성공이니"). 보이지 않는 곳·못 가는 땅·그 동맹 돈/인구 부족이면 그 능력의 대기만 되돌린다.

Usage: python3 tools/build_v059.py <0.5.8 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v041 import merge

OLD, NEW = b'version=0.5.8', b'version=0.5.9'
M5 = 'TTosh01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
PRIMAL_ICON = r'Assets\Textures\btn-ability-kerrigan-droppods.dds'

DATA = {
    'abildata.xml': '''<Catalog>
  <CAbilEffectTarget id="RM5_PrimalSupport">
    <Flags index="Transient" value="1"/>
    <Effect value="RM5_AllySupportSet"/>
    <Cost>
      <Cooldown Link="RM5_CD9" Location="Unit" TimeStart="55" TimeUse="30"/>
    </Cost>
    <Range value="500"/>
    <Arc value="360"/>
    <CursorEffect value="RM5_AllySupportSearch"/>
    <CmdButtonArray index="Execute" DefaultButtonFace="RM5_PrimalSupport"/>
  </CAbilEffectTarget>
  <CAbilEffectInstant id="RM5_CallPurifier">
    <Flags index="Transient" value="1"/>
    <Effect value="RM5_AllySupportSet"/>
    <Cost>
      <Cooldown Link="RM5_CD8" Location="Unit" TimeStart="55" TimeUse="0"/>
    </Cost>
    <CmdButtonArray index="Execute" DefaultButtonFace="RM5_AllySupport"/>
  </CAbilEffectInstant>
  <CAbilEffectInstant id="RM5_CallPrimal">
    <Flags index="Transient" value="1"/>
    <Effect value="RM5_AllySupportSet"/>
    <Cost>
      <Cooldown Link="RM5_CD9" Location="Unit" TimeStart="55" TimeUse="0"/>
    </Cost>
    <CmdButtonArray index="Execute" DefaultButtonFace="RM5_PrimalSupport"/>
  </CAbilEffectInstant>
</Catalog>''',
    'buttondata.xml': f'''<Catalog>
  <CButton id="RM5_PrimalSupport">
    <Icon value="{PRIMAL_ICON}"/>
    <Name value="Button/Name/RM5_PrimalSupport"/>
    <Tooltip value="Button/Tooltip/RM5_PrimalSupport"/>
  </CButton>
</Catalog>''',
}
# The caster shows the two instant buttons (one card, both buttons); the point-target abilities stay off the card.
CASTER_OLD = '''    <AbilArray Link="RM5_AllySupport" />
    <CardLayouts index="0">
      <LayoutButtons Face="RM5_AllySupport" Type="AbilCmd" AbilCmd="RM5_AllySupport,Execute" Row="0" Column="0" />
    </CardLayouts>'''
CASTER_NEW = '''    <AbilArray Link="RM5_AllySupport" />
    <AbilArray Link="RM5_PrimalSupport" />
    <AbilArray Link="RM5_CallPurifier" />
    <AbilArray Link="RM5_CallPrimal" />
    <CardLayouts index="0">
      <LayoutButtons Face="RM5_AllySupport" Type="AbilCmd" AbilCmd="RM5_CallPurifier,Execute" Row="0" Column="0" />
      <LayoutButtons Face="RM5_PrimalSupport" Type="AbilCmd" AbilCmd="RM5_CallPrimal,Execute" Row="0" Column="1" />
    </CardLayouts>'''
CD_OLD = '<Cooldown Location="Unit" TimeStart="55" TimeUse="30" />'
CD_NEW = '<Cooldown Link="RM5_CD8" Location="Unit" TimeStart="55" TimeUse="30" />'

SET = {
    'Button/Name/RM5_AllySupport': '정화자 지원 /// Purifier Support',
    'Button/Tooltip/RM5_AllySupport': '정화자가 지정한 지점으로 병력을 차원 소환합니다.<n/>파수병 2, 피닉스 사도 1, 동력기 1(2기 미만일 때), 해금 유닛 1<n/>비용은 정화자 자원입니다. 보이는 곳, 걸어갈 수 있는 땅에만 부를 수 있습니다. '
                                      '/// The Purifiers warp forces in at the target point.<n/>2 Sentinels, 1 Adept, 1 Energizer (if fewer than 2), 1 unlocked unit<n/>Paid with Purifier resources. Only to a visible, walkable spot.',
    'rm5/AdjSup': '1분 뒤부터 화면 위 [정화자 지원]·[원시저그 지원] 능력으로 지점을 정하면 그 동맹이 그곳으로 병력을 보냅니다. 각각 재사용 대기 30초, 비용은 그 동맹의 자원입니다. '
                  '/// In one minute, use [Purifier Support] or [Primal Zerg Support] at the top of the screen and pick a spot: that ally sends forces there. 30-second cooldown each; paid with that ally\'s resources.',
    'rm5/ObjWipe': '저그 기지 파괴 /// Destroy the Zerg Bases',
    'rm5/CallNoMoney': '그 동맹의 자원이나 인구가 모자라 지원이 오지 않았습니다. /// That ally lacks resources or supply; no support was sent.',
}
ADD = [
    'Button/Name/RM5_PrimalSupport=원시저그 지원 /// Primal Zerg Support',
    'Button/Tooltip/RM5_PrimalSupport=원시저그가 지정한 지점으로 병력을 낙하 주머니로 투하합니다.<n/>원시 저글링 4, 바퀴 1, 히드라 1, 해금 유닛(원시 숙주·울트라리스크)<n/>비용은 원시저그 자원입니다. 보이는 곳, 걸어갈 수 있는 땅에만 부를 수 있습니다. '
    '/// The Primal Zerg drop forces by pod at the target point.<n/>4 Primal Zerglings, 1 Roach, 1 Hydralisk, unlocked units (Swarm Host, Ultralisk)<n/>Paid with Primal Zerg resources. Only to a visible, walkable spot.',
]

OLD_CAST_START = 'void gf_m5_CallRefund (string msg) {\n'
OLD_CAST_END = 'void gf_m5_CallUI () {\n'
NEW_CAST = r'''void gf_m5_CallRefund (string abil, string msg) {
    UnitAbilityReset(gv_m5_caster,AbilityCommand(abil,0),c_spendLocationAll);
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaError,StringExternal(msg));
}

// 0.5.9: Purifier and Primal Zerg support are separate abilities (user 2026-10-27); each pays only its own ally.
void gf_m5_CallAt (int p, string abil) {
    point c=EventUnitTargetPoint();
    if (EventUnitTargetUnit()!=null) { c=UnitGetPosition(EventUnitTargetUnit()); }
    if (c==null || !VisIsVisibleForPlayer(1,c) || !PointPathingPassable(c)) {
        gf_m5_CallRefund(abil,"rm5/CallBad");
        return;
    }
    if (!gf_m5_CallPay(p)) {
        gf_m5_CallRefund(abil,"rm5/CallNoMoney");
        return;
    }
    gf_m5_CallSpots(p,c);
    if (p==8) {
        gv_m5_supTurn+=1;
        TriggerExecute(gv_m5_callTrig8,false,false);
    }
    else { TriggerExecute(gv_m5_callTrig9,false,false); }
}

// The top-bar buttons are instant abilities; like co-op (UISetTargetingOrder on the global caster) they open the
// point-target cursor of the real ability, which shares their cooldown.
bool gt_m5_CallAim_Func (bool testConds,bool runActions) {
    string a="RM5_AllySupport";
    if (!runActions || gv_gameOver) { return true; }
    if (EventUnitAbility()==AbilityCommand("RM5_CallPrimal",0)) { a="RM5_PrimalSupport"; }
    UISetTargetingOrder(PlayerGroupSingle(1),gv_m5_casterGroup,OrderTargetingPoint(AbilityCommand(a,0),UnitGetPosition(gv_m5_caster)),false);
    return true;
}

bool gt_m5_CallCast8_Func (bool testConds,bool runActions) {
    if (!runActions || gv_gameOver) { return true; }
    gf_m5_CallAt(8,"RM5_AllySupport");
    return true;
}

bool gt_m5_CallCast9_Func (bool testConds,bool runActions) {
    if (!runActions || gv_gameOver) { return true; }
    gf_m5_CallAt(9,"RM5_PrimalSupport");
    return true;
}

'''
UI = [
    ('    DialogCreate(96,96,c_anchorTop,0,64,false);\n', '    DialogCreate(176,88,c_anchorTop,0,4,false);\n'),
    ('    DialogControlSetSize(gv_m5_callPanel,PlayerGroupAll(),80,80);\n', '    DialogControlSetSize(gv_m5_callPanel,PlayerGroupAll(),160,80);\n'),
    ('    DialogControlSetPosition(gv_m5_callPanel,PlayerGroupAll(),c_anchorTopLeft,8,8);\n',
     '    DialogControlSetPosition(gv_m5_callPanel,PlayerGroupAll(),c_anchorTopLeft,8,0);\n'),
    ('    t=TriggerCreate("gt_m5_CallCast_Func");\n'
     '    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_AllySupport",0),c_abilEffectStageCast,false);\n',
     '    t=TriggerCreate("gt_m5_CallCast8_Func");\n'
     '    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_AllySupport",0),c_abilEffectStageCast,false);\n'
     '    t=TriggerCreate("gt_m5_CallCast9_Func");\n'
     '    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_PrimalSupport",0),c_abilEffectStageCast,false);\n'
     '    t=TriggerCreate("gt_m5_CallAim_Func");\n'
     '    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_CallPurifier",0),c_abilEffectStageCast,false);\n'
     '    TriggerAddEventUnitAbility(t,UnitRefFromUnit(gv_m5_caster),AbilityCommand("RM5_CallPrimal",0),c_abilEffectStageCast,false);\n'),
]


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        s = M5 + 'mapscript.galaxy'
        t = files[s].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = t.replace('\r\n', '\n')
        a, b = t.index(OLD_CAST_START), t.index(OLD_CAST_END)
        assert a < b and 'gt_m5_CallCast_Func' in t[a:b]
        t = t[:a] + NEW_CAST + t[b:]
        for x, y in UI:
            assert t.count(x) == 1, x
            t = t.replace(x, y)
        files[s] = t.replace('\n', nl).encode('utf-8')
        u = files[M5 + GD + 'unitdata.xml'].decode('utf-8')
        assert u.count(CASTER_OLD) == 1
        files[M5 + GD + 'unitdata.xml'] = u.replace(CASTER_OLD, CASTER_NEW).encode('utf-8')
        ab = files[M5 + GD + 'abildata.xml'].decode('utf-8')
        assert ab.count(CD_OLD) == 1
        files[M5 + GD + 'abildata.xml'] = ab.replace(CD_OLD, CD_NEW).encode('utf-8')
        for name, xml in DATA.items():
            key = M5 + GD + name
            files[key] = merge(files[key], xml.encode('utf-8'))
        ko = files[M5 + KO].decode('utf-8-sig')
        knl = '\r\n' if '\r\n' in ko else '\n'
        lines = ko.split(knl)
        for key, val in SET.items():
            hit = [i for i, l in enumerate(lines) if l.startswith(key + '=')]
            assert len(hit) == 1, key
            lines[hit[0]] = f'{key}={val}'
        assert not any(l.startswith('Button/Name/RM5_PrimalSupport=') for l in lines)
        files[M5 + KO] = (knl.join(lines).rstrip('\r\n') + knl + knl.join(ADD) + knl).encode('utf-8')
        V35.gate('kokr', files[M5 + KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M5}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[M5 + KO])
        for loc in ['kokr'] + V35.OTHER_LOCALES:
            hp = f'{M5}{loc}.sc2data/localizeddata/gamehotkeys.txt'
            d = files[hp]
            h = d.decode('utf-8-sig')
            hn = '\r\n' if '\r\n' in h else '\n'
            files[hp] = (h.rstrip('\r\n') + hn + 'Button/Hotkey/RM5_PrimalSupport=B' + hn).encode(
                'utf-8-sig' if d.startswith(b'\xef\xbb\xbf') else 'utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        import xml.etree.ElementTree as ET
        for n, d in files.items():
            if n.startswith(M5) and n.endswith('.xml'): ET.fromstring(d)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if not n.startswith(M5) and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
