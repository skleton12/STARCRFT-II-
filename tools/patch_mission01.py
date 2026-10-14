#!/usr/bin/env python3
"""1번 미션(해방의 날) 패치: 레이너(1번 슬롯) 측 해병을 용병 전쟁광(WarPig)으로 바꾼다.

원본 맵(source/.../traynor01.sc2map)을 build/TRaynor01.SC2Map으로 복사한 뒤
트리거 데이터(triggers)와 생성된 스크립트(mapscript.galaxy)를 같은 내용으로 고친다.
편집기는 triggers에서 mapscript.galaxy를 다시 만들기 때문에 둘 다 바꿔야 한다.

적(2번 자치령)과 연출용(4번) 해병, 자치령 해병 처치 통계 조건은 건드리지 않는다.
"""
import os, re, shutil, struct, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'liberty.sc2campaign', 'base.sc2maps', 'maps', 'campaign', 'traynor01.sc2map')
OUT = os.path.join(ROOT, 'build', 'TRaynor01.SC2Map')

MERC_MARINE = 'WarPig'  # 해병 역할 용병 (사용자 확정 2026-10-13)

# 레이너 측 해병을 만드는 트리거 함수 호출 (triggers 안의 FunctionCall Id)
P1_MARINE_CALLS = {
    '5581142B': '유닛 도움말 패널에 해병 추가',
    '0D4D4EE7': '중간 증원 3명 (지점 58)',
    'EAA58A0F': '중간 증원 3명 (지점 89)',
    '9DD16ECE': '중간 증원 3명 (지점 106)',
    '375FC5FD': '시작 연출 수송선 화물 5명',
    '0CCF2C98': '시작 배치 (지점 415)',
    '6500E82C': '시작 배치 (지점 581)',
    '90566DEC': '시작 배치 (지점 737)',
    '1EA61321': '시작 배치 (지점 885)',
    'E6D930DB': '시작 배치 (지점 1020)',
}

# mapscript.galaxy에서 바꿀 줄 (위 호출들이 만들어낸 코드)
GALAXY_PATTERNS = [
    r'libCamp_gf_AddUnitTypeToUnitHelpPanel\("Marine", false, gv_p1_USER\)',
    r'libNtve_gf_CreateUnitsWithDefaultFacing\(3, "Marine", 0, gv_p1_USER, PointFromId\(\d+\)\)',
    r'UnitCargoCreate\(gv_introDropship, "Marine", 5\)',
    r'libNtve_gf_CreateUnitsAtPoint2\(1, "Marine", 0, gv_p1_USER, PointFromId\(\d+\)\)',
]


def patch_triggers(text):
    # FunctionCall -> 그 안의 Param Id 목록
    calls = dict(re.findall(r'<Element Type="FunctionCall" Id="([0-9A-F]+)">(.*?)</Element>', text, re.S))
    done = []
    for call_id, desc in P1_MARINE_CALLS.items():
        body = calls.get(call_id)
        if body is None:
            sys.exit(f'트리거 호출 {call_id}({desc})을 찾지 못함')
        hit = False
        for pid in re.findall(r'<Parameter Type="Param" Id="([0-9A-F]+)"/>', body):
            pat = re.compile(r'(<Element Type="Param" Id="%s">.*?<Value>)Marine(</Value>.*?</Element>)' % pid, re.S)
            text, n = pat.subn(r'\g<1>%s\g<2>' % MERC_MARINE, text, count=1)
            if n:
                hit = True
                break
        if not hit:
            sys.exit(f'트리거 호출 {call_id}({desc})에 Marine 값이 없음')
        done.append(desc)
    return text, done


def patch_galaxy(text):
    total = 0
    for pat in GALAXY_PATTERNS:
        text, n = re.subn(pat, lambda m: m.group(0).replace('"Marine"', f'"{MERC_MARINE}"'), text)
        total += n
    return text, total


# 동맹 AI 플레이어 슬롯 (사용자 확정 2026-10-13: 동맹 2명은 AI)
# 바이트 구성은 GPT가 만든 사본(RaynorMercs_WoL_CCM_Players8_9.zip)과 같다. 게임 시험 미실행
ALLY_PLAYERS = [
    # (번호, 종족, 한국어 이름, 영어 이름)
    (8, b'Prot', '정화자', 'Purifiers'),
    (9, b'Zerg', '원시 저그', 'Primal Zerg'),
]
HEADER_LOCALES = ['SUne', 'RFrf', 'EDed', 'SEse', 'XMse', 'URur', 'RKok', 'NChz', 'WThz', 'LPlp', 'TIti', 'RBtp']


