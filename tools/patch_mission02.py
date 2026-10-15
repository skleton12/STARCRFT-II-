#!/usr/bin/env python3
"""2번 미션(무법자) 패치: 레이너 병력 용병화, 동맹 2명(8 정화자, 9 원시 저그), 적 강화.

원본 맵(source/.../traynor02.sc2map)을 build/TRaynor02.SC2Map으로 복사한 뒤 고친다.
동맹·용병 코드는 mapscript.galaxy에만 들어간다. 편집기로 저장하지 않는다 (CLAUDE.md 3장).
트리거 데이터(triggers)는 고치지 않는다 (편집기 저장 금지라 실행에 쓰이지 않음).

용병 (CLAUDE.md 3장, SCV는 예외):
  - 배치·연출 해병 → 전쟁광(WarPig). 레이너 측 해병 수를 세는 조건도 전쟁광으로
  - 병영 생산: 플레이어 1에게만 링크 치환(CatalogLinkReplace) 해병→전쟁광, 의무관→용병 의무관(MercMedic)
    치환이 생산에 적용되지 않을 때를 대비해 생산 완료 시 바꿔치기도 건다
  - 구출한 반군의 해병·의무관도 레이너 소유가 되는 순간 용병으로 바꾼다

동맹 (사용자 지시 2026-10-14): 표시한 지점에 몇 기씩 소환해 전진하는 방식.
  1번 원시 저그(9) 동쪽, 2번 정화자(8) 서쪽. 일정 시간 뒤 자치령 기지 공격 (C안). 핑 30초 유지 (7-0)
"""
import os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
import patch_mission01 as m1
import new_terrain

SRC = os.path.join(ROOT, 'source', 'liberty.sc2campaign', 'base.sc2maps', 'maps', 'campaign', 'traynor02.sc2map')
OUT = os.path.join(ROOT, 'build', 'TRaynor02.SC2Map')

# 동쪽 지형 확장 (사용자 지시 2026-10-15: 동쪽으로 50 정도, 반전 말고 새로 구성).
# x=104 경계 동쪽을 새 배치도로 그린다 (tools/new_terrain.py). 136 → 184 (+48). 모양·수치는 시험값
EXPAND_SEAM = 104
EXPAND_WIDTH = 184
EXPAND_CAMERA_RIGHT = 176
# 2번 진영에서 서쪽(자치령 동쪽 무리 쪽)으로 가는 길: 원본 2단계 언덕을 1단계로 뚫음 (사용자 수정본의 선, 시험값)
EAST_CARVE = [(96, 77, 103, 83, 1)]
EAST_ISLANDS = [(128.0, 72.0, 5.0), (146.0, 38.0, 4.0), (152.0, 94.0, 5.5)]  # 들판 안 3단계 고원 바위 (x, y, 반지름)
# 2026-10-15 사용자 '동쪽이 너무 평지 같음' → 층·기복·텍스처·장식 추가 (모두 시험값)
EAST_RIDGE = [(136.0, 58.0), (138.0, 66.0), (135.0, 74.0)]   # 남북으로 끊어진 3단계 능선 조각 (중심점)
EAST_MESAS = [(114.0, 60.0, 5.0), (160.0, 66.0, 4.5), (134.0, 106.0, 4.0), (126.0, 44.0, 3.5)]  # 2단계 대지
EAST_CRATERS = [(142.0, 50.0, 3.0), (117.0, 30.0, 2.6), (160.0, 104.0, 2.8)]  # 0단계 웅덩이
# 원본 쪽 x 88~103의 걸어서 못 가는 낮은 자투리는 고원으로 메움 (사용자 2026-10-15 '안 쓰는 땅 다듬어')
EAST_TIDY = (88, (29, 82))  # (x 시작, 레이너 본진 칸 (y, x))
EAST_KEEP_CLEAR = 9.0      # 동맹 진영 둘레는 비워 둠 (반지름)
EAST_RELIEF = (0.8, 1.2)   # 기복 높이(게임 단위): 들판, 대지·고원


def _wave(x, y, k):
    import math
    ph = (1.7, 4.1, 2.9, 0.6, 5.3, 3.3)
    return (math.sin(x / (7.0 + k) + ph[k % 6]) * math.cos(y / (9.0 + k) + ph[(k + 2) % 6])
            + 0.5 * math.sin((x + y) / (3.7 + k) + ph[(k + 4) % 6])) / 1.5


