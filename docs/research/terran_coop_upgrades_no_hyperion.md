# 테란 협동전 업그레이드 — 히페리온 구매 항목 제외

2026-10-19 조사. 기존 사용자 조사 범위인 **감염된 테란 제외 테란**: 레이너·스완·노바·한과 호너·멩스크·타이커스다. 프로토스·저그 전체 사령관 목록은 아니다. 일반 미션 내 광물·가스 연구와 타이커스 장비를 구분한다. 사령관 레벨 특성·마스터 힘·위신·근위대 진급을 미션 내 유료 연구로 나열하지 않는다.

한국어명에는 효과를 드러내는 설명용 표기가 포함돼 있으므로 구현에서는 원본 ID를 기준으로 한다.

**히페리온 무기고·연구실의 기존 구매 효과는 제외한다.** 이름은 같지만 협동전 추가 효과가 있는 항목은 ★로 표시해 차이 비교 대상으로 남겼다. ★는 같은 효과를 재구매시키라는 뜻이 아니다. 이 문서의 목록을 모드 구현 확정으로 간주하지 않는다.

## 일반 무기·장갑 연구

| 구분 | 단계·적용 범위 |
|---|---|
| 일반 보병 무기·장갑 | 허용되는 사령관의 1~3단계. 사령관별 실제 대상 확인 |
| 차량·함선 무기·장갑 | 허용되는 사령관의 1~3단계. 통합/분리 연구와 대상 확인 |
| 한과 호너 무기·장갑 | 별도 HH 계열 1~3단계 |
| 멩스크 부대원 무기·장갑 | 부대원 계열 1~3단계. 근위대 진급과 별개 |
| 타이커스 무법자 무기·장갑 | 각각 1~5단계 |
| 테란 건물 장갑 | 허용되는 일반 테란 구조물 대상. 멩스크 신소재 강철 장갑과 다른 업그레이드 |

사령관 레벨에 따라 무기·장갑 연구가 체력/공격 속도까지 올리는 특성은 원작 레벨 특성으로 따로 관리한다. 연구 효과와 특성 해금을 중복 구매시키지 않는다. 일반 Level4 레거시 정의가 있다는 이유로 모든 사령관에게 4단계를 추가하지 않는다.

## 레이너

| 대상 | 연구·장착 | 효과 | 실제 ID |
|---|---|---|---|
| 의무관 | 전투 안정제 ★ | 기계 치료·치료 대상 피해 감소 등 협동전 추가 효과. 자날 구매 효과와 구분 | `StabilizerMedPacks` |
| 화염방사병 | 철인 장갑 ★ | 협동전의 체력 +100 추가분. 기존 장갑 +2를 재구매시키지 않음 | `FirebatJuggernautPlating` |
| 공성 전차 | 고급 공성 기술 | 변신 시간 감소·공성 모드 장갑 +3 | `RaynorImprovedSiegeMode` |
| 밴시 | 은폐장 | 은폐 사용. 레이너 은폐 사거리 보너스는 사령관 조건과 구분 | `BansheeCloak` |
| 전투순양함 | 무기 재장착 | 야마토 포 사용 해금 | `BattlecruiserEnableSpecializations` |
| 차량·함선 | 연소 장치 | 일시 이동 속도 증가 능력 | `VehicleAfterburners` |

## 스완

| 대상 | 연구·장착 | 효과 | 실제 ID |
|---|---|---|---|
| 화염기갑병·화염차 | 지옥불 조기점화기 ★ | 화염기갑병 모드 적용분 등 자날 구매 효과와 대상 차이를 비교 | `HighCapacityBarrels` |
| 화염기갑병·화염차 | 지옥불 장갑 | 방어력 +2 | `HellbatHellArmor` |
| 사이클론 | 목표물 고정 사거리 | 목표물 고정 사거리 +3 | `CycloneLockOnRangeUpgrade` |
| 사이클론 | 자기장 가속기 | 목표물 고정 피해 증가 | `CycloneLockOnDamageUpgrade` |
| 망령 | 토마호크 전지 | 초기 에너지 증가 | `DynamicPowerRouting` |
| 망령 | 변위장 | 은폐 중 회피·이동 성능 향상 | `CloakDistortionField` |
| 망령 | 파동 증폭기 | 이동 중 공격 피해 증가 | `WraithImprovedBurstLaser` |
| 과학선 | 방어막 | 아군에게 피해 흡수막 부여 | `ScienceVesselResearchDefensiveMatrix` |
| 과학선 | 향상된 나노 수리 | 나노 수리 에너지 소모 제거 | `ScienceVesselFreeRepair` |
| 차량·함선 | 고급 조준경 | 무기 사거리 +1 | `SwannCommanderVehicleWeaponRange` |
| 차량·함선 | 재생성 생물강철 ★ | 자날 연구실의 약 0.6015/초와 협동전 2/초 회복 차이 비교 | `RegenerativeBioSteel` |
| 방어 포탑 | 정밀 보안 자동추적 ★ | 자날 미사일 포탑 구매 효과 밖의 적용 대상 확장분 비교 | `HiSecAutoTracking` |
| 방어 포탑 | KMC 자동장전기 | 포탑 공격 속도 +25% | `SwannTurretIncreasedAttackSpeed` |
| 레이저 천공기 | 천공기 2단계 | 천공기 강화·집중 광선 해금 연결 | `DrakkenLaserDrillBFG` |
| 레이저 천공기 | 천공기 3단계 | 천공기 강화·파동포 해금 연결 | `DrakkenLaserDrillNuke` |