def patch_mapinfo(d):
    """플레이어 레코드 뒤에 동맹 레코드를 붙인다.

    레코드: 번호(1) 조종(1, 1=사용자 2=컴퓨터) 0(3) 색(i32) 종족(4) 고정 13바이트 + 데칼 이름(NUL 끝).
    0x87 바이트는 레코드 수 + 1이다 (원본 6 = 레코드 5개).
    """
    count = d[0x87]
    p = 0xa2
    for _ in range(count - 1):
        p = d.index(b'\x00', p + 26) + 1
    recs = b''.join(bytes([n, 2]) + b'\x00' * 3 + struct.pack('<i', -1) + race + b'\x00' * 14
                    for n, race, *_ in ALLY_PLAYERS)
    d = bytearray(d[:p] + recs + d[p:])
    d[0x87] = count + len(ALLY_PLAYERS)
    return bytes(d)


def patch_header(d):
    """의존성 목록 뒤 속성 표에 동맹 플레이어 이름을 언어마다 추가한다.

    속성: 키 길이(u16) 키 언어(4) 값 길이(u16) 값(UTF-8). 앞에 속성 수(u32).
    """
    marker = b'Campaigns/LibertyStory.SC2Campaign\x00'
    p = d.index(marker) + len(marker)
    n = struct.unpack('<I', d[p:p + 4])[0]
    add = b''
    for loc in HEADER_LOCALES:
        for num, _, ko, en in ALLY_PLAYERS:
            k = f'MapInfo/Player{num:02d}/Name'.encode()
            v = (ko if loc == 'RKok' else en).encode('utf-8')  # 원본처럼 한국어 칸만 한국어
            add += struct.pack('<H', len(k)) + k + loc.encode() + struct.pack('<H', len(v)) + v
    return d[:p] + struct.pack('<I', n + len(HEADER_LOCALES) * len(ALLY_PLAYERS)) + d[p + 4:] + add


# 원본 문자열을 구하지 못한 이름
EXTRA_STRINGS = {}


def patch_strings(text):
    # 원본 맵 문자열 형식: '한국어 /// English'
    lines = ''.join(f'MapInfo/Player{num:02d}/Name={ko} /// {en}\r\n' for num, _, ko, en in ALLY_PLAYERS)
    lines += ''.join(f'{k}={v}\r\n' for k, v in EXTRA_STRINGS.items() if f'\n{k}=' not in text)
    if not text.endswith('\n'):
        text += '\r\n'
    return text + lines


# 동맹 스크립트 (mapscript.galaxy에만 넣는다)
# 편집기에서 맵을 저장하면 트리거 데이터로 스크립트를 다시 만들어 이 부분이 사라진다.
# 그래서 맵은 편집기로 저장하지 말고 이 도구로 원본에서 다시 만든다.
ALLY_UNITS = [  # (유닛, 수, 플레이어 변수, x 오프셋, y 오프셋) - 레이너 시작 지점(505) 기준
    # 2026-10-14 사용자 지시: 피닉스 대신 칼달리스 1 + 파수병 4 (밸런스)
    ('FenixKaldalisZealot', 1, 'gv_rm_PURIFIER', -3.0, 0.0),   # 칼달리스 (협동전 피닉스 용사), 돌진 기본 보유
    ('ZealotPurifier', 4, 'gv_rm_PURIFIER', -3.0, -2.0),
    # 2026-10-14 사용자 지시: 라바사우르스 3기를 두 번째 동맹(원시 저그 9번)이 통제 (전에는 레이너 1기)
    ('DehakaRavasaur', 3, 'gv_rm_PRIMAL', 2.0, -2.0),   # 협동전 라바사우르스 (군심 Ravasaur 아님)
]
ALLY_COLORS = {8: 3, 9: 6}  # 플레이어 색 번호: 정화자 청록, 원시 저그 주황 (임시)

# 동맹에게 처음부터 주는 업그레이드 (사용자 지시 2026-10-14: 돌진 같은 업그레이드)
# 'Charge'는 광전사(파수병) 돌진 능력의 조건(UseCharge). 칼달리스 돌진은 업그레이드 없이 기본
ALLY_UPGRADES = [('gv_rm_PURIFIER', 'Charge', 1)]

