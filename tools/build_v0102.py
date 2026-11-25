#!/usr/bin/env python3
"""0.10.1 -> 0.10.2: 뉴 폴섬 탈옥(TTosh03A) 수정 (사용자 2026-11-25 "피닉스 공격시 에러 데하카 어디감",
"뉴폴섬 미션에 동맹 지원은 넣지 말아줘 대신 레이너 그 기지 지을때 한곳은 플토 지원 한곳은 원시저그가 지원하게 해줘").

- 피닉스: 0.10.1은 FenixDragoon에서 앞으로만 데이터를 떠 와 공격 연출 액터(ColarionDragoonAttack, 미사일, 포탑,
  충전 사격 액터 등 '공격을 가리키는' 액터)가 빠졌다 -> catalog_closure 역방향(reverse=Fenix|Dragoon|Buster)으로 추가.
- 데하카: 협동전 숨은 행동 DehakaAirUnkillable(도약 중 말고는 죽지 않음)·없는 사망 효과(CommanderPrestige...) 제거,
  기본 체력바 켬, 모델 파일 경로를 직접 적음, 생성은 배치 무시로 하고 합류 자막.
- 레이너 특공대 기지 지원 (동맹 버튼 없음): 1번 방어 기지(8번 플레이어, 분홍)가 세워지면 정화자 지원(군단병 2·피닉스 사도 2),
  2번 방어 기지(9번, 초록)가 세워지면 원시저그 지원(원시 저글링 4·바퀴 1·히드라 1). 90초마다,
  그 플레이어 건물이 남아 있을 때, 쪽마다 지원 유닛 16기 상한, 유닛은 그 플레이어 소유. 모두 시험값.
  유닛 데이터는 망자의 항구(THorner02) 맵 것(군단병 0.6.36 등 포함)과 모델 Assets.
Game not run.

Usage: python3 tools/build_v0102.py <0.10.1 zip> <new output zip>
"""
import argparse, copy, re, shutil, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import build_v0101 as V1

OLD, NEW = b'version=0.10.1', b'version=0.10.2'
M = 'TTosh03A.SC2Map'
BASE = ','.join(map(str, V1.BASE))
ALLY_ROOTS = 'ZealotPurifier,AdeptFenix,DehakaZerglingLevel2,DehakaRoachLevel2,DehakaHydraliskLevel2,RM_Legionnaire,RM_LegionnairePsiBlades,RM4_AdeptFenixWeapon,AdeptProtossSpiritDeathModel,GlazeSentinelRepair,AdeptWeapon'
ALLY_ALLOW = 'allow=^(ZealotPurifier|AdeptFenix|Dehaka(Zergling|Roach|Hydralisk)Level2|RM_Legionnaire\\w*|RM4_AdeptFenixWeapon|AdeptProtossSpiritDeathModel|GlazeSentinelRepair|AdeptWeapon)$'
ALLY_REV = ('reverse=^(Adept(LM|LMSet|Damage|Weapon)|DehakaRoach(Level2)?(LM|Damage)|DehakaHydraliskLevel2NeedleSpines\\w*|'
            'RM_LegionnairePsiBlades|LegionnairePsiBlades\\w*|DehakaZerglingLevel2|DehakaRoachLevel2|DehakaHydraliskLevel2)$')

