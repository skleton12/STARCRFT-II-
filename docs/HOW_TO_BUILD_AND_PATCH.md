# Claude가 모드를 만들고 고치는 방법 (GPT 인수인계)

2026-10-20 / 사용자 요청: "Claude가 모드를 어떻게 만들고 수정하는지 남겨서 GPT가 보고 따라 하게".
CLAUDE.md 전체를 먼저 읽는다. 이 문서는 규칙이 아니라 **작업 절차와 함정 목록**이다. 규칙과 다르면 CLAUDE.md가 우선이다.

## 1. 저장소 구조

| 경로 | 내용 |
|---|---|
| `releases/RaynorMercs_WoL_CCM.zip` | 배포본. 이름 고정. 버전은 안의 `metadata.txt` (`version=0.미션.수정`) |
| `maps/original_wol/` | 원본 미션 맵 (손대지 않음) |
| `source/` | 게임 데이터 미러. 층 순서: `core.sc2mod` → `liberty.sc2mod` → `liberty.sc2campaign` → `libertystory.sc2campaign`. 협동전은 `source/starcoop/starcoop.sc2mod`, 멩스크는 `source/starcoop/commanders/arcturusmengsk.sc2mod`. 군단·공허: `swarm*`, `void*` |
| `tools/build_vXXX.py` | 버전마다 하나. **직전 ZIP → 새 ZIP** 으로 바꾸는 패치 도구. 순서대로 다시 돌리면 재현된다 |
| `tools/port_units.py` | 다른 층(협동전·공허·군단)의 유닛을 맵 데이터로 옮기는 이식 도구 |
| `tools/check_release.py` | 배포 전 필수 검사. 실패 1개라도 있으면 배포 금지 |
| `tools/check_marauder_research.py` | GPT/Codex가 만든 불곰 연구 조건 검사 |
| `tools/build_v035.py` | 문자열 도우미: `fix_kokr`, `gate`, `other_locale`, `english_sources`, `OTHER_LOCALES` |
| `tools/data/mission04_support.galaxy` | 4번 이후 공통 스크립트 원본 (`gf_m4_…`). 맵 스크립트를 고치면 **이 파일도 같이** 고쳐야 다음 미션이 물려받는다 |

## 2. 한 번의 수정 = 한 개의 build 도구

1. `git fetch` 로 다른 AI가 올린 것이 있는지 먼저 본다. 있으면 받아서(`git merge --ff-only`) **그 ZIP 위에** 만든다. 버전 번호도 그 다음 번호로.
2. `tools/build_v04NN.py` 를 만든다. 형식:
   - `OLD, NEW = b'version=0.4.41', b'version=0.4.42'`, 시작할 때 `OLD`가 맞는지 assert.
   - 바꿀 파일만 `FIX = {zip 안 경로: 함수}` 로 고친다. 문자열 치환은 **정확히 1번 나오는지 assert** (`t.count(a) == 1`).
   - 결과 ZIP에서 고치지 않은 파일이 **바이트까지 같은지** 확인한다.
   - 맨 위 docstring에 사용자 지시(날짜), 원인, 바꾼 것, 시험값 표시를 적는다.
3. 임시 출력은 스크래치 폴더에 만들고 `python3 tools/check_release.py <그 zip>` → 통과하면 `releases/` 로 복사.
4. 스크립트를 고쳤으면 같은 치환을 `tools/data/mission04_support.galaxy` 에도 적용 (build 도구의 함수를 import 해서 쓰면 같은 치환이 보장된다).
5. 규칙이 바뀌었을 때만 CLAUDE.md에 짧게 기록 (사용자 요청: 문서는 룰 적용 시에만).
6. 커밋 → `git push -u origin claude/lucid-franklin-ed0eko` → 사용자에게 ZIP 전달.

