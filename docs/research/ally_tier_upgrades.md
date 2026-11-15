# 동맹 3단계 '캠페인식' 유닛 업그레이드 — 조사·구현 가능성

작성: 2026-11-15. 상태: **조사·제안 (미구현, 사용자 결정 대기)**.

## 사용자 구상 (2026-11-15)

> 피닉스 하면 나오는 건물이랑 데하카 굴 같은 거에 업그레이드 3개(1·2·3단계). 공방업이 아니라 캠페인 업그레이드를 동맹에게 추가.
> 예: 1단계 하면 저글링 아드레날린 분비 같은 업그레이드가 붙고, 저글링에 업그레이드 아이콘이 표시된다.
> GPT에게 위키를 꼭 찾아보게 하고, 넣는 게 가능한지 파악.

## Claude 판단 — 구현 가능 (조건 있음)

1. **데이터는 거의 다 있다.** 아래 확인표처럼 협동전(starcoop)·자날·공허 데이터에 대부분의 업그레이드가 실제로 있고, `AffectedUnitArray`가 우리 동맹이 쓰는 유닛 ID(DehakaRoachLevel2, SentryFenix, Disruptor, DehakaGuardian …)를 가리킨다.
2. **'업글됨' 아이콘**: 업그레이드의 `AffectedUnitArray`에 유닛이 있으면 유닛 정보 창에 그 업그레이드 아이콘이 뜬다 (원작 방식). 따로 만들 필요가 거의 없다. 초상화·와이어프레임이 바뀌는 것은 아님.
3. **지급 방식**: 1·2·3단계 연구를 사면 스크립트가 동맹 플레이어(정화자·원시저그)에게 해당 묶음 업그레이드를 `TechTreeUpgradeAddLevel`로 준다 — 지금 쓰는 동맹 공방업 연동과 같은 구조.
4. **주의**
   - 능치·패시브형(사거리·속도·추가 피해·재생·피해 감소·부활)은 확실히 작동한다.
   - 능력형(돌진·가시 세례·폭발 포자·분해 등)은 **동맹이 AI라서 실제로 쓰는지**가 문제다. 자동 시전이 되는 것만 넣거나, 스크립트로 쓰게 해야 한다.
   - 이식이 필요한 효과·행동·액터가 업그레이드마다 다르다 (port_units로 업그레이드 단위 이식 + check_release).
   - HotS 캠페인 변이(저글링 아드레날린 과부하 등)는 원시 유닛 ID에 맞게 **모드에서 새로 이식·재정의**해야 한다 (원본은 일반 Zergling 대상).
   - 용사 전용(칼달리스 등)·데하카 영웅 연계(Tenderize의 섭취)는 우리 동맹에 없어 빼거나 효과만 쓴다.

## 데이터 확인표 (Claude, SC2GameData 6dd323a)

| 업그레이드 | 데이터 층 | 대상 유닛(AffectedUnitArray) |
|---|---|---|
| FenixSentryGuardianZoneUpgrade (보전기 보호장 지속) | starcoop | SentryFenix |
| ExtendedThermalLance (거신 사거리) | liberty·void·starcoop | Colossus (정화자 거신 ID 연결 확인 필요) |
| DisruptorCloak / DisruptorSecondExplosion | starcoop | Disruptor |
| FenixScoutWeaponRange | starcoop | Scout |
| CarrierLaunchSpeedUpgrade / KaraxCarrierInterceptorLaunchSpeed | liberty / starcoop | Carrier |
| AdeptFenixShadeSpawn (사도 분신) | starcoop | (목록 없음 — 0.4.64에서 이미 연결된 것인지 확인 필요) |
| Charge | liberty·starcoop | Zealot (군단병 ZealotPurifier 연결 확인 필요) |
| DehakaRoachMoveSpeed | starcoop | DehakaRoachLevel2/3 |
| DehakaHydraliskSpeed | starcoop | DehakaHydraliskLevel2 |
| DehakaRavasaurRange / DehakaRavasaurVSArmor | starcoop | DehakaRavasaur |
| DehakaGlevigRoachFireBreath (점화자) | starcoop | DehakaRoachLevel3 |
| DehakaImpalerTenderize | starcoop | ImpalerDehaka |
| DehakaMutaliskAirDoubleDamage / DamageReduction / RespawnOnDeath | starcoop | DehakaMutaliskLevel3 |
| DehakaGuardianFury / ExplosiveBomb | starcoop | DehakaGuardian |
| DehakaUltraliskCrashingCharge / Regen / Bash | starcoop | DehakaUltraliskLevel2(/3) |
| DehakaTyrannozorArmorAura / FanOfKnives | starcoop | DehakaUltraliskLevel3 |

