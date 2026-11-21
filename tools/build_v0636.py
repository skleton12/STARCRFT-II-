#!/usr/bin/env python3
"""0.6.35 -> 0.6.36: 코덱스 0.6.26 백업(codex/raynor-0.6.26-backup)의 일부를 흡수 (사용자 2026-11-21 선택).

0.6.26은 0.6.18에서 갈라져 코덱스가 따로 만든 판이다. 사용자가 고른 세 가지만 0.6.35 위에 옮긴다:
1. 동맹 지원 증원·상한 (3·5·6번 지원 버튼, 3~6번 상한):
   - 지원 묶음 무료분 추가: 정화자 +군단병 1, 원시저그 +히드라 1·저글링 2
     → 한 번에 정화자 군단병 6·사도 3(+동력기), 원시저그 저글링 10·바퀴 2·히드라 3 (연구실 단계·해금 보너스 별도).
   - 동맹 군대 인구 상한 100 → 120 (3~6번), 지원 묶음 칸 24 → 32.
   - 지원이 도착하면 소환된 수를 자막으로 보여 준다.
2. 정화자 파수병(ZealotPurifier) → 피닉스 군단병 (1~6번, 0.6.26 데이터 그대로): 체력 200·보호막 100·사이오닉 검 16×2·인구 3,
   군단병 모델·사망·소환·배치 모델과 아이콘, 파수병 재구축 제거, 지상 공업 적용. 모드 전용 무기·효과라 적에게 영향 없음.
   군단병 모델 파일(Zealot_Purifier_Collection*)과 0.6.26이 함께 넣은 텍스처 49개를 각 맵 Assets에 넣는다.
   4~6번 차원 관문 소환의 인구 확인도 2 → 3.
3. 3번 피닉스 연출·패시브 표시 (0.6.35에 이미 있는 피닉스 용기병 능력·초상화는 건드리지 않는다):
   - 피닉스가 나타날 때 자막 안내.
   - 전쟁광·코랄의 후예에 레이저 조준 시스템·전투 방패 연구 완료 패시브 표시.
0.6.26 문자열 중 영어가 빠진 것은 '한국어 /// English'로 고쳐 넣는다.

Usage: python3 tools/build_v0636.py <0.6.35 zip> <0.6.26 zip> <new output zip>
"""
import argparse, copy, re, sys, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD

OLD, NEW = b'version=0.6.35', b'version=0.6.36'
ALL = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
CALL = {'TRaynor03': ('m3c', 10), 'TTosh01': ('m5', 8), 'THanson01': ('m6', 8)}
LEG_REPLACE = [('unitdata', 'CUnit', 'ZealotPurifier'), ('actordata', 'CActorUnit', 'ZealotPurifier')]
LEG_ADD = [('effectdata', 'CEffectDamage', 'LegionnairePsiBlades'), ('effectdata', 'CEffectCreatePersistent', 'LegionnairePsiBladesBurst'),
           ('modeldata', 'CModel', 'FenixZealotPurifier'), ('modeldata', 'CModel', 'FenixZealotPurifierDeath'),
           ('modeldata', 'CModel', 'FenixZealotPurifierPlacement'), ('modeldata', 'CModel', 'FenixZealotPurifierWarpIn'),
           ('upgradedata', 'CUpgrade', 'ProtossGroundWeapons'), ('weapondata', 'CWeaponLegacy', 'RM_LegionnairePsiBlades')]
RMP_ADD = [('buttondata', 'CButton', 'RMP_RM3_Laser'), ('buttondata', 'CButton', 'RMP_RM3_Shield'),
           ('requirementdata', 'CRequirement', 'RMP_HaveRM3_Laser'), ('requirementdata', 'CRequirement', 'RMP_HaveRM3_Shield'),
           ('requirementnodedata', 'CRequirementCountUpgrade', 'RMP_DoneRM3_Laser'),
           ('requirementnodedata', 'CRequirementCountUpgrade', 'RMP_DoneRM3_Shield')]
RMP_CARDS = {'WarPig': ('1', '0', '1', '1'), 'RMK_MarineMengsk': ('1', '1', '1', '4')}

