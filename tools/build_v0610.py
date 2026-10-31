#!/usr/bin/env python3
"""0.6.9 -> 0.6.10: 프로메테우스 중대 모델 = Wings of Mengsk 'Incinerator' (사용자 2026-10-31 "멩스크 모드에서 모델 가져와 적용해봐,
그 프로메테우스 중대 없는 것만 빌려 적용하자").

협동전 멩스크에 화염방사병이 없으므로 WoM(WoM-1.3_Armory.zip, WoMRoyalGuards.SC2Mod) 모델을 빌린다 — 코랄의 후예(0.2.16)와 같은 방식.
0.6.9의 협동전 블레이즈(경로 추정)는 철회. 바꾸는 것은 몸체 모델뿐 (능력·수치·가격·해금·초상화·아이콘·소리·사망 모델 그대로).
넣는 파일 (4·5·6번 맵마다): Assets/Units/Terran/Incinerator/Incinerator.m3, Assets/Textures/Incinerator_{Dif,Emi,Norm,Spec}.dds,
IncineratorA_{Dif,Spec}.dds. 모델이 참조하는 나머지 텍스처(Firebat_Heavens_Parts_COOP_*, SiegeTank_Mengsk_COOP_Gloss,
Decal_Terran_0089_01, PBRReflect_LastImpact_Cubic_Envio)는 WoM에도 없고 블리자드 게임 파일이라 넣지 않는다.

Usage: python3 tools/build_v0610.py <0.6.9 zip> <WoM-1.3_Armory.zip> <new output zip>
"""
import argparse, copy, hashlib, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_v062 import find, xml_edit, GD

OLD, NEW = b'version=0.6.9', b'version=0.6.10'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
U = 'RM6_Prometheus'
OLD_PATH = 'Assets\\COOP\\Tychus\\Units\\Firebat_Heavens_COOP\\Firebat_Heavens_COOP.m3'
NEW_PATH = 'Assets\\Units\\Terran\\Incinerator\\Incinerator.m3'
WOM = 'WoM-1.3_Armory/帝国之翼军械库版v1.5/WoMRoyalGuards.SC2Mod/'
ASSETS = ['Assets/Units/Terran/Incinerator/Incinerator.m3'] + [
    f'Assets/Textures/{n}.dds' for n in ('Incinerator_Dif', 'Incinerator_Emi', 'Incinerator_Norm', 'Incinerator_Spec',
                                          'IncineratorA_Dif', 'IncineratorA_Spec')]


def models(root):
    m = find(root, 'CModel', U).find('Model')
    assert m.get('value') == OLD_PATH
    m.set('value', NEW_PATH)


def build(source, wom, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(wom) as w:
        blobs = {a: w.read(WOM + a) for a in ASSETS}
    for a, b in blobs.items():
        print(len(b), hashlib.sha256(b).hexdigest()[:16], a)
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            xml_edit(root / f'{m}.SC2Map' / GD / 'modeldata.xml', models)
            assert not any(n.startswith(f'{m}.SC2Map/Assets/Units/Terran/Incinerator') for n in names)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        changed = {f'{m}.SC2Map/{GD}modeldata.xml' for m in MAPS} | {'metadata.txt'}
        added = [f'{m}.SC2Map/{a}' for m in MAPS for a in ASSETS]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for n in added:
                    out.writestr(n, blobs[n.split('.SC2Map/', 1)[1]])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names + added
                for n in names:
                    if n not in changed:
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('wom', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.wom, a.output)