# 후반부 적 증강 (사용자 지시 2026-10-14: 적이 너무 약함, 후반부 적 수를 늘림)
# 병참 본부(배치 ID 158) 기준 오프셋에 자치령 수비대를 추가한다. 수와 위치는 시험값
# 적(자치령)의 최소 업그레이드 단계 (사용자 지시 2026-10-14: 우리는 용병이니 적 업그레이드 1)
# 원본은 어려움 이상에서만 보병 공격/방어 1을 준다(Init 06). 이미 그 단계 이상이면 더하지 않는다
ENEMY_MIN_UPGRADES = [('TerranInfantryWeaponsLevel1', 1), ('TerranInfantryArmorsLevel1', 1)]

# 난이도별 적(자치령) 공격·방어 강화 (사용자 지시 2026-10-14: 아주 어려움 50%, 약하면 150%; 난이도에 따라 다르게)
# 순서: 쉬움, 보통, 어려움, 아주 어려움. 공격 = 주는 피해 증가 %, 방어 = 받는 피해 감소로 환산 (100 / (1 + %))
# 아주 어려움 50%는 사용자 값, 나머지 단계는 시험값. 150%로 올리려면 마지막 값을 150으로
# 2026-10-14 사용자 시험 '살짝 빡셈, 동맹이 살살 녹음, 15% 줄여도 될 듯' → 단계마다 15%p 낮춤 (0 아래로 안 내림)
# 이전 값: (0, 15, 30, 50)
# 2026-10-14 사용자: 보통은 5
ENEMY_BUFF_PERCENT = (0, 5, 15, 35)

# 중앙(마을) 자치령 해병 증강 (사용자 지시 2026-10-14). 남·북 사이(y 50~90)에 있는 해병마다 추가할 수 (시험값)
MID_REGION = (0.0, 50.0, 136.0, 90.0)
MID_EXTRA_PER_MARINE = 1

# 2026-10-14 2차: 우리 병력도 좀 소모되는 정도로 → 해병 12, 화염방사병 6 (시험값)
LATE_DEFENDERS = [  # (유닛, 수, x 오프셋, y 오프셋)
    ('Marine', 4, -5.0, -8.0),
    ('Marine', 4, 0.0, -9.0),
    ('Marine', 4, 5.0, -8.0),
    ('Firebat', 3, -3.0, -6.0),
    ('Firebat', 3, 3.0, -6.0),
]  # 플레이어 색 번호: 정화자 청록, 원시 저그 주황 (임시)