LEG_STR = {
    'Unit/Name/RM_Legionnaire': '군단병 /// Legionnaire',
    'Weapon/Name/RM_LegionnairePsiBlades': '사이오닉 검 /// Psionic Blades',
    'Button/Tooltip/RM_Legionnaire': '강력한 정화자 근접 전사입니다. 체력 200, 보호막 100, 공격력 16×2. 돌진을 사용할 수 있습니다. /// A powerful Purifier melee warrior. 200 life, 100 shields, 16x2 damage. Can Charge.',
}
SUP_STR = {
    'rmSupport/PurifierCount': '정화자 지원 도착: 총  /// Purifier support arrived: ',
    'rmSupport/PrimalCount': '원시저그 지원 도착: 총  /// Primal Zerg support arrived: ',
    'rmSupport/CountEnd': '기 ///  units',
}
M3_STR = {
    'rm3/FenixArrival': '피닉스: 레이너, 그대의 전투에 힘을 보태러 왔네. 함께 이 기지를 지켜 내세. /// Fenix: Raynor, I have come to lend my strength to your fight. Let us hold this base together.',
    'Button/Name/RMP_RM3_Shield': '전투 방패 /// Combat Shield',
    'Button/Tooltip/RMP_RM3_Shield': '최대 생명력 +10. /// +10 maximum life.',
    'Button/Name/RMP_RM3_Laser': '레이저 조준 시스템 /// Laser Targeting System',
    'Button/Tooltip/RMP_RM3_Laser': '공격 사거리 증가. /// Increased attack range.',
}


def rec_re(tag, i):
    return re.compile(r'<%s id="%s"[^>]*?(?:/>|>.*?</%s>)' % (tag, re.escape(i), tag), re.S)


def get_rec(path, tag, i):
    m = rec_re(tag, i).search(path.read_text(encoding='utf-8'))
    assert m, (path, i)
    return m.group(0)


def put_rec(path, tag, i, text, replace):
    t = path.read_text(encoding='utf-8')
    ms = list(rec_re(tag, i).finditer(t))
    if replace:
        assert len(ms) == 1, (path, i)
        t = t[:ms[0].start()] + text + t[ms[0].end():]
    else:
        assert not ms, (path, i)
        k = t.rindex('</Catalog>')
        t = t[:k] + text + '\n' + t[k:]
    path.write_text(t, encoding='utf-8')


def script_edit(m, t):
    def once(old, new):
        nonlocal t
        assert t.count(old) == 1, (m, old[:60])
        t = t.replace(old, new)
    if m in ('TTychus01', 'TTosh01', 'THanson01'):
        p = {'TTychus01': 'm4', 'TTosh01': 'm5', 'THanson01': 'm6'}[m]
        once(f'gf_{p}_Food(8)+2.0>100.0', f'gf_{p}_Food(8)+3.0>120.0')   # legionnaire supply 3, cap 120
        once(f'gf_{p}_Food(9)+6.0>100.0', f'gf_{p}_Food(9)+6.0>120.0')
    if m in CALL:
        p, pp = CALL[m]
        food = 'gf_m3_Food' if m == 'TRaynor03' else f'gf_{p}_Food'
        n = t.count(f'{food}(p)+food>100.0')
        assert n == (1 if m == 'TRaynor03' else 2), (m, n)
        t = t.replace(f'{food}(p)+food>100.0', f'{food}(p)+food>120.0')
        for old in (f'string[16][24] gv_{p}_supKind', f'point[16][24] gv_{p}_supAt', f'if (gv_{p}_supN[p]>=24) {{ return; }}'):
            once(old, old.replace('24', '32'))
        for old in ('    string[24] kind;\n', '    point[24] at;\n', '    actor[24] fx;\n'):
            assert t.count(old) >= 1, (m, old)
            t = t.replace(old, old.replace('24', '32'))
        once(f'''        // 0.6.28: +3 free per group (user 2026-11-14, trial).
        gf_{p}_SupAdd(p,"ZealotPurifier");
        gf_{p}_SupAdd(p,"ZealotPurifier");
        gf_{p}_SupAdd(p,"AdeptFenix");
''', f'''        // 0.6.28: +3 free per group (user 2026-11-14, trial).
        gf_{p}_SupAdd(p,"ZealotPurifier");
        gf_{p}_SupAdd(p,"ZealotPurifier");
        gf_{p}_SupAdd(p,"AdeptFenix");
        // 0.6.36 (from Codex 0.6.26): one more free Legionnaire.
        gf_{p}_SupAdd(p,"ZealotPurifier");
''')
        once(f'''    // 0.6.28: +3 free per group (user 2026-11-14, trial).
    gf_{p}_SupAdd(p,"DehakaZerglingLevel2");
    gf_{p}_SupAdd(p,"DehakaZerglingLevel2");
    gf_{p}_SupAdd(p,"DehakaRoachLevel2");
''', f'''    // 0.6.28: +3 free per group (user 2026-11-14, trial).
    gf_{p}_SupAdd(p,"DehakaZerglingLevel2");
    gf_{p}_SupAdd(p,"DehakaZerglingLevel2");
    gf_{p}_SupAdd(p,"DehakaRoachLevel2");
    // 0.6.36 (from Codex 0.6.26): one more Hydralisk and two more zerglings, free.
    gf_{p}_SupAdd(p,"DehakaHydraliskLevel2");
    gf_{p}_SupAdd(p,"DehakaZerglingLevel2");
    gf_{p}_SupAdd(p,"DehakaZerglingLevel2");
''')
        head = f'bool gt_{p}_CallGo_Func (bool testConds,bool runActions) {{\n'
        a = t.index(head)
        b = t.index('\n}\n', a)
        body = t[a:b]
        loop = '        if (!gv_gameOver) { UnitCreate(1,kind[i],0,p,at[i],270.0); }\n    }\n'
        assert body.count(loop) == 1, m
        body = body.replace(loop, loop + f'''    // 0.6.36 (from Codex 0.6.26): show how many arrived.
    if (!gv_gameOver) {{
        if (p=={pp}) {{ UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rmSupport/PurifierCount")+IntToText(n)+StringExternal("rmSupport/CountEnd")); }}
        else {{ UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rmSupport/PrimalCount")+IntToText(n)+StringExternal("rmSupport/CountEnd")); }}
    }}
''')
        t = t[:a] + body + t[b:]
    if m == 'TRaynor03':
        once('''        UnitSetPosition(UnitLastCreated(), PlayerStartLocation(1), false);
    }
    TriggerExecute(gt_Init04Music, true, true);
''', '''        UnitSetPosition(UnitLastCreated(), PlayerStartLocation(1), false);
    }
    // 0.6.36 (from Codex 0.6.26): Fenix arrival line.
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm3/FenixArrival"));
    TriggerExecute(gt_Init04Music, true, true);
''')
    return t


