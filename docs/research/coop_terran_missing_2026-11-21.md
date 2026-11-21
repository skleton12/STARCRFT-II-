# 아직 안 넣은 협동전 테란 연구 (코덱스 조사, 2026-11-21, 0.6.37 기준)

> 조사 자료다. 구현 승인 아님. 불곰 자기 가속 탄약은 사용자가 0.4.34에서 제외했다.


**6개 전투 맵의 로컬 XML과 `mapscript.galaxy`를 대조했습니다.** 맵 전체에서 빠진 대표 연구는 한과 호너의 사신 비행, 노바의 불곰 자기 가속 탄약, 멩스크의 원본 포격 사거리 +25입니다. 후반 세 맵에는 포격 사거리 **+8**을 포함한 모드판 연구가 있습니다.

비용은 **광물/가스 · 데이터상 연구 초**이며 할인 전 기준입니다. `U` = `upgradedata.xml`, `A` = `abildata.xml`, `D` = `unitdata.xml`, `G` = `mapscript.galaxy`입니다. **후반 3맵**은 `TTychus01`, `TTosh01`, `THanson01`입니다. 판정은 제공된 파일의 연구 슬롯, 명령 카드, 효과 연결 기준이며 게임 실행과 의존 모드의 상속 데이터는 확인하지 못했습니다.

### 협동전 연구 대조