GALAXY_ALLY_BLOCK = """
//--------------------------------------------------------------------------------------------------
// RaynorMercs: co-op allies (inserted by tools/patch_mission01.py)
//--------------------------------------------------------------------------------------------------
const int gv_rm_PURIFIER = 8;
const int gv_rm_PRIMAL = 9;
unitgroup gv_rm_purifierUnits;
trigger gt_rm_AllyFollow;
trigger gt_rm_AllyPing;
point gv_rm_pingTarget;

// Living, visible, non-structure units of both AI allies (Purifiers 8, Primal Zerg 9)
unitgroup gf_rm_AllyArmy () {
    unitfilter lv_f = UnitFilter(0, 0, (1 << c_targetFilterMissile) | (1 << c_targetFilterStructure), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)));
    unitgroup lv_g = UnitGroup(null, gv_rm_PURIFIER, RegionEntireMap(), lv_f, 0);
    UnitGroupAddUnitGroup(lv_g, UnitGroup(null, gv_rm_PRIMAL, RegionEntireMap(), lv_f, 0));
    return lv_g;
}

void gf_rm_SetAllyPlayer (int lp_p) {
    libNtve_gf_SetAlliance(gv_p1_USER, lp_p, libNtve_ge_AllianceSetting_AllyWithSharedVision);
    libNtve_gf_SetAlliance(gv_p2_DOMINION_RED, lp_p, libNtve_ge_AllianceSetting_Enemy);
    libNtve_gf_SetAlliance(gv_p3_RIKSVILLE_YELLOW, lp_p, libNtve_ge_AllianceSetting_Neutral);
    libNtve_gf_SetAlliance(gv_p4_ACTORS_BLUE, lp_p, libNtve_ge_AllianceSetting_Neutral);
    libNtve_gf_SetAlliance(gv_p5_RIKSVILLE_PUSHY, lp_p, libNtve_ge_AllianceSetting_Neutral);
}

// A new human ping replaces current orders; automatic follow cannot override it.
bool gt_rm_AllyPing_Func (bool testConds, bool runActions) {
    unitgroup lv_g;
    int lv_i;
    unit lv_u;
    point lv_point;
    if (!runActions) {
        return true;
    }
    if (EventPlayer() != gv_p1_USER || gv_gameOver || gv_inCinematic || !UnitIsAlive(gv_raynor)) {
        return true;
    }
    lv_point = EventPingPoint();
    if (lv_point == null) {
        return true;
    }
    gv_rm_pingTarget = Point(PointGetX(lv_point), PointGetY(lv_point));
    lv_g = gf_rm_AllyArmy();
    lv_i = UnitGroupCount(lv_g, c_unitCountAll);
    for ( ; lv_i > 0 ; lv_i -= 1) {
        lv_u = UnitGroupUnit(lv_g, lv_i);
        UnitIssueOrder(lv_u, OrderTargetingPoint(AbilityCommand("attack", 0), gv_rm_pingTarget), c_orderQueueReplace);
    }
    return true;
}

// Idle units follow Raynor until the first ping, then rally around the last ping.
bool gt_rm_AllyFollow_Func (bool testConds, bool runActions) {
    unitgroup lv_g;
    int lv_i;
    unit lv_u;
    point lv_target;
    fixed lv_radius;

    if (!runActions) {
        return true;
    }
    if (gv_gameOver || gv_inCinematic || !UnitIsAlive(gv_raynor)) {
        return true;
    }
    lv_target = UnitGetPosition(gv_raynor);
    lv_radius = 6.0;
    if (gv_rm_pingTarget != null) {
        lv_target = gv_rm_pingTarget;
        lv_radius = 3.0; // Trial arrival tolerance; do not force units onto one point.
    }
    lv_g = gf_rm_AllyArmy();
    lv_i = UnitGroupCount(lv_g, c_unitCountAll);
    for ( ; lv_i > 0 ; lv_i -= 1) {
        lv_u = UnitGroupUnit(lv_g, lv_i);
        if (UnitOrderCount(lv_u) == 0 && DistanceBetweenPoints(UnitGetPosition(lv_u), lv_target) > lv_radius) {
            UnitIssueOrder(lv_u, OrderTargetingPoint(AbilityCommand("attack", 0), lv_target), c_orderQueueReplace);
        }
    }
    return true;
}

void gf_rm_AllyInit () {
    gv_rm_pingTarget = null;
    gv_rm_purifierUnits = UnitGroupEmpty();
    gf_rm_SetAllyPlayer(gv_rm_PURIFIER);
    gf_rm_SetAllyPlayer(gv_rm_PRIMAL);
    libNtve_gf_SetAlliance(gv_rm_PURIFIER, gv_rm_PRIMAL, libNtve_ge_AllianceSetting_AllyWithSharedVision);
%(colors)s
%(upgrades)s
    gt_rm_AllyFollow = TriggerCreate("gt_rm_AllyFollow_Func");
    TriggerAddEventTimePeriodic(gt_rm_AllyFollow, 2.0, c_timeGame);
    TriggerEnable(gt_rm_AllyFollow, false);
    gt_rm_AllyPing = TriggerCreate("gt_rm_AllyPing_Func");
    TriggerAddEventPing(gt_rm_AllyPing, gv_p1_USER);
    TriggerEnable(gt_rm_AllyPing, false);
}

// Extra Dominion defenders south of the Logistics HQ (trial values)
void gf_rm_SpawnLateDefenders () {
    point lv_hq = UnitGetPosition(UnitFromId(158));
%(defenders)s
}

// Difficulty-scaled Dominion damage dealt / taken (co-op uses the same player properties)
void gf_rm_EnemyDifficultyBuff () {
    int lv_buff = libNtve_gf_DifficultyValueInt(%(buff)s);
    PlayerModifyPropertyInt(gv_p2_DOMINION_RED, c_playerPropDamageDealtPercent, c_playerPropOperSetTo, 100 + lv_buff);
    PlayerModifyPropertyInt(gv_p2_DOMINION_RED, c_playerPropDamageTakenPercent, c_playerPropOperSetTo, 10000 / (100 + lv_buff));
}

// Extra Dominion marines next to every marine in the town band (trial value)
void gf_rm_SpawnMidReinforce () {
    unitgroup lv_g = UnitGroup("Marine", gv_p2_DOMINION_RED, RegionRect(%(mid_region)s), UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0);
    int lv_i = UnitGroupCount(lv_g, c_unitCountAll);
    unit lv_u;
    for ( ; lv_i > 0 ; lv_i -= 1) {
        lv_u = UnitGroupUnit(lv_g, lv_i);
        UnitCreate(%(mid_extra)s, "Marine", 0, gv_p2_DOMINION_RED, UnitGetPosition(lv_u), UnitGetFacing(lv_u));
    }
}

// Dominion gets at least these upgrade levels on every difficulty (never stacks past them)
void gf_rm_EnemyMinUpgrades () {
%(enemy_upgrades)s
}

void gf_rm_SpawnAllies () {
    point lv_pt = PointFromId(505);
%(spawns)s
    TriggerEnable(gt_rm_AllyFollow, true);
    TriggerEnable(gt_rm_AllyPing, true);
    gf_rm_SpawnLateDefenders();
    gf_rm_SpawnMidReinforce();
    gf_rm_EnemyMinUpgrades();
    gf_rm_EnemyDifficultyBuff();
}

"""

