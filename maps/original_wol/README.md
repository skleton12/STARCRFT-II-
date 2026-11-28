# 자유의 날개 원본 맵

드라이브의 추출 원본을 단일 MPQ `.SC2Map`으로 다시 묶은 개발용 자료다. 모드 적용 완료 맵과 구분한다.

| 파일 | 임무 | 상태 |
|---|---|---|
| TRaynor03.SC2Map | 0시를 향하여 (Zero Hour) | 원본 보관, 연구·동맹 추가 미적용 |

2026-10-16: 사용자 요청으로 3번 맵을 우선 등록했다. 나머지 자날 맵은 수집 진행 중이며 아직 이 폴더에 전부 올라온 것은 아니다.

출처: Google Drive `traynor03.sc2map` 폴더 (1RtcVk8x7G3Hgjay33X-c2IHNwv9WDfOq). 34개 원본 구성 파일을 StormLib으로 압축했다. 압축 후 모든 내부 파일을 다시 읽어 원본과 바이트 단위로 비교했다.

- 파일 크기: 1,226,397 bytes
- SHA-256: ff71dc4d23344424f4e8fe5c3b29d070d2dfb26dfbd392092e9158ba037f78f5
- 게임 실행/편집기 로드: 미실행
- 기존 maps/TRaynor02.SC2Map 및 CCM 배포 ZIP: 변경 없음
- 연구 시스템은 구상 단계이며 3번 미션부터 설계해야 한다. 이번 등록은 연구 구현이 아니다.

## thanson01 (The Evacuation, 5번 예정)

2026-10-25: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `thanson01.sc2map`(2026-10-13, 어부지리 `ttychus01.sc2map`과 같은 추출본)에서 39개 파일을 그대로 받았다. 크기 모두 드라이브와 일치. 손대지 않는 원본 보관본이다.

## ttosh01 (Devil's Playground, 레드스톤 III — 5번으로 진행 예정)

2026-10-25: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `ttosh01.sc2map`(2026-10-13)에서 38개 파일을 그대로 받았다. 크기 모두 드라이브와 일치하고, mapscript.galaxy는 공개 SC2GameData(6dd323a) 사본과 줄바꿈만 다르다. 손대지 않는 원본 보관본이다.

## tstory01 (히페리온 허브)

2026-10-27: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `tstory01.sc2map`(2026-10-13)에서 20개 파일을 그대로 받았다. 크기 모두 드라이브와 일치하고, mapscript.galaxy는 공개 SC2GameData(6dd323a) 사본과 줄바꿈만 다르다. 손대지 않는 원본 보관본이다. 언어는 kokr만 있다 (다른 언어는 빌드 때 kokr 영어 부분으로 만든다).

## ttosh02 (Welcome to the Jungle, 정글의 법칙 — 7번)

2026-11-22: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `ttosh02.sc2map`(2026-10-13)에서 36개 파일을 그대로 받았다. 크기 모두 드라이브와 일치. 손대지 않는 원본 보관본이다 (behaviordata·lightdata 없음, 드라이브에도 없음).

## ttychus02 (The Dig, 정문 돌파 — 나중 미션용)

2026-11-23: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `ttychus02.sc2map`(2026-10-13)에서 38개 파일을 그대로 받았다. 크기 모두 드라이브와 일치. 열차 강도로 잘못 알고 받았으나(열차 강도 = THorner01) 발굴 작업 미션 때 쓰도록 원본 보관본으로 둔다.

## thorner01 (The Great Train Robbery, 대열차 강도 — 8번)

2026-11-23: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `thorner01.sc2map`(2026-10-13)에서 40개 파일을 그대로 받았다. 크기 모두 드라이브와 일치. 손대지 않는 원본 보관본이다.

## thorner02 (Cutthroat, 망자의 항구 — 9번)

2026-11-24: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `thorner02.sc2map`(2026-10-13)에서 37개 파일을 그대로 받았다. 크기 모두 드라이브와 일치. gamedata는 환경 파일 4개뿐(actordata·sounddata·unitdata 없음, 드라이브에도 없음). 손대지 않는 원본 보관본이다.

## ttosh03a · ttosh03b · thorner03 (뉴 폴섬 탈옥·유령의 기회, 발할라 — 10·11번 예정)

2026-11-25: 사용자 드라이브의 블리자드 캠페인 추출 폴더 `ttosh03a.sc2map`(40개)·`ttosh03b.sc2map`(34개)·`thorner03.sc2map`(34개)을 tools/drive_download.py로 받았다(다른 언어·preloadassetdb 제외). 손대지 않는 원본 보관본이다.

## thorner04 (Media Blitz, 미디어 전격전 — 12번)

2026-11-26: 사용자 드라이브의 추출 폴더 `thorner04.sc2map`(36개)을 tools/drive_download.py로 받았다. 손대지 않는 원본 보관본이다.

## thorner05s (Piercing the Shroud, 장막 너머로 — 13번 비밀 임무)

2026-11-28: 사용자 드라이브의 추출 폴더 `thorner05s.sc2map`(36개)을 tools/drive_download.py로 받았다. 손대지 않는 원본 보관본이다.
