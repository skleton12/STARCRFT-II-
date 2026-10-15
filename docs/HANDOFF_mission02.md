# 2번 미션 인수인계 (클로드 → 다음 작업자, 2026-10-15)

현재 버전 **0.2.7** (아래 3장 설계를 2026-10-15 구현함 — 4장 1번 완료) (브랜치 `claude/lucid-franklin-ed0eko`). 빌드: `python3 tools/build_ccm.py`.
2번 미션 패치 도구: `tools/patch_mission02.py` (원본 `source/.../traynor02.sc2map` → `build/TRaynor02.SC2Map`).
규칙은 `CLAUDE.md`, 결정 기록은 `docs/DECISIONS.md`, GPT 검토는 `docs/testing/2026-10-15_mission02_review.md`.
새 컴퓨터 준비는 `docs/SETUP.md` (원본 데이터는 `source_pack.zip`, 공개 저장소에 올리지 않음).

## 1. 지금 맵 상태 (0.2.6)

| 항목 | 값 | 위치 |
|---|---|---|
| 크기 | 184x136 (원본 136, x=104 동쪽은 새 지형) | `EXPAND_*`, `east_layout`, `tools/new_terrain.py` |
| 동맹 진영 | 원시 저그(9) Base 1 (150,26), 정화자(8) Base 2 (122,95) | `ALLY_HOME` |
| 서쪽 통로 | 원본 언덕 x96~103, y77~83을 1단계로 뚫음 | `EAST_CARVE` |
| 동맹 병력 | 첫 소환 칼달리스1+파수병4 / 라바사우르스3, 이후 90초마다 무료 소환(최대 6회) | `FIRST_WAVE`, `NEXT_WAVE`, `WAVE_*` |
| 동맹 행동 | 300초까지 진영 지킴 → 자치령 사령부(ID 48) 공격. 핑 30초, 만료 시 전원 기본 목표로 | `ATTACK_*`, galaxy `gt_rm_AllyAI_Func` |
| 용병 | 레이너 해병→WarPig, 의무관→MercMedic(이식함), 구출 반군도 변환. SCV 예외 | `MERC`, `gf_rm_ToMerc` |
| 적 | 난이도 % (0/5/15/35), 보병 공방 최소 1, 본진 해병 2명마다 +1 | `ENEMY_*`, `BASE_*` |

## 2. 사용자 최신 지시 (구현 안 됨)

1. **동맹 AI가 건물 건설과 병력 생산을 해야 한다** ("지원 병력 느낌"). 방식: **엔진 AI + 스크립트 혼합** (사용자 "둘다 섞어"). 생산 유닛은 **기본 지상 병력 위주**.
2. 동맹 진영에 자원 배치 + 각 동맹 보유 자원 표시 (`docs/missions/02_ally_resources_intro.md`).
3. 미션 시작 부관 초상화 + "저그와 프로토스 지원군이 도착했습니다" 안내.
4. 자치령 일부 강화, 반란군이 구출 전에 전멸하지 않게 (수치·위치 미정, 사용자 질문 대기).
5. 동쪽 새 땅은 사용자가 편집기에서 직접 다듬을 수 있음 (`build/TRaynor02_Edit.SC2Map` 전달함). 돌려받으면 그 지형을 원본으로 쓰는 연결이 필요.
6. 미정 질문: 두 동맹 300초 동시 출발 vs 집결 후 공격.

## 3. 1번 지시의 설계 (클로드가 조사·확정한 방식, 코드 미작성)

협동전 AI(`starcoop/.../libcomi.galaxy`의 `libCOMI_gf_CM_AIThinkCoop`)와 같은 방식:
**캠페인 AI를 켜고 5초마다 stock(유지할 건물·유닛 수)을 다시 넣으면 엔진이 일꾼 채취·건설·생산을 한다. 캠페인 AI는 공격 웨이브를 시키지 않으면 공격하지 않으므로 병력 지휘는 기존 스크립트(`gt_rm_AllyAI`)가 그대로 맡는다.**

### 확인한 API (core `TriggerLibs`, 맵 스크립트에서 호출 가능 — natives가 `TriggerLibs/AI` 포함)

- 시작: `AICampaignStart(p)`는 `PlayerStartLocation(p)`를 쓰는데 8·9번은 시작 위치가 없음 → 같은 내용을 직접 호출:
  `AIStart(p, true, DifficultyAPM(c_campAdvanced)); AIDeclareTown(p, c_townOne, 진영점); AISetMainTown(p, c_townOne); AIInitCampaignTowns(p); AIInitCampaignHarvest(p); AIHarvestRate(p, 1); AISetNumScouts(p, 0);`