## 사용자 결정이 필요한 것

1. **어디서 사나**: 3·5·6번은 동맹이 건물 없이 지원 버튼만 쓴다. 후보 — (a) 레이너 공학 연구소에 '동맹 연구' 페이지, (b) 화면 위 지원 버튼 옆 버튼, (c) 연구실 단계처럼 자동.
2. **누구 돈**: 레이너 자원 / 동맹 자원.
3. **단계 묶음**: 아래 GPT 제안안을 그대로 쓸지, 고칠지.
4. **능력형 업그레이드** 포함 여부 (AI가 쓰게 스크립트를 붙일지).

---

## GPT(Codex) 웹 조사 결과 (2026-11-15, 위키 출처 포함, 원문 그대로)

**이 모드에는 “특수 업그레이드 여러 개를 묶어 해금하는 3단계 연구”가 잘 맞습니다.** 다만 원작의 **협동전 유료 연구**, **캠페인 기본 능력·유닛 선택**, **모드에서 새로 부여할 효과**를 구분해야 합니다.

비용은 **광물/가스**입니다. 아래에서 `용사 전용`은 일반 병력 전체에 적용되지 않습니다. 영문명을 함께 적어 데이터 검색에 활용할 수 있게 했습니다.

**1. 피닉스 협동전 — 연구 건물과 유닛 업그레이드**

