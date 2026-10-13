#!/usr/bin/env python3
"""1번 미션(해방의 날) 패치: 레이너(1번 슬롯) 측 해병을 용병 전쟁광(WarPig)으로 바꾼다.

원본 맵(source/.../traynor01.sc2map)을 build/TRaynor01.SC2Map으로 복사한 뒤
트리거 데이터(triggers)와 생성된 스크립트(mapscript.galaxy)를 같은 내용으로 고친다.
편집기는 triggers에서 mapscript.galaxy를 다시 만들기 때문에 둘 다 바꿔야 한다.

적(2번 자치령)과 연출용(4번) 해병, 자치령 해병 처치 통계 조건은 건드리지 않는다.
"""
import os, re, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'source', 'liberty.sc2campaign', 'base.sc2maps', 'maps', 'campaign', 'traynor01.sc2map')
OUT = os.path.join(ROOT, 'build', 'TRaynor01.SC2Map')

MERC_MARINE = 'WarPig'  # 해병 역할 용병 (사용자 확정 2026-10-13)

# 레이너 측 해병을 만드는 트리거 함수 호출 (triggers 안의 FunctionCall Id)
P1_MARINE_CALLS = {
    '5581142B': '유닛 도움말 패널에 해병 추가',
    '0D4D4EE7': '중간 증원 3명 (지점 58)',
    'EAA58A0F': '중간 증원 3명 (지점 89)',
    '9DD16ECE': '중간 증원 3명 (지점 106)',
    '375FC5FD': '시작 연출 수송선 화물 5명',
    '0CCF2C98': '시작 배치 (지점 415)',
    '6500E82C': '시작 배치 (지점 581)',
    '90566DEC': '시작 배치 (지점 737)',
    '1EA61321': '시작 배치 (지점 885)',
    'E6D930DB': '시작 배치 (지점 1020)',
}

# mapscript.galaxy에서 바꿀 줄 (위 호출들이 만들어낸 코드)
GALAXY_PATTERNS = [
    r'libCamp_gf_AddUnitTypeToUnitHelpPanel\("Marine", false, gv_p1_USER\)',
    r'libNtve_gf_CreateUnitsWithDefaultFacing\(3, "Marine", 0, gv_p1_USER, PointFromId\(\d+\)\)',
    r'UnitCargoCreate\(gv_introDropship, "Marine", 5\)',
    r'libNtve_gf_CreateUnitsAtPoint2\(1, "Marine", 0, gv_p1_USER, PointFromId\(\d+\)\)',
]


def patch_triggers(text):
    # FunctionCall -> 그 안의 Param Id 목록
    calls = dict(re.findall(r'<Element Type="FunctionCall" Id="([0-9A-F]+)">(.*?)</Element>', text, re.S))
    done = []
    for call_id, desc in P1_MARINE_CALLS.items():
        body = calls.get(call_id)
        if body is None:
            sys.exit(f'트리거 호출 {call_id}({desc})을 찾지 못함')
        hit = False
        for pid in re.findall(r'<Parameter Type="Param" Id="([0-9A-F]+)"/>', body):
            pat = re.compile(r'(<Element Type="Param" Id="%s">.*?<Value>)Marine(</Value>.*?</Element>)' % pid, re.S)
            text, n = pat.subn(r'\g<1>%s\g<2>' % MERC_MARINE, text, count=1)
            if n:
                hit = True
                break
        if not hit:
            sys.exit(f'트리거 호출 {call_id}({desc})에 Marine 값이 없음')
        done.append(desc)
    return text, done


def patch_galaxy(text):
    total = 0
    for pat in GALAXY_PATTERNS:
        text, n = re.subn(pat, lambda m: m.group(0).replace('"Marine"', f'"{MERC_MARINE}"'), text)
        total += n
    return text, total


def main():
    if not os.path.isdir(SRC):
        sys.exit(f'원본 맵 없음: {SRC}')
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    shutil.copytree(SRC, OUT)

    p = os.path.join(OUT, 'triggers')
    with open(p, encoding='utf-8', newline='') as f:
        t = f.read()
    t, done = patch_triggers(t)
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(t)

    p = os.path.join(OUT, 'mapscript.galaxy')
    with open(p, encoding='utf-8', newline='') as f:
        g = f.read()
    g, n = patch_galaxy(g)
    with open(p, 'w', encoding='utf-8', newline='') as f:
        f.write(g)

    if n != len(P1_MARINE_CALLS):
        sys.exit(f'mapscript.galaxy 변경 {n}곳, 트리거 {len(done)}곳: 개수가 다름')
    print(f'{OUT}')
    for d in done:
        print(f'  - {d}: Marine -> {MERC_MARINE}')


if __name__ == '__main__':
    main()
