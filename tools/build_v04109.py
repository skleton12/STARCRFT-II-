#!/usr/bin/env python3
"""0.4.108 -> 0.4.109: 히페리온 용병 계약 전부 무료 구매 상태 (사용자 2026-10-25 "용병 다 고용되어 있게, 돈 안 나가게").

사용자 선택: "히페리온 계약 전부 구매". 계약 상태(libCamp_gv_tSX_MercStatus)는 캠페인 전이 데이터로, 임무 시작 때
불러오고(libCamp_gf_LoadCampaignData) 임무를 끝낼 때 저장된다 (원작 CampaignLib, SC2GameData 6dd323a 확인).
그래서 1~4번 맵에서 캠페인 데이터를 불러온 바로 뒤에 '잠김(Locked)'이 아닌 계약(새 계약·구매 가능)을 모두
'구매됨(Purchased)'으로 바꾼다. 크레딧은 빼지 않는다 (SetMercStatus는 상태만 바꾼다). 임무를 끝내면 그 상태가
저장되어 히페리온 용병 화면에도 고용됨으로 나온다. 잠긴 계약(그 유닛이 아직 해금 전)은 그대로 두고,
해금된 뒤 다음 임무 시작 때 구매됨으로 바뀐다. 이미 산 계약은 그대로다 (환불 없음).
미션 안 용병 고용소 버튼·고용 비용(광물·가스)은 바꾸지 않는다.

Usage: python3 tools/build_v04109.py <0.4.108 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.108', b'version=0.4.109'
MAPS = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']
CODE = '''    // 0.4.109: every Hyperion mercenary contract that is not locked counts as bought, free (user 2026-10-25).
    gf_rmFreeMercContracts();
'''
FN = '''// 0.4.109: Hyperion mercenary contracts bought for free (user 2026-10-25). Status only, no credits.
void gf_rmFreeMercContracts () {
    int i=libCamp_gv_TSC_MERC_FIRST;
    int m;
    for (;i<=libCamp_gv_TSC_MERC_LAST;i+=1) {
        m=libCamp_gv_tS_MercID[i];
        if (!libCamp_gf_MercStatusCheck(m,libCamp_ge_StoryMercStatus_Locked)) {
            libCamp_gf_SetMercStatus(m,libCamp_ge_StoryMercStatus_Purchased);
        }
    }
}

'''


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m in MAPS:
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            nl = '\r\n' if '\r\n' in t else '\n'
            load = f'    libCamp_gf_LoadCampaignData(libCamp_ge_MapID_Map{m});{nl}'
            assert t.count(load) == 1 and 'gf_rmFreeMercContracts' not in t, m
            # define the function before the first function that calls LoadCampaignData
            i = t.index(load)
            head = max(t.rfind('\nvoid ', 0, i), t.rfind('\nbool ', 0, i)) + 1
            t = t[:head] + FN.replace('\n', nl) + t[head:]
            t = t.replace(load, load + CODE.replace('\n', nl))
            files[s] = t.encode('utf-8'); changed.add(s)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