정화자 대의회는 **용사 AI 인격 해금** 건물입니다. 일반 병력의 특수 연구는 인공제어소·황혼 의회·로봇공학 지원소·함대 신호소에 분산됩니다. 제련소에는 공방업 외에 **피닉스 영웅 전용 연구**가 있습니다. [피닉스 협동전](https://starcraft.fandom.com/wiki/Fenix_(Co-op_Missions))

| 대상 | 연구 | 건물 | 비용 | 효과 |
|---|---|---|---:|---|
| 군단병 Legionnaire | Charge | 황혼 의회 | 100/100 | 돌진 해금, 기본 이동속도 +0.25 |
| 사도 Adept | Psionic Projection | 황혼 의회 | 50/50 | 공격하는 무적 그림자 생성; 그림자 피해 8, 경장갑 11 |
| 보전기 Conservator | Optimized Emitters | 인공제어소 | 50/50 | 보호장 지속시간 100% 증가: 15→30초 |
| 불멸자 Immortal | 별도 일반 유닛 특수 연구 없음 | — | — | 아래 탈다린 연구와 구별 |
| 거신 Colossus | Extended Thermal Lance | 로봇공학 지원소 | 100/100 | 사거리 +3 |
| 분열기 Disruptor | Cloaking Module | 로봇공학 지원소 | 50/50 | 영구 은폐 |
| 분열기 Disruptor | Purification Echo | 로봇공학 지원소 | 75/75 | 신성 폭발 후 2초 뒤 추가 폭발: 피해 75, 보호막 추가 25 |
| 정찰기 Scout | Combat Sensor Array | 함대 신호소 | 50/50 | 대공 사거리 +3, 대지 +1 |
| 우주모함 Carrier | Graviton Catapult | 함대 신호소 | 150/150 | 요격기 출격 속도 증가 |

출처: [Liquipedia 피닉스 연구 목록](https://liquipedia.net/starcraft2/Fenix_(commander)), [분열기 상세](https://starcraft.fandom.com/wiki/Disruptor). **보전기는 일반 파수기의 수호 방패와 다른 ‘보호장’을 사용**합니다.

용사 연구까지 포함한 추가 목록입니다.

| 대상 | 연구 | 건물 | 비용 | 효과 |
|---|---|---|---:|---|
| 칼달리스 | Empowered Blades | 황혼 의회 | 50/50 | 공격에 기본 9의 범위 피해 추가 |
| 탈리스 | Debilitation System | 황혼 의회 | 50/50 | 쐐기 투사체가 총 8대상 타격, 피격 대상에 5초간 추가 피해 취약 효과 |
| 탈다린 | Gravimetric Overload | 로봇공학 지원소 | 75/75 | 가한 피해 25% 축적; 대상 사망 시 주변에 축적 피해 방출 |
| 전쟁인도자 | Purification Blast | 로봇공학 지원소 | 75/75 | 단일 대상 피해 150, 재사용 5초 |
| 모조 | Suppression Procedure | 함대 신호소 | 50/50 | 대공 범위 미사일 공격 및 기절; 미사일당 피해 6, 중장갑 12 |
| 클로라리온 | Interdictors | 함대 신호소 | 75/75 | 지상에 범위 폭격하는 금제기 2기 운용 |

출처: [피닉스](https://liquipedia.net/starcraft2/Fenix_(commander)), [로봇공학 지원소](https://starcraft.fandom.com/wiki/Robotics_bay), [전쟁인도자](https://starcraft.fandom.com/wiki/Warbringer_(Purifier)), [함대 신호소](https://starcraft.fandom.com/wiki/Fleet_beacon). 탈리스의 **취약 효과 정확한 추가 피해량은 이번 조사에서 확정하지 못했습니다.** Liquipedia 본문의 “8회 추가 반사” 표기는 같은 페이지 패치 기록의 “총 8대상”과 충돌하므로 후자를 채택했습니다.

| 기타 연구 | 건물 | 비용 | 효과 |
|---|---|---:|---|
| 용사 AI 인격 6종 | 정화자 대의회 | 칼달리스 100/0; 나머지 각 100/50 | 해당 일반 유닛 한 기를 용사로 전환; 사망하면 다른 숙주로 이전 |
| Purifier Armaments | 제련소 | 75/75 | 피닉스의 모든 전투복 공격력 +15 |
| Observation Protocol | 제련소 | 50/50 | 중재자 전투복 탐지 |
| A Strong Heart | 제련소 | 13/13 | 피닉스 이름을 탈란다르로 변경; 외형적 기능 |

출처: [용사 AI](https://liquipedia.net/starcraft2/Fenix_(commander)), [피닉스 전투복 연구 교차 확인](https://starcraft2coop.com/commanders/fenix). 차원 관문·관측선 이동속도 연구는 요청한 전투 병력 강화 목록에서 제외했습니다.

**파수병·동력기·선동자·폭풍함은 피닉스의 생산 유닛이 아닙니다.** 모드에서는 아래 캠페인 자료와 결합해야 합니다.

**2. 데하카 협동전 — 연구 건물과 원시 유닛 업그레이드**

**원시 감시자 Primal Warden는 생산 건물**, **원시 군락 Primal Hive는 공방업 건물**입니다. 유닛별 특수 연구는 세 우두머리의 굴에서 합니다. [데하카 연구 목록](https://liquipedia.net/starcraft2/Dehaka_(commander))

| 건물 | 대상 | 연구 | 비용 | 효과 |
|---|---|---|---:|---|
| 글레빅의 굴 | 라바사우르 | Dissolving Acid | 100/100 | 중장갑 추가 피해 +15 |
| 글레빅의 굴 | 라바사우르 | Enlarged Parotid Glands | 100/100 | 사거리 +1, 이동속도 +0.75 |
| 글레빅의 굴 | 원시 바퀴·점화자 | Glial Reconstitution | 100/100 | 이동속도 각각 31%·19% 증가 |
| 글레빅의 굴 | 원시 점화자 | Concentrated Fire | 100/100 | 경장갑 추가 피해 +15 |
| 글레빅의 굴 | 원시 히드라리스크 | Muscular Augments | 50/50 | 이동속도 +22%, 사거리 +1 |
| 글레빅의 굴 | 관통 촉수 Impaler | Tenderize | 100/100 | 공격 대상에 10초간 200 지속 피해; 데하카 섭취 재사용시간 75% 감소 |

출처: [글레빅의 굴](https://starcraft.fandom.com/wiki/Glevig%27s_den), [원시 바퀴](https://starcraft.fandom.com/wiki/Primal_roach), [원시 히드라](https://starcraft.fandom.com/wiki/Primal_hydralisk), [관통 촉수](https://starcraft.fandom.com/wiki/Impaler). Tenderize의 Fandom 설명에 남은 “재사용시간이 75%가 됨”은 패치 기록과 충돌합니다. **정정된 값은 75% 감소, 즉 원래의 25%**입니다. [패치 4.9.0](https://liquipedia.net/starcraft2/Patch_4.9.0)

| 건물 | 대상 | 연구 | 비용 | 효과 |
|---|---|---|---:|---|
| 멀바르의 굴 | 원시 뮤탈리스크 | Slicing Glave | 100/100 | 대공 피해 +100% |
| 멀바르의 굴 | 원시 뮤탈리스크 | Shifting Carapace | 100/100 | 이동 중 받는 피해 50% 감소 |
| 멀바르의 굴 | 원시 뮤탈리스크 | Primal Reconstitution | 150/150 | 사망 시 부활; 재사용 60초 |
| 멀바르의 굴 | 원시 수호군주 | Primordial Fury | 100/100 | 공격할 때마다 일시적으로 공속 +10%, 최대 +50% |
| 멀바르의 굴 | 원시 수호군주 | Explosive Spores | 100/100 | 지상 범위 피해 50 및 밀치기; 재사용 10초 |
| 멀바르의 굴 | 땅무지 숙주 Creeper Host | Aerial Burst Sacs | **미확인** | 폭발성 식충의 이동속도 증가·대공 공격 허용; 요청 편성에는 없음 |

출처: [원시 뮤탈리스크](https://starcraft.fandom.com/wiki/Primal_mutalisk), [원시 수호군주](https://starcraft.fandom.com/wiki/Primal_guardian), [멀바르의 굴](https://starcraft.fandom.com/wiki/Murvar%27s_den), [데하카 해금 목록](https://starcraft.fandom.com/wiki/Dehaka_(Co-op_Missions)).

| 건물 | 대상 | 연구 | 비용 | 효과 |
|---|---|---|---:|---|
| 다크룬의 굴 | 원시 울트라리스크 | Brutal Charge | **50/50** | 돌진, 범위 피해 25 및 밀치기 |
| 다크룬의 굴 | 울트라·티라노조르 | Healing Adaptation | 100/100 | 비전투 중 빠른 재생; 티라노조르 기준 초당 10 |
| 다크룬의 굴 | 울트라·티라노조르 | Impaling Strike | 100/100 | 근접 공격 시 20% 확률로 기절 |
| 다크룬의 굴 | 티라노조르 | Barrage of Spikes | 100/100 | 주변 지상·공중 적에게 피해 100; 재사용 10초 |
| 다크룬의 굴 | 티라노조르 | Tyrant’s Protection | 100/100 | 주변 아군 방어력 +2 |

출처: [다크룬의 굴](https://starcraft.fandom.com/wiki/Dakrun%27s_den), [티라노조르](https://starcraft.fandom.com/wiki/Tyrannozor). Brutal Charge는 건물 문서에 구형 100/100이 남아 있으나, [4.9.0 패치](https://liquipedia.net/starcraft2/Patch_4.9.0)에서 **50/50으로 인하**됐습니다.

| 유닛 | 별도 구매형 특수 연구 |
|---|---|
| 원시 저글링 | 없음. Adrenal Glands는 데하카 원본 연구가 아님 |
| 원시 숙주 Primal Host | 없음. 잠복·비행 식충은 기본 기능 |
| 진화한 원시 병력 | Gene Mutation으로 생명력 +50%, 공속 +20%, 흡혈 20% 등의 무작위 특성 획득 가능; 구매 연구가 아님 |

출처: [원시 저글링](https://starcraft.fandom.com/wiki/Primal_zergling), [원시 숙주](https://starcraft.fandom.com/wiki/Primal_host), [원시 뮤탈리스크의 유전자 변이](https://starcraft.fandom.com/wiki/Primal_mutalisk). 따라서 저글링 공속 강화를 1단계에 넣으려면 **HotS 캠페인 효과를 이식**하는 방식이 적절합니다.

**3. LotV 캠페인 정화자 — 전쟁 의회와 아둔의 창**

전쟁 의회는 기본적으로 **유닛 변종을 선택**하는 곳입니다. 아래 특성을 각각 자원으로 구매하는 연구 체계는 아닙니다. [전쟁 의회](https://starcraft.fandom.com/wiki/War_council)

| 유닛 | 캠페인 특성 | 비용·주의 | 출처 |
|---|---|---|---|
| 파수병 Sentinel | Reconstruction: 파괴 후 10초에 완전 복구, 재사용 120초 | 변종 기본 특성. Charge는 황혼 의회 100/100 연구 | [파수병](https://starcraft.fandom.com/wiki/Sentinel) |
| 선동자 Instigator | Blink 최대 3충전, 4초마다 1충전 회복 | **전쟁 의회 선택 불가**. 「정화」 임무의 AI 아군 유닛 | [선동자](https://starcraft.fandom.com/wiki/Instigator) |
| 동력기 Energizer | Chrono Beam: 대상 공속·이속 +50%, 10초; Phase Mode로 동력장 생성 | 캠페인 기본 능력. 광선 에너지 3 | [동력기](https://starcraft.fandom.com/wiki/Energizer) |
| 정화자 거신 | Fire Beam: 지면에 불길을 남겨 5초간 피해 100 | 캠페인 기본 특성. 카락스 연구의 150 피해와 구별 | [거신](https://starcraft.fandom.com/wiki/Colossus) |
| 정화자 폭풍함 | Disintegration: 단일 유닛·구조물에 20초간 피해 500, 재사용 90초 | 캠페인 기본 능력 | [폭풍함](https://starcraft.fandom.com/wiki/Tempest) |

**동력기의 캠페인 공속 +50%와 카락스 협동전의 +25%는 서로 다른 수치**입니다. Reclamation·Rapid Recharging은 카락스 협동전 연구이므로 LotV 캠페인 연구로 분류하면 안 됩니다. [동력기 모드별 능력](https://starcraft.fandom.com/wiki/Energizer)

아둔의 창에서 병력 강화로 차용하기 좋은 선택지는 다음과 같습니다.

| 태양 핵 선택 | 태양석 | 효과 |
|---|---:|---|
| Matrix Overload | 0 | 동력장 안에서 이속 +25%, 공속 +15%; 벗어난 뒤 15초 유지 |
| Guardian Shell | 50 | 치명타를 받을 때 5초 무적; 동일 유닛 재발동 60초 |
| Reconstruction Beam | 100 | 기계 유닛 초당 5, 구조물 초당 10 수리; 최대 3대상 |

원작에서는 **같은 5단계 열의 택일 능력**입니다. 이를 누적 연구로 바꾸는 것은 모드 설계입니다. [Liquipedia 태양 핵](https://liquipedia.net/starcraft2/Campaign/Solar_Core), [Fandom 태양 핵](https://starcraft.fandom.com/wiki/Solar_core)

**4. HotS 캠페인 — 변이와 진화**

정확한 장소는 임무 사이의 **진화 구덩이 Evolution Pit**입니다. 일반 **진화장 Evolution Chamber**와 다릅니다. 변이는 유닛당 3개 중 1개를 선택하며 임무 사이 변경 가능하고, 진화는 두 계통 중 하나를 선택합니다. 자원 구매 비용은 없습니다. 원시 변종에는 자동 적용되지 않습니다. [진화 구덩이](https://starcraft.fandom.com/wiki/Evolution_pit)

| 유닛 | 선택 변이 3종 |
|---|---|
| 저글링 | **Hardened Carapace**: 체력 +10 / **Adrenal Overload**: 공속 +50% / **Metabolic Boost**: 이속 +60% |
| 바퀴 | **Hydriodic Bile**: 경장갑 피해 +8 / **Adaptive Plating**: 체력 50% 미만에서 방어력 +3 / **Tunneling Claws**: 잠복 이동, 잠복 재생 2배 |
| 히드라리스크 | **Frenzy**: 15초 공속 +50%, 재사용 30초 / **Ancillary Carapace**: 체력 +20 / **Grooved Spines**: 사거리 +1 |
| 뮤탈리스크 | **Vicious Glave**: 추가 3회 반사·반사 성능 강화 / **Rapid Regeneration**: 비전투 5초 후 초당 체력 10 재생 / **Sundering Glave**: 중장갑 피해 +9, 반사 제거 |
| 울트라리스크 | **Burrow Charge**: 잠복 돌진·밀치기·2초 기절 / **Tissue Assimilation**: 일반 공격 피해의 40% 회복 / **Monarch Blades**: 방사 피해 +20 |
| 군단 숙주 | **Burrow**: 잠복 중 식충 생성 / **Rapid Incubation**: 식충 생성 속도 +20% / **Pressurized Glands**: 식충 대공 허용 |

출처: [Fandom 변이 전체 목록](https://starcraft.fandom.com/wiki/Evolution_pit), [Liquipedia 캠페인 진화 구덩이](https://liquipedia.net/starcraft2/Campaign/Evolution_Pit).

| 유닛 | 진화 계통 A | 진화 계통 B |
|---|---|---|
| 저글링 | Raptor: 피해 증가·도약·언덕 이동 | Swarmling: 두 마리 가격으로 세 마리 부화 |
| 바퀴 | Corpser: 공격 대상에 애바퀴 기생 | Vile: 적 공격·이동속도 감소 |
| 히드라 | Impaler: 잠복 단일 중장갑 공격형으로 변태 | Lurker: 잠복 직선 범위 공격형으로 변태 |
| 뮤탈 | Brood Lord 변태 | Viper 변태 |
| 울트라 | Noxious: 독성 구름·독성 폭발 | Torrasque: 사망 시 부활, 재사용 60초 |
| 군단 숙주 | Carrion: 비행 식충, 피해 +50%·체력 −25% | Creeper: 점막 생성·점막으로 굴 파기 |

출처: [Liquipedia 진화 계통](https://liquipedia.net/starcraft2/Campaign/Evolution_Pit). **HotS의 Creeper 계통과 데하카의 Creeper Host는 효과가 다릅니다.**

**5. 모드용 3단계 묶음 제안**

아래는 **원작 연구 트리가 아닌 설계안**입니다. 각 단계 연구 한 번으로 5개 효과를 함께 지급하고, 이전 단계 효과는 유지하는 구성이 좋습니다. 기본 탑재된 능력은 다시 해금하지 말고 해당 항목을 다른 강화로 교체해야 합니다.

| 정화자 단계 | 지급할 5개 업그레이드 |
|---|---|
| **1단계: 전선 가동** | ① 군단병·파수병 **Charge** ② 사도 **Psionic Projection** ③ 보전기 **Optimized Emitters** ④ 선동자 **3충전 Blink** ⑤ 동력기 **캠페인 Chrono Beam** |
| **2단계: 화력 체계** | ① 일반 불멸자에 **Gravimetric Overload 이식** ② 거신 **Extended Thermal Lance** ③ 정찰기 **Combat Sensor Array** ④ 우주모함 **Graviton Catapult** ⑤ 분열기 **Cloaking Module** |
| **3단계: 정화 프로토콜** | ① 파수병 **Reconstruction** ② 거신 **캠페인 Fire Beam** ③ 분열기 **Purification Echo** ④ 폭풍함 **Disintegration** ⑤ 기계 병력 **Reconstruction Beam 방식 수리 지원** |

불멸자의 과부하는 **탈다린 전용 효과를 일반 병력에 확대하는 개조**입니다. 마지막 수리 지원은 원작처럼 최대 3대상으로 제한하는 편이 좋습니다. 이 구성은 요청한 정화자 **12종 모두**에 직접 강화 또는 수리 지원을 제공합니다.

| 원시 단계 | 지급할 5개 업그레이드 |
|---|---|
| **1단계: 사냥 적응** | ① 저글링 **HotS Adrenal Overload** ② 바퀴·점화자 **Glial Reconstitution** ③ 히드라 **Muscular Augments** ④ 라바사우르 **Dissolving Acid** ⑤ 원시 숙주 **HotS Rapid Incubation 이식** |
| **2단계: 포식 무장** | ① 점화자 **Concentrated Fire** ② 관통 촉수 **Tenderize** ③ 뮤탈 **Slicing Glave** ④ 수호군주 **Primordial Fury** ⑤ 울트라 **Brutal Charge** |
| **3단계: 최상위 개체** | ① 울트라·티라노조르 **Healing Adaptation** ② 티라노조르 **Barrage of Spikes** ③ 티라노조르 **Tyrant’s Protection** ④ 뮤탈 **Primal Reconstitution** ⑤ 수호군주 **Explosive Spores** |

원시 저글링 공속과 원시 숙주 식충 생성 강화는 **캠페인 효과의 모드 이식**입니다. 데하카 영웅이 없는 모드라면 Tenderize의 섭취 연계는 실효성이 없으므로 **지속 피해 부분만 사용**하면 됩니다.

표시 방식은 각 유닛의 능력 패널에 **획득한 강화의 패시브 아이콘과 툴팁**을 추가하는 안을 권합니다. 일반 공격력·방어력 아이콘의 숫자와 분리하면 강화 내용을 바로 읽을 수 있습니다. **연구 완료만으로 유닛 초상화·와이어프레임이 자동 교체되는지는 확인하지 못했으며**, 원하시는 “업그레이드된 아이콘”은 모드에서 별도로 연결해야 합니다.