| 사령관 | 한국어 / English | 원본 효과 | 원본 비용·시간 | 모드 대상 | 구현 여부와 파일·ID 근거 |
|---|---|---|---|---|---|
| 레이너 | 전투 안정제 / Stabilizer Medpacks | 치료 강화, 기계 치료, 치료 중 받는 피해 25% 감소 | 100/100 · 60초 | `MercMedic` | **부분 예, 후반 3맵.** `U:StabilizerMedPacks`에 치료율·에너지 변경, `G:RMC_StabilizerCoop` 완료 시 `MercMedicHeal`에 지상 기계 치료 허용. 피해 감소 연결은 미확인. |
| 레이너 | 철인 장갑 / Juggernaut Plating | 체력 +100, 방어력 +2. 비교 대상은 협동전의 체력 증가분 | 100/100 · 60초 | `DevilDog`, `RM6_Prometheus` | **예, 후반 3맵의 DevilDog. 아니오, Prometheus.** `A/U:RMC_JuggernautCoop`의 +100 대상은 `DevilDog`와 `Firebat`. |
| 레이너 등 | 보병 무기·장갑 / Terran Infantry Weapons & Armor | 1~3단계 공격력·방어력 강화 | 각각 100/100 · 160초, 175/175 · 190초, 250/250 · 220초 | 모드 보병 | **예, 후반 3맵.** `U:TerranInfantryWeaponsLevel1~3`, `TerranInfantryArmorsLevel1~3` 및 `G`의 플레이어 1 연구 단계 참조. `TRaynor01/02`에서 확인된 단계 부여는 적군용. `TRaynor03`의 플레이어 연구는 상속 데이터 미확인. |
| 레이너 등 | 건물 장갑 / Terran Building Armor | 구조물 방어력 +2 | 100/100 · 60초¹ | 일반 벙커, 사령부, 병영, 포탑 등 | **예, TRaynor03 및 후반 3맵.** `A/U:RM3_Armor`, `D:RM3_BayResearch,Research7`. `U`에 일반 벙커 포함. |
| 스완 | KMC 자동장전기 / KMC Auto-Loaders | 방어 포탑 공격 속도 +25% | 150/150 · 90초 | 미사일 포탑 | **예, 후반 3맵.** `A/U:RMC_TurretSpeed`가 `LongboltMissile`, `HailstormMissilePods`에 적용. |
| 스완 | 정밀 보안 자동추적 / Hi-Sec Auto Tracking | 방어 포탑 사거리 +1. 비교 대상은 캠페인 미사일 포탑 밖의 확장분 | 100/100 · 60초 | 미사일 포탑 및 추가 방어 포탑이 있다면 해당 포탑 | **예, 후반 3맵에 연구 슬롯.** `A/G:HiSecAutoTracking`, `D:RMC_HiSec`. 스완 포탑 전체에 해당하는 추가 적용은 로컬 파일에서 미확인. |
| 노바 | 초 전투 자극제 / Super Stimpack | 공격·이동 속도 증가와 지속 회복 | 150/150 · 90초 | `WarPig`, `RMK_MarineMengsk`, `HammerSecurity` | **예, 후반 3맵에 모드판.** `A:RM3_Stim2` → `D:SuperStimpackMarine` / `RM3_Stim2Use`. `TRaynor03`에는 정의와 사용 능력이 있고 `D`에 `Research2` 버튼이 없음. |
| 노바 | 레이저 조준 시스템 / Laser Targeting System | 시야 +2, 무기 사거리 +1 | 100/100 · 60초 | `WarPig`, `RMK_MarineMengsk` | **예, TRaynor03 및 후반 3맵.** `A/U:RM3_Laser`, `D:RM3_TechResearch,Research5`. |
| 노바 | 자기 가속 탄약 / Magrail Munitions | 불곰이 30초마다 추가 공격으로 90 피해 | 150/150 · 90초 | `HammerSecurity`, `MarauderMengsk` | **아니오.** 후반 3맵 `U/A:MarauderMagrailMunitions`에 정의가 있으나 연구 슬롯과 대상 불곰 카드 연결이 없음. `D:RMK_MagrailMunitionsMarineMengsk`는 코랄 해병의 별도 능력. |
| 노바 | 억제탄 / Suppression Shells | 명중한 적의 이동·공격 속도 감소 | 100/100 · 60초 | `HammerSecurity` | **예, 후반 3맵에 모드판.** `A/U:RM4_Suppression`, `D:HammerSecurity`의 패시브. `U`에서 확인되는 변경은 `RM4_SuppressAOE` 반경 증가이며 감속 수치는 미확인. |
| 노바 | 도약 추진 공격 / Jump Jet Assault | 적에게 도약해 기절, 장갑 강화 | 150/150 · 90초 | `DevilDog`, `RM6_Prometheus`에 이식 가능 | **아니오.** `U/A/D/G:HellbatJumpJetAssault` 연결 없음. |
| 한과 호너 | 제트 추진기 과부하 / Jet Pack Overdrive | 일시 비행, 이동 가속, 대공 공격 | 100/100 · 90초 | `MercReaper` | **아니오.** `U/A/D/G:HHReaperFlight` 없음. `D:MercReaperJump`는 절벽 이동. |
| 한과 호너 | LE9 집속탄 / LE9 Cluster Charges | 수류탄 재사용 단축, 사망 시 집속탄 투척 | 50/50 · 60초 | `MercReaper` | **아니오, 원본 효과 기준.** `HHReaperG4ClusterBombs` 없음. `TTosh01/THanson01`에 `A/G:ClusterBomb` 연구가 있고, `D:MercReaper`는 `D8Charge`를 사용. 사망 시 투척·재사용 단축 연결은 미확인. |
| 멩스크 | 궤도 부대원 투하 / Orbital Trooper Pods | 생산 병력을 집결지에 직접 투하 | 100/100 · 60초 | `SCV` 또는 코랄 해병 생산에 이식 가능 | **아니오.** `U/A/D/G:TrooperMengskDropTrain` 없음. 이식하려면 모드 생산 명령에 연결 필요. |
| 멩스크 | 신소재 강철 장갑 / Neosteel Fortified Armor | 보급 벙커·미사일 포탑·대지파괴 포 체력 +200, 방어력 +2 | 100/100 · 90초 | `BunkerDepotMengsk`, `MissileTurret`, `ArtilleryMengsk` | **부분 예, TRaynor03 및 후반 3맵.** `A/U:MengskStructureArmor`가 보급 벙커에 적용. 포탑·포병은 `U`의 적용 대상에 없음. |
| 멩스크 | 조준 보조 총안 / Enhanced Optics | 보급 벙커 탑승 병력 사거리 +1 | 100/100 · 60초 | `BunkerDepotMengsk` | **예, TRaynor03 및 후반 3맵.** `A/U:BunkerDepotMengskRange` → `BunkerMengskWeaponRangeBonus`. |
| 멩스크 | 반구형 가속제 / Hemispheric Accelerants | 포격 사거리 +25 | 150/150 · 90초 | `ArtilleryMengsk` | **아니오, 원본 효과 기준.** `ArtilleryMengskRange` 없음. 후반 3맵의 `A/U/D:RM6_ArtyAccel`은 사거리 +8과 포격 횟수·주기·피해 변경을 적용. |
| 멩스크 | 불능탄 / Maiming Rounds | 이지스 근위대 공격에 이동 감속 | 100/100 · 60초 | `MarauderMengsk` | **예, 후반 3맵.** `A/D/G:MarauderMengskSlow`. 기존 충격탄과 겹치는 효과라 신규 후보에서는 제외. |

