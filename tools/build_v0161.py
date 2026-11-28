#!/usr/bin/env python3
"""0.15.9 -> 0.16.1: 제라툴 1번 '망각의 속삭임'(TZeratul01) 기본판 (사용자 2026-11-28 "다음 미션은 제라툴 1번 미션임",
"추적자 대신에 선동자와 땅무지 군주? 를 소환 땅무지 군주는 땅굴파기로 이동 가능(땅무지는 공중 공격가능)", 적 강화 "저그 규칙 그대로").

원본: maps/original_wol/tzeratul01 (사용자 드라이브 추출본 37개). 지형·오브젝트·트리거 그대로.
원작 플레이어: 1 제라툴(플레이어), 2 아군(추적자 차원 소환 뒤 플레이어에게 넘김), 3·4 저그(적), 5 젤나가 제단. 동맹 플레이어 없음.
- 원작이 차원 소환해 넘겨주는 추적자를 넘겨받는 순간 번갈아 선동자(StalkerPurifier)·땅무지 숙주(DehakaPrimalSwarmHost)로
  바꾼다. '땅무지 군주'는 데하카 협동전 땅무지 숙주로 해석. 원작 스크립트의 추적자 수·종류 확인(지원 상한·대사 조건·통계·
  마지막 연출)은 세 종류(+잠복 숙주) 모두를 센다.
- 땅무지 숙주: 깊은 땅굴(DehakaDeepTunnel, 데하카 협동전, 단축키 D, 재사용 60초)로 이동. 날벌레 공중 공격(협동전
  DehakaMurvarCreeperAir의 무기 부분)을 처음부터 지급.
- 적(3·4번 저그) 능력치 규칙: 주는 피해 105/110/115/125%(난이도별, 0.6.17 저그 값, 시험값). 이 임무는 적 AI·공세가 없어
  AI 한 단계 위·공세 물량은 해당 없음.
- 업적 끔. 다른 11개 언어는 kokr 영어 부분.
데이터: 선동자·땅무지 숙주는 발굴 작업 맵(TTychus02), 깊은 땅굴은 뉴 폴섬 맵(TTosh03A)의 현재 판에서 tools/catalog_closure.py로.
Game not run. Usage: python3 tools/build_v0161.py <0.15.9 zip> <tzeratul01 folder> <new output zip>
"""
import argparse, copy, re, shutil, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
import build_v0101 as B

OLD, NEW = b'version=0.15.9', b'version=0.16.1'
M = 'TZeratul01.SC2Map'
SRCS = [('TTychus02.SC2Map', 'StalkerPurifier,DehakaPrimalSwarmHost,DehakaPrimalSwarmHostBurrowed,DehakaCreeperFlying',
         'reverse=^(StalkerPurifier|DehakaPrimalSwarmHost|DehakaCreeper|DehakaSpawnCreeper)'),
        ('TTosh03A.SC2Map', 'DehakaDeepTunnel', '')]
ALLOW = 'allow=^StalkerPurifier$'
SKIP = 'skip=^(RML|RMPL|RMZL|RM12|RM5_|RM7_|RM8_|RM9_|RMA_|RM3_|RM4_|RM6_)|Merge|Mergeable|DehakaGene|^DehakaSwarmHost(Burrowed)?$|^DehakaLocust(?!EggAnimation)'
UPG = ('    <CUpgrade id="RM16_CreeperAir" parent="Research">\n'
       '        <Icon value="Assets\\Textures\\btn-ability-zerg-dehaka-creeperhost-spawncreepers.dds" />\n'
       '        <EffectArray Reference="Unit,DehakaCreeperFlying,Speed" Value="0.750000" />\n'
       '        <EffectArray Operation="Set" Reference="Weapon,DehakaCreeperSuicide,Options[Disabled]" Value="0" />\n'
       '        <EffectArray Operation="Set" Reference="Weapon,DehakaCreeperSuicide,Options[Hidden]" Value="0" />\n'
       '        <EffectArray Operation="Set" Reference="Weapon,DehakaPrimalSwarmHostFakeWeapon,TargetFilters" Value="Visible;Missile,Stasis,Dead,Hidden,Invulnerable" />\n'
       '        <AffectedUnitArray value="DehakaCreeperFlying" />\n        <AffectedUnitArray value="DehakaPrimalSwarmHost" />\n'
       '    </CUpgrade>\n')
