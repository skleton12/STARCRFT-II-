#!/usr/bin/env python3
"""0.12.10 -> 0.12.11: 코랄 영웅 지원 정리 (사용자 2026-11-27 "무기 언노운으로 나오고 키설정 않되있고 왜 수리 비행정이
과학선이 되어있지", "이 두 영웅 … 그것 끝나면 공중으로 사라지거나 지하로 탈출하는걸로").

THorner04:
  - 이름 없던 무기·버튼 문자열(무르바르 무기·능력 2개, 클로라리온 요격기·폭격기 무기, 땅무지 급강하)과
    무르바르·클로라리온·땅무지 버튼 단축키를 넣는다 (한국어 이름 공식 번역 미확인).
  - 클로라리온 양옆 수리기를 과학선 → 카락스 우주모함 수리 드론(CarrierRepairDrone, 공허 캠페인 port_units 이식)으로.
  - 오딘 단계가 끝나고 2단계(gf_m12_Start)가 시작되면 영웅이 떠난다: 클로라리온·수리 드론은 무적이 되어 하늘로 날아가 3초 뒤 사라지고,
    무르바르는 잠복 동작 뒤 땅속으로 사라진다 (2초). 잠복 동작이 없는 모델이면 그냥 사라진다.
  - 동맹 호출 버튼은 원래대로 2단계 시작 5초 뒤 생긴다(첫 사용 임무 4분 이후) — 확인만, 변경 없음.
Game not run. Codex review: 대기.

Usage: python3 tools/build_v01211.py <0.12.10 zip> <new output zip>
"""
import argparse, copy, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.12.10', b'version=0.12.11'
M = 'THorner04.SC2Map'
LOCS = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
STR = {
    'Weapon/Name/SlivanRanged': '산성 침 /// Acid Spit',
    'Weapon/Name/FenixClolarionInterceptorBeam': '요격기 광선 /// Interceptor Beam',
    'Weapon/Name/FenixClolarionBomber': '폭격기 /// Bomber',
    'Button/Name/CoopMurvarSpawnCreepers': '땅무지 소환 /// Spawn Creepers',
    'Button/Tooltip/CoopMurvarSpawnCreepers': '주변의 적에게 땅무지를 내보냅니다. 자동 시전. /// Releases Creepers at nearby enemies. Autocast.',
    'Button/Name/MurvarPukeCoop': '산성 토사물 /// Acid Puke',
    'Button/Tooltip/MurvarPukeCoop': '적에게 산성 토사물을 뱉습니다. /// Spews acid at enemies.',
    'Button/Name/DehakaLocustFlyingSwoop': '급강하 /// Swoop',
    'Button/Tooltip/DehakaLocustFlyingSwoop': '땅무지가 지상으로 내려와 싸웁니다. /// The Creeper swoops down to fight on the ground.',
    'Unit/Name/CarrierRepairDrone': '수리 드론 /// Repair Drone',
    'Param/Value/RM12_Heroes': '클로라리온과 무르바르가 오딘과 함께 싸웁니다. 수리 드론 두 기가 클로라리온을 수리합니다. /// Clolarion and Murvar fight beside the Odin. Two Repair Drones repair Clolarion.',
    'Param/Value/RM12_Leave': '클로라리온과 무르바르가 전장을 떠납니다. /// Clolarion and Murvar leave the battlefield.',
}
HOT = {'CoopMurvarSpawnCreepers': 'C', 'MurvarPukeCoop': 'P', 'DehakaLocustFlyingSwoop': 'W', 'FenixClolarionInterceptor': 'I',
       'FenixClolarionBomberDummy': 'B', 'FenixClolarionBomber': 'B', 'FenixClolarionSolarBeam': 'S'}

LEAVE = '''bool gt_rm12Leave_Func (bool testConds, bool runActions) {
    point c;
    if (!runActions) { return true; }
    if (gv_rm12Clo == null || gv_rm12Gone) { return true; }
    gv_rm12Gone = true;
    UIDisplayMessage(PlayerGroupAll(), c_messageAreaSubtitle, StringExternal("Param/Value/RM12_Leave"));
    if (UnitIsAlive(gv_rm12Clo)) {
        c = UnitGetPosition(gv_rm12Clo);
        UnitSetState(gv_rm12Clo, c_unitStateInvulnerable, true);
        UnitIssueOrder(gv_rm12Clo, OrderTargetingPoint(AbilityCommand("move", 0), PointWithOffsetPolar(c, 20.0, UnitGetFacing(gv_rm12Clo))), c_orderQueueReplace);
    }
    if (gv_rm12Sv1 != null && UnitIsAlive(gv_rm12Sv1)) { UnitSetState(gv_rm12Sv1, c_unitStateInvulnerable, true); }
    if (gv_rm12Sv2 != null && UnitIsAlive(gv_rm12Sv2)) { UnitSetState(gv_rm12Sv2, c_unitStateInvulnerable, true); }
    if (gv_rm12Mur != null && UnitIsAlive(gv_rm12Mur)) {
        UnitSetState(gv_rm12Mur, c_unitStateInvulnerable, true);
        UnitIssueOrder(gv_rm12Mur, Order(AbilityCommand("stop", 0)), c_orderQueueReplace);
        libNtve_gf_SendActorMessageToUnit(gv_rm12Mur, "AnimPlay Burrow Burrow");
    }
    Wait(2.0, c_timeGame);
    if (gv_rm12Mur != null && UnitIsAlive(gv_rm12Mur)) { UnitRemove(gv_rm12Mur); }
    Wait(1.0, c_timeGame);
    if (UnitIsAlive(gv_rm12Clo)) { UnitRemove(gv_rm12Clo); }
    if (gv_rm12Sv1 != null && UnitIsAlive(gv_rm12Sv1)) { UnitRemove(gv_rm12Sv1); }
    if (gv_rm12Sv2 != null && UnitIsAlive(gv_rm12Sv2)) { UnitRemove(gv_rm12Sv2); }
    return true;
}

void gf_rm12Leave () {
    TriggerExecute(TriggerCreate("gt_rm12Leave_Func"), false, false);
}

'''


