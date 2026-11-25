#!/usr/bin/env python3
"""0.9.8 -> 0.10.1: 10번 뉴 폴섬 '탈옥'(TTosh03A, 토시 편) 기본판 (사용자 2026-11-25
"다음 미션 뉴폴섬", "둘다 만드는데 토시쪽 선호", "둘다 데하카 영웅이랑 피닉스 영웅이 지원옴 대신 피닉스는 드라군으로",
선택 "내가 직접 조종", "시작부터, 부활 없음").

원본: maps/original_wol/ttosh03a (사용자 드라이브의 블리자드 캠페인 추출본 40개, 2026-11-25). 지형·오브젝트·트리거 그대로.
원작: 플레이어 1 = 토시(영웅 1명), 2·8·9 = 레이너 특공대(컴퓨터), 3~6 = 뉴 폴섬 방위군(적), 7 = 수감자, 11·12 = 감방 동맹.
- 영웅 두 명을 플레이어 1에게 시작 때(원작 시작 유닛을 만든 직후) 토시 옆에 만든다. 부활 없음.
  - 피닉스(용기병, FenixDragoon): 3번 제로 아워 맵의 현재 데이터(0.6.28~0.6.35 수정 포함)를 그대로 떠 온다
    (tools/catalog_closure.py: 3번 맵에만 있는 엔트리 중 FenixDragoon에서 닿는 것 + 초상화 얼굴 FenixEx2PortraitAddition).
    문자열·단축키도 3번 맵 것.
  - 데하카(협동전 DehakaCoop): tools/port_units.py로 이식. 협동전 정수 성장 체계(학습·포식·치유 오라·탐지·공중 공격·
    장갑 진화·분신·부활 고치)는 빼고 도약(Q)·위협의 포효(W)·불타는 숨결(E)·깊은 땅굴(D)만. 사령관 레벨 잠금 버튼 제거,
    PreventDestroy 끔. 도약 착지 피해는 협동전 학습 단계 계산 대신 고정 60·반경 2(시험값). 한국어 이름은 공식 번역 미확인.
- 업적 끔(AchievementsDisable). 다른 11개 언어는 kokr 영어 부분.
- 7-1 적 강화·용병 바꿈은 아직 없음(다음 판). Game not run.

Usage: python3 tools/build_v0101.py <0.9.8 zip> <ttosh03a folder> <new output zip>
"""
import argparse, copy, re, shutil, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.9.8', b'version=0.10.1'
M = 'TTosh03A.SC2Map'
LOCALES = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
S = ROOT / 'source'
BASE = [S / x / 'base.sc2data/gamedata' for x in ('core.sc2mod', 'liberty.sc2mod', 'liberty.sc2campaign', 'libertystory.sc2campaign')]
DROP = ('DehakaLearn|DehakaCoopClone|Prestige|DehakaAttEssence|DehakaPrimalMutation|DehakaCoopReviveCocoon|DehakaArmorUpgrade|'
        'DehakaAirAttackUpgrade|AllUnitBehaviorController|Essence|DehakaConsume|DehakaMendingAura|DehakaDetector|Evolve')
DEHAKA_STR = {
    'Unit/Name/DehakaCoop': '데하카 /// Dehaka',
    'Unit/Name/DehakaCoopBurrowed': '데하카 /// Dehaka',
    'Button/Tooltip/DehakaCoop': '원시 무리의 우두머리. /// Primal Pack Leader.',
    'Weapon/Name/DehakaCoop': '발톱 /// Claws',
    'Abil/Name/DehakaLeapStomp': '도약 /// Leap',
    'Button/Name/DehakaLeapStomp': '도약 /// Leap',
    'Button/Tooltip/DehakaLeapStomp': '목표 지점으로 도약해 주변 적 지상 유닛에게 피해를 줍니다. /// Dehaka leaps to the target location, dealing damage to nearby enemy ground units.',
    'Abil/Name/DehakaIntimidatingRoar': '위협의 포효 /// Intimidating Roar',
    'Button/Name/DehakaIntimidatingRoar': '위협의 포효 /// Intimidating Roar',
    'Button/Tooltip/DehakaIntimidatingRoar': '주변 적을 겁에 질리게 해 이동 속도와 공격 속도를 낮춥니다. /// Dehaka terrifies nearby enemies, reducing their movement and attack speed.',
    'Behavior/Name/DehakaIntimidatingRoar': '위협의 포효 /// Intimidating Roar',
    'Behavior/Tooltip/DehakaIntimidatingRoar': '겁에 질림.<n/>공격 속도와 이동 속도가 느려집니다. /// Intimidated.<n/>Lowered Attack and Movement speed.',
    'Abil/Name/MammothBreath': '불타는 숨결 /// Scorching Breath',
    'Button/Name/MammothBreath': '불타는 숨결 /// Scorching Breath',
    'Button/Tooltip/MammothBreath': '불타는 숨결로 경로에 있는 모든 적 지상 유닛에게 피해를 줍니다. /// Dehaka\'s fiery breath deals damage to all enemy ground units in its path.',
    'Unit/Name/MammothBreath': '불타는 숨결 /// Scorching Breath',
    'Button/Name/DehakaDeepTunnel': '깊은 땅굴 /// Deep Tunnel',
    'Button/Tooltip/DehakaDeepTunnel': '보이는 곳 어디든 빠르게 땅굴을 파고 이동합니다. /// Quickly burrow to any visible location.',
}
DEHAKA_HOT = {'Button/Hotkey/DehakaLeapStomp': 'Q', 'Button/Hotkey/DehakaIntimidatingRoar': 'W',
              'Button/Hotkey/MammothBreath': 'E', 'Button/Hotkey/DehakaDeepTunnel': 'D'}
