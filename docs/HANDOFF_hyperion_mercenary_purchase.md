# Claude 인수인계: 히페리온 용병 계약 구매 로직

조사일: 2026-10-27 (한국 시간)
상태: 원작 코드 조사 및 사용자 요청에 따른 인수인계. 신규 기획 승인이나 게임 구현 완료가 아니다.

## 원본 위치

SC2Mapster/SC2GameData의 고정 커밋 `b7587cca570f6a7ce27efa3336a6495d54a71720` 기준이다. 현재 게임 설치본과 버전이 같다고 가정하지 않는다.

파일: `campaigns/libertystory.sc2campaign/base.sc2data/TriggerLibs/CampaignLib.galaxy`

- [구매 처리 함수, 12175행부터](https://github.com/SC2Mapster/SC2GameData/blob/b7587cca570f6a7ce27efa3336a6495d54a71720/campaigns/libertystory.sc2campaign/base.sc2data/TriggerLibs/CampaignLib.galaxy#L12175)
- [용병 패널 생성·갱신·무료 지급, 3700행 부근](https://github.com/SC2Mapster/SC2GameData/blob/b7587cca570f6a7ce27efa3336a6495d54a71720/campaigns/libertystory.sc2campaign/base.sc2data/TriggerLibs/CampaignLib.galaxy#L3700)

## 구매 이벤트와 처리 순서

`libCamp_gt_TS_MercUIPurchase_Init`가 `TriggerAddEventMercenaryPanelPurchase(..., c_playerAny)`로 구매 버튼 이벤트를 등록한다.
콜백은 `libCamp_gt_TS_MercUIPurchase_Func`다. 이벤트 등록은 모든 플레이어이지만 콜백의 선택·자금 표시 접근은 플레이어 1로 고정되어 있다.

1. `MercenaryGetSelected(1)`의 UI ID를 `libCamp_gv_tS_MercUIMercenaries` 배열과 비교하여 내부 용병 ID를 찾는다.
2. 내부 ID가 `MercNone`이거나, `MercCost`가 `StoryCredits`보다 크거나, 상태가 `Available`도 `New`도 아니면 종료한다. 구매 완료·잠금 상태는 구매할 수 없다.
3. `libCamp_gf_SetMercStatus(..., libCamp_ge_StoryMercStatus_Purchased)`로 캠페인 구매 상태를 기록한다.
4. `libCamp_gf_SetStoryCredits(StoryCredits() - MercCost(...))`로 캠페인 자금을 차감한다.
5. `PlayerModifyPropertyInt(1, c_playerPropCredits, c_playerPropOperSetTo, ...)`로 플레이어 자금 표시를 맞춘다.
6. `libCamp_gf_TS_AddRecentMerc` 호출 후 `MercenaryPurchase`로 UI 구매 표시·연출을 갱신한다.
7. 고용 완료 이미지로 바꾸고 초상화 모델은 `Invisible`로 설정한다.
8. 다른 구매 가능 용병 중 남은 자금으로 살 수 없는 항목을 자금 부족 이미지로 갱신한다.
9. 용병별 구매 상태에 따라 업적 수치를 갱신한다.

**중요:** `MercenaryPurchase()`만 호출해서 캠페인 자금 차감과 소유 상태 기록까지 끝났다고 보면 안 된다. 원작 콜백은 두 처리를 따로 수행한다.
[MercenaryPurchase API 설명](https://mapster.talv.space/galaxy/reference/mercenary-purchase)

## 주변 함수

| 함수 | 확인한 역할 |
|---|---|
| `libCamp_gf_DisplayMercenaryPanel` | 종료 콜백 지정 → UI 갱신 → `MercKelmorianMercenaries` 무료 지급 함수 호출 → 패널 표시 |
| `libCamp_gf_TS_MercUIUpdateUI` | 최초 생성 시 이름·설명·가격·유닛 문구·초상화·영상 설정. 이후 Available/New/Locked/Purchased 및 자금 부족 표시 갱신 |
| `libCamp_gf_TS_MercUIGift` | 구매 상태·최근 구매·UI 연출 처리. 자금 차감 호출 없음 |
| `libCamp_gt_TS_MercUIPurchase_Init` | 구매 버튼 이벤트 등록 |
| `libCamp_gt_TS_MercUIPurchase_Func` | 구매 검증·상태 기록·자금 차감·UI·업적 갱신 |

무료 지급 함수의 원본 가드는 `MercNone && Purchased` 조합이다. 일반 구매 함수와 같은 중복 지급 방어를 갖췄다고 추정하지 말고, 재사용한다면 원본 조건과 호출 경로를 다시 검토한다.

## 모드에 적용할 때 구분할 사항

- 이번 조사 대상은 히페리온의 **캠페인 자금으로 계약 구매**하는 부분이다. 미션 중 용병 고용소의 광물·가스 지불, 분대 생성, 횟수 제한, 쿨다운과는 별도다.
- `SetMercStatus`의 저장 매체·저장 시점, 임무 진입 시 구매 정보가 업그레이드/생산 허용으로 전달되는 경로, 용병별 최초 해금·가격 데이터는 이번 조사에서 내부 구현까지 확인하지 않았다.
- 이 문서만으로 캠페인 계약 구매가 현재 모드의 코랄의 후예 고용과 자동 연결된다고 단정하지 않는다.
- 현재 프로젝트는 업적 비활성화가 확정되어 있다. 원작 구매 콜백의 업적 처리를 그대로 이식하지 않는다.
- 모드 변경 시에는 루트 CLAUDE.md와 docs/DECISIONS.md의 최신 확정 방향을 따른다.

## 검증 범위

공개 원작 데이터 미러의 구매 함수와 패널·무료 지급 함수 본문을 읽어 확인했다. Galaxy 컴파일, 게임 실행, 저장/불러오기, 임무 간 구매 상태 전달은 미검증이다. 이번 인수인계는 문서만 추가하며 맵·게임 코드·배포 ZIP은 변경하지 않는다.