# 위 블록을 넣을 자리와 호출을 넣을 자리 (원본 스크립트의 고정 문자열)
GALAXY_ANCHOR_BLOCK = 'void InitGlobals () {'
GALAXY_ANCHOR_INIT = 'PlayerSetAlliance(gv_p3_RIKSVILLE_YELLOW, c_allianceIdPushable, gv_p1_USER, true);'
GALAXY_ANCHOR_SPAWN = ('    libNtve_gf_CreateUnitsAtPoint2(1, "%s", 0, gv_p1_USER, PointFromId(1020));\r\n'
                       '    UnitGroupAdd(gv_raynorsMarines, UnitLastCreated());\r\n')


def patch_galaxy_allies(g):
    if 'const int gv_rm_PURIFIER = 8;' in g:
        sys.exit('동맹 코드가 이미 있음: 패치된 맵 대신 원본에서 빌드해야 함')
    nl = '\r\n' if '\r\n' in g else '\n'
    spawns = []
    for unit, n, player, dx, dy in ALLY_UNITS:
        spawns.append(f'    UnitCreate({n}, "{unit}", 0, {player}, PointWithOffset(lv_pt, {dx}, {dy}), 270.0);')
        if player == 'gv_rm_PURIFIER':
            spawns.append('    UnitGroupAddUnitGroup(gv_rm_purifierUnits, UnitLastCreatedGroup());')
    colors = '\n'.join(f'    PlayerSetColorIndex({p}, {c}, true);' for p, c in ALLY_COLORS.items())
    defenders = '\n'.join(f'    UnitCreate({n}, "{u}", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, {dx}, {dy}), 90.0);'
                          for u, n, dx, dy in LATE_DEFENDERS)
    upgrades = '\n'.join(f'    TechTreeUpgradeAddLevel({p}, "{u}", {lv});' for p, u, lv in ALLY_UPGRADES)
    enemy_upgrades = '\n'.join(
        f'    if (TechTreeUpgradeCount(gv_p2_DOMINION_RED, "{u}", c_techCountCompleteOnly) < {lv}) {{\n'
        f'        TechTreeUpgradeAddLevel(gv_p2_DOMINION_RED, "{u}", {lv} - TechTreeUpgradeCount(gv_p2_DOMINION_RED, "{u}", c_techCountCompleteOnly));\n'
        f'    }}' for u, lv in ENEMY_MIN_UPGRADES)
    block = GALAXY_ALLY_BLOCK % {'spawns': '\n'.join(spawns), 'colors': colors, 'defenders': defenders,
                                 'upgrades': upgrades, 'enemy_upgrades': enemy_upgrades,
                                 'buff': ', '.join(str(b) for b in ENEMY_BUFF_PERCENT),
                                 'mid_region': ', '.join(str(v) for v in MID_REGION),
                                 'mid_extra': MID_EXTRA_PER_MARINE}
    block = block.replace('\n', nl)
    for anchor in (GALAXY_ANCHOR_BLOCK, GALAXY_ANCHOR_INIT):
        if g.count(anchor) != 1:
            sys.exit(f'스크립트 기준 문자열이 1개가 아님: {anchor}')
    spawn_anchor = GALAXY_ANCHOR_SPAWN % MERC_MARINE
    if nl == '\n':
        spawn_anchor = spawn_anchor.replace('\r\n', '\n')
    if g.count(spawn_anchor) != 1:
        sys.exit('스크립트 기준 문자열(시작 배치)이 1개가 아님')
    g = g.replace(GALAXY_ANCHOR_BLOCK, block.lstrip(nl) + GALAXY_ANCHOR_BLOCK)
    g = g.replace(GALAXY_ANCHOR_INIT, GALAXY_ANCHOR_INIT + nl + '    gf_rm_AllyInit();')
    g = g.replace(spawn_anchor, spawn_anchor + '    gf_rm_SpawnAllies();' + nl)
    return g


