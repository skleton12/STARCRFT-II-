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
EAST_KEEP_CLEAR = 12.0     # 동맹 진영 둘레는 평지로 비워 둠 (반지름). 회관·자원 자리 (2026-10-15 9 → 12)
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
WAVE_MAX = 1           # 첫 소환만 (2026-10-15: 동맹이 직접 건설·생산하므로 무료 추가 소환 중단, 시험값. 이전 6)
ATTACK_DELAY = 300.0   # C안: 미션 시작 후 이 시간이 지나면 자치령 기지 공격 (게임 초, 시험값)
ATTACK_TARGET_UNIT = 48          # 자치령 사령부 배치 ID (43.5,101.5)
ATTACK_TARGET_POINT = (45.0, 94.0)  # 사령부가 없으면 이 지점

# 동맹 경제 (사용자 지시 2026-10-15: 동맹 AI가 건설·생산, 엔진 AI + 스크립트 혼합, 기본 지상 병력 위주). 수치는 시험값
# 엔진 캠페인 AI가 stock(유지할 수)에 맞춰 채취·건설·생산하고, 병력 지휘는 gt_rm_AllyAI가 맡는다
ALLY_ECON = {
    'gv_rm_PURIFIER': dict(
        hall='Nexus', worker='Probe', start_workers=8, start_extra=[], farm='Pylon', workers=16,
        buildings=[('Assimilator', 2), ('Gateway', 3), ('CyberneticsCore', 1)],
        army=[('Zealot', 'ZealotPurifier', 8), ('Stalker', 'StalkerPurifier', 6)],  # 파수병, 선동자(Instigator)
    ),
    'gv_rm_PRIMAL': dict(
        hall='Hatchery', worker='Drone', start_workers=8, start_extra=[('Overlord', 1)], farm='Overlord', workers=16,
        buildings=[('Extractor', 1), ('SpawningPool', 1), ('RoachWarren', 1)],
        army=[('Zergling', 'PrimalZergling', 12), ('Roach', 'PrimalRoach', 8)],  # 원시 저글링, 원시 바퀴
    ),
}
# 이식 시 같이 넣을 항목: 원시 바퀴가 협동전 데하카 바퀴 무기를 쓰는데 그 효과가 공용 제한에 걸려 빠짐 (끊긴 참조 방지)
PORT_EXTRA_SEEDS = ['DehakaRoachDamage', 'DehakaRoachLM', 'DehakaRoachLevel2Damage', 'DehakaRoachLevel2LM',
                    'DehakaRoachLevel3Damage', 'DehakaRoachLevel3LM',
                    # 원시 바퀴 공격·사망 연출의 물리 효과, 먹기 능력 효과 (군단 데이터)
                    'RoachAttackDeathForce', 'RoachMeleeAttackForce02', 'RoachMeleeAttackForce03',
                    'RoachMeleeAttackRightBladeForce', 'MediumTastyCorpseSet', 'MurvarRangedWeapon']
