#!/usr/bin/env python3
"""0.4.85 -> 0.4.86: 핑 유지 — 30초가 지나도 핑 주변에 적이 남아 있으면 동맹이 계속 그 자리를 지킨다 (1·3·4번, 사용자 2026-10-24).

사용자: "동맹 핑하면 공격하긴 하는데 30초 뒤 딴 데로 감. 핑 지역 근처에 적이 없을 때만 적용". 7-0 핑 유지 시간 30초는 그대로이고,
30초가 지난 뒤에는 핑 지점 반경 PING_ENEMY_RADIUS(시험값 10) 안에 동맹의 적(살아 있고 보이는 유닛·건물)이 있으면 2초씩 연장한다.
적이 없어지면 원래 기본 행동(1번 레이너 추종, 3·4번 자동 전투)으로 돌아간다. 2번 맵은 현재 핑 조종이 없어 바꾸지 않는다.

Usage: python3 tools/build_v0486.py <0.4.85 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.85', b'version=0.4.86'
PING_ENEMY_RADIUS = '10.0'
FN = f'''
// 0.4.86: ping hold continues past 30 s while the ally still sees enemies near the ping (user 2026-10-24, trial radius).
bool gf_rmPingEnemy (point pt, int ally) {{
    if (pt==null) {{ return false; }}
    return UnitGroupCount(UnitGroupAlliance(ally,c_unitAllianceEnemy,RegionCircle(pt,{PING_ENEMY_RADIUS}),
        UnitFilter(0,0,(1 << c_targetFilterMissile),(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))),1),c_unitCountAlive)>0;
}}
'''
EDITS = {
    'TRaynor01': [('bool gt_rm_AllyPing_Func (bool testConds, bool runActions) {',
                   FN + 'bool gt_rm_AllyPing_Func (bool testConds, bool runActions) {'),
                  ('    if (gv_rm_pingTarget != null && GameGetMissionTime() - gv_rm_pingTime >= 30.0) {',
                   '    if (gv_rm_pingTarget != null && GameGetMissionTime() - gv_rm_pingTime >= 30.0 && !gf_rmPingEnemy(gv_rm_pingTarget, 8)) {')],
    'TRaynor03': [('\nvoid gf_m3_Attack (int p) {', FN + '\nvoid gf_m3_Attack (int p) {'),
                  ('    if (GameGetMissionTime()<gv_m3_pingUntil) {\n',
                   '    if (gv_m3_pingUntil>0.0 && GameGetMissionTime()>=gv_m3_pingUntil && gf_rmPingEnemy(gv_m3_ping,p)) {\n'
                   '        gv_m3_pingUntil=GameGetMissionTime()+2.0;\n    }\n'
                   '    if (GameGetMissionTime()<gv_m3_pingUntil) {\n')],
    'TTychus01': [('\nvoid gf_m4_Attack (int p) {', FN + '\nvoid gf_m4_Attack (int p) {'),
                  ('    if (GameGetMissionTime()<gv_m4_pingUntil) {\n',
                   '    if (gv_m4_pingUntil>0.0 && GameGetMissionTime()>=gv_m4_pingUntil && gf_rmPingEnemy(gv_m4_ping,p)) {\n'
                   '        gv_m4_pingUntil=GameGetMissionTime()+2.0;\n    }\n'
                   '    if (GameGetMissionTime()<gv_m4_pingUntil) {\n')],
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m, pairs in EDITS.items():
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            assert 'gf_rmPingEnemy' not in t
            for a, b in pairs:
                assert t.count(a) == 1, (m, a)
                t = t.replace(a, b)
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