## 노바

| 대상 | 연구·장착 | 효과 | 실제 ID |
|---|---|---|---|
| 정예 해병 | 초 전투 자극제 | 공격·이동 속도 증가와 체력 회복 | `MarineSuperStim` |
| 정예 해병 | 레이저 조준 시스템 | 시야 +2·사거리 +1 | `LaserTargetingSystemNova` |
| 불곰 특공대 | 자기 가속 탄약 | 주기적인 추가 무기 공격 | `MarauderMagrailMunitions` |
| 불곰 특공대 | 억제탄 ★ | 기존 충격탄 이동 감속과 구분되는 공격 속도 감속 등 추가 효과 | `NovaConcussiveShells` |
| 특수 작전 유령 | EMP 탄환 | 보호막·에너지 피해 및 은폐 드러내기 | `GhostBlackOpsEMP` |
| 특수 작전 유령 | 삼연발 사격 | 저격 시 추가 2발 | `GhostBlackOpsTripleTap` |
| 화염기갑 특전병 | 지옥불 조기점화기 ★ | 노바 전용 경장갑 추가 피해. 자날 기본 구매 효과와 차이 비교 | `HighCapacityBarrels` |
| 화염기갑 특전병 | 도약 추진 공격 | 도약 공격·충격 기절·장갑 강화 | `HellbatJumpJetAssault` |
| 타격 골리앗 | 잠금 미사일 | 대공 공격으로 기계 기절·탐지 무력화 | `NovaUnitLockdown` |
| 중장갑 공성 전차 | 점진적 사거리 증가 | 공성 모드 유지 시 사거리 단계 증가 | `SiegeTankSiegeModeProgressiveRangeIncease` |
| 중장갑 공성 전차 | 거미 지뢰 | 전차가 거미 지뢰 설치 | `DeploySpiderMines` |
| 습격 해방선 | 지능형 제어장치 | 모드 전환 가속 | `MultiTaskMAFServosLiberator` |
| 습격 해방선 | 습격포 | 수호기 모드로 구조물 공격 | `LiberatorStructureAttack` |
| 비밀 밴시 | 첨단 은폐장 | 영구 은폐 | `BansheePermaCloak` |
| 비밀 밴시 | 로켓 포화 | 지정 지역 지상 폭격 | `BansheeAirstrike` |
| 밤까마귀 타입-II | 비밀 치료 | 치료 강화·치료 대상 은폐 | `HealingDroneCloakHealBeam` |
| 밤까마귀 타입-II | 향상된 제조 | 각 능력 최대 3회 충전 | `RavenSuperScience` |
| 노바 영웅 | 유령 조준경 | 탐지 능력 부여 | `NovaDetector` |
| 노바 영웅 | 작전 효율 | 저격으로 처치 시 에너지 일부 환급 | `NovaSnipeRefund` |
| 노바 영웅 | 지옥불 투사체 | 관통 산탄 사거리 +2 | `NovaShotgunBlastRange` |
| 노바 영웅 | 카두세우스 반응로 | 체력 재생 증가 | `NovaLifeRegen` |

## 한과 호너

