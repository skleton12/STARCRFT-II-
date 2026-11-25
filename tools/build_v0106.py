#!/usr/bin/env python3
"""0.10.5 -> 0.10.6: 탈옥(TTosh03A) 지원군 공격 연출 보충 (사용자 2026-11-25 "히드라 가시 괴상한 구로 나옴", "뉴폴섬 끝").
0.10.2가 망자의 항구(THorner02)에서 지원 유닛 데이터를 앞으로만 떠 와, 무기·효과가 가리키는 연출 액터(히드라·바퀴 가시 미사일,
근접 공격, 저글링 공격, 잠복 자국, 군단병 사망·소환·배치 모델, 저글링 공격 소리)가 빠져 기본 미사일이 오류 구로 보였다.
그 액터·모델·소리만 THorner02에서 옮긴다(합체·3단계·유전자 가지는 따라가지 않음, catalog_closure skip=). Game not run.
Usage: python3 tools/build_v0106.py <0.10.5 zip> <new output zip>"""
import copy, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import build_v0101 as V1
OLD, NEW = b'version=0.10.5', b'version=0.10.6'
M = 'TTosh03A.SC2Map'
ROOTS = ('DehakaHydraliskLevel2AttackMissile,DehakaHydraliskLevel2MeleeAttack,DehakaHydraliskLevel2BurrowedSplat,'
         'DehakaRoachLevel2AttackMissile,DehakaRoachLevel2MeleeAttack,DehakaRoachLevel2BurrowedSplat,DehakaRoachAttackStart,'
         'DehakaRoachAttackImpact,DehakaZerglingLevel2Attack,DehakaZerglingLevel2AttackLaunch,DehakaZerglingLevel2BurrowedSplat,'
         'ZealotPurifier_Death,ZealotPurifierWarpIn,ZealotPurifierPlacement')
SKIP = 'skip=Level3|Gene|Merge|Glevig|MoveSpeed|Igniter|Slivan'
def main(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z, tempfile.TemporaryDirectory() as tmp:
        assert OLD in z.read('metadata.txt').splitlines()
        root = Path(tmp)
        for n in z.namelist():
            if n.startswith((M + '/base.sc2data/gamedata/', 'THorner02.SC2Map/base.sc2data/gamedata/')): z.extract(n, root)
        gd, hg = root / M / 'base.sc2data/gamedata', root / 'THorner02.SC2Map/base.sc2data/gamedata'
        before = {p.name: p.read_bytes() for p in gd.glob('*.xml')}
        o = subprocess.run([sys.executable, str(HERE / 'catalog_closure.py'), str(hg), ROOTS, ','.join(map(str, V1.BASE)), SKIP],
                           check=True, capture_output=True, text=True).stdout
        items = {}
        for line in o.splitlines():
            i, fs = line.split(' ', 1)
            for fn in fs.split(','): items.setdefault(fn, []).append(i)
        print('records +', V1.add_records(gd, hg, items))
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        for p in gd.glob('*.xml'):
            E.parse(p)
            if before.get(p.name) != p.read_bytes(): rep[f'{M}/base.sc2data/gamedata/{p.name}'] = p.read_bytes()
        new = [k for k in rep if k not in z.namelist()]
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)))
                for k in new:
                    zi = zipfile.ZipInfo(k, (2026, 11, 25, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    w.writestr(zi, rep[k], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out, sorted(rep))
if __name__ == '__main__': main(*sys.argv[1:])
