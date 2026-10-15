#!/usr/bin/env python3
"""새 컴퓨터에서 source/ (블리자드 원본 데이터)를 채운다.

사용:
  python3 tools/setup_source.py 경로/source_pack.zip      # 내려받아 둔 zip
  python3 tools/setup_source.py --drive 드라이브파일ID      # 링크 공유한 구글 드라이브 zip
source_pack.zip은 기존 컴퓨터에서 tools/make_source_pack.py로 만든다.
"""
import io, os, sys, urllib.request, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 빌드에 꼭 필요한 경로 (패치·유닛 이식 도구가 읽음)
REQUIRED = [
    'source/liberty.sc2campaign/base.sc2maps/maps/campaign/traynor01.sc2map/mapscript.galaxy',
    'source/liberty.sc2campaign/base.sc2maps/maps/campaign/traynor02.sc2map/mapscript.galaxy',
    'source/core.sc2mod/base.sc2data/gamedata',
    'source/liberty.sc2campaign/base.sc2data/gamedata',
    'source/libertystory.sc2campaign/base.sc2data/gamedata',
    'source/swarm.sc2mod/base.sc2data/gamedata',
    'source/void.sc2mod/base.sc2data/gamedata',
    'source/voidmulti.sc2mod/base.sc2data/gamedata',
    'source/swarm.sc2campaign/base.sc2data/gamedata',
    'source/void.sc2campaign/base.sc2data/gamedata',
    'source/starcoop/starcoop.sc2mod/base.sc2data/gamedata',
    'source/liberty.sc2mod/base.sc2data/gamedata/abildata.xml',  # 없으면 tools/fetch_liberty_data.py
]


def load(arg):
    if arg == '--drive':
        fid = sys.argv[2]
        url = f'https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t'
        print('내려받는 중:', fid)
        with urllib.request.urlopen(url, timeout=600) as r:
            return zipfile.ZipFile(io.BytesIO(r.read()))
    return zipfile.ZipFile(arg)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    z = load(sys.argv[1])
    root = os.path.realpath(ROOT)
    n = 0
    for info in z.infolist():
        name = info.filename
        dest = os.path.realpath(os.path.join(ROOT, name))
        if not name.startswith('source/') or not dest.startswith(root + os.sep):
            continue  # source/ 밖으로 풀리는 항목은 무시
        if info.is_dir():
            continue
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with z.open(info) as s, open(dest, 'wb') as d:
            d.write(s.read())
        n += 1
    missing = [p for p in REQUIRED if not os.path.exists(os.path.join(ROOT, p))]
    print(f'{n}개 파일 풀림')
    if missing:
        sys.exit('빠진 경로:\n  ' + '\n  '.join(missing))
    print('준비 완료. 빌드: python3 tools/build_ccm.py')


if __name__ == '__main__':
    main()
