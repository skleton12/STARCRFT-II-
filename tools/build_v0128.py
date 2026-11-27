#!/usr/bin/env python3
"""0.12.7 -> 0.12.8: 코랄(THorner04) 초반 방어 강화·오딘 단계 영웅 지원 (사용자 2026-11-27).

사용자: "코랄에 방어 병력 빡세게 초반부터 대신 오딘이 전투할때 클로로리온이랑 데하카 친구 그 개큰 땅무지 군주 같은거
있잖음 그친구들을 불러와줘", "클로라리온 양옆에 수리비행정 같은거 붙일수 있니?". (멩스크 정예 병력은 다음 판.)

  - 수비대 강화(0.11.9 gf_rmDefBoost)를 코랄에서는 임무 시작 10초 뒤(오딘 단계)에 적 2~5·11번에 바로 적용하고,
    연구 점수 비율에 기본 +50%를 더한다 (gv_rm12DefBase, 시험값). 2단계 7-1은 그대로.
  - 오딘 단계 시작(gt_StartGameStage1)에 레이너(1번) 소유로 오딘 옆에:
      클로라리온(FenixClolarionCarrier, 피닉스 용사 — 맵에 이미 있음),
      무르바르(DehakaMurvar, 데하카 원시 군주 — port_units로 이식; 협동전 둥지 확인 MurvarLairCheck·위신 버튼은 뺌),
      과학선 2기(자날 ScienceVessel, 나노 수리)가 1초마다 클로라리온 양옆(±3)으로 따라붙는다 (시험값).
    부활 없음.
Game not run. Codex review: 대기.

Usage: python3 tools/build_v0128.py <0.12.7 zip> <new output zip>
"""
import argparse, copy, re, shutil, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.12.7', b'version=0.12.8'
M = 'THorner04.SC2Map'
PORT = ['DehakaMurvar', 'MurvarCoopPuke', 'MurvarCreepEggAttachment', 'MurvarCreepSpawn', 'MurvarCreepSpawnLM', 'MurvarCreepSpawnLaunch',
        'MurvarCreepSpawnSet', 'MurvarCreepSpawnWeapon', 'MurvarCreepImpactSet', 'DehakaCreeperFlying', 'SlivanPukeWeapon']
STR = {'Unit/Name/DehakaMurvar': '무르바르 /// Murvar'}

SCRIPT = '''// 0.12.8 (user 2026-11-27): Korhal - tougher defenders from the start; Clolarion + Murvar + two Science Vessels join the Odin.
const fixed gv_rm12DefBase = 0.5;  // trial: +50% defenders on top of the research-point share
unit gv_rm12Clo;
unit gv_rm12Sv1;
unit gv_rm12Sv2;

bool gf_rm12DefOn (int p) {
    return gv_rmEHOn[p] || p == 2 || p == 3 || p == 4 || p == 5 || p == 11;
}

bool gt_rm12Escort_Func (bool testConds, bool runActions) {
    point c;
    fixed f;
    if (!runActions) { return true; }
    if (gv_rm12Clo == null || !UnitIsAlive(gv_rm12Clo)) { return true; }
    c = UnitGetPosition(gv_rm12Clo);
    f = UnitGetFacing(gv_rm12Clo);
    if (gv_rm12Sv1 != null && UnitIsAlive(gv_rm12Sv1) && DistanceBetweenPoints(UnitGetPosition(gv_rm12Sv1), PointWithOffsetPolar(c, 3.0, f + 90.0)) > 1.5) {
        UnitIssueOrder(gv_rm12Sv1, OrderTargetingPoint(AbilityCommand("move", 0), PointWithOffsetPolar(c, 3.0, f + 90.0)), c_orderQueueReplace);
    }
    if (gv_rm12Sv2 != null && UnitIsAlive(gv_rm12Sv2) && DistanceBetweenPoints(UnitGetPosition(gv_rm12Sv2), PointWithOffsetPolar(c, 3.0, f - 90.0)) > 1.5) {
        UnitIssueOrder(gv_rm12Sv2, OrderTargetingPoint(AbilityCommand("move", 0), PointWithOffsetPolar(c, 3.0, f - 90.0)), c_orderQueueReplace);
    }
    return true;
}

void gf_rm12Heroes () {
    point o;
    fixed f;
    if (gv_rm12Clo != null || gv_odin == null) { return; }
    o = UnitGetPosition(gv_odin);
    f = UnitGetFacing(gv_odin);
    UnitCreate(1, "FenixClolarionCarrier", c_unitCreateIgnorePlacement, 1, PointWithOffsetPolar(o, 4.0, f + 150.0), f);
    gv_rm12Clo = UnitLastCreated();
    UnitCreate(1, "DehakaMurvar", 0, 1, PointWithOffsetPolar(o, 4.0, f - 150.0), f);
    UnitCreate(1, "ScienceVessel", c_unitCreateIgnorePlacement, 1, PointWithOffsetPolar(UnitGetPosition(gv_rm12Clo), 3.0, f + 90.0), f);
    gv_rm12Sv1 = UnitLastCreated();
    UnitCreate(1, "ScienceVessel", c_unitCreateIgnorePlacement, 1, PointWithOffsetPolar(UnitGetPosition(gv_rm12Clo), 3.0, f - 90.0), f);
    gv_rm12Sv2 = UnitLastCreated();
    TriggerAddEventTimePeriodic(TriggerCreate("gt_rm12Escort_Func"), 1.0, c_timeGame);
    UIDisplayMessage(PlayerGroupAll(), c_messageAreaSubtitle, StringExternal("Param/Value/RM12_Heroes"));
}

'''