| 대상 | 연구·장착 | 효과 | 실제 ID |
|---|---|---|---|
| 사신 | 제트 추진기 과부하 | 이동 가속·일시 비행 및 대공 공격 | `HHReaperFlight` |
| 사신 | LE9 집속탄 | KD8 재사용 감소·사망 시 수류탄 투척 | `HHReaperG4ClusterBombs` |
| 화염차 | 분무형 자극제 | 사망 시 주변 아군 자극·변신 가속 | `HHHellionStimDeath` |
| 화염차 | 타르 폭탄 | 지역 감속·공격 사거리 감소 | `HHHellionRocket` |
| 화염기갑병 | 야생 화염 폭발물 | 이동 향상·사망 시 공포 불길 | `HHHellionFearDeath` |
| 화염기갑병 | 연소성 액체 | 공격에 지속 화염 피해 추가 | `HHHellionAttackDoT` |
| 땅거미 지뢰 | 집행자 미사일 | 미사일 재사용 감소·사망 시 추가 미사일 발사 | `HHWidowMineDeathBlossom` |
| 땅거미 지뢰 | 암시장 발사기 | 사거리 증가·잠복 전환 가속 | `HHWidowMineBurrowedRange` |
| 아스테리아 망령 | 방아쇠 조절 | 공격할수록 공격 속도 증가 | `HHWraithFury` |
| 아스테리아 망령 | 미등록 은폐 시스템 | 영구 은폐 | `HHWraithPermaCloak` |
| 데이모스 바이킹 | W.I.L.D. 미사일 | 전투기 모드 추가 미사일 | `HHVikingRockets` |
| 데이모스 바이킹 | 분쇄탄 | 돌격 모드 관통 공격·변신 가속 | `HHVikingPiercingAttacks` |
| 테이아 밤까마귀 | 다중 스레드 센서 | 여러 대상에 동시 목표 고정 | `HHMultiLock` |
| 호너 함선 | 전술 차원 도약 | 망령·바이킹·밤까마귀 도약 해금 | `FleetwideJump` |
| 군주 전투순양함 | 과충전 반응로 | 강력한 입자포 공격 모드 해금 | `HHBattlecruiserYamatoAttacks` |
| 타격 전투기 플랫폼 | 네이팜 탄두 | 정밀 타격 지역에 지속 화염 | `HHBomberNapalm` |
| 강습 갈레온 | 강습 비행정 격납고 설치 | 공중·지상 공격 드론 생산. 개별 함선 장착이며 CUpgrade 연구와 구분 | `HHMercStarportHangar/Ammo2` |

## 멩스크

| 대상 | 연구·장착 | 효과 | 실제 ID |
|---|---|---|---|
| 부대원·인부 | 궤도 부대원 투하 | 징병소 집결 지점에 직접 투하 생산 | `TrooperMengskDropTrain` |
| 보급 벙커·미사일 포탑·대지파괴 포 | 신소재 강철 장갑 | 체력 +200·방어력 +2 | `MengskStructureArmor` |
| 보급 벙커 | 조준 보조 총안 | 탑승 병력 사거리 +1 | `BunkerDepotMengskRange` |
| 대지파괴 포 | 반구형 가속제 | 포격 사거리 +25 | `ArtilleryMengskRange` |
| 중재선·충격 전차 | 무장 안정기 | 수송 중인 공성 전차가 공중 사격 | `MedivacMengskSiegeTankAirlift` |
| 검은망치 | 방벽장 | 주변 아군 지상 병력 장갑 강화 | `ThorMengskArmorAura` |
| 충격 전차·검은망치·창공의 분노 | 지능형 제어장치 | 모드 전환 가속 | `MechTransformationSpeedMengsk` |
| 중재선 | 이중 소생기 | 동시 2대상 치료 | `MedivacMengskDoubleHealBeam` |
| 중재선 | 산란 장막 | 영구 은폐·피해 흡수 보호막 | `MedivacMengskPermanentCloak` |
| 증인 | 증폭 전파 | 세뇌 영향 부대원·인부의 지지 생성 증가 | `BlimpMengskTopbarRegen` |
| 창공의 분노 | 아스가르드 추진기 | 이동 속도 증가 | `VikingMengskSpeed` |
| 아우구스트그라드의 자랑 | 현장 지원 조준 시스템 | 주변 원거리 지상 병력 사거리 강화 | `BattlecruiserMengskRangeAura` |
| 황제의 그림자 | 황제의 전술 미사일 | 전술 미사일 타격 정신 집중 제거 | `GhostMengskGuidedStrike` |

## 타이커스 일반 연구

| 대상 | 연구·장착 | 효과 | 실제 ID |
|---|---|---|---|
| 타이커스·비뚤어진 샘·시리우스 | ITC-E 방아쇠 | 공격 속도 +25% | `TychusSquadAttackSpeed` |
| 블레이즈·대포알·방울뱀 | 지구력 보충제 | 해당 무법자 최대 체력 증가 | `TychusSquadHealth` |
| 베가·넉스·니카라 | 탐지 조준경 | 해당 무법자 탐지 능력 부여 | `TychusSquadDetection` |
| 오딘 | 커다란 빨간색 버튼 | 포격을 핵 공격으로 교체 | `TychusOdinRedButton` |

