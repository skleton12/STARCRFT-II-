#!/usr/bin/env python3
"""0.12.13 -> 0.12.14: 피닉스 용사 탈리스 멈춤 (사용자 2026-11-27 "탈리스 안움직이는 버그 그대로").

0.9.6에서 정의 없는 전술 AI 함수를 지웠지만 그대로였다. 다음 후보(코덱스 0.9.6 의견): 자동 시전 '튕기는 공격'.
FenixTalisAdeptBounceShot은 공격 명령에 붙는 CAbilAugment이고, 첫 탄(FenixTalisAdeptBounceShotLM1)에
'대상까지 길 거리 6.1 미만'(Pathing=1) 검사가 있다. 절벽·건물 너머 적처럼 길 거리가 멀면 이 검사가 실패하고
증강된 공격 명령이 취소돼 탈리스가 멈출 수 있다 (게임 확인 필요).

maps 3~9·11·12 (탈리스가 있는 맵):
  - 탈리스 능력 목록에서 증강 능력을 빼고, 명령 카드 (2,1) 버튼은 같은 아이콘의 패시브 표시로.
  - 대신 무기 효과를 묶음(RM14_TalisAttackSet)으로: 원래 탄(FenixTalisAdeptLM) + 튕기는 탄.
    튕기는 탄은 숨은 5초 대기 행동(RM14_TalisBounceCD)이 없을 때만 나가고 나가면 대기를 건다 = 원래 재사용 대기 5초.
  - 튕기는 첫 탄(FenixTalisAdeptBounceShotLM1)에서 길 거리 검사를 뺀다 (무기 사거리 4 안, 연출 ID 유지 — 코덱스 검토).
  - 적 업그레이드 3/3 (사용자 "적들 업그레이드 3/3 까지 할수 있게 해줘 동맹있으니 너무 잘 갈린다"): 7-1 강화를 받는 적의
    공방 줄(gf_rmVHAdd에 등록된 줄, 모든 난이도)이 임무 10분에 2단계, 18분에 3단계 (쉬움·보통 ×1.2, 아주 어려움 ×0.8, 시험값).
    원본이 더 일찍 준 단계는 그대로. 1·2번(적 업그레이드 너프 예외)·10번 탈옥은 제외.
  - 적 방어 병력 (사용자 "적들이 방어용 병력도 챙기게 해줘 공격용 따로 방어용 따로"): 7-1 적(본진 있는 최대 3명)마다
    본진 앞 수비대(스크립트 조종, 공세에 안 빠짐). 임무 3분부터 60초마다, 본진 25칸 안에 레이너·동맹이 없을 때
    상한(쉬움 6·보통 8·어려움 12·아주 어려움 16)까지 보충. 테란 해병·불곰·공성 전차, 저그 저글링·바퀴·히드라,
    프로토스 광전사·추적자. 3초마다 본진 22칸 안 적을 치고, 없으면 제자리로. 모두 시험값.
  - 정화자 대의회 시간 가속 재사용 대기 30 → 10초 (사용자 "시간 가속 10초로 해줘", 4~9·11·12번, 지속 20초 그대로).
피해·튕김 수·대상은 원작 그대로. Game not run.

Usage: python3 tools/build_v01214.py <0.12.13 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.12.13', b'version=0.12.14'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
G = '.SC2Map/base.sc2data/gamedata/'

EFFECTS = '''    <CEffectSet id="RM14_TalisAttackSet">
        <EditorCategories value="Race:Protoss" />
        <EffectArray value="FenixTalisAdeptLM" />
        <EffectArray value="RM14_TalisBounceSet" />
    </CEffectSet>
    <CEffectSet id="RM14_TalisBounceSet">
        <EditorCategories value="Race:Protoss" />
        <ValidatorArray value="RM14_TalisBounceReady" />
        <EffectArray value="RM14_TalisBounceCDAB" />
        <EffectArray value="FenixTalisAdeptBounceShotLM1" />
    </CEffectSet>
    <CEffectApplyBehavior id="RM14_TalisBounceCDAB">
        <EditorCategories value="Race:Protoss" />
        <WhichUnit Value="Caster" />
        <Behavior value="RM14_TalisBounceCD" />
    </CEffectApplyBehavior>
'''
BEHAVIOR = '''    <CBehaviorBuff id="RM14_TalisBounceCD">
        <EditorCategories value="Race:Protoss" />
        <InfoFlags index="Hidden" value="1" />
        <Duration value="5" />
    </CBehaviorBuff>
'''
VALIDATOR = '''    <CValidatorUnitCompareBehaviorCount id="RM14_TalisBounceReady">
        <WhichUnit Value="Caster" />
        <Behavior value="RM14_TalisBounceCD" />
        <Compare value="EQ" />
        <Value value="0" />
    </CValidatorUnitCompareBehaviorCount>
'''


def one(t, tag, i):
    m = list(re.finditer(r'<%s id="%s"[^>]*>.*?</%s>' % (tag, i, tag), t, re.S)); assert len(m) == 1, (tag, i, len(m))
    return m[0]


def append(t, block):
    k = t.rindex('</Catalog>'); return t[:k] + block + t[k:]


def p_unit(t, m):
    e = one(t, 'CUnit', 'FenixTalisAdept'); b = e.group(0)
    a = '\n        <AbilArray Link="FenixTalisAdeptBounceShot" />'; assert b.count(a) == 1, m
    c = '<LayoutButtons Face="FenixTalisAdeptBounceShot" Type="AbilCmd" AbilCmd="FenixTalisAdeptBounceShot,Execute" Row="2" Column="1" />'
    assert b.count(c) == 1, m
    b = b.replace(a, '').replace(c, '<LayoutButtons Face="FenixTalisAdeptBounceShot" Type="Passive" Row="2" Column="1" />')
    return t[:e.start()] + b + t[e.end():]


def p_weapon(t, m):
    e = one(t, 'CWeaponLegacy', 'FenixTalisAdept'); b = e.group(0)
    a = '<Effect value="FenixTalisAdeptLM" />'; assert b.count(a) == 1, m
    return t[:e.start()] + b.replace(a, '<Effect value="RM14_TalisAttackSet" />') + t[e.end():]


def p_effect(t, m):
    e = one(t, 'CEffectLaunchMissile', 'FenixTalisAdeptBounceShotLM1'); b = e.group(0)
    a = '\n        <ValidatorArray value="FenixTalisAdeptBounceShotMaxDistance" />'; assert b.count(a) == 1, m
    return append(t[:e.start()] + b.replace(a, '') + t[e.end():], EFFECTS)


UP_SCRIPT = (
    '// 0.12.14 (user 2026-11-27 "적들 업그레이드 3/3 까지 할수 있게"): enemy weapon/armor lines climb with mission time,\n'
    '// level 2 at 10 min, level 3 at 18 min (trial; Easy/Normal x1.2, Very Hard x0.8). Original grants still count.\n'
    'const fixed gv_rmUpT2 = 600.0;\nconst fixed gv_rmUpT3 = 1080.0;\n'
    'int gf_rmUpTimeLevel () {\n'
    '    fixed k = 1.0;\n    fixed t = GameGetMissionTime();\n'
    '    if (libNtve_gf_DifficultyValueInt(1,1,0,0)==1) { k = 1.2; }\n'
    '    if (libNtve_gf_DifficultyValueInt(0,0,0,1)==1) { k = 0.8; }\n'
    '    if (t >= gv_rmUpT3 * k) { return 3; }\n    if (t >= gv_rmUpT2 * k) { return 2; }\n    return 1;\n}\n\n')

GUARD = """// 0.12.14 (user 2026-11-27 "적들이 방어용 병력도 챙기게 해줘 공격용 따로 방어용 따로"): each 7-1 enemy with a main
// keeps a home guard (script controlled, never joins attack waves). From 3 min, every 60 s top up to the cap while no
// Raynor/ally army is within 25 of the main; every 3 s the guard attacks intruders within 22, else walks back (trial).
const int gv_rmGuardMaxPlayers = 3;
unitgroup[16] gv_rmGuard;
int[16] gv_rmGuardMade;
bool gv_rmGuardOn;

