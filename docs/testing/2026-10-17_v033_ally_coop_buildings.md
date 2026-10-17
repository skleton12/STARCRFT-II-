# 0.3.3 — 3번 미션 동맹 건물·일꾼 협동전 외형 (2026-10-17)

사용자 지시: "그 건물들도 협동전껄로 해야됨".

도구: `tools/build_v033.py` (0.3.2 ZIP 위에 덧씌움). 3번 맵만 바뀜: modeldata, actordata, behaviordata, mapscript, metadata.

| 일반 | 동맹 외형 | 출처 |
|---|---|---|
| 연결체 | Nexus_Purifier_COOP | 피닉스 협동전 |
| 관문 | Gateway_Purifier_COOP | 피닉스 협동전 |
| 융화소(풍부 포함) | Assimilator_Purifier_COOP | 피닉스 협동전 |
| 탐사정 | Probe_Purifier_Collection | 자날 데이터에 있음 |
| 수정탑 | (0.2.17부터) Pylon_Purifier_COOP | 피닉스 협동전 |
| 부화장 | DehakaHatchery (원시 부화장) | 데하카 협동전 |
| 산란못 | DehakaBarracks (원시 생산 건물 외형) | 데하카 협동전 |
| 추출장(풍부 포함) | DehakaPrimalExtractor | 데하카 협동전 |
| 드론 | Drone_Primal_Collection | 데하카 협동전 |

방식: 3번 미션 적이 저그라서 전역 모델 변경을 하지 않는다. 스크립트가 2초마다 10·11번의 완성된 유닛·건물에 숨김 행동 `RM3_AllySkin`을 붙이고, 위 액터가 그 행동이 켜질 때 ModelSwap 한다. 0.3.1의 액터 카탈로그 런타임 변경(부화장 모델) 줄은 제거했다.

한계 (미실행):
- 게임에서 실제 외형·크기·선택 원·건설 중 모습 확인 안 함. 건설 중에는 일반 건설 모델, 완성 직후(최대 2초) 바뀜.
- 파괴 모델은 일반 것 그대로.
- 산란못에 대응하는 데하카 건물이 없어 원시 생산 건물 외형을 씀 (임시 대응).
- 협동전 모델 파일이 자날 의존성 맵에서 불러와지는지 미검증 (수정탑과 같은 조건).
