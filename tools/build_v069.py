#!/usr/bin/env python3
"""0.6.8 -> 0.6.9: 프로메테우스 중대 모델 = 협동전 타이커스 무법자 블레이즈 (사용자 2026-10-31 "협동전 블레이즈", "모델만").

모델만 바꾼다 (능력·수치·가격·해금·초상화·아이콘·소리는 그대로). 블레이즈 자체 색이 있으므로 0.6.4의 검붉은 색조는 뗀다.
경로는 추정이다: 공개 데이터 사본(SC2GameData)에 타이커스 사령관 데이터가 없어 직접 확인하지 못했다.
블리자드 타이커스 협동전 에셋 이름 규칙(Assets\\COOP\\Tychus\\Buildings\\AutoTurret_Heavens_COOP\\…, Effects\\Medic_Heavens_COOP_…,
초상화 조명 Firebat_Heavens_COOP_Portrait, WoM Incinerator.m3가 참조하는 Firebat_Heavens_Parts_COOP 텍스처)과
멩스크 유닛 경로(Assets\\COOP\\Mengsk\\Units\\Marauder_Mengsk_COOP\\Marauder_Mengsk_COOP.m3)를 따라
Assets\\COOP\\Tychus\\Units\\Firebat_Heavens_COOP\\Firebat_Heavens_COOP.m3 로 둔다.
게임에서 빨간 오류 구가 나오면 경로가 틀린 것이다 (0.6.8로 되돌리거나 경로 수정).

Usage: python3 tools/build_v069.py <0.6.8 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from build_v062 import find, xml_edit, GD

OLD, NEW = b'version=0.6.8', b'version=0.6.9'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
U = 'RM6_Prometheus'
OLD_PATH = 'Assets\\Units\\Terran\\Firebat\\Firebat.m3'
BLAZE = 'Assets\\COOP\\Tychus\\Units\\Firebat_Heavens_COOP\\Firebat_Heavens_COOP.m3'
TINT = 'SetTintColor 150,45,40'


def models(root):
    m = find(root, 'CModel', U).find('Model')
    assert m.get('value') == OLD_PATH
    m.set('value', BLAZE)


def actors(root):
    a = find(root, 'CActorUnit', U)
    hit = [o for o in a.findall('On') if o.get('Send') == TINT]
    assert len(hit) == 1
    a.remove(hit[0])


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            g = root / f'{m}.SC2Map' / GD
            xml_edit(g / 'modeldata.xml', models)
            xml_edit(g / 'actordata.xml', actors)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        changed = {f'{m}.SC2Map/{GD}{f}' for m in MAPS for f in ('modeldata.xml', 'actordata.xml')} | {'metadata.txt'}
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n not in changed:
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
