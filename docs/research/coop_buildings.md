# 협동전 건물 기준표 — Claude 구현·Codex 검사 공통 참고

작성: 2026-10-17. 대상은 이 프로젝트에서 사용하는 **피닉스·카락스·데하카**, 그리고 레이너 측 연구·용병 고용에 필요한 테란 건물이다. 모든 협동전 사령관의 전체 건물 목록은 아니다.

**이 문서는 원작 데이터 참고표다. 목록에 있다고 전부 이번 임무에 추가하라는 지시가 아니다.** 새 건물·영웅·패널 능력의 도입 여부는 임무 기획과 사용자 지시를 따른다. 구현은 Claude, 버전별 파일 검사는 Codex가 담당한다.

## 1. 반드시 구분할 것

- 동맹 진영 표시 이름: **정화자**, **원시저그**. 정화자 전투 병력은 협동전 **피닉스·카락스 소속만**, **피닉스 중심**이다.
- 건물 유닛 ID, 액터 ID, 모델 ID, 표시 이름은 서로 다르다. 모델을 바꿨다고 그 사령관의 생산·건설·연구 기능이 구현되는 것은 아니다.
- 피닉스·카락스는 `Nexus`, `Gateway` 등 공통 ID를 사용한다. 공통 ID를 찾았다는 이유만으로 해당 사령관의 협동전 건물 이식이 끝났다고 판단하지 않는다.
- 공유 카탈로그를 전역 수정하면 적·플레이어·다른 동맹도 바뀔 수 있다. 사령관별 생산·연구 연결을 분리하고 대상 플레이어를 확인한다.
- 캠페인 건물, 사령관 건물, 패널로 잠시 소환하는 건물은 구분한다. 같은 외형의 장식물·미사용 레거시 ID도 실제 건설 대상으로 취급하지 않는다.

## 2. 정화자 — 피닉스 중심

피닉스의 병력 생산은 군단병·사도·보전기, 불멸자·거신, 정찰기·우주모함 계열을 기준으로 실제 생산 능력을 확인한다. 영웅 AI는 해당 기본 병력과 별개의 연구·탑승 체계다. **선동자 `StalkerPurifier`를 피닉스 협동전 병력으로 분류하지 않는다.**

| 표시 이름 | 건물 유닛 ID | 원작 역할 | 구현 시 주의 |
|---|---|---|---|
| 연결체 | `Nexus` | 탐사정 생산·자원 반납·기지 운영 | 피닉스 사령관별 연결을 확인. 기본 연결체 생성만으로 사령관 AI가 시작되지는 않음 |
| 수정탑 | `Pylon` | 동력·보급 | 정화자 모델의 완성·건설·파괴 연출을 함께 확인 |
| 융화소 | `Assimilator` | 가스 채취 | 풍부한 가스 지점과 실제 건설 능력의 대응 확인 |
| 관문 | `Gateway` | 지상 병력 생산 | 일반 광전사·추적자 목록을 그대로 두지 않음. 군단병·사도·보전기의 실제 생산 ID/능력 확인 |
| 인공제어소 | `CyberneticsCore` | 공중 무기·장갑 등 기술 연구 | 원본 사령관의 연구 목록 및 선행 조건 확인 |
| 제련소 | `Forge` | 지상 무기·장갑·보호막 연구 | 다른 사령관용 연구 능력을 통째로 복사하지 않음 |
| 황혼 의회 | `TwilightCouncil` | 관문 병력 관련 연구 | 피닉스 병력 대상에 맞는지 확인 |
| 로봇공학 시설 | `RoboticsFacility` | 로봇 병력 생산 | 일반 캠페인 로봇 병력과 피닉스 병력 정의를 구분 |
| 로봇공학 지원소 | `RoboticsBay` | 로봇 병력 관련 연구 | 개별 무기·효과 ID까지 연결 |
| 우주관문 | `Stargate` | 정찰기·우주모함 계열 생산 | 다른 사령관의 불사조·공허 포격기 생산 목록을 섞지 않음 |
| 함대 신호소 | `FleetBeacon` | 공중 병력 관련 연구 | 피닉스 공중 병력 대상 확인 |
| 광자포 | `PhotonCannon` | 고정 방어·탐지 | 카락스 전용 건물 강화가 자동 적용된다고 가정하지 않음 |
| 정화자 대의회 / Purifier Conclave | `FenixAltarOfPsiStorms` | 용사 AI 연구 | 실제 연결은 `FenixAltarOfPsiStormsResearch`. 영웅 6종을 맵에 자동 지급하는 건물이 아님 |

정화자 대의회의 원본 연구 ID:

