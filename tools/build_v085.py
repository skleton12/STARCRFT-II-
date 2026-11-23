#!/usr/bin/env python3
"""0.8.4 -> 0.8.5: 다이아몬드백 연구 버튼이 안 나오던 것 (사용자 2026-11-23 "코브라 업그레이드 어디감").

원인: 0.8.3이 성형 선체·3리튬 동력 전지 버튼을 기존 정의에 넣지 않고, 같은 파일 끝에 CUnit FactoryTechLab /
FactoryTechReactor와 CAbilResearch FactoryTechLabResearch를 두 번째로 정의해 붙였다 (맵 4~8). 같은 파일 안 두 번째
정의는 게임이 쓰지 않는다. 0.8.5는 두 번째 정의의 내용을 첫 정의로 옮긴다: 카드 버튼은 첫 정의의 CardLayouts index="0"
안으로, 연구 칸(InfoArray)은 첫 능력 정의 안으로. 0.6.77 피닉스 용사 이식에서 두 번 들어간 GlazeFenixChampionUnit 액터·
GlazeFenixChampion 모델도 두 번째를 지운다 (첫 정의와 같거나 EditorCategories만 다름).
check_release에 '같은 파일 안 같은 ID 두 번 정의' 검사를 추가했다. 버튼 자리·비용·효과는 0.8.3 그대로. Game not run.

Usage: python3 tools/build_v085.py <0.8.4 zip> <new output zip>
"""
import argparse, copy, re, zipfile, xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.8.4', b'version=0.8.5'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01']
GD = '.SC2Map/base.sc2data/gamedata/'


def blocks(t, tag, i):
    return list(re.finditer(r'<%s\s[^>]*?\bid="%s"[^>]*?(?:/>|>.*?</%s>)' % (tag, i, tag), t, re.S))


def merge_unit(t, uid):
    b = blocks(t, 'CUnit', uid)
    assert len(b) == 2, (uid, len(b))
    second = b[1].group(0)
    inner = re.fullmatch(r'<CUnit id="%s"><CardLayouts index="0">(.*)</CardLayouts></CUnit>' % uid, second, re.S)
    assert inner, (uid, second[:120])
    t = t[:b[1].start()] + t[b[1].end():]
    first = blocks(t, 'CUnit', uid)[0]
    c0 = re.search(r'<CardLayouts index="0">.*?</CardLayouts>', first.group(0), re.S)
    p = first.start() + c0.end() - len('</CardLayouts>')
    return t[:p] + inner.group(1) + t[p:]


def merge_abil(t, aid):
    b = blocks(t, 'CAbilResearch', aid)
    assert len(b) == 2, (aid, len(b))
    inner = re.fullmatch(r'<CAbilResearch id="%s">(.*)</CAbilResearch>' % aid, b[1].group(0), re.S)
    assert inner and 'Research8' in inner.group(1), aid
    t = t[:b[1].start()] + t[b[1].end():]
    first = blocks(t, 'CAbilResearch', aid)[0]
    p = first.end() - len('</CAbilResearch>')
    return t[:p] + inner.group(1) + t[p:]


def drop_second(t, tag, i):
    b = blocks(t, tag, i)
    assert len(b) == 2, (tag, i, len(b))
    norm = lambda s: re.sub(r'\s*<EditorCategories[^>]*/>', '', s)
    assert norm(b[0].group(0)) == norm(b[1].group(0)), (tag, i)
    return t[:b[1].start()] + t[b[1].end():]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            k = m + GD + 'unitdata.xml'; t = files[k].decode('utf-8')
            for u in ('FactoryTechLab', 'FactoryTechReactor'): t = merge_unit(t, u)
            files[k] = t.encode('utf-8'); changed.add(k)
            k = m + GD + 'abildata.xml'; t = files[k].decode('utf-8')
            files[k] = merge_abil(t, 'FactoryTechLabResearch').encode('utf-8'); changed.add(k)
            k = m + GD + 'actordata.xml'
            files[k] = drop_second(files[k].decode('utf-8'), 'CActorModelMaterial', 'GlazeFenixChampionUnit').encode('utf-8'); changed.add(k)
            k = m + GD + 'modeldata.xml'
            files[k] = drop_second(files[k].decode('utf-8'), 'CModel', 'GlazeFenixChampion').encode('utf-8'); changed.add(k)
            for f in ('unitdata.xml', 'abildata.xml', 'actordata.xml', 'modeldata.xml'):
                E.fromstring(files[m + GD + f])
            u = files[m + GD + 'unitdata.xml'].decode()
            for uid in ('FactoryTechLab', 'FactoryTechReactor'):
                c0 = re.search(r'<CardLayouts index="0">.*?</CardLayouts>', blocks(u, 'CUnit', uid)[0].group(0), re.S).group(0)
                assert 'RMA_ShapedHull' in c0 and 'RMA_TriLithium' in c0 and 'RMA_Multilock' in c0, (m, uid)
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
