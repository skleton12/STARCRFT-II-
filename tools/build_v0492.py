#!/usr/bin/env python3
"""0.4.91 -> 0.4.92: 이지스 근위대 방어막을 진짜 보호막 300으로 (4번, 사용자 선택 2026-10-24).

사용자: "이지스 근위대 보호막 300이 생기는 게 아님?" — 협동전 이지스 방어막(MarauderMengskAbsorb)은 피해 300 흡수 버프라
멩스크 전용 체력바(자날에 없음, 0.4.66에서 끔)가 없으면 눈에 안 보인다. 사용자 선택 "진짜 보호막 300으로".
- 흡수 버프를 유닛에서 빼고 보호막 최대·시작 300을 준다.
- 재충전: 피해를 받지 않고 60초 지나면(협동전 재충전 60초와 맞춤) 초당 30씩 다시 찬다 (회복 속도 시험값).
- 패시브 버튼은 남기고 쿨다운 표시용 행동 연결만 뗀다. 툴팁을 새 동작에 맞게 고친다.

같은 판, 사용자 2026-10-24 "동맹이 좀 맴도네", "원시 군락과 넥서스 지어졌으면 일꾼 컨트롤 동맹에게" (3·4번):
- 맴돎: 레이너 기지 방어 때 4초마다 '레이너 기지에 가장 가까운 적'에서 6 넘게 떨어진 동맹 유닛을 끌어오던 것을
  15 넘게 떨어진 유닛만 끌어오게 한다 (시험값 YANK). 다른 적과 싸우던 유닛이 왔다 갔다 하던 원인.
- 확장 기지 채굴 일꾼(RM_AllyMiner)은 동맹만 조종한다: 명령 불가로 만들고, 4번 혼합 선택에서 '내 일꾼'으로 치지 않는다.
  레이너 기지에 내려온 건설용 탐사정·원시 일벌레는 지금처럼 플레이어가 조종한다.

Usage: python3 tools/build_v0492.py <0.4.91 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines

OLD, NEW = b'version=0.4.91', b'version=0.4.92'
M4 = 'TTychus01.SC2Map/'
UD = M4 + 'base.sc2data/gamedata/unitdata.xml'
SHIELD, DELAY, RATE = 300, 60, 30  # RATE 시험값
YANK = 15.0  # 시험값
SCRIPT = {
    'TRaynor03': [('(gv_m3_threatTick==0 && DistanceBetweenPoints(UnitGetPosition(u),target)>6.0)',
                   f'(gv_m3_threatTick==0 && DistanceBetweenPoints(UnitGetPosition(u),target)>{YANK})')],
    'TTychus01': [('(gv_m4_threatTick==0 && DistanceBetweenPoints(UnitGetPosition(u),gv_m4_threat8)>6.0)',
                   f'(gv_m4_threatTick==0 && DistanceBetweenPoints(UnitGetPosition(u),gv_m4_threat8)>{YANK})'),
                  ('worker=(owner==8 && UnitGetType(u)=="Probe") || (owner==9 && UnitGetType(u)=="DehakaDrone");',
                   'worker=((owner==8 && UnitGetType(u)=="Probe") || (owner==9 && UnitGetType(u)=="DehakaDrone")) && !UnitHasBehavior2(u,"RM_AllyMiner");')],
}
MINER = [('        if (UnitHasBehavior2(u,"RM_AllyMiner")) {\n            n+=1;\n',
          '        if (UnitHasBehavior2(u,"RM_AllyMiner")) {\n            n+=1;\n            libNtve_gf_MakeUnitUncommandable(u,true);\n'),
         ('    UnitBehaviorAdd(u,"RM_AllyMiner",u,1);\n',
          '    UnitBehaviorAdd(u,"RM_AllyMiner",u,1);\n    libNtve_gf_MakeUnitUncommandable(u,true);\n')]
STR = {'Button/Tooltip/MarauderMengskShield':
       f'보호막 {SHIELD}을 갖습니다. 피해를 받지 않고 {DELAY}초가 지나면 다시 채워집니다. /// '
       f'Has {SHIELD} shields. Recharges after {DELAY} seconds without taking damage.'}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt', UD}
        u = files[UD].decode('utf-8')
        m = re.search(r'<CUnit id="MarauderMengsk">.*?</CUnit>', u, re.S)
        b = m.group(0)
        absorb = '<BehaviorArray Link="MarauderMengskAbsorb" />'
        btn = 'Behavior="MarauderMengskAbsorbReapplicator" '
        assert b.count(absorb) == 1 and b.count(btn) == 1 and '<ShieldsMax' not in b
        life = '<LifeArmor value="4" />'
        assert b.count(life) == 1
        b = b.replace(absorb, '').replace(btn, '').replace(life, life +
            f'\n    <ShieldsStart value="{SHIELD}" />\n    <ShieldsMax value="{SHIELD}" />'
            f'\n    <ShieldRegenDelay value="{DELAY}" />\n    <ShieldRegenRate value="{RATE}" />')
        files[UD] = (u[:m.start()] + b + u[m.end():]).encode('utf-8')
        for mp, pairs in SCRIPT.items():
            s = f'{mp}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            for a, c in pairs + MINER:
                assert t.count(a) == 1, (mp, a)
                t = t.replace(a, c)
            files[s] = t.encode('utf-8'); changed.add(s)
        for loc in ('kokr',) + LOCALES:
            p = f'{M4}{loc}.sc2data/localizeddata/gamestrings.txt'
            vals = STR if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in STR.items()}
            files[p] = update_lines(files[p], vals); changed.add(p)
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
