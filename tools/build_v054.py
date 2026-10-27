#!/usr/bin/env python3
"""0.5.3 -> 0.5.4: 히페리온 허브 맵(TStory01)을 CCM에 넣어 용병 계약을 허브에서도 무료로 (사용자 2026-10-27).

사용자: "용병이 다 무료이면 될 듯. 플레이어가 어차피 용병을 누를 것 같아 그걸 방지하려고."
미션 맵만으로는 임무를 깬 뒤 히페리온에서 새로 열린 계약이 '구매 가능'으로 떠 크레딧을 쓸 수 있었다.
ReOverhaul·RaynorRogue처럼 허브 맵을 CCM에 넣는다.

- 원본: maps/original_wol/tstory01/ (사용자 드라이브의 블리자드 원본 추출본, 공개 SC2GameData 스크립트와 같음 확인).
- 바꾸는 것은 스크립트뿐:
  1) 캠페인 데이터를 불러온 직후 미션 맵과 같은 gf_rmFreeMercContracts()로 잠기지 않은 계약을 크레딧 없이 '구매됨'.
     같은 줄에서 업적을 끈다 (모든 맵 규칙).
  2) 용병 패널을 열기 직전에도 한 번 더 부른다 (허브 안에서 새로 열린 계약까지).
- 문자열: kokr 원본 그대로 (이미 '한국어 /// English'), 다른 11개 언어는 kokr 영어 부분으로 만든다.
- 지형·오브젝트·트리거 데이터·의존성은 원본 그대로.

Usage: python3 tools/build_v054.py <0.5.3 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.5.3', b'version=0.5.4'
SRC = HERE.parent / 'maps' / 'original_wol' / 'tstory01'
HUB = 'TStory01.SC2Map/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'

FREE = '''// 0.5.4: mercenary contracts are free (user 2026-10-27): every unlocked contract counts as bought, no credits spent.
void gf_rmFreeMercContracts () {
    int i=libCamp_gv_TSC_MERC_FIRST;
    int m;
    for (;i<=libCamp_gv_TSC_MERC_LAST;i+=1) {
        m=libCamp_gv_tS_MercID[i];
        if (!libCamp_gf_MercStatusCheck(m,libCamp_ge_StoryMercStatus_Locked)) { libCamp_gf_SetMercStatus(m,libCamp_ge_StoryMercStatus_Purchased); }
    }
}

'''


def patch_script(t):
    a = 'void gf_MercDisplay (trigger lp_exitCallback) {\n'
    assert t.count(a) == 1
    t = t.replace(a, FREE + a)
    a = '    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_MapTStory01);\n'
    assert t.count(a) == 1
    t = t.replace(a, a + '    gf_rmFreeMercContracts();\n    AchievementsDisable(1);\n')
    t, n = re.subn(r'\n([ \t]*)libCamp_gf_DisplayMercenaryPanel\(',
                   lambda m: f'\n{m.group(1)}gf_rmFreeMercContracts();\n{m.group(1)}libCamp_gf_DisplayMercenaryPanel(', t)
    assert n == 2, n
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    hub = {}
    for p in sorted(SRC.rglob('*')):
        if p.is_file(): hub[HUB + p.relative_to(SRC).as_posix().lower()] = p.read_bytes()
    assert HUB + 'mapscript.galaxy' in hub and HUB + KO in hub and HUB + 'documentheader' in hub
    raw = hub[HUB + 'mapscript.galaxy'].decode('utf-8')
    nl = '\r\n' if '\r\n' in raw else '\n'
    hub[HUB + 'mapscript.galaxy'] = patch_script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8')
    V35.gate('kokr', hub[HUB + KO])
    for loc in V35.OTHER_LOCALES:
        hub[f'{HUB}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(hub[HUB + KO])
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any(n.lower().startswith(HUB.lower()) for n in prev.namelist())
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    out.writestr(copy.copy(info), d)
                for n, d in hub.items(): out.writestr(n, d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(hub), 'hub files')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