def _blob(x, y, cx, cy, r):
    import math
    rr = r + 0.9 * math.sin(math.atan2(y - cy, x - cx) * 3 + cx) + 0.5 * math.sin(math.atan2(y - cy, x - cx) * 5 + cy)
    return (x - cx) ** 2 + (y - cy) ** 2 <= rr * rr


def _near_base(x, y):
    return any((x - bx) ** 2 + (y - by) ** 2 < EAST_KEEP_CLEAR ** 2 for bx, by in ALLY_HOME.values())


def east_layout(x, y):
    """새 동쪽 땅: 3단계 고원이 둘러싼 1단계 들판. 안에 고원 바위·능선(3), 대지(2), 웅덩이(0)."""
    import math
    lo = 16 + 3 * math.sin(x / 6.0) + 2 * math.sin(x / 2.3) + 1.2 * math.sin(x / 1.3)
    hi = 112 + 3 * math.sin(x / 5.0 + 1) + 2 * math.sin(x / 2.9) + 1.2 * math.sin(x / 1.7)
    east = 166 + 3 * math.sin(y / 6.0) + 2 * math.sin(y / 2.7) + 1.2 * math.sin(y / 1.4)
    if not (lo <= y <= hi and x <= east):
        return 3
    if _near_base(x, y):
        return 1
    for cx, cy, r in EAST_ISLANDS:
        if _blob(x, y, cx, cy, r):
            return 3
    for cx, cy in EAST_RIDGE:
        if _blob(x, y, cx, cy, 2.6):
            return 3
    for cx, cy, r in EAST_MESAS:
        if _blob(x, y, cx, cy, r):
            return 2
    for cx, cy, r in EAST_CRATERS:
        if _blob(x, y, cx, cy, r):
            return 0
    return 1


def east_relief(x, y, level):
    amp = EAST_RELIEF[0] if level <= 1 else EAST_RELIEF[1]
    if level == 1 and _near_base(x, y):
        amp *= 0.3
    return amp * (_wave(x, y, 0) + 0.4 * _wave(x * 2.1, y * 2.1, 1))


def east_texnoise(x, y, k):
    v = 0.5 + 0.5 * _wave(x * 0.8, y * 0.8, 2 + k)
    return min(1.0, max(0.0, (v - 0.35) / 0.3)) if k == 0 else min(1.0, max(0.0, (v - 0.62) / 0.2))


def east_scatter(LV, seam):
    """새 땅 장식: 절벽 가장자리엔 나무·선인장·바위, 들판엔 균열·뼈·잔해, 고지대 위엔 나무 (시험값)."""
    import random
    rnd = random.Random(20261015)
    h, w = LV.shape
    # 2026-10-15 사용자: 나무 제거, 안 쓰는 땅(들판 밖 고원) 장식 없음
    edge_kinds = ['MarSaraCactus', 'Rock', 'Rock', 'Brambles', 'RockLarge']
    open_kinds = ['MarSaraCrack', 'MarSaraSkeletonSmall', 'MarSaraBones', 'MarSaraGroundProps', 'Rock', 'MarSaraCactus']
    out = []
    for y in range(2, h - 2):
        for x in range(seam + 2, w - 2):
            L = int(LV[y, x])
            nb = LV[y - 2:y + 3, x - 2:x + 3]
            edge = (nb != L).any()
            if L == 1:
                if _near_base(x, y):
                    continue
                kinds, p = (edge_kinds, 0.06) if edge else (open_kinds, 0.008)
            else:
                continue
            if rnd.random() < p:
                out.append((rnd.choice(kinds), x + rnd.random(), y + rnd.random(), rnd.random() * 6.2832, 0.85 + rnd.random() * 0.35))
    return out


MERC = {'Marine': 'WarPig', 'Medic': 'MercMedic'}  # 레이너 측 용병 대응

