#!/usr/bin/env python3
"""0.5.10 -> 0.5.11: 레드스톤 상단 지원 버튼 그림·지점 커서 (사용자 2026-10-27 "그림 깨짐", "커서는 안 나오는데 클릭하면 소환").

- 그림: 대화 상자 '버튼'에 아이콘을 Image 속성으로 넣으면 버튼 테두리 방식으로 늘어나 깨진다. 버튼은 기본 틀만 두고,
  그 위에 이미지 컨트롤(이미지 종류 Normal)로 아이콘을 따로 그린다. 대기 중 흑백도 이미지 컨트롤에 건다.
  원시저그 아이콘 btn-ability-kerrigan-droppods는 군심 전용(자날 맵 의존성에 없음)이라, 맵이 이미 쓰는
  btn-unit-collection-primal-Zergling으로 바꾼다.
- 커서: 시전 유닛을 스크립트로 '선택 불가'로 만들어 UISetTargetingOrder가 지점 커서를 열지 못한 것으로 본다 (협동전 전역
  시전 유닛은 선택 불가가 아님). 그 줄을 지운다. 유닛은 지도 구석 (0.5,0.5)·NoDraw·Uncursorable이라 끌어서 선택되지 않는다.
  명령 카드에도 즉시 능력 대신 지점 지정 능력(RM5_AllySupport/RM5_PrimalSupport)을 올린다 (협동전처럼 카드에 있는 능력).
  지도 클릭 대체 방식은 그대로 둔다.

Usage: python3 tools/build_v0511.py <0.5.10 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.10', b'version=0.5.11'
S = 'TTosh01.SC2Map/mapscript.galaxy'
U = 'TTosh01.SC2Map/base.sc2data/gamedata/unitdata.xml'

SCRIPT = [
    ('int[16] gv_m5_callBtnP;\n', 'int[16] gv_m5_callBtnP;\nint[16] gv_m5_callImgP;\n'),
    ('    UnitSetState(gv_m5_caster,c_unitStateSelectable,false);\n', ''),
    ('    DialogControlSetPropertyAsString(gv_m5_callBtnP[p],c_triggerControlPropertyImage,PlayerGroupAll(),icon);\n'
     '    DialogControlSetPropertyAsText(gv_m5_callBtnP[p],c_triggerControlPropertyTooltip,PlayerGroupAll(),StringExternal(tip));\n',
     '    DialogControlSetPropertyAsText(gv_m5_callBtnP[p],c_triggerControlPropertyTooltip,PlayerGroupAll(),StringExternal(tip));\n'
     '    DialogControlCreate(gv_m5_callDlg,c_triggerControlTypeImage);\n'
     '    gv_m5_callImgP[p]=DialogControlLastCreated();\n'
     '    DialogControlSetSize(gv_m5_callImgP[p],PlayerGroupAll(),52,52);\n'
     '    DialogControlSetPosition(gv_m5_callImgP[p],PlayerGroupAll(),c_anchorTopLeft,x+6,12);\n'
     '    DialogControlSetPropertyAsString(gv_m5_callImgP[p],c_triggerControlPropertyImage,PlayerGroupAll(),icon);\n'
     '    DialogControlSetPropertyAsInt(gv_m5_callImgP[p],c_triggerControlPropertyImageType,PlayerGroupAll(),c_triggerImageTypeNormal);\n'),
    ('"Assets\\\\Textures\\\\btn-ability-kerrigan-droppods.dds"', '"Assets\\\\Textures\\\\btn-unit-collection-primal-Zergling.dds"'),
    ('        DialogControlSetPropertyAsBool(gv_m5_callBtnP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),true);\n',
     '        DialogControlSetPropertyAsBool(gv_m5_callImgP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),true);\n'),
    ('        DialogControlSetPropertyAsBool(gv_m5_callBtnP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),false);\n',
     '        DialogControlSetPropertyAsBool(gv_m5_callImgP[p],c_triggerControlPropertyDesaturated,PlayerGroupAll(),false);\n'),
]
UNIT = [
    ('AbilCmd="RM5_CallPurifier,Execute"', 'AbilCmd="RM5_AllySupport,Execute"'),
    ('AbilCmd="RM5_CallPrimal,Execute"', 'AbilCmd="RM5_PrimalSupport,Execute"'),
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
        t = t.replace(a, b)
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for name, pairs in ((S, SCRIPT), (U, UNIT)):
            t = files[name].decode('utf-8')
            nl = '\r\n' if '\r\n' in t else '\n'
            t = sub(t.replace('\r\n', '\n'), pairs)
            files[name] = t.replace('\n', nl).encode('utf-8')
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in (S, U, 'metadata.txt'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