SUP_FN = '''// 0.10.2 (user 2026-11-25): Raynor's Raiders outposts get ally support. Outpost 01 (player 8) = Purifier,
// outpost 02 (player 9) = Primal Zerg. Every 90 s while that player has a structure, cap 16 support units per side (trial).
bool gv_rmSup8;
bool gv_rmSup9;
unitgroup gv_rmSupG8;
unitgroup gv_rmSupG9;

point gf_rmSupPt (point c) {
    point p;
    int i = 0;
    while (i < 8) {
        p = PointWithOffsetPolar(c, RandomFixed(2.0, 5.0), RandomFixed(0.0, 360.0));
        if (PointPathingPassable(p) && PointPathingIsConnected(p, c)) { return p; }
        i += 1;
    }
    return c;
}

void gf_rmSupUnit (int pl, string k, point c, unitgroup g) {
    point p = gf_rmSupPt(c);
    UnitCreate(1, k, c_unitCreateIgnorePlacement, pl, p, RandomFixed(0.0, 360.0));
    if (UnitLastCreated() != null) { UnitGroupAdd(g, UnitLastCreated()); }
}

void gf_rmSupWave (int pl, point c, unitgroup g) {
    int i;
    if (UnitGroupCount(UnitGroup(null, pl, RegionEntireMap(), UnitFilter((1 << c_targetFilterStructure), 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) < 1) { return; }
    if (UnitGroupCount(g, c_unitCountAlive) > 16 - 4 - 2 * (pl - 8)) { return; }
    if (pl == 8) {
        for (i = 1; i <= 2; i += 1) { gf_rmSupUnit(pl, "ZealotPurifier", c, g); gf_rmSupUnit(pl, "AdeptFenix", c, g); }
        UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaSubtitle, StringExternal("Param/Value/RM10_Sup8"));
    }
    else {
        for (i = 1; i <= 4; i += 1) { gf_rmSupUnit(pl, "DehakaZerglingLevel2", c, g); }
        gf_rmSupUnit(pl, "DehakaRoachLevel2", c, g);
        gf_rmSupUnit(pl, "DehakaHydraliskLevel2", c, g);
        UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaSubtitle, StringExternal("Param/Value/RM10_Sup9"));
    }
}

bool gt_rmSupport_Func (bool testConds, bool runActions) {
    gv_rmSupG8 = UnitGroupEmpty();
    gv_rmSupG9 = UnitGroupEmpty();
    while (true) {
        if (gv_rmSup8) { gf_rmSupWave(8, PointFromId(280), gv_rmSupG8); }
        if (gv_rmSup9) { gf_rmSupWave(9, PointFromId(434), gv_rmSupG9); }
        Wait(90.0, c_timeGame);
    }
    return true;
}

void gf_rmSupStart (int pl) {
    bool first = !gv_rmSup8 && !gv_rmSup9;
    if (pl == 8) { gv_rmSup8 = true; } else { gv_rmSup9 = true; }
    if (first) { TriggerExecute(TriggerCreate("gt_rmSupport_Func"), false, false); }
    else if (pl == 8) { gf_rmSupWave(8, PointFromId(280), gv_rmSupG8); }
    else { gf_rmSupWave(9, PointFromId(434), gv_rmSupG9); }
}

'''
HOOK8 = '    AIToggleBulliesInRegion(gv_p8_ALLIED_PINK, RegionFromId(5), true);\n'
HOOK9 = '    AIToggleBulliesInRegion(gv_p9_ALLIED_GREEN, RegionFromId(6), true);\n'
OLD_SPAWN = '    gf_rmHero("FenixDragoon", -3.0);\n    gf_rmHero("DehakaCoop", 3.0);\n'
NEW_SPAWN = OLD_SPAWN + '    UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaSubtitle, StringExternal("Param/Value/RM10_Heroes"));\n'
OLD_CREATE = '    UnitCreate(1, k, 0, 1, p, 270.0);\n'
NEW_CREATE = '    UnitCreate(1, k, c_unitCreateIgnorePlacement, 1, p, 270.0);\n    if (UnitLastCreated() == null) { UnitCreate(1, k, c_unitCreateIgnorePlacement, 1, c, 270.0); }\n'
STR = {
    'Param/Value/RM10_Heroes': '피닉스와 데하카가 합류했습니다. /// Fenix and Dehaka have joined you.',
    'Param/Value/RM10_Sup8': '정화자 지원군이 1번 기지에 도착했습니다. /// Purifier reinforcements have arrived at the first outpost.',
    'Param/Value/RM10_Sup9': '원시저그 지원군이 2번 기지에 도착했습니다. /// Primal Zerg reinforcements have arrived at the second outpost.',
}
WARP_FX = '''    <CEffectCreatePersistent id="RM10_SupWarpFx">
        <EditorCategories value="Race:Protoss" />
        <PeriodCount value="1" />
        <PeriodicPeriodArray value="1" />
    </CEffectCreatePersistent>
'''


def closure(gd, roots, *opts):
    out = subprocess.run([sys.executable, str(HERE / 'catalog_closure.py'), str(gd), roots, BASE, *opts],
                         check=True, capture_output=True, text=True).stdout
    items, ids = {}, set()
    for line in out.splitlines():
        i, files = line.split(' ', 1); ids.add(i)
        for fn in files.split(','): items.setdefault(fn, []).append(i)
    return items, ids


def sub1(t, a, b):
    assert t.count(a) == 1, a[:60]
    return t.replace(a, b)