| AI 용사 | 연구 ID |
|---|---|
| 칼달리스 | `FenixChampionKaldalisZealot` |
| 탈리스 | `FenixChampionTalisAdept` |
| 모조 | `FenixChampionMojoScout` |
| 탈다린 | `FenixChampionTaldarinImmortal` |
| 전쟁인도자 | `FenixChampionWarbringerColossus` |
| 클로라리온 | `FenixChampionClolarionCarrier` |

`FenixAltarOfPsiStormsBroken`, `FenixAltarOfPsiStormsBrokenStage2`는 파괴·복구 관련 상태다. 처음 배치할 완성 건물과 혼동하지 않는다. `FenixAltarOfPsiStormsTrain`이라는 능력 ID가 있어도 실제 대의회 유닛의 `AbilArray`와 현재 생산 경로를 확인해야 한다.

## 3. 정화자 — 카락스 보조

연결체·수정탑·융화소·관문·인공제어소·제련소·황혼 의회·로봇공학 시설·로봇공학 지원소·우주관문·함대 신호소는 위 공통 ID를 사용하지만 **카락스 생산·연구 목록을 따로 확인**한다. 카락스 관문은 파수병·동력기, 우주관문은 신기루·우주모함 계열로 구분한다.

| 표시 이름 | 건물 유닛 ID | 원작 역할 | 구현 시 주의 |
|---|---|---|---|
| 태양 제련소 | `SolarForge` | 아둔의 창 관련 연구 | `SolarForgeResearch` 사용. 일반 `Forge`와 다른 건물 |
| 광자포 | `PhotonCannon` | 고정 방어·탐지 | 카락스 전용 강화·동력 조건은 별도 연결 |
| 케이다린 초석 | `KhaydarinMonolith` | 장거리 고정 방어 | `Monolith`나 제라툴 초석 ID로 바꾸지 않음 |
| 보호막 충전소 | `ShieldBattery` | 보호막 회복·방어 지원 | 카락스 관련 `ShieldBatteryStructureBarrier`와 그 요구 조건을 별도 확인 |

태양 제련소 원본 연구는 `SolarEfficiencyLevel1/2/3`, `SOARepairBeamExtraTarget`, `SOAOrbitalStrikeUpgrade`, `SOASolarLanceUpgrade`다. 원본 태양 에너지·사령관 레벨·패널 체계를 확인하지 않고 그대로 이식하면 잠긴 연구나 끊긴 효과가 남을 수 있다. 현재 맵의 최초 태양 광선 진입 연출을 원작 카락스 패널 전체 구현으로 표기하지 않는다.

수정탑의 `Pylon_Purifier_COOP.m3` 등은 **모델 파일 경로**다. 실제 유닛 ID가 `Pylon_Purifier_COOP`인 것으로 착각하지 않는다.

## 4. 원시저그 — 데하카 협동전

| 표시 이름 | 실제 건물 유닛 ID | 실제 주요 능력 | 역할·주의 |
|---|---|---|---|
| 원시 군락 / Primal Hive | `DehakaHatchery` | `DehakaHatcheryTrainEgg`, `DehakaHatcheryBuild`, `DehakaHatcheryResearch` | 일벌레 생산·기지 운영. 일반 `Hatchery`와 다른 유닛 |
| 원시 군락 이동 상태 | `DehakaHatcheryUprooted` | `DehakaHatcheryRoot` | 뿌리 들기/박기 상태. 완성 군락 대신 이동 상태를 배치하지 않음 |
| 원시 감시자 / Primal Warden | `DehakaBarracks` | `DehakaBarracksTrainEgg`, 관련 생산 연결 `DehakaBarracksTrain` | 원시 병력 생산. 이름이 Barracks라고 테란 병영으로 분류하지 않음 |
| 원시 감시자 이동 상태 | `DehakaBarracksUprooted` | `DehakaBarracksRoot` | 이동·뿌리 박기 상태 |
| 글레빅의 굴 / Glevig's Den | `DehakaGlevigStructure` | `DehakaGlevigResearch` | 바퀴·히드라 계열 선행 기술 및 연구 연결 확인 |
| 멀바르의 굴 / Murvar's Den | `DehakaMurvarStructure` | `DehakaMurvarResearch` | 군단 숙주 계열 선행 기술 및 연구 연결 확인 |
| 다크룬의 굴 / Dakrun's Den | `DehakaDakrunStructure` | `DehakaDakrunResearch` | 울트라리스크 계열 선행 기술 및 연구 연결 확인 |
| 원시 벌레 / Primal Wurm | `DehakaNydusDestroyer` | `NydusDestroyerDeepTunnel`, `NydusDestroyerBeam` | 건설형 방어 건물. 일반 땅굴벌레/수송망으로 대체하지 않음 |
| 거대 원시 벌레 / Greater Primal Wurm | `DehakaNydusDestroyerTimedNoFood` | `DehakaNydusDestroyerTopBar`에서 소환 | 패널에서 제한 시간 소환하는 버전. 지속 건설형과 구분 |
| 추출장 | `Extractor` | `DehakaHatcheryBuild`의 `Build1` | 공유 ID가 맞다. 존재하지 않는 `DehakaExtractor` ID를 임의 생성·참조하지 않음 |

