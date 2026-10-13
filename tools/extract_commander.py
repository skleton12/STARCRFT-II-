#!/usr/bin/env python3
"""협동전 사령관 데이터 추출기.

starcoop.sc2mod(+사령관 모드)의 GameData XML에서 특정 사령관 관련 엔트리만 골라
참조를 따라가며(부모, 효과, 행동, 액터 등) 필요한 엔트리를 모은 뒤
사령관별 폴더로 따로 저장한다. 자날(Liberty) 모드에 옮겨 붙이기 위한 재료용.

사용법: python3 tools/extract_commander.py [사령관 ...]
"""
import os, re, sys, json
import xml.etree.ElementTree as ET
from collections import defaultdict, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'starcoop')
MODS = OrderedDict([
    ('starcoop', os.path.join(SRC, 'starcoop.sc2mod')),
    ('mengsk', os.path.join(SRC, 'commanders', 'arcturusmengsk.sc2mod')),
])
OUT = os.path.join(ROOT, 'coop')

# 사령관별 시작점: (엔트리 ID 정규식, 제외 정규식, 통째로 포함할 모드)
COMMANDERS = {
    'fenix':   dict(ko='피닉스',   seed=r'Fenix', exclude=r'Mutator'),
    'alarak':  dict(ko='알라라크', seed=r'Alarak|Tal[dD]arim', exclude=r'Mutator'),
    'zeratul': dict(ko='제라툴',   seed=r'Zeratul', exclude=r'Mutator|AmonZeratul'),
    'mengsk':  dict(ko='멩스크',   seed=r'Mengsk', exclude=r'Mutator', whole_mod='mengsk'),
    'dehaka':  dict(ko='데하카',   seed=r'Dehaka|Primal', exclude=r'Mutator'),
}

ASSET_RE = re.compile(r'[\w\\/.-]+\.(?:m3|m3a|dds|tga|ogg|wav|sc2layout|fxa)\b', re.I)
TOKEN_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_@]*')
# 이보다 많은 엔트리가 참조하면 공용으로 본다
SHARED_LIMIT = 3


def load_catalogs():
    """(파일명, ID) -> [(모드, 요소)] 와 ID -> {파일명} 인덱스를 만든다."""
    entries = defaultdict(list)
    by_id = defaultdict(set)
    order = defaultdict(list)
    for mod, path in MODS.items():
        gd = os.path.join(path, 'base.sc2data', 'gamedata')
        for dirpath, _, files in os.walk(gd):
            for fn in sorted(files):
                if not fn.endswith('.xml'):
                    continue
                rel = os.path.relpath(os.path.join(dirpath, fn), gd)
                try:
                    root = ET.parse(os.path.join(dirpath, fn)).getroot()
                except ET.ParseError:
                    continue
                for el in root:
                    eid = el.get('id')
                    if eid is None:
                        continue
                    key = (rel, eid)
                    if key not in entries:
                        order[rel].append(eid)
                    entries[key].append((mod, el))
                    by_id[eid].add(rel)
    return entries, by_id, order


def refs_of(el):
    """요소 안의 모든 속성값/텍스트에서 참조 후보 토큰을 뽑는다."""
    toks, assets = set(), set()
    for node in el.iter():
        vals = list(node.attrib.values())
        if node.text and node.text.strip():
            vals.append(node.text)
        for v in vals:
            assets.update(ASSET_RE.findall(v))
            toks.update(TOKEN_RE.findall(v))
    return toks, assets


def referrer_counts(entries, by_id):
    """각 엔트리를 참조하는 서로 다른 엔트리 수. 많이 참조될수록 공용 데이터다."""
    cnt = defaultdict(int)
    for key, items in entries.items():
        targets = set()
        for _, el in items:
            toks, _ = refs_of(el)
            for t in toks:
                if t != key[1]:
                    targets.update((rel, t) for rel in by_id.get(t, ()))
        for k in targets:
            cnt[k] += 1
    return cnt


