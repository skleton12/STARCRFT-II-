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

### 1번 미션 동맹 구성 (사용자 확정 2026-10-13)

| 세력 | 유닛 | ID | 수 | 조종 |
|---|---|---|---|---|
| 정화자 | 피닉스 (협동전) | `FenixCoop` | 1 | 정화자 AI |
| 정화자 | 정화자 광전사 (게임 표시: 파수병) | `ZealotPurifier` | 3 | 정화자 AI |
| 원시 저그 | 노현자 울트라리스크 | 없음 (새 캐릭터) | 0 | 대사만 (확정) |
| 원시 저그 → 레이너 | 라바사우르 (협동전, 원시 저그 용병) | `Ravasaur` | 1 | 레이너 (확정) |

1번 미션에서 맵에 유닛이 있는 AI 동맹은 정화자 하나다. 원시 저그 AI 슬롯은 대사·연출용으로만 필요하다.

### 주의: StarCoop 모드를 종속성으로 직접 걸면 안 된다

협동전 본체(`StarCoop.SC2Mod`)는 기본 유닛을 협동전용으로 덮어쓴다.
1번 미션의 적인 `Marine`, `Firebat`, `VikingFighter`, `Raven`, `LogisticsHeadquarters`까지 바뀐다
(점수 0, 협동전 행동 추가 등). CLAUDE.md 6장의 '전역 변경 피하기'에 걸린다.

그래서 피닉스, 정화자 광전사, 라바사우르에 필요한 엔트리만 `tools/extract_commander.py` 방식으로 뽑아
CCM 전용 `.SC2Mod`에 넣는다. StarCoop 폴더에는 `sc2assets`가 없어서 모델·텍스처는 기본 게임
에셋에 있는 것으로 보인다 (게임에서 확인 필요).

### 동맹 유닛 원본 정의 위치 (조사 중)

| 유닛 | 본래 정의 위치 | 상태 |
|---|---|---|
| `FenixCoop` | StarCoop | 받음 |
| `Ravasaur` | 군심 캠페인 `swarm.sc2campaign` gamedata (드라이브 폴더 `1dBE26jAoAOnbRFFlIe5zPoT27-6Ma3-N`, 10-06 업로드본) | 받음 |
| `ZealotPurifier` | 공허 캠페인 `void.sc2campaign` gamedata (`parent="Zealot"`) | 받음 |

core, voidmulti, void.sc2mod, swarm.sc2mod, liberty·libertystory, swarmstory, voidstory에는 `ZealotPurifier` 정의가 없다.
StarCoop에는 둘 다 일부 수정본만 있다.

### 동맹 데이터를 넣는 방법

캠페인 데이터를 종속성으로 통째로 걸면 1번 미션 유닛이 바뀐다 (각 데이터의 `unitdata.xml` 확인):

| 종속성 후보 | 1번 미션 유닛 중 덮어쓰는 것 |
|---|---|
| StarCoop | Marine, Firebat, VikingFighter, Raven, LogisticsHeadquarters |
| void.sc2campaign | Marine, Firebat, WarPig, Raynor01, Zealot |
| swarm.sc2campaign | VikingFighter, Raynor01 |
| void.sc2mod / swarm.sc2mod | Zealot / Raven, Zealot (기본 모드 층, 공허 적용 상태의 일부) |

그래서 캠페인·협동전 데이터는 종속성으로 걸지 않고, 피닉스·정화자 광전사·라바사우르에 필요한
엔트리만 CCM 전용 데이터로 복사한다.

### 맵 플레이어 설정 (`documentheader`/`mapinfo`, 바이너리)

원본 `mapinfo`에는 플레이어 레코드 1~5가 있다 (`documentheader`에는 0~7 이름이 있음).

**2단계 (완료, 게임 시험 미실행)**: 8번 정화자(프로토스, 컴퓨터), 9번 원시 저그(저그, 컴퓨터) 추가.
바이트 구성은 GPT가 만든 사본과 같고, `tools/patch_mission01.py`가 원본에서 똑같이 만든다.

- `mapinfo` 레코드: 번호(1) 조종(1: 1=사용자, 2=컴퓨터) 0(3) 색(i32) 종족(4) 고정 13바이트 + 데칼 이름(NUL 끝).
  0x87 바이트 = 레코드 수 + 1. 새 레코드의 색은 -1, 뒤쪽 고정 값은 0 (원본 값의 의미는 미확인)
