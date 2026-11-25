import re, sys, glob, os
from collections import defaultdict
SRC = sys.argv[1]; roots = sys.argv[2].split(','); base_dirs = sys.argv[3].split(',')
REC = re.compile(r'(?m)^[ \t]*<(C\w+)\s[^>]*?\bid="([^"]+)"[^>]*?(?:/>|>.*?</\1>)', re.S)
def recs(d):
    out = defaultdict(list)
    for f in sorted(glob.glob(d + '/*.xml')):
        t = open(f, encoding='utf-8').read()
        for m in REC.finditer(t): out[m.group(2)].append((os.path.basename(f), m.group(0)))
    return out
src = recs(SRC)
base = set()
for d in base_dirs:
    for f in glob.glob(d + '/*.xml'):
        base |= set(re.findall(r'\bid="([^"]+)"', open(f, encoding='utf-8', errors='replace').read()))
OPT = dict(a.split('=', 1) if '=' in a else (a, '.') for a in sys.argv[4:])
# allow=REGEX (0.10.2): also take the map's override of a base id when it matches (e.g. ZealotPurifier legionnaire stats)
ALLOW = re.compile(OPT['allow']) if 'allow' in OPT else None
cand = {i for i in src if i not in base or (ALLOW and ALLOW.search(i))}
# skip=REGEX (0.10.6): never follow ids matching it (e.g. merge/level-3 branches)
if 'skip' in OPT: cand = {i for i in cand if not re.search(OPT['skip'], i)}
seen, todo = set(), [r for r in roots if r in cand]
while todo:
    i = todo.pop()
    if i in seen: continue
    seen.add(i)
    for fn, body in src[i]:
        for tok in set(re.findall(r'[A-Za-z_][A-Za-z0-9_@]*', body)):
            if tok in cand and tok not in seen and not tok.startswith(('RM', 'gv_')): todo.append(tok)
# reverse pass (0.10.2): actors that point AT the chosen records (attack actions, missiles, turrets)
# are not reachable forward. Pull actordata records that mention a chosen id used by few records.
if 'reverse' in OPT:
    seed = re.compile(OPT['reverse'])
    refs = defaultdict(set)
    for i in cand:
        for fn, body in src[i]:
            for tok in set(re.findall(r'[A-Za-z_][A-Za-z0-9_@]*', body)):
                if tok in cand and tok != i: refs[tok].add(i)
    changed = True
    while changed:
        changed = False
        for i in sorted(cand - seen):
            if not any(fn == 'actordata.xml' for fn, _ in src[i]): continue
            body = ' '.join(b for _, b in src[i])
            toks = set(re.findall(r'[A-Za-z_][A-Za-z0-9_@]*', body))
            if any(t in seen and len(refs[t]) <= 6 and not t.startswith('RM') and seed.search(t) for t in toks):
                todo = [i]
                while todo:
                    j = todo.pop()
                    if j in seen: continue
                    seen.add(j); changed = True
                    for fn, b in src[j]:
                        for tok in set(re.findall(r'[A-Za-z_][A-Za-z0-9_@]*', b)):
                            if tok in cand and tok not in seen and not tok.startswith(('RM', 'gv_')): todo.append(tok)
for i in sorted(seen): print(i, ','.join(sorted({f for f, _ in src[i]})))
