# 0.3.23 — 원시저그 건물 협동전식 건설 (3번 미션)

사용자 보고 (2026-10-17): "구 없애라고", "왜 협동전처럼 안 만듦".

## 원인 (데이터·스크립트 검토, 게임 미확인)
- 0.3.12~0.3.22는 원시 군락·원시 감시자를 스크립트가 고치 모델을 땅에 따로 띄우는 방식(`CreateModelAtPoint("DehakaHatcheryBuild")`)으로 만들었다. 시간이 끝나면 고치를 지우고 완성 건물을 바로 만들었다. 협동전 방식이 아니다.
- 협동전 데하카는 다르다. 건물이 '건설 중' 상태로 생기고(건설 능력 `PrimalBuildInProgress`), 건물 액터가 건설 시작 때 고치 액터(`DehakaHatcheryBuild`/`DehakaBarracksBuild`)를 붙인다. 고치는 진행도에 따라 Build A~D 애니메이션(`PrimalZergConstructionAttached`)을 재생하고, 완성 때 사라진다.
- 0.3.4 이식 때 이 연결이 빠졌다.
  - 빠진 것: `PrimalBuildInProgress`, 액터 틀 `PrimalZergBuildingBuild`, `PrimalZergConstructionAttached`, `PrimalZergBuildingFacing`, `DehakaHatcheryBuild` 액터, 원시 군락 액터의 '건설 시작 → 고치' 이벤트.
  - 원시 감시자 고치 액터는 부모가 없는 상태였다.

## 수정
- 위 레코드를 협동전 원본(starcoop)에서 그대로 이식했다. 건설 단계 소리 2개도 포함했다(`Zerg_BuildingMorphStages`, 자날에 있음).
- 원시 군락·원시 감시자 유닛에 `PrimalBuildInProgress`를 추가했다.
- 스크립트 변경
  - 땅에 띄우던 고치 모델 3곳(초기 군락, 초기 감시자, `gf_m3_Build` 추가 감시자)을 삭제했다.
  - 일벌레가 사라지면 건물이 '건설 중'으로 생기고, 원작 건설 시간(군락 100, 감시자 60)에 맞춰 진행도가 오른다. 정화자 건물과 같은 방식이다.
- 활동 문구 `UI/Summoning`은 자날 문자열에 없어서 넣지 않았다(기본 표시).
- 건설 시간·순서·비용·위치는 그대로다.

## 검사
- 통과: ZIP CRC, 바뀐 파일 외 바이트 동일, XML 파싱, 빈 연결 검사(0.3.22 대비 새 항목 없음), 모델 경로 검사(누락 0), 스크립트 함수 인수 검사.
- 미실행: 게임 실행, Galaxy 컴파일, 고치 모습·애니메이션 실제 재생.
- 협동전 고치 에셋(`Dehaka_Primal_ZergBuild_Coop.m3`)이 자날 의존성에서 실제로 불러와지는지는 게임에서만 확인할 수 있다.

재현: `python3 tools/build_v0323.py <0.3.22 zip> <새 zip>`
