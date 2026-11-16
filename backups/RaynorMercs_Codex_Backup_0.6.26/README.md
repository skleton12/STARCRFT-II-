# 레이너 용병 캠페인 0.6.26 백업

Codex에서 작업했던 0.6.26의 ZIP, 수정 내역, 동맹 3단계 업그레이드 설계 문서입니다.

ZIP 크기는 109,370,603바이트입니다. GitHub의 일반 파일 크기 제한에 맞춰 원본 ZIP을 14개 파일로 나눴습니다.

## Windows에서 원본 ZIP 복원

1. 이 브랜치를 **Code → Download ZIP**으로 내려받아 압축을 풉니다.
2. 이 폴더에서 PowerShell을 열고 아래 명령을 실행합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\restore_zip.ps1
```

같은 폴더에 `RaynorMercs_WoL_CCM.zip`이 생성됩니다. 스크립트는 SHA-256을 대조하며 같은 이름의 ZIP이 있으면 중단합니다.

```text
833c92c252d49d621b477a53387e98d4e602b6fce41fc33ead3fc64151c9cd3e
```