## 타이커스 장비 36개 — 건물 연구와 분리

원본 `CommanderTychus.xml`의 `TychusHeroResearch`·`TychusHeroResearch2`와 무기고/유령 사관학교/고용소 명령 카드를 대조했다. 영문 장비명을 함께 적어 임의 한국어 번역명과 혼동하지 않도록 했다. 장비·궁극 장비는 사령관 해금/선행 장비 요구 조건이 있을 수 있다.

| 무법자 | 원문 장비명 | 효과 요약 | 실제 ID |
|---|---|---|---|
| 방울뱀 | Secret Stash Stimpack | 자체 자극제·체력 회복 | `TychusMarauderSuperStim` |
| 방울뱀 | Umojan Signal Modulator | 활력 장치 치료 강화 | `TychusMarauderHealingWardBuff` |
| 방울뱀 | Moebius Aggression Blend | 활력 장치 범위 아군 공격 속도 증가 | `TychusMarauderHealingWardSpeedBuff` |
| 방울뱀 | Hammer Munitions | 공격 광역화·감속 | `TychusMarauderAttackSplash` |
| 대포알 | X-71 Impact Boots | 강력한 충격 범위·기절 강화 | `TychusHercGrappleStun` |
| 대포알 | Critical Response System | 치명상 시 체력 회복·일시 무적 | `TychusHercGrappleArmor` |
| 대포알 | Redline Power Cells | 공격할수록 공격력·공격 속도 증가 | `TychusHercRage` |
| 대포알 | M.A.L.I.C.E. Ammunition | 확률적 치명타 | `TychusHercCrit` |
| 블레이즈 | High Capacity Containers | 기름 유출 범위 증가 | `TychusFirebatPremiumPetroleum` |
| 블레이즈 | Hades Oil | 경장갑 상대 불붙은 피해 증가 | `TychusFirebatBlueFlameOil` |
| 블레이즈 | Wildflame Fuel Additives | 불붙은 적 사망 시 화염 전파 | `TychusFirebatIncendiaryPetroleum` |
| 블레이즈 | XCMC-670 Combat Suit | 개별 피격 피해 상한 적용 | `TychusFirebatShield` |
| 베가 | Neural Disruption Device | 정신 지배 주변 적 혼란 | `TychusGhostDominatingDomination` |
| 베가 | Moebius Psionic Motivator | 지배 대상 회복·공격 속도 강화 | `TychusGhostDominateBuff` |
| 베가 | Type-88 Persuader | 정신 지배 지속 증가 | `TychusGhostConcentrationHelmet` |
| 베가 | Psi Projector | 공중 적을 지상으로 끌어내림 | `TychusGhostPsychicSnare` |
| 넉스 | T4 Cloudburst Shells | 초음파 파동 피해 증가 | `TychusSpectreSuperUltrasonicPulse` |
| 넉스 | Crystalline Amplifiers | 초음파 파동 지속 증가 | `TychusSpectreExtendedPulseGun` |
| 넉스 | Ultrasonic Boosters | 초음파 파동 범위 증가 | `TychusSpectreVisionSuit` |
| 넉스 | N3 Networking | 주변 무법자 주요 능력 충전·재사용 감소 | `TychusSpectreBrillianceAura` |
| 니카라 중위 | Umojan Repair Nanites | 회복 폭발 치료 강화 | `TychusMedicAdvancedHealingSpray` |
| 니카라 중위 | Procyon Twin Heal Beam Gauntlet | 동시 두 대상 치료 | `TychusMedicDoubleBeam` |
| 니카라 중위 | Procyon Serum | 일반 치료량 강화 | `TychusMedicSuperHealing` |
| 니카라 중위 | XM-77 Matrix Generator | 피해 흡수 보호막 | `TychusMedicDefensiveMatrix` |
| 타이커스 | KD9a Implosion Core | 분쇄 수류탄 끌어당김·기절 | `TychusACImplosionGrenades` |
| 타이커스 | Kel-Morian Ripper Rounds | 기본 공격으로 적 장갑 감소 | `TychusACPiercingRounds` |
| 타이커스 | Vanadium Shell | 분쇄 수류탄 피해 증가 | `TychusACRageGrenades` |
| 타이커스 | SureShot Networked Helmet | 주변 무법자 수에 따른 무기 피해 증가 | `TychusACBandofBrothers` |
| 비뚤어진 샘 | LarsCorp G7 Charges | 폭발물 피해 증가 | `TychusReaperBombDamage` |
| 비뚤어진 샘 | Enhanced Hostilities Kit | 기본 공격 시 폭발물 충전 가속 | `TychusReaperBombCharges` |
| 비뚤어진 샘 | Moebius Restraint Matrix | 폭발물 대상 기절·탐지 무력화 | `TychusReaperBombStun` |
| 비뚤어진 샘 | Procyon Shade Suit | 피격 시 일시 피해 회피·이동 증가 | `TychusReaperEvasionBuff` |
| 시리우스 | Umojan Turret Frame | 포탑 체력·피해 증가 | `TychusWarhoundTurretUpgrade` |
| 시리우스 | Moebius M34 Terror Rounds | 본체·포탑 공격에 확률적 공포 | `TychusWarhoundFear` |
| 시리우스 | SA-55 Thunderbolt Missiles | 본체·포탑 대공 미사일 | `TychusWarhoundHaywireMissiles` |
| 시리우스 | D99 Detonator | 본체·포탑 사망 시 폭발 | `TychusWarhoundDeathExplosion` |

