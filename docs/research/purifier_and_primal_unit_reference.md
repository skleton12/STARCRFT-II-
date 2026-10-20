# 정화자·데하카 원시저그 구현 참고서

조사일: 2026-10-20 (한국 시간). **자료 조사와 Claude 인수인계이며 새 병력 편성 승인이나 맵 구현이 아니다.** 기준 배포는 0.4.41. 최신 인수인계 기록 `46d3ac6`의 영웅 전투복 제외도 반영했다. 원작 XML과 영어 툴팁을 대조했다. 실제 에디터·게임 실행은 하지 않았다.

## 먼저 고쳐 읽어야 하는 이름과 ID

| 기존 혼동 지점 | 확인한 구분 | 구현에 미치는 영향 |
|---|---|---|
| `FenixDragoon` = 일반 용기병 | 협동전 **피닉스 영웅의 태양 용기병 전투복** | 일반 양산 병력으로 쓰면 영웅 능력·자원 체계를 가져오게 된다. 10월 20일 최신 기록에서는 이미 제외했으므로 다시 일반 병력 후보로 넣지 않는다. |
| `FenixArbiter` = 일반 중재자 | 협동전 **피닉스 영웅의 사이브로스 중재자 전투복** | 일반 중재자는 다른 개체다. 10월 20일 최신 기록에서 이미 제외. 피닉스 전투복을 일반 공중 지원 유닛이라고 복사하지 않는다. |
| 피닉스 / Phoenix / Fenix | **피닉스(Fenix)**는 사령관 이름, **불사조(Phoenix)**는 비행 유닛 계열 | `PhoenixPurifier`는 정화자 **신기루(Mirage)**다. 피닉스 영웅이나 피닉스 사령관의 일반 생산 병력이 아니다. |
| `DehakaPrimalSwarmHost` = 원시 숙주 | **땅무지 숙주(Creeper Host)** | 원시 숙주는 `DehakaSwarmHost`; 소환하는 개체와 공격 방식이 다르다. |
| 원시 가시지옥이 없으니 잠복 공격 병력도 없다 | 데하카 협동전의 **관통촉수(Impaler), `ImpalerDehaka`**가 실제 존재 | 일반 가시지옥(Lurker)과 동일한 유닛이라고 부르지는 않되, 관통촉수는 별도 후보/원작 병력으로 인식한다. |
| 이름에 `Purifier`가 있어야 정화자 | `Immortal`, `Scout`, `Carrier` 등 공용 ID도 사령관 설정·액터로 정화자 병력이 된다 | 이름만 검색해 누락시키거나, 일반 유닛 외형만 복사하고 협동전 구현이 끝났다고 하면 안 된다. |
| `ZealotPurifier` = 사령관과 무관하게 같은 파수병 | 캠페인·카락스에서는 파수병, 피닉스에서는 **군단병**으로 바뀌는 공용 ID | `FenixCommander`가 표시 이름·생명력·보호막·비용·인구 등을 변경한다. 카락스 재구축과 피닉스 영웅 변환을 무심코 섞지 않는다. |
| `Level2`, `Level3` = 반드시 진급 유닛 | 데하카 ID의 역사적 접미사 | 정상 생산 원시 저글링/바퀴/히드라/울트라에도 `Level2`가 붙는다. 낮은 번호부터 쓰면 다른 정의를 고를 수 있다. |

위 구분은 **ID의 의미를 바로잡는 것**이다. 사용자가 확정한 레이너 해금→동맹 역할 대응을 임의로 취소하거나 새 영웅/생산 수를 승인한 것은 아니다.

## 출처와 읽는 방법

