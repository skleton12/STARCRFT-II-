# 자날 협동 CCM

```bash
python3 tools/build_ccm.py   # build/RaynorMercs_WoL_CCM.zip
```

다른 컴퓨터에서 이어서 만들기: [`docs/SETUP.md`](docs/SETUP.md) (저장소 받기 → `tools/setup_source.py`로 원본 데이터 넣기 → 빌드)

CCM 구조: `metadata.txt` + 원본과 같은 파일명의 미션 맵(바꿔치기). 공용 데이터 `.SC2Mod`는 필요해지면 추가.

## 협동전 사령관 데이터

협동전 사령관 5명(피닉스, 알라라크, 제라툴, 멩스크, 데하카)의 데이터를 뽑아
자유의 날개(Liberty) 모드로 옮겨 붙이기 위한 작업 공간.

## 폴더

| 경로 | 내용 |
|---|---|
| `source/` | CascView로 꺼낸 원본 (`mods/starcoop/...`), 드라이브에서 내려받음 |
| `coop/<사령관>/` | 추출 결과 |
| `tools/extract_commander.py` | 협동전 사령관 추출기 |
| `tools/lookup_upgrade.py` | 연구 이름/비용/효과 조회 |
| `tools/drive_download.py` | 드라이브 폴더 내려받기 |
| `tools/patch_mission01.py` | 1번 미션 패치 → `build/TRaynor01.SC2Map` |
| `tools/port_units.py` | 다른 캠페인·협동전 유닛을 맵 데이터로 복사 |
| `tools/check_links.py` | 맵 데이터의 빈 연결 검사 |
| `tools/fetch_assets.py` | 에셋을 맵 안에 넣기 (원본 에셋 필요, 아직 미사용) |
| `tools/build_ccm.py` | CCM zip 빌드 → `build/RaynorMercs_WoL_CCM.zip` |
| `tools/patch_mission02.py` | 2번 미션 패치 → `build/TRaynor02.SC2Map` |
| `tools/setup_source.py` / `make_source_pack.py` | 새 컴퓨터에 원본 데이터 넣기 / 묶기 |
| `tools/render_map.py`, `expand_map.py`, `pack_sc2map.py`, `make_edit_map02.py` | 지형 그림, 지형 확장, 단일 맵 파일, 편집용 맵 |
| `docs/` | 기획 결정, 미션별 문서, 연구 조사, 진행 보고서(`docs/REPORT.md`) |

`source/`, `coop/`, `build/`는 블리자드 데이터라서 `.gitignore`로 빼 두었다.

## 원본 위치 (CascView)

```
mods/starcoop/starcoop.sc2mod/           협동전 본체 (피닉스, 알라라크, 데하카, 제라툴 일부)
mods/starcoop/commanders/arcturusmengsk.sc2mod/   멩스크
mods/alliedcommanders.sc2mod/            문자열만 있는 껍데기
```

## 추출 결과 (`coop/<사령관>/`)

- `gamedata/*.xml`: 그 사령관 엔트리 + 그 엔트리만 쓰는 하위 엔트리(효과, 행동, 액터, 무기 등)
- `shared_deps.txt`: 참조는 하지만 다른 데이터와 같이 쓰는 공용 엔트리 목록. 복사하지 않았으니 모드에서 따로 챙기거나 기본 게임 것을 쓴다
- `assets.txt`: 참조하는 모델/텍스처/소리 경로. CascView에서 이 목록대로 꺼내면 된다
- `kokr/`, `enus/`: 해당 엔트리의 문자열
- `summary.json`: 파일별 개수

추출 규칙: ID에 사령관 이름(예: `Fenix`, `Alarak|Taldarim`, `Dehaka|Primal`)이 들어간 엔트리에서 시작해
참조를 따라간다. 4곳 이상에서 참조되는 엔트리는 공용으로 보고 `shared_deps.txt`에만 적는다.
멩스크는 전용 모드에 새로 정의된 엔트리 전부가 시작점이다.

```bash
python3 tools/extract_commander.py            # 전부
python3 tools/extract_commander.py dehaka     # 하나만
```

## 알려진 빈 곳

- **제라툴**: 협동전 제라툴 본체(유닛, 마스터 힘)가 `starcoop`에 없다. 멩스크 모드의 종속성
  `bnet:Co-op Mission`(배틀넷 캐시로 받는 모드)에 들어 있는 것으로 보인다. 지금 `coop/zeratul`에는
  위신(Prestige), 공허 추적자 같은 일부만 있다.
- 자날 모드에는 공허의 유산·군단의 심장 에셋이 기본으로 없으므로, 모드 종속성에 `Void`/`Swarm` 계열을
  추가하거나 `assets.txt`의 파일을 직접 넣어야 한다.