def patch_script(t):
    def rep(a, b, n=1):
        nonlocal t
        assert t.count(a) == n, (a[:80], t.count(a))
        t = t.replace(a, b)
    a = '// 0.11.9 (user 2026-11-26): enemy base defenders grow'
    rep(a, SCRIPT + a)
    rep('    fixed pct = MinF(gv_rmDefMax, gv_rmDefStep * IntToFixed(pts / 5));',
        '    fixed pct = MinF(gv_rmDefMax, gv_rmDefStep * IntToFixed(pts / 5)) + gv_rm12DefBase;')
    rep('        if (gv_rmEHOn[p]) {\n            g = UnitGroup(null, p, RegionEntireMap()', '        if (gf_rm12DefOn(p)) {\n            g = UnitGroup(null, p, RegionEntireMap()')
    rep('    for (p = 2; p <= 15; p += 1) { if (gv_rmEHOn[p]) { any = true; } }', '    for (p = 2; p <= 15; p += 1) { if (gf_rm12DefOn(p)) { any = true; } }')
    # heroes at the start of the Odin stage (the trigger is defined after the mod block? -> forward declare via call site check)
    rep('    gv_missionStage1 = true;\n    GamePauseAllCharges(true);', '    gv_missionStage1 = true;\n    gf_rm12Heroes();\n    GamePauseAllCharges(true);')
    return t


def fix_xml(gd):
    p = gd / 'unitdata.xml'; t = p.read_text('utf-8')
    b = list(re.finditer(r'<CUnit id="DehakaMurvar"[^>]*>.*?</CUnit>', t, re.S)); assert len(b) == 1
    blk = b[0].group(0)
    blk2 = re.sub(r'\s*<BehaviorArray Link="MurvarLairCheck" />', '', blk)
    blk2 = re.sub(r'\s*<LayoutButtons Face="CommanderPrestigeDehakaPackLeadersRetreat"[^>]*/>', '', blk2)
    assert blk2 != blk and 'MurvarLairCheck' not in blk2 and 'CommanderPrestige' not in blk2
    p.write_text(t[:b[0].start()] + blk2 + t[b[0].end():], 'utf-8')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        root = Path(tmp)
        prev.extractall(root)
        m = root / M
        before = {str(p.relative_to(root)).replace('\\', '/') for p in m.rglob('*') if p.is_file()}
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(m), '--liberty-base', '--skip-existing', *PORT],
                       check=True, stdout=subprocess.DEVNULL)
        (m / 'ported_shared_refs.txt').unlink(missing_ok=True)
        gd = m / 'base.sc2data/gamedata'
        fix_xml(gd)
        sp = m / 'mapscript.galaxy'; raw = sp.read_bytes().decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
        t = patch_script(raw.replace('\r\n', '\n'))
        # gf_rm12Heroes is called from gt_StartGameStage1_Func, which comes before the mod block: declare it first.
        a = 'trigger gt_StartGameStage1;\n'; assert t.count(a) == 1
        t = t.replace(a, 'void gf_rm12Heroes ();\n' + a)
        sp.write_bytes(t.replace('\n', nl).encode('utf-8'))
        ko = m / 'kokr.sc2data/localizeddata/gamestrings.txt'
        d = ko.read_bytes(); enl = b'\r\n' if b'\r\n' in d else b'\n'
        lines = {**STR, 'Param/Value/RM12_Heroes': '클로라리온과 무르바르가 오딘과 함께 싸웁니다. 과학선 두 기가 클로라리온을 수리합니다. /// Clolarion and Murvar fight beside the Odin. Two Science Vessels repair Clolarion.'}
        for k in lines: assert (k + '=').encode() not in d, k
        d = d.rstrip(b'\r\n') + enl + enl.join(f'{k}={v}'.encode('utf-8') for k, v in lines.items()) + enl
        V35.gate('kokr', d); ko.write_bytes(d)
        for loc in V35.OTHER_LOCALES:
            (m / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(d))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in gd.glob('*.xml'): E.parse(f)
        names = prev.namelist()
        extra = sorted(str(p.relative_to(root)).replace('\\', '/') for p in m.rglob('*') if p.is_file()
                       and str(p.relative_to(root)).replace('\\', '/') not in before)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist(): z.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra:
                    zi = zipfile.ZipInfo(f, (2026, 11, 27, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    z.writestr(zi, (root / f).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None
                for n in names:
                    if not n.startswith(M + '/') and n != 'metadata.txt': assert z.read(n) == prev.read(n), n
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out, len(extra), 'new files')


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
