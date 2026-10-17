# 태양 광선 원작 조사 — 태양의 창과 정화 광선

조사일: 2026-10-17. 사용자 요청은 **기존 모드 구현을 다시 설명하는 것이 아니라 원작 능력을 조사해 Claude에게 전달하는 것**이다.

자료는 SC2Mapster가 공개한 게임 데이터의 공허의 유산 캠페인 층과 협동전 층, 영문 이름·툴팁을 대조했다. 아래 수치는 사령관 레벨·마스터 힘·위신 등 추가 변경을 적용하기 전 해당 데이터 정의의 기본값이다. 실제 클라이언트에서 실행한 결과는 아니다.

## 1. 무엇을 구분해야 하나

대화의 “태양 광선”만으로 서로 다른 원작 능력을 같은 것으로 취급하면 안 된다.

| 능력 | 출처·주체 | 실제 동작 | 모드에서 혼동하면 안 되는 점 |
|---|---|---|---|
| **태양의 창 / Solar Lance** | 공허의 유산 아둔의 창, 협동전 카락스 | **광선 3줄**로 지정 경로를 훑으며 직격 피해. 강화하면 경로에 불길을 남김 | 넓은 원 안의 적 전체를 일정 간격으로 때리는 능력이 아님 |
| **정화 광선 / Purifier Beam** | 공허의 유산 아둔의 창, 협동전 카락스 | **움직이는 광선 유닛**이 주변 적에게 지속 피해. 자동 표적 획득과 수동 이동 명령 가능 | 태양의 창의 강화 모델이나 동일한 능력의 다른 이름이 아님 |
| 거신의 열광선·사거리 연구 | 거신 무기·업그레이드 | 유닛의 기본 공격 또는 공격 관련 연구 | ID에 ThermalLance가 들어간다는 이유로 아둔의 창 능력과 합치지 않음 |

현재 모드에서 사용한 `SOA_SolarLance_Upgrade.m3`는 **태양의 창 계열 모델**이다. 이 파일을 사용했다는 사실만으로 원작 태양의 창의 피해·이동·화염 효과까지 구현한 것은 아니다.

## 2. 태양의 창 — 원작에서 하는 일

원문 이름은 `Button/Name/SOAThermalLance=Solar Lance`다. 공허 캠페인 툴팁은 “3 laser beams”로 지역을 훑고 **각 광선이 피해를 준다**고 명시한다. 화면상의 영문 이름은 Solar Lance이지만 핵심 능력·피해 ID에는 **ThermalLance**가 사용된다.

| 항목 | 캠페인 데이터 | 협동전 카락스 데이터 |
|---|---|---|
| 활성화 능력 | `SOAThermalLanceActivate` | 같은 ID를 협동전에서 덮어씀 |
| 조준/실행 능력 | `SOAThermalLanceTargetingDummy`, `SOAThermalLanceExecute` | 같은 실행 ID의 효과 연결이 바뀜 |
| 발동 에너지 | `Cost.Vital[Energy]=50` | 해당 협동전 덮어쓰기에서 변경하지 않아 기본 50을 상속 |
| 활성화 재사용 대기 | `Cooldown.TimeUse=60` | `Cost[0].Cooldown.TimeUse=120`으로 변경 |
| 기본 광선 수 | 툴팁상 3줄 | 강화 툴팁도 3줄을 명시 |
| 광선 1줄의 기본 직격 피해 | `SOAThermalLanceDamage.Amount=200` | 협동전 해당 정의가 금액을 바꾸지 않아 200을 상속 |
| 기본 피해 경로 | `SOAThermalLanceCP`의 연속 검색 | `SOAThermalLanceSet`에서 직격·불길 경로를 묶음 |

에너지 50은 능력 활성화 기준이다. 광선 3줄이 각각 에너지 50을 소모한다는 뜻이 아니다. `SOAThermalLanceExecute`의 `0.25`초 대기는 조준·실행 단계의 짧은 간격이며, 이를 전체 능력 재사용 대기시간으로 쓰면 안 된다.