# 한국어 이외 언어는 전부 영어로 채운다 (사용자 지시 2026-10-14). 맵 구성 목록에 이미 있는 언어들
OTHER_LOCALES = ['enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']


def write_other_locales(map_dir):
    """한국어 문자열('한국어 /// English')에서 영어만 뽑아 다른 언어 파일을 만든다."""
    src = os.path.join(map_dir, 'kokr.sc2data', 'localizeddata', 'gamestrings.txt')
    with open(src, encoding='utf-8', newline='') as f:
        text = f.read()
    nl = '\r\n' if '\r\n' in text else '\n'
    out = []
    for line in text.splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            if ' /// ' in v:
                v = v.split(' /// ', 1)[1]
            elif re.search('[\uac00-\ud7a3]', v):
                v = k.rsplit('/', 1)[-1]  # 영어 원문이 없는 한국어는 ID 이름으로 대신
            line = f'{k}={v}'
        out.append(line)
    body = nl.join(out) + nl
    for loc in OTHER_LOCALES:
        d = os.path.join(map_dir, f'{loc}.sc2data', 'localizeddata')
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'gamestrings.txt'), 'w', encoding='utf-8', newline='') as f:
            f.write(body)


def main():
    if not os.path.isdir(SRC):
        sys.exit(f'원본 맵 없음: {SRC}')
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)

    p = os.path.join(OUT, 'triggers')
    with open(p, encoding='utf-8', newline='') as f:
        t = f.read()
    t, done = patch_triggers(t)
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)

    p = os.path.join(OUT, 'mapscript.galaxy')
    with open(p, encoding='utf-8', newline='') as f:
        g = f.read()
    g, n = patch_galaxy(g)
    g = patch_galaxy_allies(g)
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(g)

    for fn, fix in (('mapinfo', patch_mapinfo), ('documentheader', patch_header)):
        p = os.path.join(OUT, fn)
        with open(p, 'rb') as f:
            b = f.read()
        with open(p, 'wb') as f:
            f.write(fix(b))
    p = os.path.join(OUT, 'kokr.sc2data', 'localizeddata', 'gamestrings.txt')
    with open(p, encoding='utf-8', newline='') as f:
        t = f.read()
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(patch_strings(t))

    # 동맹 유닛 데이터를 맵 데이터로 복사 (피닉스, 정화자 광전사, 라바사우르)
    import subprocess
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'port_units.py'), OUT] + [u for u, *_ in ALLY_UNITS],
                   check=True, stdout=subprocess.DEVNULL)

    write_other_locales(OUT)

    if n != len(P1_MARINE_CALLS):
        sys.exit(f'mapscript.galaxy 변경 {n}곳, 트리거 {len(done)}곳: 개수가 다름')
    print(f'{OUT}')
    for d in done:
        print(f'  - {d}: Marine -> {MERC_MARINE}')
    for num, race, ko, en in ALLY_PLAYERS:
        print(f'  - 플레이어 {num} 추가: {race.decode()} 컴퓨터 "{ko} / {en}"')
    for unit, n, player, *_ in ALLY_UNITS:
        print(f'  - 시작 배치: {unit} x{n} ({player})')
    for p, u, lv in ALLY_UPGRADES:
        print(f'  - 동맹 업그레이드: {u} {lv}단계 ({p})')
    for u, lv in ENEMY_MIN_UPGRADES:
        print(f'  - 적 최소 업그레이드: {u} {lv}단계')
    print(f'  - 적 공격·방어 강화 % (쉬움/보통/어려움/아주 어려움): {ENEMY_BUFF_PERCENT}')
    print(f'  - 중앙 해병 증강: 해병마다 +{MID_EXTRA_PER_MARINE} (시험값)')
    for u, n, *_ in LATE_DEFENDERS:
        print(f'  - 후반부 적 추가 (시험값): {u} x{n}')


if __name__ == '__main__':
    main()