- `documentheader`: 의존성 목록 뒤에 속성 수(u32)와 속성 표(키 길이 u16, 키, 언어 4바이트, 값 길이 u16, 값).
  8·9번 이름을 12개 언어에 추가 (144 → 168개)
- 맵 한국어 문자열에 `MapInfo/Player08/Name`, `Player09/Name` 추가
- 자동 검사: 두 바이너리를 위 규칙으로 끝까지 파싱 성공, GPT 사본과 바이트 동일

### 3단계: 동맹 데이터·스크립트 (완료, 게임 시험 미실행)

**데이터** (`tools/port_units.py`, 패치 도구가 자동 실행): 피닉스·정화자 광전사·라바사우르와 딸린
능력·무기·효과·행동·연출 246개 엔트리를 맵 데이터(`base.sc2data/gamedata`)에 복사.
- 맵이 이미 가진 층(core, 자날 캠페인·스토리)과 맵에 나오는 유닛 이름은 복사하지 않음 (덮어쓰기 금지)
- 여러 층에 같은 ID가 있으면 낮은 층 정의 뒤에 높은 층 수정 내용을 이어 붙여 합침
  (swarm 모드 → void 모드 → voidmulti → 군심 캠페인 → 공허 캠페인 → 협동전)
- 대사, 사령관 목록, 스킨, 마스터 힘·위신·돌연변이는 따라가지 않음. 6곳 넘게 참조되는 공용 엔트리도
  따라가지 않음 (단 시작 유닛이 직접 가진 것과 이름에 `Fenix`가 든 것은 따라감). 목록은 맵 폴더의
  `ported_shared_refs.txt`
- 한국어 문자열 138줄 복사. 라바사우르 이름은 원본 문자열이 없어 `라바사우르`로 직접 넣음.
  정화자 광전사(`ZealotPurifier`)의 게임 표시 이름은 원본대로 `파수병` (사용자 확인 2026-10-13)

**스크립트** (`mapscript.galaxy`에 직접 삽입):
- 맵 초기화(동맹 설정 직후)에 `gf_rm_AllyInit()`: 8·9번을 레이너와 시야 공유 동맹, 자치령과 적, 주민·연출과 중립.
  색은 8번 청록(3), 9번 주황(6) (임시)
- 레이너 시작 배치 직후 `gf_rm_SpawnAllies()`: 레이너 시작 지점(505) 옆에 피닉스 1 + 정화자 광전사 3 (8번),
  라바사우르 1 (레이너)
- 동맹 AI (임시, 단순): 2초마다 할 일 없는 8번 유닛 중 레이너에게서 6 넘게 떨어진 유닛을 레이너 위치로 어택땅
- 호출한 함수 이름·인자는 core `natives.galaxy`, `nativelib_h.galaxy`와 대조함
- **주의**: 이 코드는 트리거 데이터(`triggers`)에는 없다. 편집기에서 맵을 저장하면 사라지므로
  맵은 편집기로 저장하지 말고 `tools/build_ccm.py`로 원본에서 다시 만든다

**확인 못 한 것**
- 모델·텍스처·소리 파일 위치: 드라이브의 `liberty.sc2mod` 에셋 폴더가 비어 있어 확인 불가.
  그 폴더 구조에 `coop`, `units`가 있어 자날 모드 묶음에 들어 있을 것으로 보고 따로 넣지 않음.
  게임에서 유닛이 안 보이면 `tools/fetch_assets.py`로 맵 안에 넣는다 (지금은 원본 에셋이 드라이브에 없어 동작 안 함)
- 게임 실행, 편집기 열기: 미실행

### 다음 단계

1. 동맹 2명(AI) 슬롯 추가. 맵 플레이어 설정(`mapinfo`, 바이너리)에 자리가 없어 편집기 작업이 필요할 수 있다
2. 동맹 시작 병력과 위치
3. 적은 동맹 성능을 확인한 뒤 조정 (CLAUDE.md 7장). 참고: 드라이브의 `Wings of Liberty Nightmare Difficulty.zip` 모드

## 남은 결정

1. 1번 미션의 동맹 시작 병력과 위치