간단한 예: `tools/build_v0438.py` (버튼 한 칸 옮기기), `tools/build_v0431.py`(Claude판은 `build_v0436.py`, 검증기 덮어쓰기).
이식이 들어가는 예: `tools/build_v0442.py` (ZIP 풀기 → port_units → 데이터 보정 → 문자열 → 스크립트 → 다시 묶기).

## 3. 데이터 찾는 법

- ID 검색은 `grep -rn 'id="XXX"' source/<층>/base.sc2data/gamedata/<파일>.xml`. `source/` 전체 grep은 매우 느리니 파일을 좁힌다.
- 같은 ID가 여러 층에 있으면 **뒤 층이 앞 층을 덮는다**. 특히 `libertystory.sc2campaign` 이 원작 효과를 몰래 바꾼다 (예: 충격탄 검증기를 히페리온 구매로 바꿈).
- 캠페인이 유닛·연구를 어떻게 막는지는 `source/libertystory.sc2campaign/base.sc2data/triggerlibs/campaignlib.galaxy` (`TechTreeAbilityAllow(... "FactoryTrain", n)` 등).
- 무기고 항목 목록과 업그레이드 ID는 `libertystory` 의 `conversationstatedata.xml` (`Tech_*`).
- Galaxy 함수·상수가 있는지는 `source/core.sc2mod/base.sc2data/triggerlibs/natives.galaxy` 와 `triggerlibs/gamedata/*.galaxy`. **이 환경에는 Galaxy 컴파일러가 없다.** 쓰기 전에 반드시 시그니처를 확인한다.

## 4. 유닛 이식 (port_units.py)

```
python3 tools/port_units.py <풀어 놓은 맵 폴더> --liberty-base --skip-existing "--drop=정규식" 유닛ID 능력ID ...
```
- `--liberty-base` 필수(2번 미션부터). `--skip-existing` 은 이미 맵에 있는 ID를 건너뛴다. 멩스크는 `--with-mengsk`.
- `--drop` 으로 사령관 체계(영웅 변신·챔피언·마스터 힘·아둔의 창·부활 알 등)를 끊는다. 안 끊으면 1000개 넘게 딸려 온다. 먼저 한 번 돌려 새로 생긴 `CUnit` 목록을 보고 drop을 정한다.
- 이식 뒤 거의 항상 고쳐야 하는 것 (check_release가 알려 준다):
  - 사령관 레벨 잠금 (`DehakaLevel07` 등): 버튼·요구조건 삭제. 레벨로 켜지는 기능은 끈다 (예: 데하카 유전자 → 절대 안 통과하는 요구조건 `RMZ_Never`).
  - 공용이라 안 따라온 작은 레코드: `X_Land` 소리 액터, `DeathRagdollDetonationForce`, 포탑(`FreeRotate`, `Phoenix`, `Colossus`). 자날 층에는 포탑 정의가 없으므로 맵 `turretdata.xml` 에 부모 없이 정의한다 (`NydusCanalAttacker` 방식).
  - 종족 줄 누락, 모델 경로 누락(빨간 오류 구), 대상 없는 Create/ModelSwap.
  - 문자열: 한국어만 있거나 영어만 있는 줄. 빌드 도구에 `EN_FIX`(영어 보충), `KO_FIX`(한국어 보충) 표를 두고 `fix_kokr` → `gate` 순서로 통과시킨다.
- 적과 같은 유닛 ID를 동맹이 쓸 때는 전역 외형을 바꾸지 않고 `On Terms="Behavior.RM3_AllySkin.On" Send="ModelSwap 모델"` 을 액터에 단다. 모델은 자날 층(`liberty.sc2mod`)에 있는 ID인지 확인 (예: `ImmortalPurifier` 가 아니라 `Immortal_Purifier`).

## 5. 스크립트 (mapscript.galaxy)