# 동맹 소환 지점 (사용자가 지도에 X로 표시, 2026-10-14). 지도 그림 좌표에서 읽은 값
ALLY_HOME = {
    # 2026-10-15 사용자 수정본: 두 동맹 진영을 동쪽 새 들판으로 옮김 (이전: 원시 저그 (84,73), 정화자 (30,49))
    'gv_rm_PRIMAL': (150.0, 26.0),   # 1번 원시 저그: 남동쪽 'Base 1'
    'gv_rm_PURIFIER': (122.0, 95.0), # 2번 정화자: 북동쪽 'Base 2'
}
# 소환 구성 (시험값: 사용자가 2번 미션 구성을 정하기 전까지 1번 미션 구성을 첫 소환에 씀)
FIRST_WAVE = [  # (유닛, 수, 플레이어)
    ('FenixKaldalisZealot', 1, 'gv_rm_PURIFIER'),
    ('ZealotPurifier', 4, 'gv_rm_PURIFIER'),
    ('DehakaRavasaur', 3, 'gv_rm_PRIMAL'),
]
NEXT_WAVE = [
    ('ZealotPurifier', 2, 'gv_rm_PURIFIER'),
    ('DehakaRavasaur', 2, 'gv_rm_PRIMAL'),
]
WAVE_INTERVAL = 90.0   # 추가 소환 간격 (게임 초, 시험값)
WAVE_MAX = 6           # 첫 소환 포함 최대 횟수 (시험값)
ATTACK_DELAY = 300.0   # C안: 미션 시작 후 이 시간이 지나면 자치령 기지 공격 (게임 초, 시험값)
ATTACK_TARGET_UNIT = 48          # 자치령 사령부 배치 ID (43.5,101.5)
ATTACK_TARGET_POINT = (45.0, 94.0)  # 사령부가 없으면 이 지점

ENEMY_PLAYERS = ['gv_pLAYER_02_DOMINION', 'gv_pLAYER_05_PATROL']
# 자치령 기지 지역(배치 지역 ID 8 'Dominion Base') 해병 증강: 해병 N명마다 1기 (시험값)
BASE_REGION_ID = 8
BASE_EVERY_NTH = 2

# mapscript.galaxy에서 플레이어 1 해병·의무관을 용병으로 바꿀 줄 (원본 줄 내용으로 찾음)
P1_LINE_FIXES = [
    ('libCamp_gf_AddUnitTypeToUnitHelpPanel("Marine", false, gv_pLAYER_01_USER);', 'Marine', 1),
    ('libCamp_gf_AddUnitTypeToUnitHelpPanel("Medic", false, gv_pLAYER_01_USER);', 'Medic', 1),
    ('UnitGroup("Marine", gv_pLAYER_01_USER, RegionPlayableMap()', 'Marine', 1),   # 반군 등장 조건: 해병 12
    ('UnitGroup("Medic", gv_pLAYER_01_USER, RegionEntireMap()', 'Medic', 1),     # 의무관 안내 조건
    ('libNtve_gf_CreateUnitsAtPoint2(1, "Marine", 0, gv_pLAYER_01_USER, PointFromId(13', 'Marine', 5),  # 승리 연출
    ('UnitCreate(1, "Marine", 0, gv_pLAYER_01_USER, lv_marinePoints1[1], 225.0);', 'Marine', 1),
    ('UnitGroup("Marine", gv_pLAYER_01_USER, RegionCircle(PointFromId(130', 'Marine', 2),
]