## 제외하거나 별도 취급한 것

- 전투 방패·일반 전투 자극제, 화염방사병 화염 증폭/장갑 기본분, 일반 불곰 충격탄, 시체매 케르베로스 지뢰/재장전, 골리앗 아레스급 조준/다중 조준, 공성 전차 소용돌이 포탄, 바이킹 포보스 무기/분쇄파 미사일, 밴시 충격파 미사일 포대 등 히페리온 구매 효과는 새 연구 목록에서 뺐다.
- 화재 진압 시스템, 신소재 강철 틀/기본 벙커 수용량, 까치날개 포탑, 강화 벙커 및 연구실의 기존 선택 효과도 중복 신규 연구로 넣지 않는다.
- 멩스크 불능탄 `MarauderMengskSlow`의 기본 이동 감속은 기존 불곰 충격탄과 기능이 겹쳐 별도 비교 대상으로 분리한다. 새 추가 효과가 확인되지 않은 상태에서 독립 중복 연구로 추천하지 않는다.
- 레이너 자극제 기본 제공, 코랄의 후예 고급 자극제·자기 가속 탄약·방패/사거리 진급 보너스 등은 사령관 기본/진급 체계와 구분한다. 이들을 모드 연구로 바꾸려면 재설계라고 표시한다.
- 노바의 자기 가속 탄약 연구와 코랄의 후예의 같은 계열 능력은 서로 다른 원본 연결이다. 이름만 보고 같은 연구로 합치지 않는다.
- 원작 건설 명령/사령관 특성을 보급 벙커 건설 해금 같은 새 연구로 바꾸는 것은 모드 재설계다. 원작 협동전 연구 목록에 섞지 않는다.
- `TrooperMengskInstantTransform`, `NovaImprovedWeaponDamage`, 타이커스 오딘 대공 미사일/PDD/방호 장갑, HH 전투견/망령 4배 공속 등은 정의 존재만으로 실사용 연구에 넣지 않았다. 실제 명령 카드 연결이 없는 레거시·미사용 항목을 배제한다.
- 비용·연구 시간·효과 수치는 사령관 레벨·위신·마스터 힘으로 달라질 수 있으므로 이번 표에서는 확인하지 않은 값을 쓰지 않았다.

## 출처·검증 범위

공개 게임 데이터 SC2Mapster/SC2GameData를 기준으로 캠페인과 협동전 정의를 비교했다. 데이터 덤프의 최신 게임 전체와의 일치 또는 실제 실행을 확인한 것은 아니다. 기본 게임·군심·공허·캠페인 층의 상속과 협동전 덮어쓰기를 구분해 읽었다.

- 확인한 저장소 스냅샷: `6dd323aae4209a01f110719a00b4e8f7a88389bc`.
- [협동전 AbilData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/AbilData.xml), [UpgradeData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/UpgradeData.xml), [UnitData](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/UnitData.xml).
- [타이커스 전체 정의](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/Commanders/CommanderTychus.xml).
- [멩스크 연구](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/commanders/arcturusmengsk.sc2mod/base.sc2data/GameData/AbilData.xml), [업그레이드 효과](https://github.com/SC2Mapster/SC2GameData/blob/master/mods/starcoop/commanders/arcturusmengsk.sc2mod/base.sc2data/GameData/UpgradeData.xml).
- [자날 캠페인 업그레이드 효과](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/liberty.sc2campaign/base.sc2data/GameData/UpgradeData.xml), [히페리온 문자열](https://github.com/SC2Mapster/SC2GameData/blob/master/campaigns/libertystory.sc2campaign/enus.sc2data/LocalizedData/GameStrings.txt).

이번 결과는 조사·비교 자료다. 맵·코드·배포 ZIP은 변경하지 않는다.