- 동맹 코드는 `mapscript.galaxy` 에만 있다. **편집기로 맵을 저장하면 사라진다.**
- 공통 스크립트는 `InitGlobals` 앞에 들어가고, `gf_m4_Init` 은 `PurchaseStorymodeTech` 뒤, `gf_m4_Start` 는 게임 시작 때 실행. 주기 처리는 `gt_m4_Tick_Func`.
- 함수는 **쓰기 전에 선언**되어야 한다 (check_release가 검사). 지역 변수는 함수 맨 위에서만 선언. 지역 문자열 배열은 `""` 로 먼저 채운다 (기본값 null).
- 플레이어별 데이터 변경은 `CatalogFieldValueSet(카탈로그, ID, 필드, 플레이어, 값)`. **`CatalogLinkReplace` 를 플레이어 유닛 종류 전체에 쓰지 않는다** (드래그 선택 고장 원인).
- 동맹 자원은 한쪽만 공유: `PlayerSetAlliance(동맹, c_allianceIdSpend, 1, true)`, 레이너→동맹은 false.

## 6. 자주 밟은 함정 (실제 사고 목록)

| 증상 | 원인 | 대응 |
|---|---|---|
| 연구 버튼이 안 보임 | 원작 버튼이 같은 칸을 먼저 차지 (먼저 적힌 버튼이 보임) | 빈 칸으로 옮김. check_release가 연구 버튼 겹침 검사 |
| 연구해도 효과 없음 | 스토리 층이 검증기를 히페리온 구매로 바꿈 | 맵에서 그 검증기를 덮어씀 |
| 연구 전부터 효과 적용 | `CValidatorPlayerRequirement` 의 `Find` 기본값이 false(=미충족일 때 통과) | `Find=1` 명시 |
| 버튼은 데이터에 있는데 안 나옴 | 캠페인 기술 제한 | 스크립트에서 `TechTreeAbilityAllow`/`TechTreeUpgradeAllow`/`TechTreeUnitAllow` |
| 일반 벙커에 다른 모델이 겹침 | 모드 액터가 실제 유닛 액터를 부모로 써서 `UnitBirth.<부모>` 를 물려받음 | 모드 액터는 템플릿 부모만. check_release 검사 |
| 효과가 아예 안 나감 | 이름 바꾸기에서 검증기 ID 하나를 빠뜨림 | check_release의 '효과가 부르는 검증기 정의' 검사 |
| 원시 알 비용 두 번 | 알 생성 비용 + 부화 변태 비용 | 변태 비용 0 |
| 동맹이 맵 구석에서 멈춤 | 원본의 숨은 인구 건물(Food1000)·연출 건물을 적 기지로 인식 | 목표에서 제외, 무적·숨김 건물 제외 |
| 용병 효과가 안 들어감 | 원작 업그레이드가 일반 유닛 ID만 바꿈 (예: 전투 안정제 → `heal`) | 맵에서 용병 효과(`MercMedicHeal`)까지 넓힘 |
| 공통 스크립트 파일이 빈 파일이 됨 | `open(p,'wb').write(f(open(p,'rb').read()))` — 쓰기 열기가 먼저 파일을 비움 | 먼저 읽고, 그다음 `with open(p,'wb')` 로 쓴다 |
| push 거절 | 다른 AI가 같은 브랜치에 먼저 올림 | fetch → 내용 확인 → 그 위에 다음 버전으로 다시 빌드. 강제 푸시 금지 |

## 7. 배포 전 체크리스트

1. `python3 tools/check_release.py <zip>` 통과 (이름 검사 때문에 파일 이름이 `RaynorMercs_WoL_CCM.zip` 이어야 함).
2. 불곰 연구를 건드렸으면 `python3 tools/check_marauder_research.py <zip>`.
3. 공통 스크립트에도 같은 변경을 넣었는지.
4. 게임 실행은 이 환경에서 못 한다. 보고에 "게임 미실행"이라고 쓰고, 사용자에게 확인할 점을 짧게 적는다.
5. 새 실수 유형이 나오면 check_release에 검사를 추가하고, 옛 ZIP에 돌려서 실제로 잡히는지 확인한다.