중요한 연결:

- 건설 일꾼은 `DehakaDrone`, 건설 능력은 `DehakaDroneMorph`다. 일반 `Drone`의 `ZergBuild`에 원시 건물이 자동으로 생기지 않는다.
- `DehakaDroneMorph`의 `Build1~6`은 각각 원시 군락·원시 감시자·글레빅의 굴·멀바르의 굴·다크룬의 굴·원시 벌레를 가리킨다.
- 추출장은 확인한 데이터에서 **군락의 `DehakaHatcheryBuild`**가 건설한다. 일벌레 건설 목록에 보이지 않는다는 이유만으로 누락 판정을 내리지 않는다.
- 군락의 일벌레 생산은 `DehakaTrainEggDrone` 등을 거치는 원시 알 경로다. 일반 부화장의 애벌레·대군주 체계를 데하카 체계로 간주하지 않는다.
- 원시 감시자 생산도 `DehakaTrainEggZergling/Roach/Hydralisk` 등의 알·변태 경로를 함께 확인한다. `DehakaBarracksTrain`만 유닛에 붙이면 원작 알 생산이 완성되는 것이 아니다.
- 실제 확인한 지상 생산 ID는 `DehakaZerglingLevel2`, `DehakaRoachLevel2`, `DehakaHydraliskLevel2`다. 예전 `DehakaRoach` 등 레거시 정의와 혼동하지 않는다.
- 원시 결투·합체, 우두머리 소환, 영웅 부활과 사령관 성장 체계는 별도 기능이다. 건물 ID를 참고했다는 이유로 자동 추가하지 않는다.

### 가장 혼동하기 쉬운 ID

| 구분 | ID | 판정 |
|---|---|---|
| 원시 군락 유닛 | `DehakaHatchery` | 건물 생성·건설·재건 대상으로 사용 |
| 원시 군락 모델 | `DehakaHive` | 모델 카탈로그 ID. 건물 유닛으로 생성하면 안 됨 |
| 일반 저그 부화장 | `Hatchery` | 외형만 바꿔도 데하카 군락의 기능이 되지 않음 |
| 일반 산란못 | `SpawningPool` | 데하카 원시 감시자의 대체물이 아님 |
| 일반 바퀴 소굴 | `RoachWarren` | 글레빅의 굴이나 원시 병력 생산 체계의 대체물이 아님 |

## 5. 레이너 측 — 이 프로젝트에서 필요한 테란 건물

| 표시 이름 | 원본 유닛 ID | 범위 |
|---|---|---|
| 병영 | `Barracks` | 해병 역할 용병 생산. 현재 병영의 전쟁광 생산과 고용소의 코랄의 후예 고용은 구분 |
| 병영 기술실 | `BarracksTechLab` | 해병 자극제 단계·추가 연구. 사령관별 원본 연구와 모드 재설계 구분 |
| 공학 연구소 | `EngineeringBay` | 보병 무기/장갑, 보급 벙커 건설 해금, 건물 장갑 계획 |
| 벙커 | `Bunker` | 기본 벙커. 보급 벙커로 전역 교체하지 않음 |
| 멩스크 보급 벙커 | `BunkerDepotMengsk` | 원본은 보급 12·수용 공간 6·광물 100. 원본 탑승 대상 제한 등도 확인 |
| 용병 고용소 | `MercCompound` | `SummonMercenaries`로 **코랄의 후예 4기 유료 고용** 연결 |

멩스크 원본 보급 벙커의 수송 능력은 `BunkerMengskTransport`다. 원작 멩스크 부대원/인부 제한을 그대로 복사하면 전쟁광·코랄의 후예가 탑승하지 못할 수 있다. 모드 대상 병력에 맞춰 검증자를 검토하고, 제한을 바꿨다면 원작 그대로가 아닌 수정 이식임을 기록한다.