ALLY_START_MINERALS = 400   # 시작 광물 (시험값)
ALLY_MINERAL_FIELDS = 8     # 진영마다 광물 덩이 (시험값)
ALLY_GEYSERS = 2            # 진영마다 가스 (시험값)
ALLY_EXIT_POINT = (100.0, 65.0)  # 자원은 이 점의 반대쪽(진영 뒤쪽)에, 집결·소환점은 이쪽(앞쪽)에 둔다

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
    // Army only: no workers, air (overlords), structures, larva or eggs
    unitfilter lv_f = UnitFilter(0, 0, (1 << c_targetFilterMissile) | (1 << c_targetFilterStructure) | (1 << c_targetFilterAir) | (1 << c_targetFilterWorker), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)));
    unitgroup lv_g = UnitGroup(null, gv_rm_PURIFIER, RegionEntireMap(), lv_f, 0);
    UnitGroupAddUnitGroup(lv_g, UnitGroup(null, gv_rm_PRIMAL, RegionEntireMap(), lv_f, 0));
    UnitGroupRemoveUnitGroup(lv_g, UnitGroup("Larva", c_playerAny, RegionEntireMap(), UnitFilter(0, 0, 0, 0), 0));
    UnitGroupRemoveUnitGroup(lv_g, UnitGroup("Egg", c_playerAny, RegionEntireMap(), UnitFilter(0, 0, 0, 0), 0));
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
    bool lv_expired;
    if (!runActions) {
        return true;
    }
    if (gv_gameOver || gv_inCinematic) {
        return true;
    }
    // Ping expiry: switch every ally to its default target once (GPT review M02-03), not only idle ones
    lv_expired = false;
    if (gv_rm_pingTarget != null && GameGetMissionTime() - gv_rm_pingTime >= %(ping_hold)s) {
        gv_rm_pingTarget = null;
        lv_expired = true;
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
        if (lv_target != null && (lv_expired || (UnitOrderCount(lv_u) == 0 && DistanceBetweenPoints(UnitGetPosition(lv_u), lv_target) > lv_radius))) {
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
    gf_rm_AllyBases();
    gt_rm_AllyEcon = TriggerCreate("gt_rm_AllyEcon_Func");
    TriggerAddEventTimePeriodic(gt_rm_AllyEcon, 5.0, c_timeGame);
    TriggerExecute(gt_rm_AllyEcon, false, false);
    gf_rm_SpawnWave(true);
    gf_rm_AnnounceAllies();
    gf_rm_ResUIInit();
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


def plan_bases(map_dir):
    """빌드된 지형(절벽 단계)에서 동맹 회관·광물·가스·집결점 위치를 정한다.

    쓰는 칸은 모두 1단계이고 주변 1칸도 1단계(절벽 가장자리 아님)여야 한다.
    자원은 ALLY_EXIT_POINT 반대쪽(진영 뒤), 집결점은 앞쪽. 광물 2x1, 가스 3x3, 회관 5x5.
    """
    import math, struct
    import numpy as np
    w, h = struct.unpack('<II', open(os.path.join(map_dir, 'mapinfo'), 'rb').read()[0x10:0x18])
    cl = np.frombuffer(open(os.path.join(map_dir, 't3syncclifflevel'), 'rb').read()[32:32 + w * h * 2], '<u2').reshape(h, w)
    good = np.zeros_like(cl, dtype=bool)
    good[1:-1, 1:-1] = True
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            good[1:-1, 1:-1] &= cl[1 + dy:h - 1 + dy, 1 + dx:w - 1 + dx] == 64
    ok = lambda cells: all(0 <= y < h and 0 <= x < w and good[y, x] for x, y in cells)
    plans = {}
    for p, (cx, cy) in ALLY_HOME.items():
        tx, ty = math.floor(cx) + 0.5, math.floor(cy) + 0.5
        town = {(int(tx) + i, int(ty) + j) for i in range(-2, 3) for j in range(-2, 3)}
        assert ok(town), (p, '회관 자리가 평지가 아님')
        ex, ey = ALLY_EXIT_POINT
        back = math.atan2(ty - ey, tx - ex)
        used = {(x + i, y + j) for x, y in town for i in (-1, 0, 1) for j in (-1, 0, 1)}

        def angdiff(a):
            return abs((a - back + math.pi) % (2 * math.pi) - math.pi)
        # 광물: 회관 뒤쪽에 반지름 약 7의 호로 늘어놓음 (각도 간격 약 15도)
        minerals = []
        n = ALLY_MINERAL_FIELDS
        for k in range(n):
            a0 = back + (k - (n - 1) / 2) * math.radians(15)
            for r in (7.0, 6.5, 7.5, 8.0, 6.0):
                for da in (0.0, 0.08, -0.08):
                    mx = round(tx + r * math.cos(a0 + da))
                    my = math.floor(ty + r * math.sin(a0 + da)) + 0.5
                    cells = {(mx - 1, int(my)), (mx, int(my))}
                    if ok(cells) and not (cells & used):
                        minerals.append((mx, my))
                        used |= cells
                        break
                else:
                    continue
                break
        geysers = []
        cands = []
        for x in range(int(tx) - 11, int(tx) + 12):
            for y in range(int(ty) - 11, int(ty) + 12):
                gx, gy = x + 0.5, y + 0.5
                d = math.hypot(gx - tx, gy - ty)
                a = angdiff(math.atan2(gy - ty, gx - tx))
                if 7.0 <= d <= 9.0 and math.radians(60) <= a <= math.radians(120):
                    cands.append((abs(a - math.radians(90)), d, gx, gy, {(x + i, y + j) for i in (-1, 0, 1) for j in (-1, 0, 1)}))
        for _, _, gx, gy, cells in sorted(cands):
            if len(geysers) >= ALLY_GEYSERS:
                break
            margin = {(a + i, b + j) for a, b in cells for i in (-1, 0, 1) for j in (-1, 0, 1)}
            if ok(cells) and not (margin & used):
                geysers.append((gx, gy))
                used |= cells
        rally = None
        for r in (8.5, 7.5, 9.5, 10.5, 6.5):
            for da in (0, 0.3, -0.3, 0.6, -0.6):
                rx = tx - r * math.cos(back + da)
                ry = ty - r * math.sin(back + da)
                c = {(int(rx) + i, int(ry) + j) for i in (-1, 0, 1) for j in (-1, 0, 1)}
                if ok(c) and not (c & used):
                    rally = (round(rx, 1), round(ry, 1))
                    break
            if rally:
                break
        assert len(minerals) == ALLY_MINERAL_FIELDS and len(geysers) == ALLY_GEYSERS and rally, (p, len(minerals), len(geysers), rally)
        plans[p] = dict(town=(tx, ty), minerals=minerals, geysers=geysers, rally=rally)
    return plans


ECON_GALAXY = """
// ---- Ally economy (2026-10-15): engine campaign AI harvests/builds/trains from stock; gt_rm_AllyAI commands the army ----
trigger gt_rm_AllyEcon;
trigger gt_rm_ResUI;
int gv_rm_resDlg;
int gv_rm_resLbl;

void gf_rm_AIStartAlly (int lp_p, point lp_town) {
    AIStart(lp_p, true, DifficultyAPM(c_campAdvanced));
    AIDeclareTown(lp_p, c_townOne, lp_town);
    AISetMainTown(lp_p, c_townOne);
    AIInitCampaignTowns(lp_p);
    AIInitCampaignHarvest(lp_p);
    AIHarvestRate(lp_p, 1);
    AISetNumScouts(lp_p, 0);
}

void gf_rm_AllyBases () {
@BASES@
}

bool gt_rm_AllyEcon_Func (bool testConds, bool runActions) {
    if (!runActions) {
        return true;
    }
    if (gv_gameOver) {
        return true;
    }
@STOCK@
    return true;
}

// Ally resource panel: real minerals/gas of players 8 and 9
void gf_rm_ResUIUpdate () {
    text lv_t;
    lv_t = StringExternal("rm/AllyRes/Purifier") + StringExternal("rm/AllyRes/Minerals") + IntToText(PlayerGetPropertyInt(gv_rm_PURIFIER, c_playerPropMinerals));
    lv_t = lv_t + StringExternal("rm/AllyRes/Gas") + IntToText(PlayerGetPropertyInt(gv_rm_PURIFIER, c_playerPropVespene));
    lv_t = lv_t + StringToText("<n/>") + StringExternal("rm/AllyRes/Primal") + StringExternal("rm/AllyRes/Minerals") + IntToText(PlayerGetPropertyInt(gv_rm_PRIMAL, c_playerPropMinerals));
    lv_t = lv_t + StringExternal("rm/AllyRes/Gas") + IntToText(PlayerGetPropertyInt(gv_rm_PRIMAL, c_playerPropVespene));
    DialogControlSetPropertyAsText(gv_rm_resLbl, c_triggerControlPropertyText, PlayerGroupAll(), lv_t);
}

bool gt_rm_ResUI_Func (bool testConds, bool runActions) {
    if (!runActions) {
        return true;
    }
    gf_rm_ResUIUpdate();
    return true;
}

void gf_rm_ResUIInit () {
    gv_rm_resDlg = DialogCreate(330, 80, c_anchorTopLeft, 20, 180, false);
    gv_rm_resLbl = DialogControlCreate(gv_rm_resDlg, c_triggerControlTypeLabel);
    DialogControlSetSize(gv_rm_resLbl, PlayerGroupAll(), 310, 60);
    DialogControlSetPosition(gv_rm_resLbl, PlayerGroupAll(), c_anchorTopLeft, 12, 10);
    DialogSetVisible(gv_rm_resDlg, PlayerGroupAll(), true);
    gf_rm_ResUIUpdate();
    gt_rm_ResUI = TriggerCreate("gt_rm_ResUI_Func");
    TriggerAddEventTimePeriodic(gt_rm_ResUI, 1.0, c_timeGame);
}

// Adjutant announces the reinforcements (subtitle only; no matching voice line chosen)
void gf_rm_AnnounceAllies () {
    TransmissionSend(PlayerGroupAll(), TransmissionSourceFromModel("AdjutantPortrait"), PortraitGetGame(), "Talk", null, StringExternal("rm/Adjutant/Name"), StringExternal("rm/Adjutant/Arrive"), 6.0, c_transmissionDurationSet, false);
}

"""


def econ_galaxy(plans):
    bases, stock = [], []
    for p, e in ALLY_ECON.items():
        pl = plans[p]
        tx, ty = pl['town']
        for mx, my in pl['minerals']:
            bases.append(f'    UnitCreate(1, "MineralField", c_unitCreateIgnorePlacement, 0, Point({mx}, {my}), 0.0);')
        for gx, gy in pl['geysers']:
            bases.append(f'    UnitCreate(1, "VespeneGeyser", c_unitCreateIgnorePlacement, 0, Point({gx}, {gy}), 0.0);')
        bases.append(f'    UnitCreate(1, "{e["hall"]}", c_unitCreateIgnorePlacement, {p}, Point({tx}, {ty}), 270.0);')
        rx, ry = pl['rally']
        bases.append(f'    UnitCreate({e["start_workers"]}, "{e["worker"]}", 0, {p}, Point({(tx + rx) / 2:.1f}, {(ty + ry) / 2:.1f}), 270.0);')
        for u, n in e['start_extra']:
            bases.append(f'    UnitCreate({n}, "{u}", 0, {p}, Point({tx}, {ty}), 270.0);')
        bases.append(f'    PlayerModifyPropertyInt({p}, c_playerPropMinerals, c_playerPropOperSetTo, {ALLY_START_MINERALS});')
        for base, real, _ in e['army']:
            bases.append(f'    TechTreeUnitAllow({p}, "{real}", true);')
            bases.append(f'    CatalogLinkReplace({p}, c_gameCatalogUnit, "{base}", "{real}");')
        bases.append(f'    gf_rm_AIStartAlly({p}, Point({tx}, {ty}));')
        stock.append(f'    AIClearStock({p});')
        stock.append(f'    AISetStockUnitNext({p}, {e["workers"]}, "{e["worker"]}", false);')
        stock.append(f'    AISetStock({p}, 1, "{e["hall"]}");')
        stock.append(f'    AISetStockFarms({p}, "{e["farm"]}", true);')
        for b, n in e['buildings']:
            stock.append(f'    AISetStock({p}, {n}, "{b}");')
        for base, real, n in e['army']:  # AI counts the base type; replaced units are counted here instead
            stock.append(f'    AISetStock({p}, MaxI(0, {n} - TechTreeUnitCount({p}, "{real}", c_techCountCompleteOnly)), "{base}");')
        stock.append(f'    AIEnableStock({p});')
    return ECON_GALAXY.replace('@BASES@', '\n'.join(bases)).replace('@STOCK@', '\n'.join(stock))


ECON_STRINGS = {  # 사용자 요구 문장. 부관 대사는 GPT 초안 (docs/missions/02_ally_resources_intro.md)
    'rm/AllyRes/Purifier': ('정화자', 'Purifiers'),
    'rm/AllyRes/Primal': ('원시 저그', 'Primal Zerg'),
    'rm/AllyRes/Minerals': ('  광물 ', '  Minerals '),
    'rm/AllyRes/Gas': ('  가스 ', '  Gas '),
    'rm/Adjutant/Name': ('부관', 'Adjutant'),
    'rm/Adjutant/Arrive': ('사령관님, 저그와 프로토스 지원군이 도착했습니다.', 'Commander, Zerg and Protoss reinforcements have arrived.'),
}


def patch_galaxy(g, plans=None):
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
    rallies = {p: plans[p]['rally'] for p in ALLY_HOME} if plans else ALLY_HOME
    homes = '\n'.join(f'    if (lp_p == {p}) {{\n        return Point({x}, {y});\n    }}' for p, (x, y) in rallies.items())
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
    if plans:
        block = block.replace('void gf_rm_Start () {', econ_galaxy(plans) + 'void gf_rm_Start () {', 1)
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
                                       relief=east_relief, scatter=None,  # 2026-10-15 사용자: 새 장식물(초록 점) 전부 빼기
                                      
                                       tidy=EAST_TIDY) if EXPAND_WIDTH else None

    p = os.path.join(OUT, 'mapscript.galaxy')
    g = open(p, encoding='utf-8', newline='').read()
    plans = plan_bases(OUT)
    g, changed = patch_galaxy(g, plans)
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
    t = m1.patch_strings(t)
    nl = '\r\n' if '\r\n' in t else '\n'
    t += ''.join(f'{k}={ko} /// {en}{nl}' for k, (ko, en) in ECON_STRINGS.items())
    open(p, 'w', encoding='utf-8', newline='').write(t)

    # 소환 유닛 + 용병 대상 중 자날 기본 데이터에 없는 것 (GPT 검토 M02-02: MercMedic은 군단/공허 캠페인 정의)
    units = sorted({u for u, *_ in FIRST_WAVE + NEXT_WAVE} | {'MercMedic'}
                   | {real for e in ALLY_ECON.values() for _, real, _ in e['army']})
    subprocess.run([sys.executable, os.path.join(ROOT, 'tools', 'port_units.py'), '--liberty-base', OUT] + units + PORT_EXTRA_SEEDS,
                   check=True, stdout=subprocess.DEVNULL)
    # 따라오지 않은 협동전 응급 의료선(EmergencyMedivac)을 가리키는 행위자 이벤트 줄 제거
    p = os.path.join(OUT, 'base.sc2data', 'gamedata', 'actordata.xml')
    t = open(p, encoding='utf-8', newline='').read()
    t = re.sub(r'[ \t]*<On [^>]*EmergencyMedivac[^>]*/>\r?\n', '', t)
    open(p, 'w', encoding='utf-8', newline='').write(t)
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
    for p, pl in plans.items():
        print(f"  - 동맹 기지 {p}: 회관 {pl['town']}, 광물 {len(pl['minerals'])}, 가스 {pl['geysers']}, 집결 {pl['rally']}")


if __name__ == '__main__':
    main()