### 피해·대상·이동 구조

- 캠페인 연결: `SOAThermalLanceExecute` → `SOAThermalLanceCP` → `SOAThermalLanceSearch/SearchWithModel` → `SOAThermalLanceDamage`.
- 협동전 연결: `SOAThermalLanceExecute` → `SOAThermalLanceSet` → `SOAThermalLanceCP` 및 `SOASolarLanceFireBeamInitialCP`.
- `SOAThermalLanceCP`는 위치 오프셋과 주기 효과를 이용해 경로를 따라 검색한다. **큰 원을 한 번에 전부 타격하는 구조가 아니다.**
- 직격 검색은 Ground로 한정되지 않는다. 공중·지상 적이 대상이 될 수 있다. 사망·숨김·무적 등 제외 필터는 실제 원본 검색을 따라 확인한다.
- `Marker.MatchFlags[Id]=1`, `noMarkers` 검증이 있다. 경로를 구성하는 여러 검색 지점에 같은 대상이 겹쳤다는 이유로 **한 광선의 피해 200을 검색 횟수만큼 반복 계산하면 안 된다.**
- 한 대상에 여러 광선 경로가 겹치는 경우와 한 광선 안에서 검색 지점이 겹치는 경우는 별개다. 광선 1줄 피해를 주기 피해로 바꾸거나 3줄 합을 무조건 모든 적에게 적용하지 않는다.
- 원본 검색 필터 중에는 Neutral을 명시적으로 제외하지 않는 항목도 있다. 이 모드의 아군·주민 보호 요구는 별도 대상 필터로 보장해야 한다.

## 3. 태양의 창 강화 — Solar Flare

협동전 원작 업그레이드 ID는 `SOASolarLanceUpgrade`, 영문 연구명은 **Solar Flare**다. 태양의 창의 경로에 불길을 남겨 추가 피해를 주는 강화다.

| 원본 요소 | 값·역할 |
|---|---|
| `SOASolarLanceFireBeamInitialCP` | 경로를 따라 불길 지속 효과를 생성. `HaveSOASolarLanceUpgrade` 검증 조건 있음 |
| `SOASolarLanceFireBeamCP` | `PeriodCount=40`, `PeriodicPeriodArray=0.5` |
| `SOASolarLanceFireBeamSearch` | **Ground** 대상 검색. 아군·중립·숨김·무적 등을 제외 |
| `SOASolarLanceFireBeamAB` | `SOASolarLanceFireBeam` 행동 부여 |
| `SOASolarLanceFireBeam` | 짧은 행동을 재적용하며 주기 피해 연결 |
| `ThermalLancesFireBeamDamage.Amount` | 캠페인 층 10 → 협동전 층 **15** |

원작 협동전 툴팁의 식은 `40 × 15 = 600` 추가 피해, `40 × 0.5 = 20`초다. 이는 **경로에 계속 머문 경우의 툴팁 기준 계산**이며 움직이는 적에게 600을 즉시 주는 효과가 아니다. 불길 피해는 지상 대상이다. 여러 불길 경로가 겹쳤을 때 무조건 배수로 중첩된다고 가정하지 않는다.

**모델을 강화형으로 바꾸는 것과 불길 효과를 구현하는 것은 별개다.** 원작 업그레이드는 모델뿐 아니라 업그레이드 판정·지속 효과·지상 검색·행동·주기 피해가 연결돼 있다.

## 4. 태양의 창의 실제 연출 연결

