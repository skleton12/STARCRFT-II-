#!/usr/bin/env python3
"""링크 공유된 구글 드라이브 폴더를 통째로 내려받는다 (다른 언어 폴더와 preloadassetdb.txt는 건너뜀).

사용법: python3 tools/drive_download.py 폴더ID=저장경로 [폴더ID=저장경로 ...]

source/ 재생성:
  python3 tools/drive_download.py \\
    1g598JR1Pp5otJ_R4CBgd3UNC1Uwxup8z=source/starcoop/starcoop.sc2mod \\
    1dF-h_PaC8gUT12Grp59TGlCqlsDEEB_T=source/starcoop/commanders/arcturusmengsk.sc2mod \\
    1P68eHd6zGa9VBY2IbA-qQXNne08lWYRo=source/alliedcommanders.sc2mod
  python3 tools/extract_commander.py
"""
import re, sys, os, urllib.request, html, concurrent.futures as cf
SKIP_LOCALES = {'dede','eses','esmx','frfr','itit','plpl','ptbr','ruru','zhcn','zhtw'}
SKIP_FILES = {'preloadassetdb.txt'}
def get(url):
    with urllib.request.urlopen(url, timeout=120) as r: return r.read()
def ls(fid):
    h = get(f"https://drive.google.com/embeddedfolderview?id={fid}").decode('utf-8','replace')
    out=[]
    for m in re.finditer(r'<div class="flip-entry" id="entry-([^"]+)".*?<a href="([^"]+)".*?flip-entry-title">([^<]+)<', h, re.S):
        i,href,name=m.group(1),m.group(2),html.unescape(m.group(3))
        out.append((i,name,'/folders/' in href))
    return out
jobs=[]
def walk(fid, path):
    for i,name,isdir in ls(fid):
        if isdir:
            if name.split('.')[0] in SKIP_LOCALES: continue
            walk(i, os.path.join(path,name))
        elif name not in SKIP_FILES:
            jobs.append((i, os.path.join(path,name)))
def dl(j):
    i,p=j; os.makedirs(os.path.dirname(p),exist_ok=True)
    data=get(f"https://drive.usercontent.google.com/download?id={i}&export=download&confirm=t")
    open(p,'wb').write(data); return len(data)
for spec in sys.argv[1:]:
    fid,dest=spec.split('=',1); walk(fid,dest)
print(len(jobs),'files', file=sys.stderr)
with cf.ThreadPoolExecutor(8) as ex: tot=sum(ex.map(dl,jobs))
print('bytes',tot, file=sys.stderr)
