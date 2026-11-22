# 배포 ZIP 조각

GitHub는 파일 하나가 100MiB를 넘으면 받지 않는다. 그래서 전체 ZIP(`RaynorMercs_WoL_CCM.zip`)을 45MiB 조각으로 나눠 여기에 둔다 (0.6.74부터).
사용자에게는 항상 합친 전체 ZIP을 준다. 조각 목록과 해시는 `SHA256SUMS.txt`.

- 합치기 (저장소 최상위에서): `python3 tools/split_release.py --join` → `releases/RaynorMercs_WoL_CCM.zip` (조각 목록·해시 확인 후 씀)
- 나누기 (빌드 뒤, 커밋 전에): `python3 tools/split_release.py`
- 도구 없이 (이 폴더에서): `SHA256SUMS.txt`에 적힌 조각을 번호 순서대로 이어 붙인 뒤 `sha256sum RaynorMercs_WoL_CCM.zip`이 마지막 줄과 같은지 확인