- 5초마다: `AIClearStock(p); AISetStockUnitNext(p, 16, "Probe"|"Drone", false); AISetStock(p, n, "건물/유닛"); AISetStockFarms(p, "Pylon"|"Overlord", true); AIEnableStock(p);`
- 기타: `MaxI`, `TechTreeUnitCount(p, type, c_techCountCompleteOnly)`, `PlayerModifyPropertyInt(p, c_playerPropMinerals/Vespene, ...)`, `CatalogLinkReplace(p, c_gameCatalogUnit, 원래, 바꿀것)`.
- 대화창: `DialogCreate(w, h, c_anchorTopLeft, x, y, modal)`, `DialogControlCreate(dlg, c_triggerControlTypeLabel)`, `DialogControlSetSize/Position`, `DialogControlSetPropertyAsText(ctl, c_triggerControlPropertyText, PlayerGroupAll(), text)`, `DialogSetVisible`. 텍스트는 `StringExternal(...) + IntToText(...)`로 이어 붙일 수 있음.
- 부관: 모델 `AdjutantPortrait` (Liberty.SC2Mod 존재). `TransmissionSend(PlayerGroupAll(), TransmissionSourceFromModel("AdjutantPortrait"), PortraitGetGame(), "Talk", null, 화자text, 자막text, 5.0, c_transmissionDurationSet, false)` (nativelib 정의). 맞는 음성은 찾지 않음(자막만).
- 필터 상수: `c_targetFilterWorker = 18`, `c_targetFilterAir = 5`.

### 유닛 (기본 지상 위주, 시험값)

| 동맹 | 일반 유닛(AI가 뽑음) | 실제로 나올 유닛 (`CatalogLinkReplace`) | 한글 이름 |
|---|---|---|---|
| 정화자 8 | Zealot | ZealotPurifier | 파수병 |
| 정화자 8 | Stalker | StalkerPurifier | 선동자 (Instigator) |
| 원시 저그 9 | Zergling | PrimalZergling | 원시 저글링 |
| 원시 저그 9 | Roach | PrimalRoach | 원시 바퀴 |

- 바꿀 유닛은 `port_units.py`로 이식해야 함 (군단 캠페인·협동전 층 정의). 이식 후 `tools/check_links.py` 결과를 1번 미션과 비교 (`diff` 해서 새 끊긴 참조가 없어야 함).
- AI는 "Zealot" 수를 세므로 바뀐 유닛이 계속 0으로 보임 → stock을 `MaxI(0, 목표 - TechTreeUnitCount(p, "ZealotPurifier", complete))`로 넣어 과생산 방지.
- 시작 지급(시험값): 정화자 Nexus1+Probe8, 원시 저그 Hatchery1+Drone8+Overlord1, 광물 400. stock: 정화자 Assimilator2·Gateway3·CyberneticsCore1, 파수병8·선동자6 / 원시 저그 Extractor1·SpawningPool1·RoachWarren1, 저글링12·바퀴8. 일꾼 16.
- 자원: 진영마다 MineralField 8, VespeneGeyser 2 (중립 0번). 위치는 빌드 시 절벽 격자(`t3syncclifflevel`)를 읽어 1단계·절벽에서 1칸 떨어진 곳에 자동 배치하는 것을 계획(광물 고리 6~7.5, 가스 7~8.5, 출구 반대쪽). 진영 둘레 평지 반지름 `EAST_KEEP_CLEAR`를 12로 올려야 함.
- 소환 지점(`gf_rm_Home`)은 회관과 겹치므로 회관 앞(출구 쪽) 집결점으로 분리할 것.
- `gf_rm_AllyArmy`의 필터에서 일꾼·공중·구조물 제외, 애벌레·알(Larva/Egg)도 제외해야 함 (지금은 구조물·미사일만 제외).
- 무료 웨이브는 첫 소환만 남기고(`WAVE_MAX = 1`) 생산으로 대체하는 안. 사용자 확정은 아님 — 확인하고 바꿀 것.

## 4. 남은 일 (우선순위)

1. ~~위 3장 구현~~ **완료 (0.2.7)**: `ALLY_ECON`, `plan_bases`, `econ_galaxy`, `ECON_STRINGS`. 남은 끊긴 참조는 `PortraitPurifierStalker`(초상화 조명, lightdata 미이식) 하나. 위 3장 구현 → `patch_mission02.py`의 `GALAXY_BLOCK`과 `gf_rm_Start`에 추가, 문자열은 `kokr` 게임 문자열에 `한국어 /// English`, 다른 언어는 `write_other_locales`로 영어.
2. 버전 0.2.7, `python3 tools/build_ccm.py`, `maps/TRaynor02.SC2Map` 갱신(단일 파일 묶기는 `tools/pack_sc2map.py` + StormLib, `docs/SETUP.md`).
3. 사용자 질문 대기 항목(2장 4·6, 자원 수량) 답 받으면 반영.
4. 게임 시험 항목: GPT 검토서 M02-04~06, 동맹 AI가 실제로 채취·건설·생산하는지, 바뀐 유닛이 나오는지, 자원 표시값이 실제 잔고와 같은지.

## 5. 주의 (실수했던 것)

- `t3texturemasks`는 텍스처 8장 x (칸x8 픽셀), 64x64 타일, 4비트(상위 니블 먼저). `new_terrain.load_masks/save_masks`만 쓸 것. 0.2.1~0.2.4는 이걸 잘못 다뤄 텍스처가 깨졌을 수 있음.
- 맵 크기를 바꾸면 `t3terrain.xml`의 `blockTextureSetList`, `cliffCellList`도 다시 만들어야 함 (`new_terrain._terrain_lists`).
- `tools/expand_map.py`(거울 복사)는 사용자 지시로 안 씀. 지형 목록 갱신도 안 함 — 쓰지 말 것.
- 맵을 편집기로 저장하면 동맹 코드가 사라짐. 편집기 작업은 `make_edit_map02.py`가 만든 편집용 맵에서만.
- 게임·편집기·Galaxy 컴파일 검증은 지금까지 한 번도 실행 못 함 (환경에 게임 없음).
