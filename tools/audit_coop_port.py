#!/usr/bin/env python3
"""맵 데이터에서 협동전 원본(starcoop·멩스크·공허)과 같은 ID를 가진 레코드를 원본과 비교한다.

사용법: python3 tools/audit_coop_port.py 맵폴더   (빠진 항목 -, 더한 항목 +)
"""
import glob,sys,re,collections
import xml.etree.ElementTree as ET
S='/home/user/STARCRFT-II-/source/'
COOP=[S+'starcoop/starcoop.sc2mod',S+'starcoop/commanders/arcturusmengsk.sc2mod',S+'voidmulti.sc2mod',S+'void.sc2mod']
def load(L):
    d={}
    for f in glob.glob(L+'/base.sc2data/gamedata/*.xml'):
        for el in ET.parse(f).getroot():
            if el.get('id'): d[(f.split('/')[-1],el.get('id'))]=el
    return d
src={}
for L in COOP:
    for k,v in load(L).items(): src.setdefault(k,(L.split('/')[-1],v))
def items(el):
    out=collections.Counter()
    for c in el:
        out[(c.tag,tuple(sorted(c.attrib.items())),ET.tostring(c,encoding='unicode').count('<'))]+=1
    return out
MAP=sys.argv[1]
mp=load(MAP)
stats=collections.Counter(); rows=[]
for k,el in mp.items():
    if k not in src: continue
    name,s=src[k]
    a,b=items(el),items(s)
    miss=b-a; extra=a-b
    if not miss and not extra and el.get('parent')==s.get('parent'): stats['same']+=1; continue
    stats['diff']+=1
    rows.append((k,name,len(miss),len(extra),[m[0]+':'+','.join(f'{x}={y}' for x,y in m[1])[:90] for m in list(miss)[:4]],[m[0]+':'+','.join(f'{x}={y}' for x,y in m[1])[:90] for m in list(extra)[:4]]))
print(MAP.split('/')[-1],dict(stats))
for r in sorted(rows,key=lambda r:-r[2]):
    print(r[0][0],r[0][1],'from',r[1],'missing',r[2],'added',r[3]); print('   -',r[4]); print('   +',r[5])