STR = {'Param/Value/RM16_Swap': '추적자 대신 선동자와 땅무지 숙주가 합류합니다. /// Instigators and Creeper Hosts join you instead of Stalkers.'}
FUNCS = r'''// 0.16.1 (user 2026-11-28): Stalkers warped in for Zeratul become Instigators / Creeper Hosts (alternating).
int gv_rm16N;

bool gf_rmStk (string t) {
    return t == "Stalker" || t == "StalkerPurifier" || t == "DehakaPrimalSwarmHost" || t == "DehakaPrimalSwarmHostBurrowed";
}

unitgroup gf_rmStkGroup (int p, region r, unitfilter f) {
    unitgroup g = UnitGroup("Stalker", p, r, f, 0);
    UnitGroupAddUnitGroup(g, UnitGroup("StalkerPurifier", p, r, f, 0));
    UnitGroupAddUnitGroup(g, UnitGroup("DehakaPrimalSwarmHost", p, r, f, 0));
    UnitGroupAddUnitGroup(g, UnitGroup("DehakaPrimalSwarmHostBurrowed", p, r, f, 0));
    return g;
}

void gf_rm16Init () {
    int p;
    AchievementsDisable(1);
    TechTreeUpgradeAllow(1, "RM16_CreeperAir", true);
    TechTreeUpgradeAddLevel(1, "RM16_CreeperAir", 1);
    TechTreeUnitAllow(1, "StalkerPurifier", true);
    TechTreeUnitAllow(1, "DehakaPrimalSwarmHost", true);
    TechTreeAbilityAllow(1, AbilityCommand("DehakaDeepTunnel", 0), true);
    // enemy zerg (3, 4): damage dealt +5/10/15/25% by difficulty (trial)
    for (p = 3; p <= 4; p += 1) {
        PlayerModifyPropertyInt(p, c_playerPropDamageDealtPercent, c_playerPropOperSetTo, 100 + libNtve_gf_DifficultyValueInt(5, 10, 15, 25));
    }
}

'''


def port(m, src, roots, extra):
    args = [sys.executable, str(HERE / 'catalog_closure.py'), str(src / 'base.sc2data/gamedata'), roots, ','.join(map(str, B.BASE)), 'rm', SKIP]
    if extra: args += [extra, ALLOW]
    out = subprocess.run(args, check=True, capture_output=True, text=True).stdout
    items, ids = {}, set()
    for line in out.splitlines():
        i, files = line.split(' ', 1); ids.add(i)
        for fn in files.split(','): items.setdefault(fn, []).append(i)
    print(src.name, 'records', B.add_records(m / 'base.sc2data/gamedata', src / 'base.sc2data/gamedata', items))
    return ids


def data(gd):
    p = gd / 'unitdata.xml'; t = p.read_text('utf-8')
    s = t.index('<CUnit id="DehakaPrimalSwarmHost">'); e = t.index('</CUnit>', s); u = t[s:e]
    assert 'DehakaDeepTunnel' not in u and 'Row="2" Column="3"' not in u
    u = u.replace('<AbilArray Link="attack" />', '<AbilArray Link="attack" />\n        <AbilArray Link="DehakaDeepTunnel" />', 1)
    u = u.replace('Row="2" Column="4" />', 'Row="2" Column="4" />\n            <LayoutButtons Face="DehakaDeepTunnel" Type="AbilCmd" AbilCmd="DehakaDeepTunnel,Execute" Row="2" Column="3" />', 1)
    assert u.count('DehakaDeepTunnel') == 3
    p.write_text(t[:s] + u + t[e:], 'utf-8')
    # merge abilities and HotS landing models are not in this map (check_release)
    t = p.read_text('utf-8')
    t2 = re.sub(r'\s*<AbilArray Link="PrimalSwarmHostMerge(?:able)?" />', '', t)
    t2 = re.sub(r'\s*<LayoutButtons [^>]*AbilCmd="PrimalSwarmHostMerge(?:able)?,[^"]*"[^>]*/>', '', t2)
    p.write_text(t2, 'utf-8')
    a = gd / 'actordata.xml'; at = a.read_text('utf-8')
    a.write_text(re.sub(r'\s*<On [^>]*Send="Create (?:Locust_Land|SwarmHost_Land|DehakaSwarmHostMerge)"[^>]*/>', '', at), 'utf-8')
    q = gd / 'upgradedata.xml'; body = q.read_text('utf-8') if q.exists() else '<?xml version="1.0" encoding="utf-8"?>\n<Catalog>\n</Catalog>\n'
    i = body.rindex('</Catalog>'); q.write_text(body[:i] + UPG + body[i:], 'utf-8')


