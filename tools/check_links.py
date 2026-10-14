#!/usr/bin/env python3
"""맵 데이터에서 빈 연결(가리키는데 맵에도 기본 층에도 없는 ID)을 찾는다.

사용법: python3 tools/check_links.py 맵폴더 [시작ID ...]
시작 ID를 주면 그 엔트리에서 닿는 것만 검사한다.
"""
import os, sys
import xml.etree.ElementTree as ET
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import port_units as P


def main():
    gd = os.path.join(sys.argv[1], 'base.sc2data', 'gamedata')
    starts = sys.argv[2:]
    els = defaultdict(list)
    for fn in os.listdir(gd):
        for el in ET.parse(os.path.join(gd, fn)).getroot():
            if el.get('id'):
                els[el.get('id')].append((fn, el))
    base = set()
    for p in P.BASE_LAYERS:
        base |= {i for _, i in P.load_layer(p)}
    copyids = set()
    for _, p in P.COPY_LAYERS:
        copyids |= {i for _, i in P.load_layer(p)}
    todo = list(starts or els)
    seen, dangling = set(), defaultdict(set)
    while todo:
        i = todo.pop()
        if i in seen:
            continue
        seen.add(i)
        for fn, el in els.get(i, []):
            for node in el.iter():
                for v in list(node.attrib.values()) + ([node.text] if node.text and node.text.strip() else []):
                    for t in P.TOKEN_RE.findall(v):
                        if t in els:
                            if starts:
                                todo.append(t)
                        elif t in copyids and t not in base:
                            dangling[t].add(f'{fn}:{i}')
    for t, src in sorted(dangling.items()):
        print(f'{t:40} <- {sorted(src)[:2]}')
    print(f'빈 연결 후보 {len(dangling)}개 (애니메이션 이름 같은 오탐 포함)')


if __name__ == '__main__':
    main()
