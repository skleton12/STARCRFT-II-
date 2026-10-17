# 0.2.22 — 데하카 협동전 지원 유닛

2026-10-16: 데하카 협동전 지원 유닛 교체 — 0.2.22

사용자 지시로 2번 미션의 반복 투하 병력을 데하카 협동전 실제 생산 ID(DehakaZerglingLevel2 6기, DehakaHydraliskLevel2 2기, DehakaRoachLevel2 2기)로 교체했다. DehakaRavasaur 2기는 유지한다. 부대 편성·90초 반복·기존 인구수 20 이상 보류·지원군 위치는 유지한다. 새 편성 인구수는 18이며 다음 투하 뒤 20을 넘을 수 있는 기존 보류 방식이다. 1번 미션 및 기존 모든 배치·카탈로그 정의를 보존했다. 실사용 생산 능력에서 바퀴는 legacy DehakaRoach가 아닌 DehakaRoachLevel2임을 확인했다. 새로운 데하카 영웅·진화 합체·유전자·마스터 힘 체계를 추가하지 않았다. 필요한 무기·투사체·모델·연출·잠복 연결을 함께 이식했다.

전달 파일은 RaynorMercs_WoL_CCM.zip, 내부 버전 0.2.22다. CRC·XML·기존 데이터 보존·유닛/액터/원본 능력치/소환 ID 검사를 통과했으며 게임·Galaxy 컴파일은 미실행이다.

재현: `python3 tools/patch_dehaka_support.py 입력_0.2.21.zip 새폴더/RaynorMercs_WoL_CCM.zip`. tools/data/dehaka_support.json과 기존 재현 도구가 필요하다.

출처: SC2Mapster/SC2GameData starcoop의 DehakaTrainEggMorph 및 DehakaBarracksTrain에서 실제 생성 ID를 확인했다. 추가 카탈로그 53개와 지역화 20개 키를 포함한다. 기존 공유 종족 PZrg 대신 이 맵에 정의된 Zerg 종족을 사용하는 기존 이식 원칙을 유지한다. 기존 군심형 Primal 유닛의 정의는 삭제하지 않고 소환 ID만 데하카판으로 바꿨다. 게임의 원본 자원에 있는 모델·텍스처·소리 경로를 사용하며 해당 파일을 이 환경에서 실행·렌더 검증한 것은 아니다.

재시험: 새 2번 미션에서 반란군 구출 후 저글링 6·라바사우르스 2·히드라 2·바퀴 2가 데하카 외형·무기로 등장하는지 확인한다. 반복 투하·손실 후 재개, 중립 주민 비공격, 공격 모션·투사체·피해·초상화도 확인한다. 게임 실행·공격·잠복·연출·통행은 미검증이다.
