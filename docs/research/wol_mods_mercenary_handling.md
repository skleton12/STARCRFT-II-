# 참고: 드라이브의 자날 모드 두 개는 용병을 어떻게 처리했나

조사일: 2026-10-27. 사용자 요청 ("드라이브에 자날 모드는 용병을 어떻게 처리했는지 파악해봐").
참고용 분석이다. 두 모드의 파일은 가져와 쓰지 않는다 (CLAUDE.md 1장).

자료: 드라이브 `다른 커스텀 캠페인 zip` 폴더
- `Wol ReOverhaul with friends.zip` (Coop AI ReOverhaul, Nekromant, ReAllies 1.9.13)
- `RaynorRogue - Benny's Mayhem.zip`

zip 전체를 받지 않고 필요한 파일만 범위 요청으로 받아 MPQ를 풀어 봤다
(ReOverhaul: tstory01·ttosh01·traynor01, CoopAI·Utils·Utils_WoL·WOLReOverhaulUED 모드 / RaynorRogue: tstory01·ttosh01, BennyMayhem 모드).

## 공통점: 두 모드 모두 히페리온 허브 맵(tstory01)을 CCM 안에 넣었다

- 두 zip 모두 `tstory01.SC2Map`(히페리온)을 미션 맵과 함께 넣었다.
- 그래서 CCM도 허브 화면 스크립트를 바꿀 수 있다. 우리 CCM에는 지금 허브 맵이 없어서 블리자드 원본 허브가 쓰인다.

## Coop AI ReOverhaul

- **히페리온 계약 구매는 원작 그대로다.**
  - 허브 스크립트를 공개 원본(SC2GameData tstory01 MapScript)과 비교했다. 용병 관련 줄은 바뀐 게 없다.
  - 캠페인 자금(크레딧)으로 사고, 미션 4개를 깨면 켈모리안을 무료로 주는 원작 코드도 그대로다.
- 허브에서 바꾼 것은 자기 모드 상점이다.
  - 크레딧으로 사는 협동 서비스를 추가했다 (`CoopServicesStoryGetPrice`: Shielding·WASUp·ShieldBreaker·Medkits·MirasMarauders 등).
  - 크레딧 표시 패널도 새로 붙였다.
  - 용병 고용소 설명 버튼(`MercUnits2`)에는 "계약한 용병마다 동맹 Hill에게 추가 수입"이라고 적혀 있다.
- **미션 안 고용은 공짜·무제한으로 바꿨다** (CoopAI 모드 `SummonMercenaries`).
  - 모든 칸이 광물·가스 0, 충전 횟수 없음(CountMax 0)이고 재사용 대기만 있다 (30·40·45·60·300초).
  - 분대 대신 1기가 나온다 (Unit index 1~3 제거).
  - '미라의 약탈자' 서비스를 샀으면 첫 칸을 숨긴다 (`NotMiraHired`). 그 서비스는 망치 경호대·스파르탄 중대의 인구를 0으로 만든다.
- 미션 맵은 원작처럼 `libCamp_gf_LoadCampaignData` → `libCamp_gf_PurchaseStorymodeTech`를 그대로 부른다.

## RaynorRogue (Benny's Mayhem)

- 원작 허브의 계약 구매를 쓰지 않는다.
- 새 캠페인 라이브러리 `LibWoLC`를 쓴다. 용병은 UserData `Mercenaries`, `WC_MercenaryPurchased`로 다룬다. 우리 맵이 쓰는 `libCamp_` 체계와는 다르다.
- **미션 시작 때 해당 일반 유닛이 해금돼 있으면 용병판을 공짜로 켠다** (`gf_MercUnlock`).
  - 해병 → 전쟁광, 불곰 → 망치 경호대, 화염방사병 → 악마의 개
  - 골리앗 → 스파르탄 중대, 공성 전차 → 공성 파괴단, 바이킹 → 지옥의 천사
  - 밴시 → 황혼의 날개, 전투순양함 → 듀크의 복수
- 로그라이트 모드에서는 재능(Talent)을 얻으면 해당 유닛·용병 고용소·용병 유닛을 `TechTreeUnitAllow`로 연다.
- 용병 고용소 해금 조건은 THanson01 또는 TTychus01 클리어다.

## 우리 모드와 비교

| | ReOverhaul | RaynorRogue | 우리 (0.4.109~) |
|---|---|---|---|
| 히페리온 계약 | 원작 그대로 (크레딧 구매) | 안 씀 (LibWoLC, 재능) | 잠기지 않은 계약을 미션 시작 때 '구매됨'으로 기록 (돈 안 씀) |
| 허브 맵 포함 | O (자기 상점 추가) | O | X (블리자드 허브 사용) |
| 미션 안 고용 비용 | 0, 무제한, 대기 시간만 | 일반 생산으로 엶 | 원작 고용소 비용·횟수 그대로 |

시사점: 히페리온 화면에서 바로 '고용됨'을 보이려면, 두 모드처럼 허브 맵 tstory01을 CCM에 넣고 허브가 캠페인 데이터를 불러온 직후 같은 무료 계약 함수를 부르는 방법이 있다. 미구현이고 사용자 결정이 필요하다. 원본 허브 맵 전체 파일(지형·MapInfo 등)이 필요하다. 공개 미러에는 스크립트·Objects만 있다.

검증 범위: 파일을 풀어 스크립트·데이터를 읽은 정적 조사다. 게임 실행은 미실행.