원본 게임 데이터 공개 미러 [SC2Mapster/SC2GameData](https://github.com/SC2Mapster/SC2GameData), 확인 스냅샷 `6dd323aae4209a01f110719a00b4e8f7a88389bc`를 사용했다. 협동전 `UnitData.xml`, `AbilData.xml`은 기존 조사 파일과 이 스냅샷 바이트가 같은지 확인했다.

- [협동전 UnitData](https://github.com/SC2Mapster/SC2GameData/blob/6dd323aae4209a01f110719a00b4e8f7a88389bc/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/UnitData.xml): 유닛, 능력·무기·명령창 연결.
- [협동전 AbilData](https://github.com/SC2Mapster/SC2GameData/blob/6dd323aae4209a01f110719a00b4e8f7a88389bc/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/AbilData.xml): 생산·합체·연구의 실제 결과 유닛.
- [협동전 UpgradeData](https://github.com/SC2Mapster/SC2GameData/blob/6dd323aae4209a01f110719a00b4e8f7a88389bc/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/UpgradeData.xml): `FenixCommander`, `KaraxCommander`, 연구 효과와 사령관 기본 보정.
- [공허 캠페인 UnitData](https://github.com/SC2Mapster/SC2GameData/blob/6dd323aae4209a01f110719a00b4e8f7a88389bc/campaigns/void.sc2campaign/base.sc2data/GameData/UnitData.xml): 캠페인 정화자 정의와 능력.
- [공허 캠페인 AbilData](https://github.com/SC2Mapster/SC2GameData/blob/6dd323aae4209a01f110719a00b4e8f7a88389bc/campaigns/void.sc2campaign/base.sc2data/GameData/AbilData.xml): 캠페인 생산 연결.
- 기계 판독용 [레이어별 유닛/연구 색인](data/ally_unit_reference_index.json): 63개 그룹별 유닛 항목과 연구 정의 후보 53개. 같은 유닛을 여러 진영에서 쓰면 중복 항목이 있다. **53개 모두를 현재 사용 가능한 연구라고 해석하지 않는다.** 데하카 건물/정화자 대의회의 실제 명령창 연결 여부를 별도 필드로 제공한다.

XML 레코드는 부모/다른 모드/캠페인/사령관 업그레이드가 합쳐져 실제 값이 된다. 단일 레코드의 체력·가격을 최종 협동전 수치라고 복사하지 않는다. 위신·마스터 힘·사령관 레벨이 적용된 수치도 기본값과 구분한다. 유닛 정의가 존재하는 것과 그 사령관이 생산할 수 있는 것은 별개다.

## 협동전 피닉스

### 일반 병력

| 유닛 | 실제 Unit ID | 생산 계통 | 역할·이식 시 핵심 |
|---|---|---|---|
| 군단병 / Legionnaire | `ZealotPurifier` + 피닉스 설정 | 관문·차원 관문 | 중장갑 근접 전열. `FenixCommander`가 이름을 `Unit/Name/ZealotFenix`로 바꾼다. 칼달리스의 몸체 계열. |
| 사도 / Adept | `AdeptFenix` | 관문·차원 관문 | 원거리 지상 공격. 사이오닉 투영 연구로 공격 시 그림자. 캠페인 사도나 일반 멀티 사도와 구분. |
| 보전기 / Conservator | `SentryFenix` | 관문·차원 관문 | 보호장으로 아군 지원, 위상 모드로 소환 지원. **동력기와 다른 유닛**. 위상형은 `SentryFenixPhasing`. |
| 불멸자 / Immortal | `Immortal` | 로봇공학 시설 | 지상 중장갑 대응. 탈다린 몸체 계열. 카락스의 그림자 포 연구를 피닉스 기본 능력으로 취급하지 않는다. |
| 거신 / Colossus | `ColossusPurifier` | 로봇공학 시설 | 지상 광역 화력. 전쟁인도자 몸체 계열. 카락스 화염 광선 연구와 분리. |
| 분열기 / Disruptor | `Disruptor` | 로봇공학 시설 | 정화 폭발 계열 광역 공격. 협동전 `FenixPurificationNova` 및 기본 공격 관련 보정 확인. 멀티플레이 분열기를 외형만 바꿔 대체하지 않는다. |
| 정찰기 / Scout | `Scout` | 우주관문 | 지상·공중 공격, 모조 몸체 계열. 공중/지상 사거리 연구 효과가 서로 다르다. |
| 우주모함 / Carrier | `Carrier` | 우주관문 | 요격기 운용, 클로라리온 몸체 계열. 요격기 생산/자동 운용 능력까지 가져와야 한다. |
| 관측선 / Observer | `Observer` | 로봇공학 시설 | 은폐 탐지·정찰. 전투 유닛 증원과 탐지 역할을 구분. |
| 탐사정 / Probe | `Probe` | 연결체 | 채취·건설. 정화자 외형과 사령관 건설 가능 목록은 별도 연결. |

피닉스의 일반 생산 병력에 **선동자·신기루·폭풍함·일반 용기병·일반 중재자**를 섞어 놓고 '원작 피닉스 병력'이라 부르지 않는다. 캠페인 정화자까지 섞는다면 모드 편성 변경임을 명시한다.

### 영웅 피닉스와 6용사

| 구분 | Unit ID | 의미 |
|---|---|---|
| 법무관 전투복 | `FenixCoop` | 피닉스 본체의 근접 전투복. 돌진·회전 공격 계열. |
| 태양 용기병 전투복 | `FenixDragoon` | 피닉스 본체의 원거리 전투복. `ChargedBuster`, `FenixDragoonArsenalOvercharge`, `FenixDragoonAirBomb`. |
| 사이브로스 중재자 전투복 | `FenixArbiter` | 피닉스 본체의 지원 전투복. `FenixArbiterStasisField`, `FenixArbiterCloakingField`, `ArbiterMPRecall`. |
| 칼달리스 / Kaldalis | `FenixKaldalisZealot` | 군단병 몸체, 강화된 근접 광역 공격. |
| 탈리스 / Talis | `FenixTalisAdept` | 사도 몸체, 도탄과 추가 피해 취약 효과. |
| 탈다린 / Taldarin | `FenixTaldarinImmortal` | 불멸자 몸체, 피해 축적·폭발과 적 집결 계열. |
| 전쟁인도자 / Warbringer | `FenixWarbringerColossus` | 거신 몸체, 정화 폭발 계열 특수 사격. |
| 모조 / Mojo | `FenixMojoScout` | 정찰기 몸체, 대공 광역 미사일·기절. |
| 클로라리온 / Clolarion | `FenixClolarionCarrier` | 우주모함 몸체, 별도 요격기·금제기 운용. |

세 전투복은 각각 일반 병력으로 무한 생산하는 세 종류가 아니다. 여섯 용사도 일반 병력의 외형 변형이 아니라 AI 인격 다운로드·몸체 승계·사망 처리 체계를 가진다. `FenixAltarOfPsiStormsResearch`의 Research1~6과 실제 대의회 명령창 연결을 확인했다. 유닛 ID만 생성해서 원작 승계 체계까지 구현됐다고 하지 않는다.

### 확인할 연구·기능 연결

| 대상 | 확인 ID | 구분 |
|---|---|---|
| 보전기 보호장 지속 강화 | `FenixSentryGuardianZoneUpgrade` | `CyberneticsCoreResearch,Research15` |
| 사도 그림자 생성 | `AdeptFenixShadeSpawn` | `TwilightCouncilResearch,Research27` |
| 정찰기 사거리 | `FenixScoutWeaponRange` | `FleetBeaconResearch,Research22`; 공중 +3, 지상 +1이라는 원문 툴팁 확인 |
| 칼달리스 강화 검 | `FenixKaldalisCleave` | 용사 전용; 일반 군단병 전체에 주는 연구가 아님 |
| 탈리스 약화 체계 | `FenixChampionTalisAdeptBounceShotUpgrade` | 용사 전용 |
| 탈다린 중력 과충전 | `FenixImmortalDetonationShot` | 용사 전용 |
| 전쟁인도자 정화 폭발 | `FenixWarbringerColossusPowerShot` | 용사 전용 |
| 모조 제압 절차 | `FenixChampionScoutAOEMissiles` | 용사 전용 |
| 클로라리온 금제기 | `FenixChampionCarrierBombers` | 용사 전용 |
| 영웅 무장 강화·중재자 탐지 | `FenixSuitAttackDamage`, `FenixArbiterDetection` | 영웅 전투복 전용, 일반 유닛 연구와 분리 |

전체 연구 비용표가 아니다. 원작 연구·기본 특성·용사 다운로드·전술 데이터망/보복 프로토콜 같은 사령관 특성을 서로 같은 유료 연구로 묶지 않는다.

## 협동전 카락스

| 유닛 | Unit ID | 특징·주의 |
|---|---|---|
| 파수병 / Sentinel | `ZealotPurifier` | 재구축으로 사망 후 복귀. `ZealotResearchReconstruction` 연구, 재사용 제한과 시체·부활 액터 연결 필요. 피닉스 군단병과 구분. |
| 동력기 / Energizer | `SentryPurifier` | 시간 광선으로 아군 공격·이동 지원, 위상 모드, 교화 연구. 보전기 보호장과 다름. |
| 불멸자 / Immortal | `Immortal` | 그림자 포 연구로 강한 단일 대상 사격. `ImmortalResearchShadowCannon` 및 실제 `ImmortalShakurasShadowCannon` 계열 연결 확인. |
| 거신 / Colossus | `ColossusPurifier` | 광역 지상 화력, 화염 광선 관련 강화. 같은 ID인 피닉스 거신의 사령관 보정과 구분. |
| 신기루 / Mirage | `PhoenixPurifier` | 공중 공격·중력자 광선·위상 장갑. 피닉스 사령관 이름과 혼동 금지. |
| 우주모함 / Carrier | `Carrier` | 요격기와 수리 비행정 연구. `CarrierRepairDrones`는 카락스 기능으로 구분. |
| 관측선·탐사정 | `Observer`, `Probe` | 탐지·채취·건설 보조. |

주요 연구: `ZealotResearchReconstruction`(재구축), `EnergizerReclamation`(교화), `KaraxEnergyRegenUpgrade`(동력기·보호막 충전소 재생), `ImmortalResearchShadowCannon`, `MiragePhaseArmor`, `CarrierRepairDrones`, `KaraxCarrierInterceptorLaunchSpeed`. 구조물 강화 `KaraxTurretRange`, `KaraxTurretAttackSpeed`는 병력 연구와 분리한다.

카락스의 재구축을 모든 정화자 유닛의 공통 부활로 확장하거나, 재구축 연구만 복사하고 `ZealotPurifierReviveCorpse`·행동·쿨다운·부활 효과 연결을 빼면 안 된다. 동력기의 교화는 단순 아군화 영구 전환과 같지 않으며 원작 지속·자폭 처리까지 확인한다. 수리 광선 등 사령관 패시브도 개별 유닛 능력과 분리한다.

## 공허의 유산 캠페인 정화자

| 캠페인 정화자 | Unit ID | 핵심 능력 | 협동전과의 관계 |
|---|---|---|---|
| 파수병 / Sentinel | `ZealotPurifier` | `ZealotPurifierReviveDeath`, 재구축 계열 | 카락스 파수병과 공용 ID지만 캠페인/협동전 연구·보정은 별개. |
| 선동자 / Instigator | `StalkerPurifier` | `BlinkMultiple` 연속 점멸 계열 | 캠페인 정화자. 피닉스·카락스 일반 생산 병력은 아님. |
| 동력기 / Energizer | `SentryPurifier` | `VoidSentryChronoBeam`, `VoidSentryPhasingMode` | 협동전 카락스에서 교화 등 추가 구성. |
| 거신 / Colossus | `ColossusPurifier` | `ColossusPurifierThermalLances` | 피닉스/카락스도 사용하지만 연구·피해·사령관 보정이 달라질 수 있음. |
| 신기루 / Mirage | `PhoenixPurifier` | 중력자 광선·위상 장갑 계열 | 협동전 카락스 병력에도 해당. |
| 폭풍함 / Tempest | `TempestPurifier` | `LightningBomb`, 지상·공중 무기 | 캠페인 정화자. 피닉스·카락스 일반 생산 목록에는 없음. |
| 탈란다르(피닉스) / Talandar | `FenixChampion` | `ThunderousCharge`, `FenixWhirlwind`, `VoidShieldCapacitor` | 캠페인 영웅. 협동전 전투복 `FenixCoop` 등과 별도 정의. |

분열기는 피닉스 협동전 병력에 포함하지만, 이번 확인만으로 공허 캠페인 전쟁 의회에서 선택하는 여섯 정화자 대체 병력 중 하나라고 추가하지 않는다. 시네마틱·시설·파괴 대상·미션 전용 `Purifier*` 이름도 정규 생산 병력과 구분한다.

현재 사용자 규칙은 협동전 피닉스·카락스 중심이다. 캠페인 정화자 자료를 조사했다는 이유만으로 선동자·폭풍함 등을 기존 동맹에 자동 편입하지 않는다. 새 해금표와 이 제한 사이의 선택은 사용자/구현 담당자가 명시적으로 정리한다.

## 협동전 데하카 원시저그

### 직접 생산과 원시 전투 결과

| 유닛 | 최종 Unit ID | 원작 획득 계통 | 역할 |
|---|---|---|---|
| 원시 저글링 | `DehakaZerglingLevel2` | 원시 감시자→저글링 알 | 근접 경량 병력, 원시 전투 재료. |
| 원시 바퀴 | `DehakaRoachLevel2` | 원시 감시자→바퀴 알 | 지상 원거리, 점화자/수호군주 계열 재료. `DehakaRoach`라고 추측하지 않는다. |
| 원시 히드라리스크 | `DehakaHydraliskLevel2` | 원시 감시자→히드라 알 | 지상·공중 원거리, 관통촉수/뮤탈리스크 계열 재료. |
| 원시 숙주 / Primal Host | `DehakaSwarmHost` | 원시 감시자→숙주 알 | 식충 운용. 잠복형 `DehakaSwarmHostBurrowed`. |
| 원시 울트라리스크 | `DehakaUltraliskLevel2` | 원시 감시자→울트라 알 | 중장갑 근접·돌진. 티라노조르 재료. |
| 라바사우르스 / Ravasaur | `DehakaRavasaur` | 저글링 2기 원시 전투 | 원거리 지상 공격, 사거리·중장갑 피해 연구. |
| 원시 점화자 / Primal Igniter | `DehakaRoachLevel3` | 바퀴 2기 원시 전투 | 근접 범위의 화염 공격, 경장갑 대응. |
| 관통촉수 / Impaler | `ImpalerDehaka` | 히드라 2기 원시 전투 | 잠복 후 지상 관통 공격. `ImpalerDehakaBurrowed`와 잠복 전환 필요. |
| 원시 뮤탈리스크 | `DehakaMutaliskLevel3` | 히드라 2기 원시 전투 | 지상·공중 공격, 이동 중 피해 감소·사망 복귀 등 연구. `DehakaMutalisk`/`Level2` 존재만으로 최종 생산형이라고 고르지 않는다. |
| 원시 수호군주 | `DehakaGuardian` | 바퀴 2기 원시 전투 | 장거리 지상 공격, 공격 속도 중첩·폭발 포자 연구. |
| 땅무지 숙주 / Creeper Host | `DehakaPrimalSwarmHost` | 원시 숙주 2기 원시 전투 | 자폭성 땅무지 운용. 원시 숙주의 식충과 다른 계통. |
| 티라노조르 / Tyrannozor | `DehakaUltraliskLevel3` | 울트라 2기 원시 전투 | 중장갑 전열, 가시 일제 사격·방어 지원 등 연구. |

`Level2/3`는 위 표에서 확인된 최종형의 ID 일부이지, 코랄의 후예와 같은 진급 시스템을 추가하라는 뜻이 아니다. 단순 UnitCreate로 완성형을 투입하는 것은 모드의 직접 소환 방식이며 원작 원시 전투를 재현한 것은 아니다.

### 생산·진화 경로를 확인하는 정확한 ID

`DehakaBarracksTrainEgg`는 완성 병력이 아닌 알을 생성한다.

| 생산 슬롯 | 알 | 알의 능력 | 최종 생산 결과 |
|---|---|---|---|
| Train1 | `DehakaTrainEggZergling` | `DehakaTrainEggMorphToZergling` | `DehakaZerglingLevel2` |
| Train2 | `DehakaTrainEggRoach` | `DehakaTrainEggMorphToRoach` | `DehakaRoachLevel2` |
| Train3 | `DehakaTrainEggHydralisk` | `DehakaTrainEggMorphToHydralisk` | `DehakaHydraliskLevel2` |
| Train4 | `DehakaTrainEggSwarmHost` | `DehakaTrainEggMorphToSwarmHost` | `DehakaSwarmHost` |
| Train5 | `DehakaTrainEggUltralisk` | `DehakaTrainEggMorphToUltralisk` | `DehakaUltraliskLevel2` |

원본 알 부화 능력에 비용이 들어 있다. 맵에서 알을 낳을 때 비용을 받도록 바꿨다면, 부화 비용을 그대로 남겨 **이중 지불**하게 하지 않는다. 충전 수·시작 충전·대기 시간도 별도 값이다. 지금 모드의 수정값과 원작 값을 구분한다.

원시 전투 능력: 저글링→라바사우르스 `PrimalZerglingRavasaurMerge`, 바퀴→점화자 `PrimalRoachLevel2Merge`, 히드라→관통촉수 `PrimalHydraliskImpalerMerge`, 히드라→뮤탈 `PrimalHydraliskToMutalisk`, 바퀴→수호군주 `PrimalRoachGuardianMerge`, 숙주→땅무지 숙주 `PrimalSwarmHostMerge`, 울트라→티라노조르 `PrimalUltraliskLevel2Merge`.

뮤탈리스크와 수호군주는 `DehakaMutaliskLevel3FightMorph`, `DehakaGuardianFightMorph`라는 전투/변태 중간형을 거친다. 중간형을 영구 전투 유닛으로 남기지 않는다. 원시 전투 유전자 돌연변이·확률·강화는 별도 행동/효과다. 합체 결과 유닛만 복사하면 원작 돌연변이 체계가 자동으로 생기지 않는다.

### 주요 연구와 실제 건물

다음은 **건물 명령창에 연결된** 항목을 기준으로 한 요약이다. 오래된 AbilData의 사용하지 않는 슬롯까지 새 연구라고 추가하지 않는다.

| 건물 | Unit ID / 연구 능력 | 확인한 연구 Upgrade ID |
|---|---|---|
| 글레빅의 굴 | `DehakaGlevigStructure` / `DehakaGlevigResearch` | `DehakaRoachMoveSpeed`, `DehakaGlevigRoachFireBreath`, `DehakaHydraliskSpeed`, `DehakaRavasaurRange`, `DehakaRavasaurVSArmor`, `DehakaImpalerTenderize` |
| 멀바르의 굴 | `DehakaMurvarStructure` / `DehakaMurvarResearch` | `DehakaMutaliskDamageReduction`, `DehakaMutaliskRespawnOnDeath`, `DehakaMutaliskAirDoubleDamage`, `DehakaGuardianFury`, `DehakaGuardianExplosiveBomb`, `DehakaMurvarCreeperAir` |
| 다크룬의 굴 | `DehakaDakrunStructure` / `DehakaDakrunResearch` | `DehakaUltraliskCrashingCharge`, `DehakaUltraliskRegen`, `DehakaUltraliskBash`, `DehakaTyrannozorArmorAura`, `DehakaTyrannozorFanOfKnives` |
| 원시 군락 | `DehakaHatchery` / `DehakaHatcheryResearch` | `DehakaPrimalWeaponsLevel1~3`, `DehakaPrimalArmorLevel1~3` |

위 이름 일부는 내부 역사 때문에 실제 대상과 다르다. 예를 들어 `DehakaGlevigRoachFireBreath`는 원시 점화자 연구다. 실제 효과의 대상·명령창·툴팁을 같이 보며 이름만 해석하지 않는다. 모든 ID를 각각 독립적인 영구 능력으로 처음부터 지급하지 않는다.

### 일꾼·방어 건물·영웅·패널 소환

| 종류 | ID | 구분 |
|---|---|---|
| 원시 일벌레 | `DehakaDrone` | 실제 건설/변태 능력과 연결. 일반 저그 일벌레의 외형 교체만으로 대체하지 않는다. |
| 원시 군락 | `DehakaHatchery` | 유닛 ID. **`DehakaHive`는 모델 ID**이며 유닛 ID 대체값이 아님. |
| 원시 감시자 | `DehakaBarracks` | 알 생산 건물. `DehakaBarracksUprooted`는 이동 상태. 건설 중 고치/완료/뿌리 들기 액터를 확인. |
| 원시 벌레 | `DehakaNydusDestroyer` | 영구 건설 방어·탐지 개체. 이동/공격/포탑 연결 확인. |
| 패널 거대 원시 벌레 | `DehakaNydusDestroyerTimedNoFood` | 제한 시간 소환형. 위 영구 건설 벌레와 별도. |
| 데하카 영웅 | `DehakaCoop` | 성장·정수·섭취·부활·능력 해금 체계. `Dehaka`, 캠페인 데하카나 `MutatorAmonDehaka`로 바꾸지 않는다. |
| 글레빅·멀바르·다크룬 | `DehakaGlevig`, `DehakaMurvar`, `DehakaDakrun` | 패널 무리 우두머리. 위 연구 건물과 같은 유닛이 아니며 일반 반복 생산 병력도 아니다. |

## 0.4.41 해금표에 대한 구현 전 검토

현재 CLAUDE.md에는 레이너 해금에 맞춘 동맹 유닛 표와 10월 20일 영웅 전투복 제외 수정이 기록돼 있다. 최신 기록은 GPT 조사 뒤 정화자 목록을 확정하고 그 전에는 구현하지 않는다고 명시한다. 다음은 역할 변경 요구가 아니라, 과거 표의 잘못된 ID 해석을 다시 사용하지 않기 위한 기술적 정정/결정 사항이다.

1. 과거 화염차→용기병의 `FenixDragoon`은 피닉스 영웅 전투복이다. **최신 기록에서 제외된 항목**이므로 복원하지 않는다.
2. 과거 토르→중재자의 `FenixArbiter`도 같은 이유로 **최신 기록에서 제외됐다.**
3. 바이킹→'피닉스'의 의미를 **불사조 계열 신기루**로 쓴 것인지 구분한다. `PhoenixPurifier`의 원작 명칭은 신기루이며 카락스/캠페인 병력이다.
4. 과학선/밤까마귀→폭풍함 `TempestPurifier`는 캠페인 정화자다. 협동전 피닉스·카락스만이라는 기존 제한과 조정이 필요하다. 이번 조사로 자동 승인하지 않는다.
5. 공성 전차→원시 숙주는 `DehakaSwarmHost`. `DehakaPrimalSwarmHost`를 사용하면 실제로는 땅무지 숙주가 된다.
6. 원시 가시지옥을 제외하더라도 **관통촉수 존재**와는 구분한다. 역할상 채택 여부는 사용자 편성 결정이다.
7. 불멸자·우주모함·정찰기는 공용 ID에 사령관 능력·모델 보정이 얹히므로, `*Purifier` 전용 Unit ID를 새로 만들어야만 가능한 것으로 단정하지 않는다.

## Claude용 이식 점검 순서

1. 먼저 캠페인/피닉스/카락스/데하카와 일반 병력/영웅/건물/알/중간형/투사체를 분류한다.
2. 생산 버튼→생산 능력→최종 유닛까지 확인한다. 유닛 이름 검색만으로 후보를 확정하지 않는다.
3. 유닛의 능력·무기·행동에서 효과·검증기·연구 요구조건까지 추적한다. 기본 공격, 연구 후 능력, 패널 특성을 분리한다.
4. 기본·원작 캠페인·협동전·사령관 Upgrade의 겹침을 확인한다. `FenixCommander` 전체를 켜면 경제/비용/이름/다른 유닛까지 바뀔 수 있으므로 현재 모드에 필요한 변화만 선택한다.
5. 액터·모델·투사체·이동자·포탑·언어·단축키·에셋을 함께 확인한다. 다른 실제 유닛 액터를 부모로 삼아 원래 유닛에 모델이 중복 생성되는 과거 실수를 반복하지 않는다.
6. 적도 같은 ID를 쓰면 동맹 소유에만 적용한다. 현재 모드의 `RM21_...`, `RM3_...` 복제 ID와 원작 ID를 구분한다.
7. 사령관 레벨 잠금을 제거하는 것과 진영/연구/생산 건물 조건을 모두 지우는 것은 다르다. 원시 전투·용사 다운로드·패널을 일반 무료 반복 생성으로 바꾸면 모드 변경이라고 기록한다.
8. 긍정 `CValidatorPlayerRequirement`의 `Find=1`, 검사 플레이어, 연구 완료 전/후 동작을 확인한다. 버튼 존재·XML 파싱 통과만으로 실제 연구 적용이 검증됐다고 쓰지 않는다.
9. 마지막으로 에디터/게임에서 생성·기본 공격·능력·연구 전후·생산 비용·사망/부활·AI가 직접 사용할 수 있는지를 검증한다. 이 문서는 그 게임 시험의 대체물이 아니다.

외형 추가 확인: 협동전 ModelData에서 `ScoutFenix` 모델은 `Assets\Units\Protoss\Scout_Purifier_Coop\Scout_Purifier_Coop.m3`를 참조한다. 모델 ID는 Unit ID `Scout`와 다르다. 영웅 모델 `FenixTaldarinImmortal`, `FenixClolarionCarrier`도 일반 병력 모델이라고 곧바로 대체하지 않는다. 다른 모델 경로는 최신 액터/스킨 층을 함께 확인한다.
