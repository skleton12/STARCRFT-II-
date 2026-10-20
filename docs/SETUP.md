# 다른 컴퓨터에서 이어서 만들기

저장소에는 도구·문서만 있고 블리자드 원본 데이터(`source/`)는 없다 (공개 저장소라 올리지 않음).
새 컴퓨터에서는 **저장소 받기 → 원본 데이터 넣기 → 빌드** 세 단계다.

## 1. 준비물

- Python 3.9 이상 (Windows는 python.org 설치 시 "Add to PATH" 체크)
- Git
- `source_pack.zip` — 원본 데이터 묶음 (약 16MB). 개인 드라이브 등 **비공개 위치**에만 보관

## 2. 저장소 받기

```bash
git clone https://github.com/skleton12/STARCRFT-II-.git
cd STARCRFT-II-
git checkout claude/lucid-franklin-ed0eko
pip install -r requirements.txt
```

Windows에서는 `python3` 대신 `python`(또는 `py`)을 쓴다.

## 3. 원본 데이터 넣기

```bash
python3 tools/setup_source.py 내려받은경로/source_pack.zip
```

드라이브에 올리고 "링크가 있는 모든 사용자"로 공유했다면 파일 ID로 바로 받을 수도 있다:

```bash
python3 tools/setup_source.py --drive 드라이브파일ID
```

`source/` 밖으로 풀리는 항목은 무시하고, 빌드에 필요한 경로가 빠지면 알려 준다.

`source_pack.zip`이 없을 때 (2026-10-20 확인): 게임 데이터 XML은 공개 사본 [SC2Mapster/SC2GameData](https://github.com/SC2Mapster/SC2GameData)(스냅샷 6dd323a)에서 `mods/…`·`campaigns/…`의 `base.sc2data/GameData/*.xml`을 `source/<이름>/base.sc2data/gamedata/`에 소문자 파일명으로 복사하면 `check_release.py`가 돈다. 맵 원본·에셋은 들어 있지 않아 빌드 도구 일부는 여전히 묶음이 필요하다.

2026-10-15 이전에 만든 묶음에는 자날 기본 모드 게임 데이터가 없다. 그때는 `python3 tools/fetch_liberty_data.py`로 받는다 (2번 미션 빌드에 필요).

## 4. 빌드

```bash
python3 tools/build_ccm.py      # build/RaynorMercs_WoL_CCM.zip (1·2번 미션)
```

게임에 넣기: zip을 `StarCraft II/Maps/` 아래에 풀거나 CCM 방식대로 설치한다.

## 도구별 추가 준비물 (필요할 때만)

| 도구 | 필요 |
|---|---|
| `tools/patch_mission01.py`, `patch_mission02.py`, `build_ccm.py`, `port_units.py` | Python 기본 라이브러리만 |
| `tools/render_map.py`, `tools/expand_map.py` | `numpy`, `pillow` |
| `tools/pack_sc2map.py` (편집기용 단일 `.SC2Map`) | StormLib 공유 라이브러리. 빌드: `cmake .. -DBUILD_SHARED_LIBS=ON -DSTORM_USE_BUNDLED_LIBRARIES=ON && make`, 실행 시 `STORMLIB=경로/libstorm.so` (Windows는 `StormLib.dll`) |
| `tools/drive_download.py` | 드라이브 폴더가 링크 공유 상태일 것 |

## 원본 데이터 묶음 다시 만들기

`source/`가 있는 컴퓨터에서:

```bash
python3 tools/make_source_pack.py   # build/source_pack.zip
```

## 지켜야 할 것

- 작업 규칙은 `CLAUDE.md`, 결정 기록은 `docs/DECISIONS.md`. 새 컴퓨터의 클로드도 이 두 파일을 기준으로 이어 간다.
- 미션 맵은 편집기로 저장하지 않는다 (동맹 코드가 사라짐). 항상 패치 도구로 원본에서 다시 만든다.
- `source/`, `build/`, `source_pack.zip`은 git에 올리지 않는다.
