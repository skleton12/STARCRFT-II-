#!/usr/bin/env python3
"""자날 CCM(커스텀 캠페인) zip을 만든다.

구조 (원시저그 프로젝트 분석 노트 #1의 CCM 구조를 따름):
  <ZIP_NAME>.zip
  ├─ metadata.txt          title/desc/author/campaign/version 5줄
  └─ TRaynor01.SC2Map      원본과 같은 파일명 (바꿔치기)

공용 데이터를 담을 .SC2Mod는 아직 없다. 지금 바뀐 내용(레이너 해병 → 전쟁광)은
맵 트리거 안에서만 바뀌기 때문이다. 모드가 필요해지면 여기에 추가한다.
"""
import os, shutil, subprocess, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BUILD = os.path.join(ROOT, 'build')
STAGE = os.path.join(BUILD, 'ccm')

# 제목과 zip 이름은 임시. 사용자가 정하면 바꾼다
METADATA = {
    'title': 'Raynor Mercenaries (WoL Co-op)',
    'desc': 'Wings of Liberty rebuilt as a co-op campaign: Raynor commands only mercenaries, fighting alongside two AI allies',
    'author': 'dy7043',
    'campaign': 'WoL',
    'version': '0.1',
}
ZIP_NAME = 'RaynorMercs_WoL_CCM'

# 미션별 패치 스크립트와 결과 맵
MAPS = [
    ('patch_mission01.py', 'TRaynor01.SC2Map'),
]


def main():
    if os.path.exists(STAGE):
        shutil.rmtree(STAGE)
    os.makedirs(STAGE)
    with open(os.path.join(STAGE, 'metadata.txt'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(''.join(f'{k}={v}\n' for k, v in METADATA.items()))
    for script, name in MAPS:
        subprocess.run([sys.executable, os.path.join(ROOT, 'tools', script)], check=True, stdout=subprocess.DEVNULL)
        shutil.copytree(os.path.join(BUILD, name), os.path.join(STAGE, name))

    out = os.path.join(BUILD, ZIP_NAME + '.zip')
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for dirpath, _, files in os.walk(STAGE):
            for fn in sorted(files):
                p = os.path.join(dirpath, fn)
                z.write(p, os.path.relpath(p, STAGE))
    print(out)


if __name__ == '__main__':
    main()