int gf_rmGuardCap () {
    return libNtve_gf_DifficultyValueInt(6, 8, 12, 16);
}

point gf_rmGuardPt (int p, unit h) {
    point c = UnitGetPosition(h);
    point home = PlayerStartLocation(1);
    point pt;
    if (home != null) { c = PointWithOffsetPolar(c, 7.0, AngleBetweenPoints(c, home)); }
    pt = UnitTypePlacementFromPoint("Marine", p, c, 8.0);
    if (pt == null) { pt = c; }
    return pt;
}

string gf_rmGuardKind (int p, int n) {
    string r = PlayerRace(p);
    if (r == "Zerg") { if (ModI(n, 4) == 3) { return "Hydralisk"; } if (ModI(n, 4) == 2) { return "Roach"; } return "Zergling"; }
    if (r == "Prot") { if (ModI(n, 2) == 1) { return "Stalker"; } return "Zealot"; }
    if (ModI(n, 6) == 5) { return "SiegeTank"; }
    if (ModI(n, 3) == 2) { return "Marauder"; }
    return "Marine";
}

bool gf_rmGuardIntrudersFor (int p, point c, fixed r) {
    return UnitGroupCount(UnitGroupAlliance(p, c_unitAllianceEnemy, RegionCircle(c, r), UnitFilter(0, 0, (1 << c_targetFilterMissile) | (1 << c_targetFilterStructure), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0), c_unitCountAlive) > 0;
}

bool gt_rmGuardTop_Func (bool testConds, bool runActions) {
    int p;
    int k;
    int used = 0;
    unit h;
    point pt;
    string kind;
    if (!runActions || GameGetMissionTime() < 180.0) { return true; }
    for (p = 2; p <= 15; p += 1) {
        if (!gv_rmEHOn[p] || used >= gv_rmGuardMaxPlayers) { continue; }
        h = gf_rmVHHall(p);
        if (h == null) { continue; }
        used += 1;
        if (gv_rmGuard[p] == null) { gv_rmGuard[p] = UnitGroupEmpty(); }
        pt = gf_rmGuardPt(p, h);
        if (gf_rmGuardIntrudersFor(p, UnitGetPosition(h), 25.0)) { continue; }
        for (k = UnitGroupCount(gv_rmGuard[p], c_unitCountAlive); k < gf_rmGuardCap(); k += 1) {
            kind = gf_rmGuardKind(p, gv_rmGuardMade[p]);
            gv_rmGuardMade[p] += 1;
            if (!PointPathingPassable(pt)) { break; }
            UnitCreate(1, kind, 0, p, pt, 270.0);
            if (UnitLastCreated() == null) { continue; }
            AISetUnitScriptControlled(UnitLastCreated(), true);
            UnitGroupAdd(gv_rmGuard[p], UnitLastCreated());
        }
    }
    return true;
}

bool gt_rmGuardAct_Func (bool testConds, bool runActions) {
    int p;
    int i;
    unit h;
    unit u;
    point pt;
    unitgroup foes;
    if (!runActions) { return true; }
    for (p = 2; p <= 15; p += 1) {
        if (gv_rmGuard[p] == null || UnitGroupCount(gv_rmGuard[p], c_unitCountAlive) == 0) { continue; }
        h = gf_rmVHHall(p);
        if (h == null) { continue; }
        pt = gf_rmGuardPt(p, h);
        foes = UnitGroupAlliance(p, c_unitAllianceEnemy, RegionCircle(UnitGetPosition(h), 22.0), UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);
        for (i = UnitGroupCount(gv_rmGuard[p], c_unitCountAll); i > 0; i -= 1) {
            u = UnitGroupUnit(gv_rmGuard[p], i);
            if (!UnitIsAlive(u)) { continue; }
            if (UnitGroupCount(foes, c_unitCountAlive) > 0) {
                if (UnitOrderCount(u) == 0) { UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), UnitGetPosition(UnitGroupClosestToPoint(foes, UnitGetPosition(u)))), c_orderQueueReplace); }
            }
            else if (DistanceBetweenPoints(UnitGetPosition(u), pt) > 8.0) {
                UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), pt), c_orderQueueReplace);
            }
        }
    }
    return true;
}