| 카탈로그 ID | 실제 파일/동작 |
|---|---|
| 모델 `SOA_SolarLance_Upgrade` | `Assets\Effects\Protoss\SOA_SolarLance_Upgrade\SOA_SolarLance_Upgrade.m3` |
| 모델 `SOA_SolarLance_Trail_Upgrade` | `Assets\Effects\Protoss\SOA_SolarLance_Trail_Upgrade\SOA_SolarLance_Trail_Upgrade.m3` |
| 액터 `SOAThermalLanceBeam` | 생성 시 `AnimBracketStart BSD Birth Stand Death`; 원본 CP 시작/종료에 맞춰 생성·종료 |
| 액터의 호스트 | `SOAThermalLanceImpactSite`에 붙어 이동. 검색 효과가 진행될 때 `MoverMove` 메시지 사용 |
| 협동전 모델 교체 | `HaveSOASolarLanceUpgrade` 판정 후 강화 모델로 `ModelSwap` |
| 불길 액터 `SOA_SolarLance_Trail_Upgrade` | `SOASolarLanceFireBeamCP` 시작/종료에 따라 생성·제거 |

강화 광선 모델의 원본 `ScaleMin/ScaleMax`는 **2.5,2.5,2.5**다. 파일 경로만 가져오고 원본 스케일·회전·호스트·애니메이션을 생략하면 크기와 방향이 달라질 수 있다. 불길 액터에는 별도 스케일도 있다.

`CreateModelAtPoint`로 정지 모델을 만들고 `AnimPlay Attack Attack`만 보내는 구현을 원작 연출과 같다고 설명하지 않는다. 해당 M3가 그 애니메이션 메시지로 정상 표시되는지는 별도 게임 확인이 필요하다.

## 5. 정화 광선 — 태양의 창과 다른 능력

정화 광선은 `SOAPurifierBeam` 능력이 `SOAPurifierBeamCU` 효과로 **`SOAPurifierBeamUnit` 유닛을 만드는 구조**다. 광선 유닛은 이동·표적 획득을 수행하고 주변 검색으로 지속 피해를 준다. 원본 툴팁도 수동 조종하지 않으면 자동으로 대상을 찾는다고 설명한다.

| 항목 | 확인한 기본 정의 |
|---|---|
| 능력 | `SOAPurifierBeam` |
| 생성 효과·유닛 | `SOAPurifierBeamCU` → `SOAPurifierBeamUnit` |
| 준비 행동 | `SOAPurifierBeamBuildUp`, 1.5초 뒤 발사 행동 연결 |
| 실제 발사 행동 | `SOAPurifierBeamFiring`, 지속 15초·주기 0.125초 |
| 피해 검색 | `SOAPurifierBeamSearch`, 기본 반경 3 |
| 주기 피해 | `SOAPurifierBeamDamage`, 기본 6.25 + 중장갑 추가 6.25 |
| 이동 속도 | `SOAPurifierBeamUnit.Speed=1.5` |
| 캠페인 재사용 대기 | 초기/사용 후 300초 |
| 협동전 덮어쓰기 | `Cooldown.TimeStart=450`, `TimeUse=360` |
| 기본 모델 | `Assets\Effects\Protoss\SOA_PurifierBeam\SOA_PurifierBeam.m3` |
| 협동전 강화 모델 | `Assets\Effects\Protoss\SOA_PurifierBeam_Upgrade\SOA_PurifierBeam_Upgrade.m3` |

이론상 기본 DPS는 `6.25 / 0.125 = 50`, 중장갑 상대는 100이다. 한 대상이 15초 내내 맞는 계산은 750 / 중장갑 1500이다. 여러 대상에게 광역으로 들어갈 수 있으며 대상이 범위를 벗어나면 그 대상이 전체 피해를 받는 것은 아니다.

협동전 업그레이드 `SOAPurifierBeamUpgrade`는 이동 속도에 **+3**, 발사 지속 시간에 **+5초**를 더한다. 이 정의를 적용한 계산은 속도 4.5·지속 20초이며, 마스터 힘·위신 등은 별도로 확인한다. 이 업그레이드를 태양의 창의 `SOASolarLanceUpgrade`와 바꾸어 연결하지 않는다.

