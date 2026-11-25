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
cand = {i for i in src if i not in base}
seen, todo = set(), [r for r in roots if r in cand]
while todo:
    i = todo.pop()
    if i in seen: continue
    seen.add(i)
    for fn, body in src[i]:
        for tok in set(re.findall(r'[A-Za-z_][A-Za-z0-9_@]*', body)):
            if tok in cand and tok not in seen and not tok.startswith(('RM', 'gv_')): todo.append(tok)
for i in sorted(seen): print(i, ','.join(sorted({f for f, _ in src[i]})))
