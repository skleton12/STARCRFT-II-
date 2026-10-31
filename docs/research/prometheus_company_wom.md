# 프로메테우스 중대(FirebatMengsk) — Wings of Mengsk 구성 분석

조사: 2026-10-31. 원본: 사용자 드라이브 공유 `WoM-1.3_Armory.zip` → `帝国之翼军械库版v1.5/WoMRoyalGuards.SC2Mod` (파일만 열어 봄, 저장소·배포본에 넣지 않음).
상태: 조사 기록. 가져올지·다시 만들지는 사용자 결정 대기.

## 결론 — 외형은 모드 자작(커스텀) 에셋

| 부분 | 쓰는 것 | 출처 |
|---|---|---|
| 유닛 모델 | `Assets\Units\Terran\Incinerator\Incinerator.m3` (모드 안 513KB) | **커스텀** (블리자드 데이터에 없음) |
| 모델 텍스처 | `Incinerator_Dif/Norm/Spec/Emi`, `IncineratorA_Dif/Spec` 등 | **커스텀** (모드 Assets/Textures) |
| 화염 발사 연출 | `FirebatAttackLaunchRed` → `Assets\Effects\FirebatRedFlameSprite.m3` | **커스텀** (붉은 불꽃) |
| 아이콘·와이어프레임 | `BTN_Incinerator.dds`, `Wireframe-Incinerator.dds` | **커스텀** |
| 초상화 | `FirebatMercenaryPortrait` | 블리자드 (자날 용병 화염방사병) |
| 자극제 연출 | `StimpackStartImpact`, `Marauder_Mengsk_COOP_StimpackEnd` | 블리자드 |
| 피격 불꽃·음성·사운드 | `ImpactModelFlames`, `Firebat_*` 음성 | 블리자드 |
| 상태바 | `Coop_UnitStatus_Mengsk/MengskFirebat_StatusFrame` | 협동전 멩스크 UI (우리 맵엔 없음, 0.4.66 이지스와 같은 문제) |

참고: 모델 정의 틀(`TextureDeclares Prefix="incinerator_"`, `merc_incinerator_`)은 군단의 심장 캠페인의 블리자드 `MengskFirebat` 모델(`FirebatMercenary.m3`)과 같다. 모드는 그 틀에 경로만 커스텀 `Incinerator.m3`로 바꿨다. 즉 블리자드에도 **멩스크 화염방사병 모델 정의(`MengskFirebat`)가 있다** (군심 캠페인 층, 실제 모델은 용병 화염방사병).
커스텀 모델 제작자·배포 허락은 모드 안에서 확인하지 못했다.

## 데이터 (모두 블리자드 데이터 구조로 직접 만든 것)

- 유닛: 생명력 350, 장갑 2(보병 장갑), 이동 2.5, 인구 4, 광물 200·가스 400, 중장갑·생체, 수송 칸 4. 무기 사거리 2, 주기 1.4, 화염 4칸 앞으로 뻗는 영역 피해 15(경장갑·생체 +5).
- 진급(멩스크 근위대 경험치 1200/2400/3600):
  - 1등급: 피해 +25%, 장갑 +1, 생명력 +50.
  - 2등급 **점프 제트 강습**(Jump Jet Assault): 공격 명령에 붙는 자동 도약(재사용 5초), 착지 시 기절·5초 장갑 +2.
  - 3등급 **저거너트 장갑**(Juggernaut Plating): 피해 +25%, 장갑 +3, 생명력 +50, 숨은 피해 감소(한 번에 30 이상 받는 주문 외 피해를 30으로 자름).
  - 4등급(최대) **고급 자극제**(Advanced Stimpack): 15초 공격·이동 속도 +50%, 초당 생명력 10, 자동 시전, 재사용 30초.
- 연구: 소각 건틀릿(주변 적에 초당 16 지속 피해), 곰발톱 노즐(화염 길이·폭 증가 — 업그레이드가 효과 값을 바꾸는 방식), 저거너트 장갑 업그레이드(장갑 +2, 건틀릿 피해 +2).
- 멩스크 사령관 체계에 묶인 것: 근위대 재생 생체강철, 황제의 지원(Imperial Support, 상단 패널 자원) 생성 패시브, 진급 표시.

## 우리 모드에 들일 때 선택지

1. **블리자드 에셋으로 재구성 (추천)**: 군심 `MengskFirebat`/자날 `FirebatMercenary` 모델 + 붉은/검은 색조(액터 `SetTintColor` 또는 팀색), 블리자드 초상화·아이콘. 능력·수치는 위 표를 참고해 직접 데이터로 만든다. 다른 프로젝트 파일을 가져오지 않으므로 CLAUDE.md 1장 규칙에 맞다.
2. **모드에서 가져오기**: `Incinerator.m3`와 텍스처 10여 개(수 MB)를 CCM에 넣어야 한다. 제작자 허락이 확인되지 않았고, CLAUDE.md 1장("다른 프로젝트의 파일을 가져와 적용하지 않는다")의 예외를 사용자가 정해야 한다.

어느 쪽이든 멩스크 사령관 체계(황제의 지원·레벨)는 넣지 않고, 0.4.68 규칙대로 처음부터 3등급 능력치·진급 능력으로 고용하는 것이 기존 결정과 맞다 (등급·인구·비용은 미정).
