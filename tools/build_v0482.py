#!/usr/bin/env python3
"""0.4.81 -> 0.4.82: 저그 적에게 물량에 더해 능력치 10% 강화 (3·4번, 사용자 2026-10-24 "저그 물량에 10% 강화, 좀 약하다").

7-1 종족별 규칙(2026-10-17)은 저그 = 물량(공세 +50%), 피해 % 없음이었다. 사용자 지시로 저그 적 플레이어에도
주는 피해 110%, 받는 피해 10000/110 = 90% (정수) 를 준다. 난이도와 무관한 고정 시험값 ZERG_BUFF_PERCENT = 10.
최소 업그레이드는 주지 않는다(물량 규칙 유지). 프로토스·테란 규칙과 동맹·레이너·중립은 그대로.
  3번 제로 아워: 적 2~5번(모두 저그) — gf_m3_Init 에서 한 번.
  4번 어부지리: 적 2번(저그) — gf_m4_EnemyRules 에서 한 번 (탈다림 3~6번은 기존 난이도 강화).

Usage: python3 tools/build_v0482.py <0.4.81 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.81', b'version=0.4.82'
ZERG_BUFF_PERCENT = 10
FN = f'''
// 0.4.82: Zerg enemies keep the +50% waves and also get a flat stat buff (user 2026-10-24, trial ZERG_BUFF_PERCENT).
const int gv_rmZergBuffPercent = {ZERG_BUFF_PERCENT};

void gf_rmZergBuff (int p) {{
    PlayerModifyPropertyInt(p,c_playerPropDamageDealtPercent,c_playerPropOperSetTo,100+gv_rmZergBuffPercent);
    PlayerModifyPropertyInt(p,c_playerPropDamageTakenPercent,c_playerPropOperSetTo,10000/(100+gv_rmZergBuffPercent));
}}
'''
EDITS = {
    'TRaynor03': [('\nvoid gf_m3_Init () {', FN + '\nvoid gf_m3_Init () {'),
                  ('    trigger ping;\n    gv_m3_pending=UnitGroupEmpty();\n',
                   '    trigger ping;\n    gv_m3_pending=UnitGroupEmpty();\n    for (p=2;p<=5;p+=1) { gf_rmZergBuff(p); }\n')],
    'TTychus01': [('\nvoid gf_m4_EnemyRules () {', FN + '\nvoid gf_m4_EnemyRules () {'),
                  ('    lv_buff=libNtve_gf_DifficultyValueInt(0,5,15,35);\n    for (p=3;p<=6;p+=1) {',
                   '    lv_buff=libNtve_gf_DifficultyValueInt(0,5,15,35);\n    gf_rmZergBuff(2);\n    for (p=3;p<=6;p+=1) {')],
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
            assert 'gf_rmZergBuff' not in t
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
