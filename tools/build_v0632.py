#!/usr/bin/env python3
"""0.6.31 -> 0.6.32: 1번 미션 동맹 명령 도움말 (사용자 2026-11-15).

사용자: "1번 미션에 애들 어떻게 공격 이동시키는지 설명하면 좋을듯 도움말이나 설명하는걸로 추가 부탁".
1번(TRaynor01)에서 동맹이 나온 뒤, 인트로 연출이 끝나고 조작이 돌아오면(5초 뒤) 한 번:
- 도움말 패널에 팁 추가 (HelpPanelAddTip, 왼쪽 알림 + F12 도움말에 남음), 아이콘 자날 '단축키' 안내 아이콘.
- 화면 지시문(Directive) 한 줄.
내용은 7-0 규칙 그대로: 평소 레이너 추종, 핑(Alt+왼쪽 클릭, 지도·미니맵)하면 두 동맹이 그곳으로 공격 이동해 지킴,
새 핑이면 목적지 변경, 30초 동안 새 핑이 없고 근처 적이 없으면 다시 레이너를 따라옴. 게임 미실행.

Usage: python3 tools/build_v0632.py <0.6.31 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO

OLD, NEW = b'version=0.6.31', b'version=0.6.32'
M = 'TRaynor01.SC2Map'
ICON = 'Assets\\\\Textures\\\\btn-tips-hotkeys.dds'
STRINGS = {
    'RM1/AllyTip/Title': '동맹에게 명령하기 /// Commanding Allies',
    'RM1/AllyTip/Alert': '도움말: 동맹 명령 /// Tip: Commanding Allies',
    'RM1/AllyTip/Desc': ('정화자와 원시저그 동맹은 평소 레이너를 따라다니며 함께 싸웁니다.<n/><n/>'
                         '지도나 미니맵에 <c val="ffff8a">핑(Alt + 왼쪽 클릭)</c>을 찍으면 두 동맹이 그곳으로 공격 이동하고 그 자리를 지킵니다. '
                         '새 핑을 찍으면 목적지가 바뀝니다.<n/><n/>'
                         '30초 동안 새 핑이 없고 그 근처에 적이 없으면 다시 레이너를 따라옵니다. 동맹은 직접 선택해 명령할 수 없습니다. '
                         '/// Your Purifier and Primal Zerg allies follow Raynor and fight alongside him.<n/><n/>'
                         'Ping the map or minimap <c val="ffff8a">(Alt + Left Click)</c> and both allies attack-move there and hold the spot. '
                         'A new ping changes the destination.<n/><n/>'
                         'After 30 seconds without a new ping, and with no enemies nearby, they follow Raynor again. Allies cannot be commanded directly.'),
    'RM1/AllyTip/Line': '핑(Alt + 왼쪽 클릭)으로 동맹을 그 지점으로 공격 이동시킬 수 있습니다. /// Ping (Alt + Left Click) to send your allies to attack-move there.',
}
FN_ANCHOR = 'void gf_rm_SpawnAllies () {\n'
FN = f'''// 0.6.32 (user 2026-11-15): explain how to send the allies (ping) once control returns after the intro.
trigger gt_rm_AllyTip;
bool gt_rm_AllyTip_Func (bool testConds, bool runActions) {{
    if (!runActions) {{ return true; }}
    Wait(5.0, c_timeGame);
    while (gv_inCinematic && !gv_gameOver) {{ Wait(1.0, c_timeGame); }}
    if (gv_gameOver) {{ return true; }}
    HelpPanelAddTip(PlayerGroupAll(), StringExternal("RM1/AllyTip/Title"), StringExternal("RM1/AllyTip/Desc"), StringExternal("RM1/AllyTip/Alert"), "{ICON}");
    UIDisplayMessage(PlayerGroupAll(), c_messageAreaDirective, StringExternal("RM1/AllyTip/Line"));
    return true;
}}

'''
CALL_OLD = '    TriggerEnable(gt_rm_AllyPing, true);\n'
CALL_NEW = CALL_OLD + ('    gt_rm_AllyTip = TriggerCreate("gt_rm_AllyTip_Func");\n'
                       '    TriggerExecute(gt_rm_AllyTip, false, false);\n')


def once(t, a, b):
    assert t.count(a) == 1, a[:60]
    return t.replace(a, b)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        d = root / M
        p = d / 'mapscript.galaxy'
        raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
        t = raw.replace('\r\n', '\n')
        t = once(t, FN_ANCHOR, FN + FN_ANCHOR)
        a = t.index(FN_ANCHOR)
        b = t.index('\n}\n', a)
        body = once(t[a:b], CALL_OLD, CALL_NEW)
        t = t[:a] + body + t[b:]
        p.write_bytes(t.replace('\n', nl).encode('utf-8'))
        ko = set_lines((d / KO).read_bytes(), STRINGS)
        (d / KO).write_bytes(ko)
        V35.gate('kokr', ko)
        for loc in V35.OTHER_LOCALES:
            (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if not n.startswith(M + '/') and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
