# 1번 미션: 해방의 날 (Liberation Day)

원본 맵: `liberty.sc2campaign/base.sc2maps/maps/campaign/traynor01.sc2map` (마 사라)
종속성: `Mods/Liberty.SC2Mod`, `Campaigns/Liberty.SC2Campaign`, `Campaigns/LibertyStory.SC2Campaign`

## 원본 분석 (맵 파일 확인)

### 목표 (`mapscript.galaxy`, 한국어 문자열)

| 목표 | 내용 |
|---|---|
| 주 목표 | 병참 본부 파괴 (백워터 기지의 `LogisticsHeadquarters`) |
| 패배 조건 | 레이너(`Raynor01`) 사망 |
| 부가 | 자치령 선전물(홀로그램 광고판 `MengskHologramBillboard` 6개) 파괴 |

### 플레이어 슬롯

| 변수 | 슬롯 | 역할 |
|---|---|---|
| `gv_p1_USER` | 1 | 레이너 (플레이어) |
| `gv_p2_DOMINION_RED` | 2 | 자치령 (적). 핸디캡 50 설정 (`mapscript.galaxy:628`) |
| — | 3, 5 | 민간인, 가축 |
| `gv_p4_ACTORS_BLUE` | 4 | 연출용 해병 |

동맹 2명이 들어갈 빈 슬롯이 필요하다 (6번 이후 후보, 미정).

### 레이너 측 유닛이 생기는 곳 (전부 트리거, 맵에 미리 놓인 것 없음)

| 위치 | 유닛 | 수 | 비고 |
|---|---|---|---|
| `mapscript.galaxy:4945-4948` | `Raynor01`, `Marine` | 1, 5 | 시작 연출 수송선 화물 |
| `mapscript.galaxy:5124-5135` | `Raynor01`, `Marine` | 1, 5 | 시작 배치 |
| `mapscript.galaxy:1808-1816` | `Marine` | 3 × 3 | 중간 증원 |
| `mapscript.galaxy:655-659` | `Marine`, `Raynor01`, `Firebat` | | 유닛 도움말 패널 (화염방사병은 조건부) |
| `mapscript.galaxy:4034` | `Marine` 판정 | | 유닛 종류를 `"Marine"`으로 검사하는 이벤트 |

### 적 (자치령, 2번 슬롯)

맵 배치: 해병 30, 화염방사병 1, 바이킹(전투기) 3, 병참 본부 1, 수송 트럭.
트리거 추가: 해병 4, 레이븐 1, 수송 트럭 2.

## 이 모드에서 바뀌는 점

| 항목 | 상태 | 내용 |
|---|---|---|
| 레이너 유닛은 모두 용병 | **확정** (2026-10-13) | 위 표의 `Marine` 생성 전부를 용병 유닛으로 바꿔야 한다 |
| 해병 역할 용병 | **확정** (2026-10-13) | 전쟁광 `WarPig` (자날 용병 해병) |
| 협동전 구조 (동맹 2명) | **확정** (2026-10-13) | 1번 미션에도 동맹 2명 자리 필요. **AI 조종** (확정) |
| 동맹 세력 | 확정 방향 | 정화자 프로토스, 원시 저그 |
| 레이너 영웅 | 원본 유지 | 바꾸라는 지시 없음 |

## 해병 역할 용병 후보

| 후보 ID | 출처 | 표시 이름 | 비고 |
|---|---|---|---|
| `TrooperMengsk` | 협동전 멩스크 | 자치령 부대원 | 체력 45. "멩스크 유닛 기반" 방향과 맞음 |
| `TrooperMengskImproved` | 협동전 멩스크 | 자치령 돌격병 | 무기 지급형 |
| `WarPig` | 자날 캠페인 | 전쟁광 | 자날 원작의 용병 해병 |
| `MercMedic` | 협동전 | 용병 의무관 | 의무관 역할 후보 (1번 미션엔 의무관 없음) |

## 진행 상황

### 1단계: 레이너 해병 → 전쟁광 (완료, 게임 시험 미실행)

`python3 tools/patch_mission01.py` → `build/TRaynor01.SC2Map`

- 트리거 데이터(`triggers`)와 스크립트(`mapscript.galaxy`)를 같은 10곳씩 바꾼다.
  편집기가 저장할 때 `triggers`로 스크립트를 다시 만들기 때문에 둘 다 고친다
- 바뀌는 곳: 도움말 패널 1, 시작 연출 화물 5명 1, 시작 배치 5, 중간 증원 3명 × 3
- 그대로 두는 곳: 자치령 해병(2번), 연출 해병(4번), `mapscript.galaxy:4034`의 자치령 해병 처치 통계 조건
- 자동 검사: 변경 줄 diff 확인, `triggers` XML 파싱 통과, 남은 `"Marine"` 16곳이 모두 2번·4번 슬롯인지 확인
- **미실행**: 편집기에서 열기, 게임 실행. 전쟁광은 체력 75로 원래 해병(45)보다 세다. 난이도 조정은 동맹 추가 후

### 다음 단계

1. 동맹 2명(AI) 슬롯 추가. 맵 플레이어 설정(`mapinfo`, 바이너리)에 자리가 없어 편집기 작업이 필요할 수 있다
2. 동맹 시작 병력과 위치
3. 적은 동맹 성능을 확인한 뒤 조정 (CLAUDE.md 7장). 참고: 드라이브의 `Wings of Liberty Nightmare Difficulty.zip` 모드

## 남은 결정

1. 1번 미션의 동맹 시작 병력과 위치
