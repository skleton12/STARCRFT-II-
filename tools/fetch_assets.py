#!/usr/bin/env python3
"""데이터가 참조하는 에셋(모델·텍스처·소리)을 드라이브의 CascView 추출본에서 찾아 맵 안에 넣는다.

맵이 이미 불러오는 묶음(core, 자날 모드·캠페인)에 있는 파일은 건너뛴다.
공허·군심 묶음에만 있는 파일을 맵 폴더의 같은 경로(Assets/...)로 복사한다.
.m3 모델 안에서 참조하는 텍스처도 따라가 함께 가져온다.

사용법: python3 tools/fetch_assets.py 맵폴더
"""
import os, re, sys, json, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drive_download import ls, get

# 드라이브의 각 묶음 base.sc2assets 폴더 (CascView 추출본, 이름은 소문자)
AVAILABLE = {  # 맵이 이미 불러오는 묶음
    'core': ('14s_9pK98CZ94JoU9mbeHeTM--AJ3OEzU', 'base.sc2assets'),
    'liberty.sc2mod': ('18fnk7T4a56RcMGedmRVMsxFSXYBdCRdl', 'base.sc2assets'),
    'liberty.sc2campaign': ('16dsf4D-x1OTjzwB1lBAU8ScVWRx8pjx6', 'base.sc2assets'),
}
SOURCES = {  # 맵 안에 복사해 넣을 원본 묶음 (앞쪽 우선)
    'void.sc2campaign': ('1dNseNYLXYRi5ju-ViFrbThhyyAP3a44o', 'base.sc2assets'),
    'swarm.sc2campaign': ('146No6uTNn_bNqv_MRHq_c-cF2GWgM3Wz', 'base.sc2assets'),
    'void.sc2mod': ('1yLDzuir3Iu6sEPlfsNNC3XhzE-T02vPv', 'base.sc2assets'),
}
ASSET_RE = re.compile(r'Assets[\\/][^"<>\x00]*?\.(?:m3|dds|ogg|wav|tga)', re.I)

_cache = {}


def listing(fid):
    if fid not in _cache:
        _cache[fid] = {n.lower(): (i, d) for i, n, d in ls(fid)}
    return _cache[fid]


def find(root, path):
    """root 폴더에서 경로를 한 칸씩 내려가며 파일 ID를 찾는다 (대소문자 무시)."""
    fid, sub = root
    try:
        cur = listing(fid)[sub][0]
        parts = re.split(r'[\\/]', path)
        for i, part in enumerate(parts):
            ent = listing(cur).get(part.lower())
            if ent is None:
                return None
            cur = ent[0]
        return cur
    except Exception:
        return None


def main():
    map_dir = sys.argv[1]
    gdir = os.path.join(map_dir, 'base.sc2data', 'gamedata')
    todo = set()
    for fn in os.listdir(gdir):
        with open(os.path.join(gdir, fn), encoding='utf-8', errors='replace') as f:
            todo |= {a.replace('/', '\\') for a in ASSET_RE.findall(f.read())}
    done, report = set(), {'already_available': [], 'copied': [], 'missing': []}
    while todo:
        a = todo.pop()
        if a.lower() in done:
            continue
        done.add(a.lower())
        if any(find(r, a) for r in AVAILABLE.values()):
            report['already_available'].append(a)
            continue
        for name, r in SOURCES.items():
            fid = find(r, a)
            if fid:
                data = get(f'https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t')
                dest = os.path.join(map_dir, *re.split(r'[\\/]', a))
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                with open(dest, 'wb') as f:
                    f.write(data)
                report['copied'].append(f'{a}  <- {name} ({len(data)} B)')
                if a.lower().endswith('.m3'):
                    todo |= {x.decode('latin-1').replace('/', '\\') for x in re.findall(rb'Assets[\\/][^"<>\x00]*?\.(?:dds|tga)', data, re.I)}
                break
        else:
            report['missing'].append(a)
    with open(os.path.join(map_dir, 'ported_assets.json'), 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    print({k: len(v) for k, v in report.items()})


if __name__ == '__main__':
    main()