def patch_script(t):
    def rep(a, b):
        nonlocal t
        assert t.count(a) == 1, a[:80]
        t = t.replace(a, b)
    rep('unit gv_rm12Sv2;\n', 'unit gv_rm12Sv2;\nunit gv_rm12Mur;\nbool gv_rm12Gone;\n')
    rep('    UnitCreate(1, "DehakaMurvar", 0, 1, PointWithOffsetPolar(o, 4.0, f - 150.0), f);\n',
        '    UnitCreate(1, "DehakaMurvar", 0, 1, PointWithOffsetPolar(o, 4.0, f - 150.0), f);\n    gv_rm12Mur = UnitLastCreated();\n')
    assert t.count('"ScienceVessel", c_unitCreateIgnorePlacement') == 2
    t = t.replace('"ScienceVessel", c_unitCreateIgnorePlacement', '"CarrierRepairDrone", c_unitCreateIgnorePlacement')
    a = 'void gf_rm12Heroes () {\n'
    rep(a, LEAVE + a)
    # the escort follow stops once the heroes leave
    rep('    if (gv_rm12Clo == null || !UnitIsAlive(gv_rm12Clo)) { return true; }\n',
        '    if (gv_rm12Clo == null || !UnitIsAlive(gv_rm12Clo) || gv_rm12Gone) { return true; }\n')
    # gf_m12_Start (stage 2) is above the mod block: forward-declare and call
    rep('void gf_m12_Start () {\n', 'void gf_rm12Leave ();\nvoid gf_m12_Start () {\n')
    rep('    gv_m12_started=true;\n', '    gv_m12_started=true;\n    gf_rm12Leave();\n')
    return t


def set_lines(path, d):
    raw = path.read_bytes(); txt = raw.decode('utf-8-sig'); bom = raw.startswith(b'\xef\xbb\xbf')
    nl = '\r\n' if '\r\n' in txt else '\n'
    lines = txt.split(nl) if txt else []
    keys = {}
    for i, l in enumerate(lines):
        if '=' in l: keys[l.split('=', 1)[0]] = i
    for k, v in d.items():
        if k in keys: lines[keys[k]] = f'{k}={v}'
        else:
            while lines and lines[-1] == '': lines.pop()
            lines.append(f'{k}={v}')
    out = nl.join(lines).rstrip(nl) + nl
    path.write_bytes((b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8'))


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        root = Path(tmp); prev.extractall(root); m = root / M
        before = {str(p.relative_to(root)).replace('\\', '/') for p in m.rglob('*') if p.is_file()}
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(m), '--liberty-base', '--skip-existing', 'CarrierRepairDrone'],
                       check=True, stdout=subprocess.DEVNULL)
        (m / 'ported_shared_refs.txt').unlink(missing_ok=True)
        ad = m / 'base.sc2data/gamedata/actordata.xml'; at = ad.read_text('utf-8')
        blk = list(re.finditer(r'<CActorUnit id="CarrierRepairDrone"[^>]*>.*?</CActorUnit>', at, re.S)); assert len(blk) == 1
        nb = re.sub(r'\s*<On [^>]*Send="Create Observer_Land"[^>]*/>', '', blk[0].group(0))
        assert nb != blk[0].group(0) and 'Observer_Land' not in nb
        ad.write_text(at[:blk[0].start()] + nb + at[blk[0].end():], 'utf-8')
        sp = m / 'mapscript.galaxy'; raw = sp.read_bytes().decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
        sp.write_bytes(patch_script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'))
        ko = m / 'kokr.sc2data/localizeddata/gamestrings.txt'
        set_lines(ko, STR); V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (m / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        for loc in LOCS:
            set_lines(m / f'{loc}.sc2data/localizeddata/gamehotkeys.txt', {f'Button/Hotkey/{k}': v for k, v in HOT.items()})
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in (m / 'base.sc2data/gamedata').glob('*.xml'): E.parse(f)
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
