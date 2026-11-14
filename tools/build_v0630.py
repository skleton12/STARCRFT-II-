#!/usr/bin/env python3
"""0.6.29 -> 0.6.30: 1번 미션 울타리에 끼는 추가 해병 정리 (사용자 2026-11-14).

사용자: "그 조정 잘 않되어있네 1번미션에 울타리에 낑기는 해병들 아직도 있네".
원인: 0.6.27 맵 점검은 맵에 배치된 유닛(objects)만 원본과 비교했고, 스크립트가 만드는 추가 적은 보지 않았다.
1번은 7-1 병력 증강으로 스크립트가 해병을 만든다:
  - gf_rm_SpawnMidReinforce: 마을 띠의 해병 2명마다 1명을 그 해병 '바로 옆'에 복제 -> 울타리 사이에 끼일 수 있다.
  - gf_rm_SpawnLateDefenders: 본부 앞 해병 9·화염방사병 4.
수정: 만든 직후 그 유닛 자리가 '지나갈 수 있는 땅'이고 동맹 등장 지점(PointFromId(505), 레이너 출발 쪽)과
길이 이어져 있는지 확인한다. 아니면 그 추가 유닛을 지운다 (끼인 채 남기지 않음). 원본 배치 유닛은 건드리지 않는다.
같은 확인을 3번 피닉스(0.6.28) 생성에도 건다: 생성 지점이 막혔으면 레이너 사령부 쪽 출발 위치로 옮긴다.
적 물량 증가 (사용자 "적군도 병력 많이 생성하거나 물량으로 오게 하는것이 나을듯"):
  - 2~6번 공세 수 AI 칸별 배수 1.0/1.0/1.1/1.2 -> 1.25/1.25/1.35/1.5, 정예 1.5 -> 1.8 (시험값, 0.6.27 gf_rmWave4 상수).
  - 1번 마을 띠 추가 해병: 2명마다 1명 -> 1명마다 1명 (시험값, 끼면 위 확인으로 지움).
게임 미실행 (경로 확인 함수 PointPathingPassable·PointPathingIsConnected는 core natives).

Usage: python3 tools/build_v0630.py <0.6.29 zip> <new output zip>
"""
import argparse, copy, tempfile, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.29', b'version=0.6.30'

KEEP_FN = '''// 0.6.30 (user 2026-11-14): extra spawned enemies stuck in fences/doodads are removed.
// Kept only if standing on passable ground that connects to the ally spawn point (Raynor's side).
void gf_rmDropStuck (unitgroup g) {
    point lv_anchor = PointFromId(505);
    int lv_i;
    unit lv_u;
    for (lv_i = UnitGroupCount(g, c_unitCountAll); lv_i > 0; lv_i -= 1) {
        lv_u = UnitGroupUnit(g, lv_i);
        if (!PointPathingPassable(UnitGetPosition(lv_u)) || !PointPathingIsConnected(UnitGetPosition(lv_u), lv_anchor)) {
            UnitRemove(lv_u);
        }
    }
}

'''
M1 = [
    ('void gf_rm_SpawnLateDefenders () {\n', KEEP_FN + 'void gf_rm_SpawnLateDefenders () {\n'),
]
LATE = [
    ('    UnitCreate(3, "Marine", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, -5.0, -8.0), 90.0);\n', 1),
    ('    UnitCreate(3, "Marine", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, 0.0, -9.0), 90.0);\n', 1),
    ('    UnitCreate(3, "Marine", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, 5.0, -8.0), 90.0);\n', 1),
    ('    UnitCreate(2, "Firebat", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, -3.0, -6.0), 90.0);\n', 1),
    ('    UnitCreate(2, "Firebat", 0, gv_p2_DOMINION_RED, PointWithOffset(lv_hq, 3.0, -6.0), 90.0);\n', 1),
]
MID_OLD = '            UnitCreate(1, "Marine", 0, gv_p2_DOMINION_RED, UnitGetPosition(lv_u), UnitGetFacing(lv_u));\n'
MID_NEW = MID_OLD + '            gf_rmDropStuck(UnitLastCreatedGroup());\n'

M3_OLD = '    UnitCreate(1, "FenixDragoon", 0, 1, Point(100.0, 38.0), 270.0);\n'
M3_NEW = ('    UnitCreate(1, "FenixDragoon", 0, 1, Point(100.0, 38.0), 270.0);\n'
          '    if (!PointPathingPassable(UnitGetPosition(UnitLastCreated()))) {\n'
          '        UnitSetPosition(UnitLastCreated(), PlayerStartLocation(1), false);\n'
          '    }\n')


WAVE_CONST = [('const fixed gv_rmEliteWaveMult = 1.5;', 'const fixed gv_rmEliteWaveMult = 1.8;'),
              ('const fixed gv_rmWaveMult2 = 1.0;', 'const fixed gv_rmWaveMult2 = 1.25;'),
              ('const fixed gv_rmWaveMult3 = 1.0;', 'const fixed gv_rmWaveMult3 = 1.25;'),
              ('const fixed gv_rmWaveMult4 = 1.1;', 'const fixed gv_rmWaveMult4 = 1.35;'),
              ('const fixed gv_rmWaveMult5 = 1.2;', 'const fixed gv_rmWaveMult5 = 1.5;')]
MID_EVERY = ('        if (ModI(lv_i, 2) == 0) {\n', '        if (ModI(lv_i, 1) == 0) {\n')


def once(t, a, b):
    assert t.count(a) == 1, a[:70]
    return t.replace(a, b)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        changed = {'metadata.txt'}
        for m in ('TRaynor02', 'TTychus01', 'TTosh01', 'THanson01'):
            p = root / f'{m}.SC2Map/mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            for a, b in WAVE_CONST: t = once(t, a, b)
            p.write_bytes(t.replace('\n', nl).encode('utf-8'))
            changed.add(f'{m}.SC2Map/mapscript.galaxy')
        for m, fn in (('TRaynor01', 'm1'), ('TRaynor03', 'm3')):
            p = root / f'{m}.SC2Map/mapscript.galaxy'
            raw = p.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            t = raw.replace('\r\n', '\n')
            if fn == 'm1':
                for a, b in M1: t = once(t, a, b)
                for a, _ in LATE: t = once(t, a, a + '    gf_rmDropStuck(UnitLastCreatedGroup());\n')
                t = once(t, MID_OLD, MID_NEW)
                t = once(t, *MID_EVERY)
            else:
                t = once(t, M3_OLD, M3_NEW)
                for a, b in WAVE_CONST: t = once(t, a, b)
            p.write_bytes(t.replace('\n', nl).encode('utf-8'))
            changed.add(f'{m}.SC2Map/mapscript.galaxy')
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names
                for n in names:
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
