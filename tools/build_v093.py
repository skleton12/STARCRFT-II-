#!/usr/bin/env python3
"""0.9.2 -> 0.9.3: 동맹 관측선 오류 구 수정 (사용자 2026-11-24 "탐지기 역할하는 놈 오류구로 나옴").

원인: 0.8.8이 동맹 관측선 외형을 Observer_Purifier_Collection 모델로 바꿨는데, 이 모델은 협동전 스킨(컬렉션) 정의라 데이터에
파일 경로(Model)가 없다 — 스킨 시스템 밖(이 맵)에서는 그릴 파일이 없어 빨간 오류 구로 나온다.
수정 (maps 3~9): 파일 경로를 직접 적은 모드 모델 RM9_ObserverPurifier(Assets\\Units\\Protoss\\Observer_Purifier_Collection\\
Observer_Purifier_Collection.m3, 원본 크기·선택 반경·필요 애니메이션 Observer_KaraxAnims 그대로)를 만들고 ModelSwap이 그것을 가리키게
한다. 동맹 소유일 때만 바뀌는 것은 그대로. 원시저그 땅무지 숙주가 뱉는 유닛 모델 CreeperHostSpawn_Primal_Collection도 맵 정의에
파일 경로가 없어 같은 오류 구가 나므로(사용자 "저그 지원군"), 첫 정의에 협동전 데이터의 파일 경로를 넣는다. check_release에
'ModelSwap 대상 *_Collection 모델에 파일 경로가 없음' 검사를 더했다. 동맹 탐사정 외형 바꿈(Probe_Purifier_Collection, 경로 없음)은
동맹 일꾼을 더 내보내지 않으므로 지운다. Game not run (파일이 게임에 있는지는 게임 확인 필요).

Usage: python3 tools/build_v093.py <0.9.2 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.9.2', b'version=0.9.3'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02']
G = '.SC2Map/base.sc2data/gamedata/'
MODEL = ('<CModel id="RM9_ObserverPurifier" parent="Unit" Race="Protoss">'
         '<Model value="Assets\\Units\\Protoss\\Observer_Purifier_Collection\\Observer_Purifier_Collection.m3" />'
         '<RequiredAnims value="Assets\\Units\\Protoss\\Observer_KaraxAnims\\Observer_KaraxAnims.m3a" />'
         '<Occlusion value="Show" /><ScaleMax value="0.850000,0.850000,0.850000" /><ScaleMin value="0.850000,0.850000,0.850000" />'
         '<SelectionOffset value="0.000000,0.000000,-0.350000" /><SelectionRadius value="0.470200" /><SquibTypeDefault value="Metal" />'
         '</CModel>')
A_OLD = 'Send="ModelSwap Observer_Purifier_Collection"'
A_NEW = 'Send="ModelSwap RM9_ObserverPurifier"'


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            k = m + G + 'actordata.xml'; t = files[k].decode('utf-8')
            assert t.count(A_OLD) == 1, m
            t = t.replace(A_OLD, A_NEW)
            # Ally probes are no longer sent (support-button allies since 0.6.16/0.6.59); their skin swap to the path-less
            # Probe_Purifier_Collection would also be an error sphere, so the swap line is dropped.
            t, n = re.subn(r'[ \t]*<On Terms="Behavior\.RM3_AllySkin\.On" Send="ModelSwap Probe_Purifier_Collection" ?/>\r?\n?', '', t)
            assert n == 1, (m, n)
            files[k] = t.encode('utf-8'); changed.add(k)
            k = m + G + 'modeldata.xml'; t = files[k].decode('utf-8')
            assert 'RM9_ObserverPurifier' not in t, m
            i = t.rindex('</Catalog>'); files[k] = (t[:i] + MODEL + t[i:]).encode('utf-8'); changed.add(k)
            t = files[k].decode('utf-8')
            hit = list(re.finditer(r'<CModel id="CreeperHostSpawn_Primal_Collection"[^>]*>(.*?)</CModel>', t, re.S))
            if hit:
                assert len(hit) == 1 and '<Model ' not in hit[0].group(1), m
                p = hit[0].start(1)
                t = t[:p] + '<Model value="Assets\\Units\\Zerg\\CreeperHostSpawn_Primal_Collection\\CreeperHostSpawn_Primal_Collection.m3" />' + t[p:]
                files[k] = t.encode('utf-8')
            for f in ('actordata.xml', 'modeldata.xml'): E.fromstring(files[m + G + f])
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