GALAXY_BLOCK = """
//--------------------------------------------------------------------------------------------------
// RaynorMercs: mercenaries + co-op allies (inserted by tools/patch_mission02.py)
//--------------------------------------------------------------------------------------------------
const int gv_rm_PURIFIER = 8;
const int gv_rm_PRIMAL = 9;
trigger gt_rm_AllyAI;
trigger gt_rm_AllyPing;
trigger gt_rm_AllyWave;
trigger gt_rm_TrainMerc;
point gv_rm_pingTarget;
fixed gv_rm_pingTime;
int gv_rm_waves;

// ---- Mercenaries (Raynor's units must all be mercenaries; SCVs excepted) ----
void gf_rm_ToMerc (unit lp_u) {
    string lv_t;
    if (lp_u == null || !UnitIsAlive(lp_u) || UnitGetOwner(lp_u) != gv_pLAYER_01_USER) {
        return;
    }
    lv_t = UnitGetType(lp_u);
%(merc_cases)s
}

void gf_rm_ConvertMercs () {
    unitgroup lv_g;
    int lv_i;
    unit lv_u;
    unit lv_new;
    lv_g = UnitGroup(null, gv_pLAYER_01_USER, RegionEntireMap(), UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32))), 0);
    lv_i = UnitGroupCount(lv_g, c_unitCountAll);
    for ( ; lv_i > 0 ; lv_i -= 1) {
        lv_u = UnitGroupUnit(lv_g, lv_i);
        if (%(merc_types)s) {
            gf_rm_ToMerc(lv_u);
            lv_new = libNtve_gf_LastReplacedUnit();
            if (UnitGroupHasUnit(gv_marinesRescued, lv_u)) {
                UnitGroupRemove(gv_marinesRescued, lv_u);
                UnitGroupAdd(gv_marinesRescued, lv_new);
            }
        }
    }
}

bool gt_rm_TrainMerc_Func (bool testConds, bool runActions) {
    if (!runActions) {
        return true;
    }
    gf_rm_ToMerc(EventUnitProgressUnit());
    return true;
}

void gf_rm_MercInit () {
%(merc_link)s
    gt_rm_TrainMerc = TriggerCreate("gt_rm_TrainMerc_Func");
    TriggerAddEventUnitTrainProgress(gt_rm_TrainMerc, null, c_unitProgressStageComplete);
}

// ---- Allies ----
unitgroup gf_rm_AllyArmy () {
    unitfilter lv_f = UnitFilter(0, 0, (1 << c_targetFilterMissile) | (1 << c_targetFilterStructure), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)));
    unitgroup lv_g = UnitGroup(null, gv_rm_PURIFIER, RegionEntireMap(), lv_f, 0);
    UnitGroupAddUnitGroup(lv_g, UnitGroup(null, gv_rm_PRIMAL, RegionEntireMap(), lv_f, 0));
    return lv_g;
}

void gf_rm_SetAllyPlayer (int lp_p) {
    libNtve_gf_SetAlliance(gv_pLAYER_01_USER, lp_p, libNtve_ge_AllianceSetting_AllyWithSharedVision);
    libNtve_gf_SetAlliance(gv_pLAYER_02_DOMINION, lp_p, libNtve_ge_AllianceSetting_Enemy);
    libNtve_gf_SetAlliance(gv_pLAYER_03_COLONISTS, lp_p, libNtve_ge_AllianceSetting_Neutral);
    libNtve_gf_SetAlliance(gv_pLAYER_04_REBELS, lp_p, libNtve_ge_AllianceSetting_Neutral);
    libNtve_gf_SetAlliance(gv_pLAYER_05_PATROL, lp_p, libNtve_ge_AllianceSetting_Enemy);
}

point gf_rm_Home (int lp_p) {
%(homes)s
    return null;
}

// C plan: hold at the spawn point, then attack the Dominion base after the delay (trial value)
point gf_rm_DefaultTarget (int lp_p) {
    if (GameGetMissionTime() >= %(attack_delay)s) {
        if (UnitIsAlive(UnitFromId(%(target_unit)s))) {
            return UnitGetPosition(UnitFromId(%(target_unit)s));
        }
        return Point(%(target_point)s);
    }
    return gf_rm_Home(lp_p);
}

bool gt_rm_AllyPing_Func (bool testConds, bool runActions) {
    unitgroup lv_g;
    int lv_i;
    point lv_point;
    if (!runActions) {
        return true;
    }
    if (EventPlayer() != gv_pLAYER_01_USER || gv_gameOver || gv_inCinematic) {
        return true;
    }
    lv_point = EventPingPoint();
    if (lv_point == null) {
        return true;
    }
    gv_rm_pingTarget = Point(PointGetX(lv_point), PointGetY(lv_point));
    gv_rm_pingTime = GameGetMissionTime();
    lv_g = gf_rm_AllyArmy();
    lv_i = UnitGroupCount(lv_g, c_unitCountAll);
    for ( ; lv_i > 0 ; lv_i -= 1) {
        UnitIssueOrder(UnitGroupUnit(lv_g, lv_i), OrderTargetingPoint(AbilityCommand("attack", 0), gv_rm_pingTarget), c_orderQueueReplace);
    }
    return true;
}

// Idle allies go to the ping (held %(ping_hold)s s) or their mission default target
bool gt_rm_AllyAI_Func (bool testConds, bool runActions) {
    unitgroup lv_g;
    int lv_i;
    unit lv_u;
    point lv_target;
    fixed lv_radius;
    if (!runActions) {
        return true;
    }
    if (gv_gameOver || gv_inCinematic) {
        return true;
    }
    if (gv_rm_pingTarget != null && GameGetMissionTime() - gv_rm_pingTime >= %(ping_hold)s) {
        gv_rm_pingTarget = null;
    }
    lv_g = gf_rm_AllyArmy();
    lv_i = UnitGroupCount(lv_g, c_unitCountAll);
    for ( ; lv_i > 0 ; lv_i -= 1) {
        lv_u = UnitGroupUnit(lv_g, lv_i);
        if (gv_rm_pingTarget != null) {
            lv_target = gv_rm_pingTarget;
            lv_radius = 3.0;
        }
        else {
            lv_target = gf_rm_DefaultTarget(UnitGetOwner(lv_u));
            lv_radius = 5.0;
        }
        if (lv_target != null && UnitOrderCount(lv_u) == 0 && DistanceBetweenPoints(UnitGetPosition(lv_u), lv_target) > lv_radius) {
            UnitIssueOrder(lv_u, OrderTargetingPoint(AbilityCommand("attack", 0), lv_target), c_orderQueueReplace);
        }
    }
    return true;
}

void gf_rm_SpawnWave (bool lp_first) {
    if (lp_first) {
%(first_wave)s
    }
    else {
%(next_wave)s
    }
    gv_rm_waves += 1;
}

bool gt_rm_AllyWave_Func (bool testConds, bool runActions) {
    if (!runActions) {
        return true;
    }
    if (gv_gameOver || gv_rm_waves >= %(wave_max)s) {
        return true;
    }
    gf_rm_SpawnWave(false);
    return true;
}

void gf_rm_AllyInit () {
    gv_rm_pingTarget = null;
    gv_rm_waves = 0;
    gf_rm_SetAllyPlayer(gv_rm_PURIFIER);
    gf_rm_SetAllyPlayer(gv_rm_PRIMAL);
    libNtve_gf_SetAlliance(gv_rm_PURIFIER, gv_rm_PRIMAL, libNtve_ge_AllianceSetting_AllyWithSharedVision);
%(colors)s
%(upgrades)s
    gt_rm_AllyAI = TriggerCreate("gt_rm_AllyAI_Func");
    TriggerAddEventTimePeriodic(gt_rm_AllyAI, 2.0, c_timeGame);
    TriggerEnable(gt_rm_AllyAI, false);
    gt_rm_AllyPing = TriggerCreate("gt_rm_AllyPing_Func");
    TriggerAddEventPing(gt_rm_AllyPing, gv_pLAYER_01_USER);
    TriggerEnable(gt_rm_AllyPing, false);
    gt_rm_AllyWave = TriggerCreate("gt_rm_AllyWave_Func");
    TriggerAddEventTimePeriodic(gt_rm_AllyWave, %(wave_interval)s, c_timeGame);
    TriggerEnable(gt_rm_AllyWave, false);
    gf_rm_MercInit();
}

// ---- Enemy rules (CLAUDE.md 7-1) ----
void gf_rm_EnemyDifficultyBuff () {
    int lv_buff = libNtve_gf_DifficultyValueInt(%(buff)s);
%(buff_lines)s
}

void gf_rm_EnemyMinUpgrades () {
%(enemy_upgrades)s
}

// Extra Dominion marines next to every Nth marine inside the Dominion Base region (trial value)
void gf_rm_SpawnBaseReinforce () {
    unitgroup lv_g = UnitGroup("Marine", gv_pLAYER_02_DOMINION, RegionFromId(%(base_region)s), UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0);
    int lv_i = UnitGroupCount(lv_g, c_unitCountAll);
    unit lv_u;
    for ( ; lv_i > 0 ; lv_i -= 1) {
        if (ModI(lv_i, %(base_every)s) == 0) {
            lv_u = UnitGroupUnit(lv_g, lv_i);
            UnitCreate(1, "Marine", 0, gv_pLAYER_02_DOMINION, UnitGetPosition(lv_u), UnitGetFacing(lv_u));
        }
    }
}

void gf_rm_Start () {
    gf_rm_ConvertMercs();
    gf_rm_SpawnWave(true);
    TriggerEnable(gt_rm_AllyAI, true);
    TriggerEnable(gt_rm_AllyPing, true);
    TriggerEnable(gt_rm_AllyWave, true);
    gf_rm_SpawnBaseReinforce();
    gf_rm_EnemyMinUpgrades();
    gf_rm_EnemyDifficultyBuff();
}

"""

