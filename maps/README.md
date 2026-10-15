# 빌드한 미션 맵

| 파일 | 내용 | 버전 |
|---|---|---|
| `TRaynor02.SC2Map` | 2번 미션(무법자) 패치 결과, 단일 파일(MPQ). 동쪽 새 지형 확장 184x136, 동맹 진영 동쪽, 텍스처 버그 수정, 새 장식물 없음 | 0.2.5 |

- 사용자 지시 (2026-10-15)로 올린 빌드 결과물이다. 원본은 `tools/patch_mission02.py`로 다시 만든다.
- **편집기로 저장하지 않는다** (동맹·용병 코드가 `mapscript.galaxy`에만 있어 저장하면 사라짐).
- 만들기: `python3 tools/patch_mission02.py` → `STORMLIB=경로/libstorm.so python3 tools/pack_sc2map.py build/TRaynor02.SC2Map maps/TRaynor02.SC2Map`
- 게임·편집기에서 연 검증은 미실행.
