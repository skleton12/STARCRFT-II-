# 0.4.33 연구 전 파편탄 발동 조건 수정

## 확인한 결함

RM4_HaveShrapnel, RM4_HaveSuppression은 CValidatorPlayerRequirement이지만 Find가 없다. core 기본 정의에도 Find=true 지정이 없다. Liberty 원작의 NoMarineShield, MissingMarineShieldUpgrade, MissingZerglingWingsUpgrade가 이를 미연구 검사에 쓰며, PunisherGrenadesResearched는 Find=1로 연구 완료를 검사한다. 앞선 표시는 요구조건 내부의 CompleteOnly만 검사했으므로 검증기 바깥의 반전을 놓쳤다. 0.4.32의 초기화는 이 반전을 고치지 못한다.

각 검증기에 Find=1과 WhichPlayer=Caster를 지정했다. 파편탄은 공격자의 RM4_Shrapnel 완료 후, 억제탄 주변 감속은 공격자의 RM4_Suppression 완료 후에만 통과해야 한다. 비용/시간/연구 명령/배치/효과 수치 변경 없음. 자기가속은 별도 CmdButton 요구조건 경로이며 이번 사용자 답변상 자동 적용 여부는 미확인이다.

## 검사

- tools/check_release.py: 네 임무 통과. 긍정 연구 검증기에 Find=1 및 공격자 지정 누락 시 실패하도록 검사 추가.
- tools/check_marauder_research.py: 표시/선행/중복 방지 및 검증기 완료 전·후 18사례 통과.
- 같은 회귀 검사를 0.4.32에 실행하면 inverted requirement로 실패함을 확인(예상 실패).
- ZIP CRC/전체 XML/파일 목록 통과. 0.4.32 대비 metadata.txt와 TTychus01 validatordata.xml만 변경.
- SC2 실제 실행·Galaxy 컴파일은 미실행. 게임에서 연구 전 피해/연출 없음, 비용을 내고 완료한 뒤 발동, 저장 로드 후 유지 여부를 확인해야 한다.