def build(source, codex, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, zipfile.ZipFile(codex) as cdx, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert b'version=0.6.26' in cdx.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp + '/b')
        cdx.extractall(tmp + '/a')
        A, B = Path(tmp) / 'a', Path(tmp) / 'b'
        prev_names = set(names)
        leg_assets = sorted(n for n in cdx.namelist() if n.startswith('TRaynor01.SC2Map/Assets/') and n not in prev_names)
        assert len(leg_assets) == 54, len(leg_assets)
        added = []
        for m in ALL:
            ga, gb = A / f'{m}.SC2Map' / GD, B / f'{m}.SC2Map' / GD
            for f, tag, i in LEG_REPLACE:
                put_rec(gb / f'{f}.xml', tag, i, get_rec(ga / f'{f}.xml', tag, i), True)
            for f, tag, i in LEG_ADD:
                put_rec(gb / f'{f}.xml', tag, i, get_rec(ga / f'{f}.xml', tag, i), False)
            for n in leg_assets:
                dst = n.replace('TRaynor01.SC2Map/', f'{m}.SC2Map/', 1)
                assert dst not in prev_names
                (B / dst).parent.mkdir(parents=True, exist_ok=True)
                (B / dst).write_bytes(cdx.read(n))
                added.append(dst)
            strings = dict(LEG_STR)
            if m in CALL: strings.update(SUP_STR)
            if m == 'TRaynor03':
                strings.update(M3_STR)
                for f, tag, i in RMP_ADD:
                    put_rec(gb / f'{f}.xml', tag, i, get_rec(ga / f'{f}.xml', tag, i), False)
                ud = gb / 'unitdata.xml'
                for u, (r1, c1, r2, c2) in RMP_CARDS.items():
                    rec = get_rec(ud, 'CUnit', u)
                    k = rec.rindex('</CardLayouts>')
                    new = (rec[:k] + f'<LayoutButtons Face="RMP_RM3_Shield" Type="Passive" Requirements="RMP_HaveRM3_Shield" Row="{r1}" Column="{c1}" />\n'
                           f'<LayoutButtons Face="RMP_RM3_Laser" Type="Passive" Requirements="RMP_HaveRM3_Laser" Row="{r2}" Column="{c2}" />\n' + rec[k:])
                    put_rec(ud, 'CUnit', u, new, True)
            sp = B / f'{m}.SC2Map' / 'mapscript.galaxy'
            raw = sp.read_bytes().decode('utf-8')
            nl = '\r\n' if '\r\n' in raw else '\n'
            sp.write_bytes(script_edit(m, raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'))
            d = B / f'{m}.SC2Map'
            ko = set_lines((d / KO).read_bytes(), strings)
            (d / KO).write_bytes(ko)
            V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
        (B / 'metadata.txt').write_bytes((B / 'metadata.txt').read_bytes().replace(OLD, NEW))
        import xml.etree.ElementTree as E
        for f in B.rglob('*.xml'): E.parse(f)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos:
                    out.writestr(copy.copy(info), (B / info.filename).read_bytes())
                for n in added:
                    out.write(B / n, n)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == names + added
                for n in names:
                    if not any(n.startswith(m + '.SC2Map/') for m in ALL) and n != 'metadata.txt':
                        assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, 'added assets', len(added))


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('codex', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.codex, a.output)