SPAWN_ANCHOR = '    TriggerExecute(gt_Init03Units, true, true);\n'
SPAWN = SPAWN_ANCHOR + '''    // 0.10.1 (user 2026-11-25): Fenix (Dragoon) and Dehaka join Tosh as player heroes, no revive.
    gf_rmHero("FenixDragoon", -3.0);
    gf_rmHero("DehakaCoop", 3.0);
'''
HERO_FN = '''// 0.10.1: player hero next to Tosh (walkable spot, else on Tosh).
void gf_rmHero (string k, fixed dx) {
    point c = UnitGetPosition(gv_tosh);
    point p = UnitTypePlacementFromPoint(k, 1, Point(PointGetX(c) + dx, PointGetY(c) - 2.0), 6.0);
    if (p == null || !PointPathingPassable(p) || !PointPathingIsConnected(p, c)) { p = c; }
    UnitCreate(1, k, 0, 1, p, 270.0);
}

'''


def recs(path):
    t = path.read_text('utf-8')
    return {m.group(2): m.group(0) for m in re.finditer(r'(?m)^[ \t]*<(C\w+)\s[^>]*?\bid="([^"]+)"[^>]*?(?:/>|>.*?</\1>)', t, re.S)}


def add_records(dst_gd, src_gd, items):
    n = 0
    for fn, ids in items.items():
        src = recs(src_gd / fn)
        dst = dst_gd / fn
        body = dst.read_text('utf-8') if dst.exists() else '<?xml version="1.0" encoding="utf-8"?>\n<Catalog>\n</Catalog>\n'
        have = set(re.findall(r'\bid="([^"]+)"', body))
        add = ''.join('    ' + src[i].strip() + '\n' for i in ids if i in src and i not in have)
        n += add.count('\n')
        i = body.rindex('</Catalog>')
        dst.write_text(body[:i] + add + body[i:], 'utf-8')
    return n


def fenix(m, m3):
    out = subprocess.run([sys.executable, str(HERE / 'catalog_closure.py'), str(m3 / 'base.sc2data/gamedata'),
                          'FenixDragoon,FenixEx2PortraitAddition', ','.join(map(str, BASE))],
                         check=True, capture_output=True, text=True).stdout
    items, ids = {}, set()
    for line in out.splitlines():
        i, files = line.split(' ', 1)
        ids.add(i)
        for fn in files.split(','): items.setdefault(fn, []).append(i)
    print('fenix records', add_records(m / 'base.sc2data/gamedata', m3 / 'base.sc2data/gamedata', items))
    return ids


def strip_lines(lines_src, ids):
    d = {}
    for l in lines_src.splitlines():
        if '=' not in l: continue
        k, v = l.split('=', 1); p = k.split('/')
        if len(p) >= 3 and (p[2] in ids or p[2].startswith(('FenixDragoon', 'ChargeBuster', 'ChargedBuster'))): d[k] = v
    return d


