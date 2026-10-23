# 0.4.67 — 이지스 공격의 암묵적 탄환 유닛 누락

사용자는 이지스가 공격 중 자폭하듯 사라지는지 확인을 요청했다. 기본 공격에서 파편까지 대상·자기 피해 경로를 확인하던 중, PunisherGrenadesMengskLM이 사용할 실제 유닛 PunisherGrenadesMengskLMWeapon이 맵에 없음을 발견했다. 같은 이름의 모델과 이를 unitName으로 사용하는 MarauderMengskAttackMissile 액터는 이미 있었다.

Core CEffectLaunchMissile의 기본 AmmoUnit은 `##id##Weapon`이다. 따라서 이 발사 효과는 AmmoUnit을 명시하지 않아도 PunisherGrenadesMengskLMWeapon을 요구한다. 기존 이식/연결 검사는 명시적인 링크만 검사하여 이 누락을 놓쳤다. 원본 arcturusmengsk.sc2mod에는 해당 CUnit(parent MISSILE, Mover PunisherGrenadesWeapon, Race Terr)이 존재한다.

원본 출처: SC2Mapster/SC2GameData 6dd323aae4209a01f110719a00b4e8f7a88389bc. 해당 투사체 유닛을 그대로 추가하고 발사 효과에 AmmoUnit을 명시했다. 기존 모델·액터·무기·피해량·보호막·경험치는 변경하지 않는다. 이는 확인된 공격 이식 결함의 복구다. 없는 AmmoUnit이 실제 게임에서 발사자 소실을 일으켰는지, 사용자가 관찰한 현상의 원인인지는 게임에서 확인되지 않았다. 앞선 '자폭 효과 없음' 결론은 이 암묵적 참조 점검을 포함하지 못했다.

검증: 0.4.66의 투사체 누락 재현, 복구 유닛이 원본 속성/자식 필드와 일치, 기존 모든 유닛 레코드 보존, 해당 발사 효과 이외 효과 보존, 파편 SearchFilters의 Self/Player/Ally 제외 확인, 전체 check_release 통과. 변경 ZIP 항목은 metadata·4번 unitdata·4번 effectdata뿐이다. 실제 SC2·Galaxy 컴파일은 미실행이다. 다음 게임 확인은 새 어부지리에서 이지스가 탄환을 발사하는 동안 남아 있는지 확인한다.

재현: `python3 tools/build_v0467.py <0.4.66 ZIP> <새 출력 ZIP>`