히페리온 무기고·연구실에서 **캠페인 자금으로 구매하는 항목은 새 미션 내 연구에서 제외**한다. 관련 계획은 [3번 맵 연구 계획](https://github.com/skleton12/STARCRFT-II-/blob/codex/ccm-0.3.1/docs/missions/03_upgrade_plan.md)를 참고한다.

## 6. 현재 0.3.1과 원작의 차이 — 수정할 때 숨기지 말 것

기준 ZIP: `codex/ccm-0.3.1`의 `releases/RaynorMercs_WoL_CCM.zip`. 이 문서를 추가하면서 ZIP이나 코드를 변경하지 않았다.

| 항목 | 0.3.1 상태 | 원작 구현으로 보아도 되는가 |
|---|---|---|
| 정화자 초기 기지 | `Pylon`·`Nexus`·`Gateway`, 초기에는 스크립트가 건설 진행률을 처리 | 피닉스/카락스 생산·연구 전체 이식 완료는 아님 |
| 원시저그 일꾼 | 일반 `Drone` | 데하카 일벌레 이식이 아님 |
| 원시저그 본진 | 일반 `Hatchery`에 `RM3_PrimalHallModel` 외형을 적용 | `DehakaHatchery` 기능 이식이 아님 |
| 원시저그 생산 건물 | 일반 `SpawningPool` | `DehakaBarracks` 이식이 아님 |
| 원시저그 병력 | 데하카의 실제 병력 ID를 스크립트로 반복 투하 | 원작 건물의 알 생산·진화 체계와는 별개 |
| 보급 벙커 | 모드 ID `RM3_SupplyBunker`, 멩스크 모델·보급·수용 공간을 일반 벙커 기반에 연결 | 원본 `BunkerDepotMengsk` 전체 이식은 아님 |
| 태양 광선 진입 | 모드 효과·모델을 사용한 최초 지역 공격 | 카락스 패널/태양 에너지 전체 구현은 아님 |

사용자의 최신 피닉스 중심 병력 규칙에 맞춘 재편도 필요하다. 0.3.1의 파수병·선동자·동력기를 전부 피닉스 협동전 유닛이라고 보고하지 않는다.

## 7. 버전별 확인 절차

1. **유닛 → 건설 능력 → 생성 건물**의 연결을 확인한다. 일꾼 명령 카드의 `AbilCmd`가 실제 건설 능력과 맞아야 한다.
2. **건물 → 생산 능력 → 알/변태 → 최종 유닛**을 끝까지 확인한다. 모델만 나오고 기능이 없거나 레거시 유닛을 생산하면 실패다.
3. **연구 버튼 → 연구 능력 → 요구 조건 → 업그레이드 → 실제 대상**을 확인한다. 해금되지 않는 사령관 레벨·마스터 힘·영웅 조건이 남았는지 검사한다.
4. 완성·건설·파괴·뿌리 들기 등 액터 상태에 필요한 모델·효과·음성 링크를 확인한다. 유닛 ID와 모델 ID를 혼동하지 않는다.
5. 생산·건설·AI 재건에 같은 대응표를 사용한다. 재건한 건물로 지원 조건의 유닛 핸들도 갱신해야 한다.
6. 피닉스·카락스 공유 건물의 생산 목록에 추적자·다른 사령관 병력이 섞이지 않았는지 확인한다.
7. 일반 `Probe`/`Pylon` 등의 협동전 정의 전체를 복사하지 않는다. 원본에는 제라툴 건설·돌연변이·다른 사령관 연결도 섞여 있어 필요한 부분만 이식한다.
8. ZIP CRC·XML·참조 검사를 통과해도 게임 성공으로 보고하지 않는다. 실제 게임에서 건설·채취·생산·연구·재건·길찾기를 따로 확인한다.

3번 맵의 원본 슬롯 8·9는 타우렌·주민이다. 0.3.1의 동맹 슬롯 10·11을 이유 없이 8·9로 되돌리지 않는다. 맵을 편집기로 저장하면 수작업 `mapscript.galaxy`가 재생성될 수 있으므로 저장 금지 규칙을 지킨다.

## 8. 확인 출처

- [SC2GameData — 협동전 UnitData.xml](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/UnitData.xml)
- [SC2GameData — 협동전 AbilData.xml](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/AbilData.xml)
- [SC2GameData — 공허 캠페인 UnitData.xml](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/void.sc2campaign/base.sc2data/GameData/UnitData.xml)
- [SC2GameData — 멩스크 UnitData.xml](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/commanders/arcturusmengsk.sc2mod/base.sc2data/GameData/UnitData.xml)
- [SC2GameData — 멩스크 AbilData.xml](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/commanders/arcturusmengsk.sc2mod/base.sc2data/GameData/AbilData.xml)
- [SC2GameData — 협동전 영문 이름](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/enus.sc2data/LocalizedData/GameStrings.txt)

위 XML을 로컬에 확보해 유닛·건설·생산·연구 연결을 대조했다. 원본 데이터는 여러 의존성 층이 합쳐져 동작하므로 한 파일에 속성이 없다는 이유로 능력이 없다고 단정하지 않는다. 표의 공통 프로토스 건물 ID는 해당 사령관의 세부 설정 전체를 확인했다는 뜻이 아니다. 실제 게임 실행·에셋 표시 검증은 미실행이다.