ANCHOR_BLOCK = 'void InitGlobals () {'
ANCHOR_INIT = 'PlayerSetAlliance(gv_pLAYER_03_COLONISTS, c_allianceIdPushable, gv_pLAYER_01_USER, true);'
ANCHOR_START = 'TriggerExecute(gt_ObjectiveDestroytheDominionBaseDiscoverQ, true, true);'
ANCHOR_RESCUE = 'UnitIssueOrder(UnitFromId(600), OrderTargetingPoint(AbilityCommand("move", 0), PointFromId(736)), c_orderQueueReplace);'


def patch_galaxy(g):
    if 'const int gv_rm_PURIFIER = 8;' in g:
        sys.exit('동맹 코드가 이미 있음: 원본에서 빌드해야 함')
    nl = '\r\n' if '\r\n' in g else '\n'
    changed = 0
    lines = g.split(nl)
    for key, unit, count in P1_LINE_FIXES:
        hits = [i for i, l in enumerate(lines) if key in l]
        if len(hits) != count:
            sys.exit(f'용병 교체 줄 수가 다름 ({len(hits)} != {count}): {key}')
        for i in hits:
            lines[i] = lines[i].replace(f'"{unit}"', f'"{MERC[unit]}"', 1)
            changed += 1
    g = nl.join(lines)

    def spawn(wave):
        out = []
        for unit, n, player in wave:
            out.append(f'        UnitCreate({n}, "{unit}", 0, {player}, gf_rm_Home({player}), 270.0);')
        return '\n'.join(out)

    merc_cases = '\n'.join(
        f'    {"if" if i == 0 else "else if"} (lv_t == "{a}") {{\n'
        f'        libNtve_gf_ReplaceUnit(lp_u, "{b}", libNtve_ge_ReplaceUnitOptions_OldUnitsRelative);\n'
        f'    }}' for i, (a, b) in enumerate(MERC.items()))
    merc_types = ' || '.join(f'UnitGetType(lv_u) == "{a}"' for a in MERC)
    merc_link = '\n'.join(
        f'    TechTreeUnitAllow(gv_pLAYER_01_USER, "{b}", true);\n'
        f'    CatalogLinkReplace(gv_pLAYER_01_USER, c_gameCatalogUnit, "{a}", "{b}");' for a, b in MERC.items())
    homes = '\n'.join(f'    if (lp_p == {p}) {{\n        return Point({x}, {y});\n    }}' for p, (x, y) in ALLY_HOME.items())
    colors = '\n'.join(f'    PlayerSetColorIndex({p}, {c}, true);' for p, c in m1.ALLY_COLORS.items())
    upgrades = '\n'.join(f'    TechTreeUpgradeAddLevel({p}, "{u}", {lv});' for p, u, lv in m1.ALLY_UPGRADES)
    buff_lines = '\n'.join(
        f'    PlayerModifyPropertyInt({p}, c_playerPropDamageDealtPercent, c_playerPropOperSetTo, 100 + lv_buff);\n'
        f'    PlayerModifyPropertyInt({p}, c_playerPropDamageTakenPercent, c_playerPropOperSetTo, 10000 / (100 + lv_buff));'
        for p in ENEMY_PLAYERS)
    enemy_upgrades = '\n'.join(
        f'    if (TechTreeUpgradeCount({p}, "{u}", c_techCountCompleteOnly) < {lv}) {{\n'
        f'        TechTreeUpgradeAddLevel({p}, "{u}", {lv} - TechTreeUpgradeCount({p}, "{u}", c_techCountCompleteOnly));\n'
        f'    }}' for p in ENEMY_PLAYERS for u, lv in m1.ENEMY_MIN_UPGRADES)
    block = GALAXY_BLOCK % {
        'merc_cases': merc_cases, 'merc_types': merc_types, 'merc_link': merc_link, 'homes': homes,
        'attack_delay': ATTACK_DELAY, 'target_unit': ATTACK_TARGET_UNIT,
        'target_point': ', '.join(str(v) for v in ATTACK_TARGET_POINT),
        'ping_hold': m1.PING_HOLD_SECONDS, 'first_wave': spawn(FIRST_WAVE), 'next_wave': spawn(NEXT_WAVE),
        'wave_max': WAVE_MAX, 'wave_interval': WAVE_INTERVAL, 'colors': colors, 'upgrades': upgrades,
        'buff': ', '.join(str(b) for b in m1.ENEMY_BUFF_PERCENT), 'buff_lines': buff_lines,
        'enemy_upgrades': enemy_upgrades, 'base_region': BASE_REGION_ID, 'base_every': BASE_EVERY_NTH,
    }
    block = block.replace('\n', nl)
    for a in (ANCHOR_BLOCK, ANCHOR_INIT, ANCHOR_START, ANCHOR_RESCUE):
        if g.count(a) != 1:
            sys.exit(f'스크립트 기준 문자열이 1개가 아님: {a}')
    g = g.replace(ANCHOR_BLOCK, block.lstrip(nl) + ANCHOR_BLOCK)
    g = g.replace(ANCHOR_INIT, ANCHOR_INIT + nl + '    gf_rm_AllyInit();')
    g = g.replace(ANCHOR_START, 'gf_rm_Start();' + nl + '    ' + ANCHOR_START)
    g = g.replace(ANCHOR_RESCUE, 'gf_rm_ConvertMercs();' + nl + '    ' + ANCHOR_RESCUE)
    return g, changed