void gf_rmGuardStart () {
    if (gv_rmGuardOn) { return; }
    gv_rmGuardOn = true;
    TriggerAddEventTimePeriodic(TriggerCreate("gt_rmGuardTop_Func"), 60.0, c_timeGame);
    TriggerAddEventTimePeriodic(TriggerCreate("gt_rmGuardAct_Func"), 3.0, c_timeGame);
}

"""


def p_script(t, m):
    def rep(a, b):
        nonlocal t
        assert t.count(a) == 1, (m, a[:60]); t = t.replace(a, b)
    rep('void gf_rmVHLevel (int p, int s) {', UP_SCRIPT + 'void gf_rmVHLevel (int p, int s) {')
    rep('    want=MinI(3,orig+gv_rmVeryHardExtraLevels);\n', '    want=MinI(3,MaxI(orig+gv_rmVeryHardExtraLevels,gf_rmUpTimeLevel()));\n')
    rep('    if (gv_rmVeryHardExtraLevels<=0 || libNtve_gf_DifficultyValueInt(0,0,0,1)==0 || gv_rmVHLines[p]>=8) { return; }',
        '    gf_rmGuardStart();\n    if (gv_rmVHLines[p]>=8) { return; }')
    # guard needs gf_rmVHHall (0.6.40, defined later): place the guard block right before gf_rmVHAdd's 0.6.17 neighbour? no -
    # put it just before the 0.6.40 block is too early for gf_rmVHAdd; so declare the starter first and define after gf_rmVHHall.
    rep('void gf_rmVHAdd (int p, string line) {', 'void gf_rmGuardStart ();\nvoid gf_rmVHAdd (int p, string line) {')
    a = 'bool gf_rmVHBaseBuild (int p, string k, point c) {'
    rep(a, GUARD + a)
    return t


CHRONO_MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
LOCALES = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']


def p_chrono_abil(t, m):
    e = one(t, 'CAbilEffectTarget', 'RM9_Chrono'); b = e.group(0)
    a = '<Cooldown TimeUse="30" />'; assert b.count(a) == 1, m
    return t[:e.start()] + b.replace(a, '<Cooldown TimeUse="10" />') + t[e.end():]


def p_chrono_str(d, m, loc):
    lines = d.split(b'\n'); hit = 0
    for i, l in enumerate(lines):
        if l.startswith(b'Button/Tooltip/RM9_Chrono='):
            n = l.replace('재사용 대기시간 30초'.encode(), '재사용 대기시간 10초'.encode()).replace(b'Cooldown 30 seconds', b'Cooldown 10 seconds')
            assert n != l, (m, loc); lines[i] = n; hit += 1
    assert hit == 1, (m, loc, hit)
    return b'\n'.join(lines)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            for f, fn in (('unitdata.xml', p_unit), ('weapondata.xml', p_weapon),
                          ('effectdata.xml', p_effect),
                          ('behaviordata.xml', lambda t, m: append(t, BEHAVIOR)),
                          ('validatordata.xml', lambda t, m: append(t, VALIDATOR))):
                k = m + G + f; t = files[k].decode('utf-8')
                assert 'RM14_Talis' not in t or f in ('unitdata.xml', 'weapondata.xml'), (m, f)
                t = fn(t, m); E.fromstring(t.encode('utf-8'))
                files[k] = t.encode('utf-8'); changed.add(k)
            if m in CHRONO_MAPS:
                k = m + G + 'abildata.xml'; files[k] = p_chrono_abil(files[k].decode('utf-8'), m).encode('utf-8'); changed.add(k)
                for loc in LOCALES:
                    k = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[k] = p_chrono_str(files[k], m, loc); changed.add(k)
            k = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
            files[k] = p_script(raw.replace('\r\n', '\n'), m).replace('\n', nl).encode('utf-8'); changed.add(k)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