def extract(name, cfg, entries, by_id, order, refcnt):
    seed_re, excl_re = re.compile(cfg['seed']), re.compile(cfg['exclude'])
    selected, queue = set(), []
    for (rel, eid), items in entries.items():
        # 사령관 전용 모드에서 새로 정의한 엔트리만 통째로 (다른 사령관 덮어쓰기는 제외)
        whole = cfg.get('whole_mod') and all(m == cfg['whole_mod'] for m, _ in items)
        if whole or (seed_re.search(eid) and not excl_re.search(eid)):
            selected.add((rel, eid)); queue.append((rel, eid))
    seeds = set(selected)
    assets = set()
    shared = set()
    while queue:
        key = queue.pop()
        for _, el in entries[key]:
            toks, a = refs_of(el)
            assets |= a
            for t in toks:
                if excl_re.search(t):
                    continue
                for rel in by_id.get(t, ()):
                    k = (rel, t)
                    if k in selected or k in shared:
                        continue
                    # 여러 곳에서 쓰는 공용 엔트리는 복사하지 않고 목록으로만 남긴다
                    if refcnt[k] > SHARED_LIMIT and not seed_re.search(t):
                        shared.add(k)
                    else:
                        selected.add(k); queue.append(k)

    out = os.path.join(OUT, name)
    gd_out = os.path.join(out, 'gamedata')
    os.makedirs(gd_out, exist_ok=True)
    stats = {}
    ids = set()
    for rel in sorted(order):
        keep = [eid for eid in order[rel] if (rel, eid) in selected]
        if not keep:
            continue
        cat = ET.Element('Catalog')
        for eid in keep:
            for _, el in entries[(rel, eid)]:
                cat.append(el)
        ET.indent(cat, space='    ')
        dest = os.path.join(gd_out, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        ET.ElementTree(cat).write(dest, encoding='utf-8', xml_declaration=True)
        n_seed = sum((rel, e) in seeds for e in keep)
        stats[rel] = dict(total=len(keep), direct=n_seed, via_refs=len(keep) - n_seed)
        ids.update(keep)

    # 문자열: 키의 마지막 경로 조각이 선택된 ID인 줄만
    for loc in ('kokr', 'enus'):
        lines = defaultdict(list)
        for mod, path in MODS.items():
            ld = os.path.join(path, f'{loc}.sc2data', 'localizeddata')
            if not os.path.isdir(ld):
                continue
            for fn in ('gamestrings.txt', 'objectstrings.txt', 'gamehotkeys.txt'):
                p = os.path.join(ld, fn)
                if not os.path.exists(p):
                    continue
                with open(p, encoding='utf-8-sig', errors='replace') as f:
                    for line in f:
                        k = line.split('=', 1)[0]
                        parts = k.split('/')
                        if any(seg in ids for seg in parts[1:]):
                            lines[fn].append(line.rstrip('\r\n'))
        for fn, ls in lines.items():
            d = os.path.join(out, loc)
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, fn), 'w', encoding='utf-8') as f:
                f.write('\n'.join(ls) + '\n')

    with open(os.path.join(out, 'shared_deps.txt'), 'w', encoding='utf-8') as f:
        f.write('# 이 사령관이 참조하지만 다른 데이터와 같이 쓰는 공용 엔트리 (파일<TAB>ID<TAB>참조 수)\n')
        for rel, eid in sorted(shared):
            f.write(f'{rel}\t{eid}\t{refcnt[(rel, eid)]}\n')
    with open(os.path.join(out, 'assets.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(assets, key=str.lower)) + '\n')
    summary = dict(commander=name, ko=cfg['ko'], entries=sum(s['total'] for s in stats.values()), shared=len(shared),
                   direct=sum(s['direct'] for s in stats.values()), assets=len(assets), files=stats)
    with open(os.path.join(out, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def main():
    names = sys.argv[1:] or list(COMMANDERS)
    entries, by_id, order = load_catalogs()
    refcnt = referrer_counts(entries, by_id)
    for n in names:
        s = extract(n, COMMANDERS[n], entries, by_id, order, refcnt)
        print(f"{n:8} {s['ko']:5} 엔트리 {s['entries']:6} (직접 {s['direct']}) 공용 {s['shared']:5} 에셋 {s['assets']}")


if __name__ == '__main__':
    main()