def dehaka(gd):
    u = gd / 'unitdata.xml'; t = u.read_text('utf-8')
    t = sub1(t, '        <BehaviorArray Link="DehakaAirUnkillable" />\n', '')
    t = sub1(t, '        <EffectArray index="Death" value="CommanderPrestigeDehakaCloneFateIterate" />\n', '')
    u.write_text(t, 'utf-8')
    a = gd / 'actordata.xml'; t = a.read_text('utf-8')
    i = t.index('<CActorMissile id="DehakaCoop" parent="GenericUnitBase"'); j = t.index('</CActorMissile>', i)
    blk = t[i:j]
    assert blk.count('<UnitFlags index="SuppressDefaultStatusBar" value="1" />') == 1
    t = t[:i] + blk.replace('<UnitFlags index="SuppressDefaultStatusBar" value="1" />', '<UnitFlags index="SuppressDefaultStatusBar" value="0" />') + t[j:]
    a.write_text(t, 'utf-8')
    m = gd / 'modeldata.xml'; t = m.read_text('utf-8')
    for mid in ('Dehaka_Coop_Young', 'Dehaka_Coop_Mammoth'):
        h = f'<CModel id="{mid}" parent="Unit" Race="Zerg">\n'
        t = sub1(t, h, h + f'        <Model value="Assets\\Units\\Zerg\\{mid}\\{mid}.m3" />\n')
    m.write_text(t, 'utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        root = Path(tmp); prev.extractall(root)
        m, m3, h2 = root / M, root / 'TRaynor03.SC2Map', root / 'THorner02.SC2Map'
        gd = m / 'base.sc2data/gamedata'
        changed = set()
        before = {p: p.read_bytes() for p in m.rglob('*') if p.is_file()}
        # Fenix reverse closure
        it, fids = closure(m3 / 'base.sc2data/gamedata', 'FenixDragoon,FenixEx2PortraitAddition', 'reverse=Fenix|Dragoon|Buster')
        print('fenix +', V1.add_records(gd, m3 / 'base.sc2data/gamedata', it))
        dehaka(gd)
        # ally support units from THorner02
        it, aids = closure(h2 / 'base.sc2data/gamedata', ALLY_ROOTS, ALLY_ALLOW, ALLY_REV)
        print('ally +', V1.add_records(gd, h2 / 'base.sc2data/gamedata', it))
        # model assets used by the ported legionnaire
        mtxt = (gd / 'modeldata.xml').read_text('utf-8')
        for p in (h2 / 'Assets').rglob('*'):
            if not p.is_file(): continue
            rel = p.relative_to(h2)
            if 'Zealot_Purifier_Collection' in str(rel) or (rel.parts[1] == 'Textures' and ('Zealot_Purifier' in p.name or 'Legion' in p.name or 'zealot_purifier' in p.name.lower())):
                d = m / rel
                if not d.exists(): d.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(p, d)
        # script
        sp = m / 'mapscript.galaxy'; raw = sp.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
        t = raw.replace('\r\n', '\n')
        t = sub1(t, OLD_SPAWN, NEW_SPAWN); t = sub1(t, OLD_CREATE, NEW_CREATE)
        t = sub1(t, HOOK8, HOOK8 + '    gf_rmSupStart(8);\n'); t = sub1(t, HOOK9, HOOK9 + '    gf_rmSupStart(9);\n')
        t = sub1(t, '// 0.10.1: player hero next to Tosh', SUP_FN + '// 0.10.1: player hero next to Tosh')
        sp.write_bytes(t.replace('\n', nl).encode('utf-8'))
        # strings
        k3 = (m3 / 'kokr.sc2data/localizeddata/gamestrings.txt').read_bytes().decode('utf-8-sig')
        kh = (h2 / 'kokr.sc2data/localizeddata/gamestrings.txt').read_bytes().decode('utf-8-sig')
        ko = m / 'kokr.sc2data/localizeddata/gamestrings.txt'
        V1.add_lines(ko, {**V1.strip_lines(k3, fids), **V1.strip_lines(kh, aids), **STR})
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (m / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        hk3 = (m3 / 'kokr.sc2data/localizeddata/gamehotkeys.txt').read_bytes().decode('utf-8-sig')
        for loc in V1.LOCALES:
            V1.add_lines(m / f'{loc}.sc2data/localizeddata/gamehotkeys.txt', V1.strip_lines(hk3, fids))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in m.rglob('*.xml'): E.parse(f)
        names = set(prev.namelist())
        allf = sorted(str(p.relative_to(root)).replace('\\', '/') for p in m.rglob('*') if p.is_file())
        new = [f for f in allf if f not in names]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in new:
                    zi = zipfile.ZipInfo(f, (2026, 11, 25, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    out.writestr(zi, (root / f).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if n != 'metadata.txt' and not n.startswith(M + '/'): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(new), 'new files')


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