능력 비용에 기본 Energy 항목은 보이지 않고 재사용 대기 항목이 있다. 태양의 창의 에너지 50을 정화 광선의 비용으로 복사하지 않는다. 이 원본 수치들을 모드의 최초 진입 연출에 그대로 강제할 필요는 없지만, 바꾸면 **모드 재설계 수치**로 기록해야 한다.

## 6. 이번 맵에 적용할 때 Claude가 알아야 하는 결론

사용자가 합의한 것은 **광선으로 남서쪽 적 기지를 정리하고 동맹이 진입하는 흐름**이다. 원작 수치를 사용자가 확정한 것은 아니다. “태양 광선”이라는 대화 명칭을 이유로 Solar Lance와 Purifier Beam을 임의로 같은 능력으로 합치지 않는다.

- 3개의 경로를 훑는 선제 타격을 원한다면 **태양의 창**의 효과·이동 액터 구조를 참고한다.
- 한 줄기의 굵은 광선이 움직이며 기지를 태우는 연출을 원한다면 **정화 광선**의 생성 유닛·이동·검색·발사 행동 구조가 해당한다. 이는 선택 후보 설명이며 사용자 동의 없이 능력을 교체하라는 지시가 아니다.
- 기존 모드의 `RM3_SolarDamage=250`, 12회·0.5초 간격·반경 20 전체 타격은 **자체 제작한 지역 정리 효과**다. 원작 Solar Lance 수치나 원작 Purifier Beam 효과로 설명하면 안 된다.
- 적 건물이 남으면 어떻게 할지, 건설 시작 조건·아군/주민 보호·시야·임무 목표/업적 영향을 따로 확인한다. 광선 모델을 바꾼 것만으로 이 문제가 해결되지는 않는다.

기존 구현의 시각·피해 범위 등 현황은 [진입 구현 인수인계](../HANDOFF_mission03_solar_lance.md)에 별도로 기록돼 있다. **원작 능력 설명은 이 조사 문서를 기준으로 한다.** 이번에는 조사 문서만 추가하며 코드·맵·ZIP을 수정하지 않는다.

## 7. 출처와 재확인 위치

원작 이름·설명:

- [공허 캠페인 영문 GameStrings](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/void.sc2campaign/enus.sc2data/LocalizedData/GameStrings.txt): `Button/Name/SOAThermalLance`, `Button/Tooltip/SOAThermalLance`, `Button/Tooltip/SOAPurifierBeam`.
- [협동전 영문 GameStrings](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/enus.sc2data/LocalizedData/GameStrings.txt): `ResearchSOASolarLanceUpgrade`, `SOAThermalLanceFireBeam` 및 불길 피해 계산식.

원작 능력·수치·연출:

- [공허 캠페인 AbilData](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/void.sc2campaign/base.sc2data/GameData/AbilData.xml), [EffectData](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/void.sc2campaign/base.sc2data/GameData/EffectData.xml), [BehaviorData](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/void.sc2campaign/base.sc2data/GameData/BehaviorData.xml), [ActorData](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/void.sc2campaign/base.sc2data/GameData/ActorData.xml).
- [협동전 AbilData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/AbilData.xml), [EffectData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/EffectData.xml), [BehaviorData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/BehaviorData.xml), [UpgradeData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/UpgradeData.xml), [ModelData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/ModelData.xml), [ActorData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/ActorData.xml).

여러 층이 합쳐지는 데이터다. 협동전 파일의 빈 정의를 피해 0으로 해석하거나, 공허 캠페인 재사용 대기시간을 협동전 값으로 그대로 인용하지 않는다. 주석 처리된 Upgrade EffectArray도 활성 효과로 집계하지 않는다. 마스터 힘·위신 적용 수치와 실제 게임 시간 환산은 이번 기본값 조사 범위 밖이다.
