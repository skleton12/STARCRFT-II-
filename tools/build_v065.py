#!/usr/bin/env python3
"""0.6.4 -> 0.6.5: 프로메테우스 중대 고용 버튼·해금 수정 (사용자 2026-10-31 "화염방사병 미션 안 했는데 풀려 있음", "악마의 개로 나옴").

원인:
- 원작 고용소 카드(자날 캠페인 층)에 '악마의 개' 버튼(HireDevilDogs, 0행 1열, Train2)이 이미 있다. 맵의 CardLayouts는
  원작 카드에 덧붙는 방식이라, 0.6.4가 같은 칸에 붙인 RM6_HirePrometheus 버튼이 원작 '악마의 개' 버튼에 가렸다
  (4번이 코랄의 후예를 HireKelmorianMiners 버튼 이름 바꾸기로 해결한 것과 같은 구조).
- 0.6.4가 Train2 고용을 조건 없이 허용했다.
수정 (4·5·6번):
- 덧붙인 RM6_HirePrometheus 카드 버튼·버튼 정의를 지우고, 원작 HireDevilDogs 버튼의 이름·설명·아이콘·단축키를
  프로메테우스 중대로 바꾼다 (이 맵 안에서만).
- 고용은 원작처럼 히페리온 '악마의 개' 계약(libCamp 용병 MercDevilDogs, 화염방사병 해금 = 대피 임무 뒤)이
  '구매됨'일 때만 허용한다. 계약은 0.4.109부터 해금되면 자동 무료 구매이므로, 대피를 끝낸 뒤부터 고용소에 나온다.

Usage: python3 tools/build_v065.py <0.6.4 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import find, xml_edit, add_xml, set_lines, KO, GD

OLD, NEW = b'version=0.6.4', b'version=0.6.5'
MAPS = ('TTychus01', 'TTosh01', 'THanson01')
ALLOW_OLD = '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",1),true);\n'
ALLOW_NEW = ('    // 0.6.5: only once the Hyperion Devil Dogs contract is bought (free once unlocked, i.e. after The Evacuation).\n'
             '    TechTreeAbilityAllow(1,AbilityCommand("SummonMercenaries",1),'
             'libCamp_gf_MercStatusCheck(libCamp_ge_StoryMercID_MercDevilDogs,libCamp_ge_StoryMercStatus_Purchased));\n')
HIRE_BUTTON = ('<CButton id="HireDevilDogs"><Icon value="Assets\\Textures\\btn-unit-terran-firebat.dds" />'
               '<AlertIcon value="Assets\\Textures\\btn-unit-terran-firebat.dds" />'
               '<Name value="Button/Name/RM6_HirePrometheus" /><Tooltip value="Button/Tooltip/RM6_HirePrometheus" />'
               '<Hotkey value="Button/Hotkey/RM6_HirePrometheus" /></CButton>')
STRINGS = {
    'Button/Tooltip/RM6_HirePrometheus': '3등급 프로메테우스 중대 2기를 고용합니다. 기당 인구 4, 총 인구 8. 점프 제트 강습·저거너트 장갑·고급 전투 자극제를 처음부터 사용합니다. 보병 공방업이 적용됩니다. 대피 임무로 화염방사병을 얻은 뒤부터 고용할 수 있습니다.<n/><n/>자치령 근위대의 중화염방사병입니다. '
                                         '/// Hires 2 rank 3 Prometheus Company troopers. 4 supply each, 8 total. Jump Jet Assault, Juggernaut Plating and Advanced Stimpack are available immediately. Receives infantry weapon and armor upgrades. Available after the Firebat is acquired in The Evacuation.<n/><n/>Dominion Royal Guard heavy flamethrower troopers.',
}


def edit_map(d):
    g = d / GD

    def units(root):
        cards = find(root, 'CUnit', 'MercCompound').findall('CardLayouts')
        hit = [b for b in cards[0] if b.get('Face') == 'RM6_HirePrometheus']
        assert len(cards) == 1 and len(hit) == 1
        cards[0].remove(hit[0])
    xml_edit(g / 'unitdata.xml', units)

    def abils(root):
        t2 = [i for i in find(root, 'CAbilTrain', 'SummonMercenaries').findall('InfoArray') if i.get('index') == 'Train2']
        b = t2[0].find('Button')
        assert len(t2) == 1 and b.get('DefaultButtonFace') == 'RM6_HirePrometheus'
        b.set('DefaultButtonFace', 'HireDevilDogs')
    xml_edit(g / 'abildata.xml', abils)

    def buttons(root):
        root.remove(find(root, 'CButton', 'RM6_HirePrometheus'))
        assert not [e for e in root if e.get('id') == 'HireDevilDogs']
    xml_edit(g / 'buttondata.xml', buttons)
    add_xml(g / 'buttondata.xml', HIRE_BUTTON)

    p = d / 'mapscript.galaxy'
    raw = p.read_bytes().decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    t = raw.replace('\r\n', '\n')
    assert t.count(ALLOW_OLD) == 1 and 'libCamp_gf_MercStatusCheck(' in t
    t = t.replace(ALLOW_OLD, ALLOW_NEW)
    p.write_bytes(t.replace('\n', nl).encode('utf-8'))


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        for m in MAPS:
            d = root / f'{m}.SC2Map'
            edit_map(d)
            ko = set_lines((d / KO).read_bytes(), STRINGS)
            (d / KO).write_bytes(ko)
            V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in MAPS) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