def patch_objects(o):
    """배치된 플레이어 1 해병을 전쟁광으로 (SCV는 그대로)."""
    n = 0

    def fix(m):
        nonlocal n
        n += 1
        return m[0].replace('UnitType="Marine"', 'UnitType="WarPig"')
    o = re.sub(r'<ObjectUnit [^>]*UnitType="Marine" Player="1"', fix, o)
    return o, n


def main():
    if not os.path.isdir(SRC):
        sys.exit(f'원본 맵 없음: {SRC}')
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)
    expanded = new_terrain.build_east(OUT, EXPAND_SEAM, EXPAND_WIDTH, east_layout, EXPAND_CAMERA_RIGHT, EAST_CARVE,
                                       relief=east_relief, texnoise=east_texnoise, scatter=east_scatter,
                                       tidy=EAST_TIDY) if EXPAND_WIDTH else None

    p = os.path.join(OUT, 'mapscript.galaxy')
    g = open(p, encoding='utf-8', newline='').read()
    g, changed = patch_galaxy(g)
    open(p, 'w', encoding='utf-8', newline='').write(g)

    p = os.path.join(OUT, 'objects')
    o = open(p, encoding='utf-8', newline='').read()
    o, placed = patch_objects(o)
    open(p, 'w', encoding='utf-8', newline='').write(o)

    for fn, fix in (('mapinfo', m1.patch_mapinfo), ('documentheader', m1.patch_header)):
        p = os.path.join(OUT, fn)
        b = open(p, 'rb').read()
        open(p, 'wb').write(fix(b))
    p = os.path.join(OUT, 'kokr.sc2data', 'localizeddata', 'gamestrings.txt')
    t = open(p, encoding='utf-8', newline='').read()
    open(p, 'w', encoding='utf-8', newline='').write(m1.patch_strings(t))

    units = sorted({u for u, *_ in FIRST_WAVE + NEXT_WAVE})
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'port_units.py'), OUT] + units,
                   check=True, stdout=subprocess.DEVNULL)
    m1.write_other_locales(OUT)

    print(OUT)
    if expanded:
        print(f"  - 지형 확장: {expanded['old_w']} → {expanded['new_w']} x {expanded['h']}, 카메라 {expanded['camera']}, 길 뚫은 칸 {expanded['carved']}, 지운 물체 {expanded['removed']}, 새 장식물 {expanded['doodads']}")
    print(f'  - 스크립트 용병 교체 {changed}곳, 배치 해병 {placed}기 → WarPig')
    print(f'  - 병영 생산 링크 치환 (플레이어 1): {MERC}')
    for p, (x, y) in ALLY_HOME.items():
        print(f'  - 동맹 소환 지점 {p}: ({x}, {y})')
    print(f'  - 첫 소환: {FIRST_WAVE}')
    print(f'  - 추가 소환 {WAVE_INTERVAL}초마다 최대 {WAVE_MAX}회: {NEXT_WAVE}')
    print(f'  - C안 공격 시작: {ATTACK_DELAY}초 (시험값)')


if __name__ == '__main__':
    main()