def script(t):
    def rep(a, b, n=1):
        nonlocal t
        assert t.count(a) == n, (a[:70], t.count(a)); t = t.replace(a, b)
    filt = 'UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0)'
    t, k = re.subn(r'UnitGroup\("Stalker", gv_p1_USER, (.*?), ' + re.escape(filt),
                   lambda mm: 'gf_rmStkGroup(gv_p1_USER, ' + mm.group(1) + ', ' + filt[:-4] + ')', t)
    assert k >= 20 and 'UnitGroup("Stalker"' not in t, k
    t, k2 = re.subn(r'UnitGetType\(((?:[^()]|\([^()]*\))*)\) == "Stalker"', r'gf_rmStk(UnitGetType(\1))', t)
    assert k2 == 7 and "== \"Stalker\"" not in t, k2
    rep('libCamp_gf_AddUnitTypeToUnitHelpPanel("Stalker", false, gv_p1_USER);',
        'libCamp_gf_AddUnitTypeToUnitHelpPanel("StalkerPurifier", false, gv_p1_USER);\n    libCamp_gf_AddUnitTypeToUnitHelpPanel("DehakaPrimalSwarmHost", false, gv_p1_USER);')
    old = ('    libNtve_gf_RescueUnit(EventUnitProgressUnit(), gv_p1_USER, true);\n'
           '    UnitFlashSelection(EventUnitProgressUnit(), 1.5);\n'
           '    UnitIssueOrder(EventUnitProgressUnit(), Order(AbilityCommand("move", 2)), c_orderQueueReplace);\n')
    new = ('    libNtve_gf_RescueUnit(EventUnitProgressUnit(), gv_p1_USER, true);\n'
           '    // 0.16.1: alternate Instigator / Creeper Host instead of the Stalker\n'
           '    gv_rm16N += 1;\n'
           '    if (ModI(gv_rm16N, 2) == 1) { libNtve_gf_ReplaceUnit(EventUnitProgressUnit(), "StalkerPurifier", libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'
           '    else { libNtve_gf_ReplaceUnit(EventUnitProgressUnit(), "DehakaPrimalSwarmHost", libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }\n'
           '    if (gv_rm16N == 1) { UIDisplayMessage(PlayerGroupSingle(gv_p1_USER), c_messageAreaSubtitle, StringExternal("Param/Value/RM16_Swap")); }\n'
           '    UnitFlashSelection(libNtve_gf_LastReplacedUnit(), 1.5);\n'
           '    UnitIssueOrder(libNtve_gf_LastReplacedUnit(), Order(AbilityCommand("move", 2)), c_orderQueueReplace);\n')
    rep(old, new)
    # Codex: a flying creeper reaching the Void Seeker must not pause the escape timers
    a2 = ('        if (!((UnitTypeTestFlag(UnitGetType(EventUnit()), c_unitFlagMissile) == false))) {\n            return false;\n        }\n    }\n\n'
          '    // Actions\n    if (!runActions) {\n        return true;\n    }\n\n    TimerPause(gv_runoutTimer, true);')
    rep(a2, a2.replace('    }\n\n    // Actions', '\n        if ((UnitGetType(EventUnit()) == "DehakaCreeperFlying") || (UnitGetType(EventUnit()) == "DehakaPlacement")) {\n            return false;\n        }\n    }\n\n    // Actions', 1))
    # Codex: the Xel'Naga shrine also resets the new units' abilities
    b = '            UnitAbilityReset(autoD29854AF_var, AbilityCommand("Blink", 0), c_spendLocationAll);\n'
    rep(b, b + b.replace('"Blink"', '"BlinkMultiple"') + b.replace('"Blink"', '"DehakaDeepTunnel"'))
    a = '//--------------------------------------------------------------------------------------------------\n// Global Function Declarations'
    assert t.count(a) == 1
    i = t.index(a); t = t[:i] + FUNCS + t[i:]
    rep('void InitMap () {\n    InitLibs();\n    InitGlobals();\n    InitTriggers();\n}',
        'void InitMap () {\n    InitLibs();\n    InitGlobals();\n    InitTriggers();\n    gf_rm16Init();\n}')
    return t


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        root = Path(tmp); prev.extractall(root)
        m = root / M; assert not m.exists()
        shutil.copytree(folder, m)
        gd = m / 'base.sc2data/gamedata'
        allids = {}
        for sname, roots, extra in SRCS:
            allids[sname] = port(m, root / sname, roots, extra)
        data(gd)
        # legionnaire-style mod model files are not needed; StalkerPurifier/host use game assets
        sp = m / 'mapscript.galaxy'; raw = sp.read_bytes().decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
        assert 'AchievementsDisable' not in raw
        sp.write_bytes(script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'))
        ko = m / 'kokr.sc2data/localizeddata/gamestrings.txt'
        hot = {}
        for sname, ids in allids.items():
            ks = (root / sname / 'kokr.sc2data/localizeddata/gamestrings.txt').read_bytes().decode('utf-8-sig')
            kh = (root / sname / 'kokr.sc2data/localizeddata/gamehotkeys.txt').read_bytes().decode('utf-8-sig')
            B.add_lines(ko, B.strip_lines(ks, ids)); hot.update(B.strip_lines(kh, ids))
        hot['Button/Hotkey/DehakaDeepTunnel'] = 'D'
        B.add_lines(ko, STR)
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            q = m / f'{loc}.sc2data/localizeddata/gamestrings.txt'; q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(V35.other_locale(ko.read_bytes()))
        for loc in B.LOCALES:
            B.add_lines(m / f'{loc}.sc2data/localizeddata/gamehotkeys.txt', hot)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in m.rglob('*.xml'): E.parse(f)
        names = prev.namelist()
        extra = sorted(str(p.relative_to(root)).replace('\\', '/') for p in m.rglob('*') if p.is_file())
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra:
                    zi = zipfile.ZipInfo(f, (2026, 11, 28, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    out.writestr(zi, (root / f).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(extra), 'new files')


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('source', type=Path); a.add_argument('folder', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.folder, a.output)