def dehaka_unit(gd):
    p = gd / 'unitdata.xml'; t = p.read_text('utf-8')
    s = t.index('id="DehakaCoopBase"'); s = t.rindex('<CUnit', 0, s); e = t.index('</CUnit>', s)
    u = t[s:e]
    u = u.replace('<FlagArray index="PreventDestroy" value="1" />', '<FlagArray index="PreventDestroy" value="0" />')
    u = re.sub(r'\s*<LayoutButtons[^>]*Requirements="DehakaLevel\d\d"[^>]*/>', '', u)
    u = re.sub(r'\s*<LayoutButtons>\s*</LayoutButtons>', '', u)
    u = re.sub(r'\s*<LayoutButtons Face="Cancel" Type="CancelSubmenu"[^>]*/>', '', u)
    u = u.replace('Face="MoveChampions"', 'Face="Move"').replace('Face="AttackChampions"', 'Face="Attack"')
    # the co-op Learn (essence) submenu and its empty card are not ported (Codex review)
    u = re.sub(r'\s*<LayoutButtons>\s*<Face value="DehakaLearnAbilities" />.*?</LayoutButtons>', '', u, flags=re.S)
    u = re.sub(r'\s*<CardLayouts CardId="Lear">\s*</CardLayouts>', '', u)
    assert 'DehakaLevel' not in u and 'PreventDestroy" value="0"' in u and 'DehakaLearn' not in u
    p.write_text(t[:s] + u + t[e:], 'utf-8')
    # Leap landing: the co-op damage set scales with learned ability level/veterancy (not ported) ->
    # a fixed landing hit (trial: 60 damage, radius 2), Codex review
    f = gd / 'effectdata.xml'; ft = f.read_text('utf-8')
    a0 = ft.index('<CEffectEnumArea id="DehakaStompSearchC">'); a1 = ft.index('</CEffectEnumArea>', a0)
    blk = ft[a0:a1]
    blk = blk.replace('<AreaArray Effect="DehakaStompSearchCSet" />', '<AreaArray Radius="2" Effect="RM10_DehakaStompDamage" />')
    blk = re.sub(r'\s*<ExtraRadiusBonus value="0">.*?</ExtraRadiusBonus>', '', blk, flags=re.S)
    assert 'RM10_DehakaStompDamage' in blk and 'Accumulator' not in blk
    ft = ft[:a0] + blk + ft[a1:]
    i = ft.rindex('</Catalog>')
    ft = ft[:i] + ('    <CEffectDamage id="RM10_DehakaStompDamage"><Kind value="Spell" /><Amount value="60" />'
                   '<Death value="Blast" /></CEffectDamage>\n') + ft[i:]
    f.write_text(ft, 'utf-8')
    # devour (consume) is not ported: drop its glaze event on the Dehaka actor
    a = gd / 'actordata.xml'
    a.write_text(re.sub(r'\s*<On [^>]*Send="Create DehakaConsumeEffect\w*"\s*/>', '', a.read_text('utf-8')), 'utf-8')
    for fn in ('requirementdata.xml', 'requirementnodedata.xml'):
        q = gd / fn
        if q.exists():
            q.write_text(re.sub(r'\s*<C\w+ id="DehakaLevel\d\d"[^>]*>.*?</C\w+>', '', q.read_text('utf-8'), flags=re.S), 'utf-8')


def add_lines(path, items):
    raw = path.read_bytes().decode('utf-8-sig') if path.exists() else ''
    nl = '\r\n' if '\r\n' in raw else '\n'
    keys = {l.split('=', 1)[0] for l in raw.splitlines() if '=' in l}
    add = [f'{k}={v}' for k, v in items.items() if k not in keys]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(((raw.rstrip('\r\n') + nl if raw else '') + nl.join(add) + nl).encode('utf-8'))


def build(source, folder, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        root = Path(tmp)
        prev.extractall(root)
        m, m3 = root / M, root / 'TRaynor03.SC2Map'
        assert not m.exists()
        shutil.copytree(folder, m)
        D = '--drop=' + DROP
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(m), '--liberty-base', '--skip-existing', D,
                        'DehakaCoopBase', 'DehakaCoop', 'DehakaCoopBurrowed', 'MammothBreath', 'DehakaAirWeapon'], check=True, stdout=subprocess.DEVNULL)
        (m / 'ported_shared_refs.txt').unlink(missing_ok=True)
        gd = m / 'base.sc2data/gamedata'
        dehaka_unit(gd)
        fids = fenix(m, m3)
        # script
        sp = m / 'mapscript.galaxy'; raw = sp.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
        t = raw.replace('\r\n', '\n')
        assert t.count(SPAWN_ANCHOR) == 1 and t.count('void InitMap () {') == 1 and 'AchievementsDisable' not in t
        t = t.replace(SPAWN_ANCHOR, SPAWN)
        a = '//--------------------------------------------------------------------------------------------------\n// Trigger: '
        i = t.index(a)
        t = t[:i] + HERO_FN + t[i:]
        t = t.replace('void InitMap () {\n', 'void InitMap () {\n    AchievementsDisable(1);\n', 1)
        sp.write_bytes(t.replace('\n', nl).encode('utf-8'))
        # strings / hotkeys
        k3 = (m3 / 'kokr.sc2data/localizeddata/gamestrings.txt').read_bytes().decode('utf-8-sig')
        h3 = (m3 / 'kokr.sc2data/localizeddata/gamehotkeys.txt').read_bytes().decode('utf-8-sig')
        ko = m / 'kokr.sc2data/localizeddata/gamestrings.txt'
        add_lines(ko, {**strip_lines(k3, fids), **DEHAKA_STR})
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            q = m / f'{loc}.sc2data/localizeddata/gamestrings.txt'; q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(V35.other_locale(ko.read_bytes()))
        hot = {**strip_lines(h3, fids), **DEHAKA_HOT}
        for loc in LOCALES:
            add_lines(m / f'{loc}.sc2data/localizeddata/gamehotkeys.txt', hot)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in m.rglob('*.xml'): E.parse(f)
        names = prev.namelist()
        extra = sorted(str(p.relative_to(root)).replace('\\', '/') for p in m.rglob('*') if p.is_file())
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra:
                    zi = zipfile.ZipInfo(f, (2026, 11, 25, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    out.writestr(zi, (root / f).read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, len(extra), 'new files')


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('folder', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.folder, a.output)
