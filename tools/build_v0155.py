#!/usr/bin/env python3
"""0.15.4 -> 0.15.5: 고용소 공성 파괴단 칸 -> 충격 전차 (사용자 2026-11-28 "용병유닛(용병고용소에서 고용하는 유닛)이 그 충격전차여야").
10개 공장 맵: SummonMercenaries Train5(원작 HireSiegeBreakers, 2기)의 유닛을 SiegeTankMengsk 2기로, 원작 버튼 HireSiegeBreakers의
이름·설명·아이콘을 충격 전차로(0.6.5 규칙: 새 버튼을 덧붙이지 않고 원작 버튼을 다시 정의), 충격 전차 액터에 고용 낙하 주머니
(원작 SiegeBreakerDropModel, 0.6.6 규칙). 충전·대기·계약 해금은 원작 그대로. 고용 가격 = 칸 비용 + 유닛 비용(150/125) x 2.
Usage: build_v0155.py <0.15.4 zip> <out>"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import find, xml_edit, add_xml, set_lines, KO, GD
import re

OLD, NEW = b'version=0.15.4', b'version=0.15.5'
MAPS = ('TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04', 'TTychus03', 'TTychus02')
BUTTON = ('<CButton id="HireSiegeBreakers"><Icon value="Assets\\Textures\\btn-unit-terran-siegetankmengsk.dds" />'
          '<AlertIcon value="Assets\\Textures\\btn-unit-terran-siegetankmengsk.dds" />'
          '<Name value="Button/Name/RM15_HireShockTank" /><Tooltip value="Button/Tooltip/RM15_HireShockTank" /></CButton>')
UP, NODE, REQ = 'RM15_ShockHireUnlocked', 'RM15_HaveShockHire', 'RM15_CanHireShock'
DATA = {
    'upgradedata.xml': f'<CUpgrade id="{UP}"><Race value="Terr" /></CUpgrade>',
    'requirementnodedata.xml': f'<CRequirementCountUpgrade id="{NODE}"><Count Link="{UP}" State="CompleteOnly" /></CRequirementCountUpgrade>',
    'requirementdata.xml': f'<CRequirement id="{REQ}"><NodeArray index="Show" Link="{NODE}" /><NodeArray index="Use" Link="{NODE}" /></CRequirement>',
}
COND = 'libCamp_gf_MercStatusCheck(libCamp_ge_StoryMercID_MercSiegeBreakers,libCamp_ge_StoryMercStatus_Purchased)'
ANCHOR = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",3),true);\n'
SCRIPT = (f'    // 0.15.5: Shock Division in the Siege Breakers hire slot, once the Siege Breakers contract is bought.\n'
          f'    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",4),{COND});\n'
          f'    TechTreeUpgradeAllow(1,"{UP}",true);\n'
          f'    if ({COND} && TechTreeUpgradeCount(1,"{UP}",c_techCountQueuedOrBetter)==0) {{\n'
          f'        TechTreeUpgradeAddLevel(1,"{UP}",1);\n'
          f'    }}\n')
DROP = '        <On Terms="Behavior.MercGroundDrop.Create" Send="Create SiegeBreakerDropModel" />\n'
STRINGS = {
    'Button/Name/RM15_HireShockTank': '충격 전차 고용 /// Hire Shock Division',
    'Button/Tooltip/RM15_HireShockTank': '3등급 충격 전차 2기를 고용합니다. 기당 인구 3. 공성 포격 기절·넓은 폭발을 처음부터 사용합니다. 차량 공방업이 적용됩니다.<n/><n/>멩스크 협동전 공성 전차입니다. '
                                         '/// Hires 2 rank 3 Shock Division tanks. 3 supply each. Concussive Bombardment and the improved blast are available immediately. Receives vehicle weapon and plating upgrades.<n/><n/>Mengsk co-op siege tank.',
}


def edit_map(d):
    g = d / GD

    def abils(root):
        t5 = [i for i in find(root, 'CAbilTrain', 'SummonMercenaries').findall('InfoArray') if i.get('index') == 'Train5']
        assert len(t5) == 1 and not t5[0].findall('Unit'), d
        for k in range(2): E.SubElement(t5[0], 'Unit', index=str(k), value='SiegeTankMengsk')
        b = t5[0].find('Button'); assert b.get('State') == 'Suppressed'
        b.set('State', 'Restricted'); b.set('Requirements', REQ)
    xml_edit(g / 'abildata.xml', abils)

    def buttons(root):
        assert not [e for e in root if e.get('id') == 'HireSiegeBreakers']
    xml_edit(g / 'buttondata.xml', buttons)
    add_xml(g / 'buttondata.xml', BUTTON)

    for f, x in DATA.items(): add_xml(g / f, x)
    s = d / 'mapscript.galaxy'; raw = s.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
    st = raw.replace('\r\n', '\n'); assert st.count(ANCHOR) == 1 and 'SummonMercenaries",4' not in st, d
    s.write_bytes(st.replace(ANCHOR, ANCHOR + SCRIPT).replace('\n', nl).encode('utf-8'))
    p = g / 'actordata.xml'; t = p.read_text('utf-8')
    m = list(re.finditer(r'<CActorUnit id="SiegeTankMengsk" [^>]*>.*?</CActorUnit>', t, re.S))
    assert m and 'MercGroundDrop' not in m[0].group(0)
    k = m[0].end() - len('</CActorUnit>')
    p.write_text(t[:k] + DROP + '    ' + t[k:], 'utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert OLD in prev.read('metadata.txt').splitlines()
        infos = prev.infolist(); prev.extractall(tmp); root = Path(tmp)
        for m in MAPS:
            d = root / f'{m}.SC2Map'; edit_map(d)
            ko = set_lines((d / KO).read_bytes(), STRINGS); (d / KO).write_bytes(ko); V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
                for i in infos: out.writestr(copy.copy(i), (root / i.filename).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
