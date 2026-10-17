# 자유의 날개 임무 해금 순서 (원작 데이터, 2026-10-17 조사)

출처: `source/libertystory.sc2campaign/base.sc2data/triggerlibs/campaignlib.galaxy`의 임무 잠금/해제 조건(`libCamp_gf_TS_LockUnlockMissionIfCondition`)과 임무 정보(`InitializeMapDataSingle`).
'완료 수'는 끝낸 임무 개수다. 임무 이름은 영어 원제이고, 한국어 공식 제목은 데이터에서 확인하지 못했다 (게임 문자열에는 '핸슨 01' 같은 내부 이름만 있다).
해금 유닛은 자날 원작 기준이다. 이 모드에서 용병 대응은 docs/research/wol_merc_mapping.md를 따른다.

| 맵 ID | 원제 | 행성 | 의뢰인 | 열리는 조건 | 원작 해금 |
|---|---|---|---|---|---|
| TRaynor01 | Liberation Day | 마 사라 | 부관 | 처음 | 해병 |
| TRaynor02 | The Outlaws | 마 사라 | 부관 | TRaynor01 | 의무관 |
| TRaynor03 | Zero Hour | 마 사라 | 부관 | TRaynor02 | 벙커 |
| THanson01 | The Evacuation | 아그리아 | 핸슨 | TRaynor03 | 화염방사병 |
| THanson02 | Outbreak | 마인호프 | 핸슨 | THanson01 | 화염차 |
| THanson03A/B | Safe Haven / Haven's Fall (둘 중 하나) | 헤이븐 | 핸슨 | THanson02 후 임무 2개 더, 또는 완료 12 | 바이킹 |
| TTychus01 | Smash and Grab | 몬리스 | 타이커스 | TRaynor03 | 불곰 |
| TTychus02 | The Dig | 실 | 타이커스 | TTychus01 + 완료 8 | 공성 전차 |
| TTychus03 | The Moebius Factor | 타이라도르 | 타이커스 | TTychus02 + 완료 11 | 의료선 |
| TTychus04 | Supernova | 티폰 | 타이커스 | TTychus03 + 완료 14 | 밴시 |
| TTychus05 | Maw of the Void | 시그마 사분면 | 발레리안 | TTychus04 | 전투순양함 |
| TTosh01 | Devil's Playground | 레드스톤 | 토시 | 완료 4 | 사신 |
| TTosh02 | Welcome to the Jungle | 벨시르 | 토시 | TTosh01 | 골리앗 |
| TTosh03A/B | Breakout / Ghost of a Chance (둘 중 하나) | 뉴 폴섬 / 아베르누스 | 토시 | TTosh02 후 임무 2개 더, 또는 완료 13 | 악령 / 유령 |
| THorner01 | The Great Train Robbery | 타소니스 | 호너 | 완료 6 | 다이아몬드백 |
| THorner02 | Cutthroat | 데드맨스 포트 | 호너 | THorner01 | 벌처 |
| THorner03 | Engine of Destruction | 발할라 | 호너 | THorner02 | 레이스 |
| THorner04 | Media Blitz | 코랄 | 호너 | THorner03 | 토르 |
| THorner05S | Piercing the Shroud (비밀) | 카스타나르 | 호너 | THorner04 + 비밀 조건 | — |
| TZeratul01~04 | 제라툴 예언 임무 4개 | 울란·자쿨·아이어·울나르 | 제라툴 | TTychus02 후 차례로 | — |
| TValerian01 | Gates of Hell | 차 | 발레리안 | TTychus05 | — |
| TValerian02A/B | Belly of the Beast / Shatter the Sky (둘 중 하나) | 차 | 발레리안 | TValerian01 | — |
| TValerian03 | All In | 차 | 발레리안 | TValerian02A 또는 B | — |

## 3번 이후

- 3번(Zero Hour)을 끝내면 곧바로 **THanson01(The Evacuation)**과 **TTychus01(Smash and Grab)** 두 임무가 열린다. 임무 사이에는 히페리온(무기고·연구실·용병 고용)이 열린다.
- 토시 임무는 4개, 호너 임무는 6개를 끝내면 열린다.
- 이 모드는 '1번 임무부터 순서대로' 만든다 (CLAUDE.md 3장). 4번으로 어느 임무를 만들지는 사용자가 정한다 (미정).