¹ 건물 장갑은 협동전 `EngineeringBayResearch/Research2`의 덮어쓰기 기준입니다. 기본 테란 데이터는 150/150 · 140초입니다. 노바의 표기 비용·시간은 원본 데이터값이며 사령관의 50% 할인을 적용하면 절반입니다. 한국어명은 기존 목록의 표기를 따랐습니다. [협동전 AbilData](https://raw.githubusercontent.com/SC2Mapster/SC2GameData/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/AbilData.xml), [기본 테란 AbilData](https://raw.githubusercontent.com/SC2Mapster/SC2GameData/master/mods/liberty.sc2mod/base.sc2data/GameData/AbilData.xml), [멩스크 AbilData](https://raw.githubusercontent.com/SC2Mapster/SC2GameData/master/mods/starcoop/commanders/arcturusmengsk.sc2mod/base.sc2data/GameData/AbilData.xml), [블리자드 노바 소개](https://news.blizzard.com/en-us/article/20320355/patch-3-7-new-co-op-commander-nova), [전투 안정제 패치 노트](https://news.blizzard.com/de-de/article/20303494/starcraft-ii-legacy-of-the-void-3-7-0-patchnotes)

### 타이커스에서 이식 가능한 연구·장비

| 사령관 | 한국어 / English | 효과 → 모드 대상 | 원본 비용·시간 | 구현 여부와 파일·ID 근거 |
|---|---|---|---|---|
| 타이커스 | ITC-E 방아쇠 / ITC-E Triggers | 공격 속도 +25% → `MercReaper` | 150/150 · 90초 | **아니오.** `U/A/D/G:TychusSquadAttackSpeed` 없음. |
| 타이커스 | 지구력 보충제 / Endurance Supplements | 최대 체력 +25% → 화염방사병·불곰 계열 | 150/150 · 90초 | **아니오.** `U/A/D/G:TychusSquadHealth` 없음. |
| 타이커스 | 탐지 조준경 / Flashforce GDM Visor | 탐지 부여 → `MercMedic` | 75/75 · 90초 | **아니오.** `U/A/D/G:TychusSquadDetection` 없음. |
| 타이커스 | Procyon Twin Heal Beam Gauntlet / Procyon Serum | 동시 두 대상 치료 / 기본 치료량 2배 → `MercMedic` | 각각 700/250 · 즉시 | **아니오.** `U/A/D/G:TychusMedicDoubleBeam`, `TychusMedicSuperHealing` 없음. |
| 타이커스 | XM-77 Matrix Generator | 아군에게 피해 흡수 보호막 → `MercMedic` | 1200/400 · 즉시 | **아니오.** `U/A/D/G:TychusMedicDefensiveMatrix` 없음. |
| 타이커스 | XCMC-670 Combat Suit | 한 번에 받는 피해 상한 30 → `DevilDog`, `RM6_Prometheus` | 1200/400 · 즉시 | **아니오.** `U/A/D/G:TychusFirebatShield` 없음. |
| 타이커스 | Procyon Shade Suit | 피격 후 일시 피해 회피·이동 가속 → `MercReaper` | 700/250 · 즉시 | **아니오.** `U/A/D/G:TychusReaperEvasionBuff` 없음. |
| 타이커스 | Hammer Munitions | 공격 광역화·감속 → `HammerSecurity`, `MarauderMengsk` | 1200/400 · 즉시 | **아니오, 원본 장비 기준.** `TychusMarauderAttackSplash` 없음. 후반 3맵 `U/A:RM4_Shrapnel`과 억제·감속 연구가 일부 효과를 구현. |

타이커스 장비 가격은 할인 전 `TychusHeroResearch` 데이터 기준입니다. 활력 장치, 기름 유출, 회복 폭발, 샘의 폭발물 전용 장비는 해당 기반 능력을 먼저 이식해야 합니다. [CommanderTychus.xml](https://raw.githubusercontent.com/SC2Mapster/SC2GameData/master/mods/starcoop/starcoop.sc2mod/base.sc2data/GameData/Commanders/CommanderTychus.xml)

### 맵별 확인 결과

| 맵 | 확인된 협동전 연구·모드판 |
|---|---|
| `TRaynor01`, `TRaynor02` | 플레이어용 협동전 연구 연결 미확인. `U/D:RMK_MarineMengskCombatShield*`, `D:RMK_MagrailMunitionsMarineMengsk`는 코랄 해병 기능 정의. |
| `TRaynor03` | `A/D:RM3_Laser`, `RM3_Armor`, `MengskStructureArmor`, `BunkerDepotMengskRange`. 모드 자체 연구 `RM3_Shield`, `RM3_SupplyBunker`, `RM6_Multishot`, `RM6_EternalRes`도 연결됨. |
| `TTychus01` | `TRaynor03`의 연결 항목에 더해 `RM3_Stim1~3`, `RM4_Suppression`, `RM4_Shrapnel`, `MarauderMengskSlow`, `RMC_StabilizerCoop`, `RMC_JuggernautCoop`, `RMC_TurretSpeed`, `HiSecAutoTracking`, `RM6_ArtyAccel`, 보병 공방 1~3단계. |
| `TTosh01`, `THanson01` | `TTychus01`과 같은 계열에 `A/D/G:ClusterBomb` 연구 슬롯 추가. |
| `TStory01` | `mapscript.galaxy`만 제공된 스토리 맵. 미션 내 연구 연결 미확인. |

`HHBomberNapalm`은 전투 맵 6개의 `U`에서 발견됐지만 대상 타격 전투기 플랫폼의 연구 연결은 확인되지 않았습니다. 파일은 변경하지 않았습니다.
