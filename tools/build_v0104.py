#!/usr/bin/env python3
"""0.10.3 -> 0.10.4: 탈옥(TTosh03A) 레이너 기지 지원군 수정 (사용자 2026-11-25 "플토 지원군이 움직이지 않음 이름도 이상하게 나옴").
- 이름: 망자의 항구에서 가져온 군단병(ZealotPurifier)은 이름 문자열 Unit/Name/RM_Legionnaire를 쓰는데, 0.10.2가 레코드 ID 기준으로만
  문자열을 옮겨 이 키(와 설명)가 빠졌다 -> 추가.
- 움직임: 이식한 동맹 유닛 5종(군단병·피닉스 사도·원시 저글링·바퀴·히드라)은 다른 미션에서 '명령 불가'(Uncommandable)라
  8·9번 컴퓨터 AI도 못 움직였다. 이 맵에서만 그 깃발을 끄고, 스크립트가 3초마다 지원군을 지휘한다:
  기지 둘레 18칸 안에 적이 있으면 가장 가까운 적에게 공격 이동, 없고 기지에서 8칸 넘게 떨어졌으면 기지로 공격 이동(시험값).
  지원 주기 90초는 그대로. Game not run.
Usage: python3 tools/build_v0104.py <0.10.3 zip> <new output zip>"""
import copy, re, sys, zipfile
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import build_v035 as V35
OLD, NEW = b'version=0.10.3', b'version=0.10.4'
M = 'TTosh03A.SC2Map/'
UD = M + 'base.sc2data/gamedata/unitdata.xml'; SP = M + 'mapscript.galaxy'
KO = M + 'kokr.sc2data/localizeddata/gamestrings.txt'
TYPES = ['ZealotPurifier', 'AdeptFenix', 'DehakaZerglingLevel2', 'DehakaRoachLevel2', 'DehakaHydraliskLevel2']
STR = {'Unit/Name/RM_Legionnaire': '군단병 /// Legionnaire',
       'Button/Tooltip/RM_Legionnaire': '강력한 정화자 근접 전사입니다. 체력 200, 보호막 100, 공격력 16×2. 돌진을 사용할 수 있습니다. /// A powerful Purifier melee warrior. 200 life, 100 shields, 16x2 damage. Can Charge.'}
OLD_LOOP = '''    while (true) {
        if (gv_rmSup8) { gf_rmSupWave(8, PointFromId(280), gv_rmSupG8); }
        if (gv_rmSup9) { gf_rmSupWave(9, PointFromId(434), gv_rmSupG9); }
        Wait(90.0, c_timeGame);
    }'''
NEW_LOOP = '''    t = 0;
    while (true) {
        if (t <= 0) {
            if (gv_rmSup8) { gf_rmSupWave(8, PointFromId(280), gv_rmSupG8); }
            if (gv_rmSup9) { gf_rmSupWave(9, PointFromId(434), gv_rmSupG9); }
            t = 30;
        }
        gf_rmSupGuard(8, PointFromId(280), gv_rmSupG8);
        gf_rmSupGuard(9, PointFromId(434), gv_rmSupG9);
        Wait(3.0, c_timeGame);
        t -= 1;
    }'''
GUARD = '''// 0.10.4: the support units are commanded by script (guard their outpost, trial radii 18 / 8).
void gf_rmSupGuard (int pl, point c, unitgroup g) {
    unitgroup e;
    unit u;
    int i;
    point tgt;
    if (g == null || UnitGroupCount(g, c_unitCountAlive) < 1) { return; }
    e = UnitGroupAlliance(pl, c_unitAllianceEnemy, RegionCircle(c, 18.0), UnitFilter(0, 0, (1 << c_targetFilterMissile) | (1 << c_targetFilterStructure), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0);
    if (UnitGroupCount(e, c_unitCountAlive) < 1) {
        e = UnitGroupAlliance(pl, c_unitAllianceEnemy, RegionCircle(c, 18.0), UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0);
    }
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {
        u = UnitGroupUnit(g, i);
        if (u == null || !UnitIsAlive(u)) { continue; }
        if (UnitGroupCount(e, c_unitCountAlive) > 0) {
            tgt = UnitGetPosition(UnitGroupClosestToPoint(e, UnitGetPosition(u)));
            if (UnitOrderCount(u) < 1 || DistanceBetweenPoints(UnitGetPosition(u), tgt) > 6.0) {
                UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), tgt), c_orderQueueReplace);
            }
        }
        else if (DistanceBetweenPoints(UnitGetPosition(u), c) > 8.0) {
            UnitIssueOrder(u, OrderTargetingPoint(AbilityCommand("attack", 0), c), c_orderQueueReplace);
        }
    }
}

'''
ANCHOR = 'bool gt_rmSupport_Func (bool testConds, bool runActions) {'
def main(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        t = z.read(UD).decode('utf-8')
        for k in TYPES:
            m = re.search(r'<CUnit id="%s"[^>]*>.*?</CUnit>' % k, t, re.S)
            assert m and m.group(0).count('<FlagArray index="Uncommandable" value="1" />') == 1, k
            t = t[:m.start()] + m.group(0).replace('<FlagArray index="Uncommandable" value="1" />', '<FlagArray index="Uncommandable" value="0" />') + t[m.end():]
        rep[UD] = t.encode('utf-8')
        raw = z.read(SP).decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'; s = raw.replace('\r\n', '\n')
        assert s.count(OLD_LOOP) == 1 and s.count(ANCHOR) == 1
        s = s.replace(OLD_LOOP, NEW_LOOP).replace(ANCHOR, GUARD + ANCHOR + '\n    int t;')
        rep[SP] = s.replace('\n', nl).encode('utf-8')
        kb = z.read(KO); bom = kb.startswith(b'\xef\xbb\xbf'); k = kb.decode('utf-8-sig'); knl = '\r\n' if '\r\n' in k else '\n'
        keys = {l.split('=', 1)[0] for l in k.splitlines() if '=' in l}
        add = [f'{a}={b}' for a, b in STR.items() if a not in keys]; assert len(add) == 2
        k = k.rstrip('\r\n') + knl + knl.join(add) + knl
        kb = k.encode('utf-8-sig' if bom else 'utf-8'); V35.gate('kokr', kb); rep[KO] = kb
        for loc in V35.OTHER_LOCALES:
            rep[M + f'{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(kb)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                for i in z.infolist(): o.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)))
            with zipfile.ZipFile(out) as o: assert o.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out, len(rep), 'files changed')
if __name__ == '__main__': main(*sys.argv[1:])
