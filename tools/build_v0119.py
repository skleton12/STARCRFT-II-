#!/usr/bin/env python3
"""0.11.8 -> 0.11.9: 적 기지 수비대 = 연구 점수에 맞춰 강화 (사용자 2026-11-26 "적들 방어 병력좀 강화해줘 동맹이 점점 많아지니
적들도 약해짐", 선택 "연구 점수에 맞춰", "3~11번 전부" — 10번 탈옥은 7-1·동맹 지원이 없어 제외).
동맹 지원을 키우는 히페리온 연구 점수(프로토스 + 저그, 각 최대 25)로 5점마다 +10%, 최대 +100% (시험값).
7-1 강화를 받는 적(gv_rmEHOn)이 처음 정해지고 게임 10초가 지난 뒤 한 번: 그 적의 무기 있는 비건물·비일꾼·비영웅 유닛 중
자기 건물 15칸 안(기지 수비대)에 있는 것마다 비율만큼(누적 반올림) 같은 유닛을 옆에 하나 더 만든다.
지나갈 수 있고 레이너 본진과 길이 이어진 자리만(0.6.30 규칙). 발할라는 7-1이 호위 단계 시작에 걸리므로 창고 단계는 영향 없음.
Game not run.  Usage: python3 tools/build_v0119.py <0.11.8 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.11.8', b'version=0.11.9'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03']

CODE = r'''// 0.11.9 (user 2026-11-26): enemy base defenders grow with the Hyperion research points that also grow the allies.
const fixed gv_rmDefStep = 0.10;  // trial: +10% per 5 points (Protoss + Zerg)
const fixed gv_rmDefMax = 1.0;    // trial: at most +100%
bool gv_rmDefDone;

void gf_rmDefBoost () {
    int pts = MaxI(0, MinI(libCamp_gf_StoryResearchPoints(libCamp_ge_StoryResearchCategory_ResearchCategoryProtoss), 25))
            + MaxI(0, MinI(libCamp_gf_StoryResearchPoints(libCamp_ge_StoryResearchCategory_ResearchCategoryZerg), 25));
    fixed pct = MinF(gv_rmDefMax, gv_rmDefStep * IntToFixed(pts / 5));
    fixed carry = 0.0;
    point home = gf_rmVHTarget();
    int p;
    int i;
    int n;
    unitgroup g;
    unit u;
    string t;
    point pt;
    if (pct <= 0.0) { return; }
    for (p = 2; p <= 15; p += 1) {
        if (gv_rmEHOn[p]) {
            g = UnitGroup(null, p, RegionEntireMap(), UnitFilter(0, 0, (1 << c_targetFilterStructure) | (1 << c_targetFilterWorker) | (1 << c_targetFilterHeroic) | (1 << c_targetFilterMissile) | (1 << c_targetFilterUncommandable), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterHallucination - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);
            n = UnitGroupCount(g, c_unitCountAll);
            for (i = 1; i <= n; i += 1) {
                u = UnitGroupUnit(g, i);
                if (UnitWeaponCount(u) > 0 && UnitTransport(u) == null
                    && UnitGroupCount(UnitGroup(null, p, RegionCircle(UnitGetPosition(u), 15.0), UnitFilter((1 << c_targetFilterStructure), 0, 0, (1 << (c_targetFilterDead - 32))), 1), c_unitCountAlive) > 0) {
                    carry += pct;
                    if (carry >= 1.0) {
                        carry -= 1.0;
                        t = UnitGetType(u);
                        pt = UnitTypePlacementFromPoint(t, p, UnitGetPosition(u), 4.0);
                        if (pt != null && PointPathingPassable(pt) && (home == null || PointPathingIsConnected(pt, home))) {
                            UnitCreate(1, t, 0, p, pt, UnitGetFacing(u));
                        }
                    }
                }
            }
        }
    }
}

bool gt_rmDefBoost_Func (bool testConds, bool runActions) {
    int p;
    bool any = false;
    if (!runActions || gv_rmDefDone) { return true; }
    if (GameGetMissionTime() < 10.0) { return true; }
    for (p = 2; p <= 15; p += 1) { if (gv_rmEHOn[p]) { any = true; } }
    if (!any) { return true; }
    gv_rmDefDone = true;
    TriggerEnable(TriggerGetCurrent(), false);
    gf_rmDefBoost();
    return true;
}

'''
REG = '    TriggerAddEventTimePeriodic(TriggerCreate("gt_rmDefBoost_Func"), 2.0, c_timeGame);  // 0.11.9\n'


def script(t):
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    a = 'void InitMap () {\n    InitLibs();\n'
    assert t.count(a) == 1 and 'gf_rmDefBoost' not in t and 'point gf_rmVHTarget ()' in t and 'bool[16] gv_rmEHOn;' in t
    t = t.replace(a, CODE + a + REG)
    return t.replace('\n', '\r\n') if crlf else t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    targets = {f'{m}.SC2Map/mapscript.galaxy' for m in MAPS}
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                done = 0
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    elif info.filename in targets: d = script(d.decode('utf-8')).encode('utf-8'); done += 1
                    o.writestr(copy.copy(info), d, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                assert done == len(MAPS), done
            with zipfile.ZipFile(out) as o:
                assert o.testzip() is None
                for n in prev.namelist():
                    if n != 'metadata.txt' and n not in targets: assert o.read(n) == prev.read(n), n
        except BaseException:
            out.unlink(missing_ok=True); raise


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
