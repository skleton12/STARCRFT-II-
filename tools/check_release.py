#!/usr/bin/env python3
"""배포 전 검사 (CLAUDE.md 3·3-1·8). 하나라도 실패하면 종료 코드 1 — 그 ZIP은 배포하지 않는다.

검사 항목
  1. 파일 이름 RaynorMercs_WoL_CCM.zip, metadata 버전 0.x
  2. 번역: 세 맵 kokr에 (a) 한글 없는 표시 문자열 (b) '///' 영어 없는 한국어 줄이 0개, 11개 언어 파일 존재
  3. 모델 경로: 맵이 정의한 모델이 기본 경로(##id##)로 떨어지는데 원본에는 실제 경로가 있으면 실패 (오류 구 원인)
  4. 부모: 이번에 새로 생긴 '정의되지 않은 부모' 레코드 (기준선은 원본 이식 시 남은 것)
  5. 액터 이벤트: Create/ModelSwap 대상이 액터·모델 어디에도 없으면 실패 (기준선 제외)
  6. 스크립트: 동맹 협동전 건물 고치를 땅에 따로 띄우는 CreateModelAtPoint("...Build") 금지 (0.3.23 규칙)

사용법: python3 tools/check_release.py releases/RaynorMercs_WoL_CCM.zip
"""
import glob
import re
import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
S = ROOT / 'source'
MAPS = ['TRaynor01.SC2Map', 'TRaynor02.SC2Map', 'TRaynor03.SC2Map', 'TTychus01.SC2Map']
LOCALES = ['enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
DEPS = ['core.sc2mod', 'liberty.sc2mod', 'liberty.sc2campaign', 'libertystory.sc2campaign']
ALL_SRC = DEPS + ['swarm.sc2mod', 'void.sc2mod', 'voidmulti.sc2mod', 'starcoop/starcoop.sc2mod',
                  'swarm.sc2campaign', 'swarmstory.sc2campaign', 'void.sc2campaign', 'voidstory.sc2campaign']
HANGUL = re.compile('[가-힣]')
# 플레이어에게 보이지 않는 편집기 전용 문자열 (Editor*, 액터·모델·소리·검증기 등의 이름)
EDITOR_ONLY = {'Actor', 'Model', 'Sound', 'Validator', 'Requirement', 'RequirementNode', 'Effect', 'Footprint',
               'Light', 'Mover', 'VoiceOver', 'Race'}
# 원본 이식 때부터 남아 있던 항목 (안 쓰는 노바·데하카 영웅 연출, 착지 소리). 새로 생기면 실패.
KNOWN_PARENTS = {'NovaDeathWarpOutParent', 'DehakaConsumeEffectBase',
                 'BelShir'}  # 4번 원본 맵의 물(CWater): 자날 물 데이터는 source에 풀려 있지 않다
# WarpGateBuild: 차원 관문은 관문에서 변신하므로 건설 액터가 원래 없다 (원작 템플릿 이벤트, 발생 안 함)
KNOWN_EVENTS = {'WarpGateBuild', 'Adept_Land', 'Drone_Land', 'Hydra_Land', 'Zealot_Land', 'Sentry_Land', 'Stalker_Land',
                'DetectionConeRevealText', 'HeroNovaMP1_Respawn', 'HeroNovaMP2_Respawn',
                'ShieldBatteryRechargeEx5@SoundEnd', 'ShieldBatteryRechargeEx5@SoundLoop',
                'ShieldBatteryRechargeEx5@SoundStart', 'SiegeTank_Land', 'SiegeTankSiegeModeRange',
                'Templar_LandSweetener',
                # 쓰지 않는 영웅(노바·케리건·데하카 영웅) 연출
                'StimPackDevice_Nova', 'ZergHeroRevive'}

# 원작·이식 원본에서부터 비어 있던 연결 (쓰지 않는 영웅·능력). 새로 생기면 실패.
KNOWN_LINKS = set()

# 협동전 사령관 레벨 요구조건 ID (예: FenixLevel04, MengskLevel06)
COMMANDER_LEVEL = re.compile(r'^(Raynor|Kerrigan|Artanis|Swann|Zagara|Vorazun|Karax|Abathur|Alarak|Nova|Stukov|Fenix|Dehaka|Horner|Han|Tychus|Zeratul|Stetmann|Mengsk)Level\d\d$')

fails = []


def fail(msg):
    fails.append(msg)
    print('  실패:', msg)


def records(layers, fname):
    d = {}
    for L in layers:
        for f in glob.glob(str(L) + '/base.sc2data/gamedata/' + fname):
            for el in ET.parse(f).getroot():
                if el.get('id'):
                    d.setdefault(el.get('id'), []).append(el)
    return d


def model_path(d, i, seen=()):
    if i not in d or i in seen:
        return None
    for el in reversed(d[i]):
        m = el.find('Model')
        if m is not None and m.get('value'):
            return m.get('value')
    for el in reversed(d[i]):
        if el.get('parent'):
            return model_path(d, el.get('parent'), seen + (i,))
    return None


def strings(path):
    out = {}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            out[k] = v
    return out


def check_map(base, name):
    m = base / name
    print(name)
    # And/Or 피연산자는 늘어나는 배열이라 번호(index)를 붙이면 엔진이 무시해 조건이 거짓이 된다 (0.4.49, 연구 버튼 숨김).
    # 블리자드 원본 And/Or 약 780개는 번호를 안 쓴다. Not/Eq 같은 고정 칸 노드는 번호가 맞다.
    rn = m / 'base.sc2data/gamedata/requirementnodedata.xml'
    if rn.exists():
        for el in ET.parse(rn).getroot():
            if el.tag in ('CRequirementAnd', 'CRequirementOr') and any(o.get('index') is not None for o in el.findall('OperandArray')):
                fail(f'{name} {el.tag} {el.get("id")}: OperandArray에 index가 있음 (엔진이 무시 → 조건 거짓)')
    # 모드 버튼(RM3_/RM4_)은 단축키가 있어야 한다 (사용자 요청 2026-10-18)
    hk = m / 'kokr.sc2data/localizeddata/gamehotkeys.txt'
    have = hk.read_text(encoding='utf-8-sig') if hk.exists() else ''
    bd = m / 'base.sc2data/gamedata/buttondata.xml'
    if bd.exists():
        for b in ET.parse(bd).getroot():
            bid = b.get('id') or ''
            if b.tag == 'CButton' and re.match(r'RM\d+_', bid) and f'Button/Hotkey/{bid}=' not in have:
                fail(f'{name} 단축키 없음 {bid}')
    # 업적은 이 모드에서 꺼야 한다 (사용자 확정 2026-10-18)
    if 'AchievementsDisable(1);' not in (m / 'mapscript.galaxy').read_text(encoding='utf-8', errors='replace'):
        fail(f'{name} 업적 끄기(AchievementsDisable) 없음')
    ko = strings(m / 'kokr.sc2data/localizeddata/gamestrings.txt')
    shown = {k: v for k, v in ko.items()
             if k.split('/')[0] not in EDITOR_ONLY and not k.split('/')[1:2] == [''] and not (k.count('/') and k.split('/')[1].startswith('Editor'))}
    no_ko = [k for k, v in shown.items() if v.strip() and not HANGUL.search(v) and re.search('[A-Za-z]', re.sub(r'<[^>]*>', '', v))]
    no_en = [k for k, v in ko.items() if HANGUL.search(v) and '///' not in v]
    if no_ko: fail(f'{name} kokr 한글 없는 문자열 {len(no_ko)}개 {no_ko[:5]}')
    if no_en: fail(f'{name} kokr 영어 없는 한국어 줄 {len(no_en)}개 {no_en[:5]}')
    for loc in LOCALES:
        if not (m / f'{loc}.sc2data/localizeddata/gamestrings.txt').exists():
            fail(f'{name} {loc} 언어 파일 없음')

    dep = [S / x for x in DEPS] + [m]
    # 같은 칸은 먼저 적힌(원작) 버튼이 보인다. 숨김 처리 안 된 원작 버튼과 칸이 겹친 모드 버튼은 가려진다 (0.4.38 파편탄)
    def slots(el):  # first page only (cards with a CardId are submenu pages)
        for lb in [x for card in el.findall('CardLayouts') if not card.get('CardId') for x in card.iter('LayoutButtons')]:
            g = lambda k: lb.get(k) or (lb.find(k).get('value') if lb.find(k) is not None else None)
            yield g('Face'), g('AbilCmd'), g('Row'), g('Column')
    suppressed, research = set(), set()
    for f in [S / x / 'base.sc2data/gamedata/abildata.xml' for x in DEPS] + [m / 'base.sc2data/gamedata/abildata.xml']:
        if f.exists():
            for ab in ET.parse(f).getroot():
                if ab.tag == 'CAbilResearch':
                    research.add(ab.get('id'))
                for ia in ab.findall('InfoArray'):
                    bt = ia.find('Button')
                    if bt is not None and bt.get('State') == 'Suppressed':
                        suppressed.add(f'{ab.get("id")},{ia.get("index")}')
    base_cards = {}
    for x in DEPS:
        f = S / x / 'base.sc2data/gamedata/unitdata.xml'
        if f.exists():
            for el in ET.parse(f).getroot():
                if el.tag == 'CUnit' and el.get('id'):
                    base_cards.setdefault(el.get('id'), []).extend(slots(el))
    for el in ET.parse(m / 'base.sc2data/gamedata/unitdata.xml').getroot():
        for face, cmd, row, col in slots(el):
            if not (face or '').startswith('RM') or row is None:
                continue
            for bface, bcmd, brow, bcol in base_cards.get(el.get('id'), []):
                # 연구 버튼끼리만 본다 (같은 명령·상태로 바뀌는 칸 공유는 의도된 것)
                if ((brow, bcol) == (row, col) and bcmd and bcmd != cmd and bcmd not in suppressed
                        and bcmd.split(',')[0] in research and (cmd or '').split(',')[0] in research):
                    fail(f'{name} {el.get("id")} {face}({row},{col}): 원작 버튼 {bface}({bcmd})에 가려짐')
    eff = records(dep, 'modeldata.xml')
    mine = records([m], 'modeldata.xml')
    src = records([S / x for x in ALL_SRC], 'modeldata.xml')
    for i in sorted(mine):
        p, q = model_path(eff, i), model_path(src, i)
        if (p is None or '##' in p) and q and '##' not in q:
            fail(f'{name} 모델 경로 빠짐 {i} (원본 {q})')

    ids = {}
    for L in dep:
        for f in glob.glob(str(L) + '/base.sc2data/gamedata/*.xml'):
            for el in ET.parse(f).getroot():
                if el.get('id'):
                    ids.setdefault(Path(f).name, set()).add(el.get('id'))
    for f in glob.glob(str(m) + '/base.sc2data/gamedata/*.xml'):
        for el in ET.parse(f).getroot():
            p = el.get('parent')
            if p and p not in ids.get(Path(f).name, ()) and p not in KNOWN_PARENTS:
                fail(f'{name} 부모 없음 {el.tag} {el.get("id")} → {p}')
            # 실제 유닛 액터를 부모로 하면 'UnitBirth.<부모>'까지 물려받아 원래 유닛에 액터가 겹친다 (0.4.24 벙커)
            if (el.tag == 'CActorUnit' and (el.get('id') or '').startswith('RM') and p
                    and p in ids.get('unitdata.xml', ())):
                fail(f'{name} 액터 {el.get("id")}: 실제 유닛 액터 {p}를 부모로 씀 (원래 {p}에 겹쳐 생김)')
    # 효과 묶음이 정의 안 된 효과를 부르면 그 부분이 조용히 빠진다 (0.4.43 이지스 근위대 파편)
    # 무기 공격 줄기(무기 효과 → 투사체 명중 효과 → 묶음)만 본다. 이식에서 일부러 끊은 사령관 효과는 대상이 아니다.
    effs = ids.get('effectdata.xml', set())
    eroot = ET.parse(m / 'base.sc2data/gamedata/effectdata.xml').getroot()
    chain = set()
    wd = m / 'base.sc2data/gamedata/weapondata.xml'
    if wd.exists():
        for w in ET.parse(wd).getroot():
            for x in w.iter('Effect'):
                if x.get('value'): chain.add(x.get('value'))
    for el in eroot:
        if el.tag == 'CEffectLaunchMissile' and el.get('id') in chain:
            for x in el.iter('ImpactEffect'):
                if x.get('value'): chain.add(x.get('value'))
    for el in eroot:
        if el.tag == 'CEffectSet' and el.get('id') in chain:
            for ea in el.findall('EffectArray'):
                x = ea.get('value')
                if x and x not in effs:
                    fail(f'{name} 효과 묶음 {el.get("id")}: 효과 {x} 정의 없음')
    # 효과가 부르는 검증기가 정의되지 않으면 효과가 실행되지 않는다 (0.4.26 파편탄)
    # Positive paid-research checks must not inherit Find=false (0.4.33).
    for v in ET.parse(m / 'base.sc2data/gamedata/validatordata.xml').getroot():
        if v.get('id') in {'RM4_HaveSuppression', 'RM4_HaveShrapnel'}:
            f, who = v.find('Find'), v.find('WhichPlayer')
            if f is None or f.get('value') != '1':
                fail(f'{name} 연구 검증기 {v.get("id")}: Find=1 없음 (미연구 조건으로 반전)')
            if who is None or who.get('Value') != 'Caster':
                fail(f'{name} 연구 검증기 {v.get("id")}: 공격자 Caster 검사 아님')
    vals = ids.get('validatordata.xml', set())
    for el in ET.parse(m / 'base.sc2data/gamedata/effectdata.xml').getroot():
        for v in el.iter():
            x = v.get('value') if v.tag == 'ValidatorArray' else v.get('Validator')
            if x and (x.startswith('RM') or el.get('id', '').startswith('RM')) and x not in vals:
                fail(f'{name} 효과 {el.get("id")}: 검증기 {x} 정의 없음')

    actors = ids.get('actordata.xml', set())
    models = set(eff)
    root = ET.parse(m / 'base.sc2data/gamedata/actordata.xml').getroot()
    for el in root:
        for o in el.iter('On'):
            for kind, x in re.findall(r'(?<![A-Za-z])(Create|ModelSwap) ([A-Za-z0-9_@]+)', o.get('Send', '')):
                if x in KNOWN_EVENTS:
                    continue
                if (kind == 'Create' and x not in actors) or (kind == 'ModelSwap' and x not in models):
                    fail(f'{name} 액터 {el.get("id")}: {kind} {x} 대상 없음')

    # 템플릿(##unitName##)으로 만들어지는 이름: 맵 유닛 액터마다 부모를 따라 올라가 실제 이름으로 바꿔 확인한다.
    # (0.3.22 보급 벙커: 'Create ##unitName##Build' 액터가 없어 건설 중 오류 구)
    all_actors = {}
    for L in dep:
        for f in glob.glob(str(L) + '/base.sc2data/gamedata/actordata.xml'):
            for el in ET.parse(f).getroot():
                if el.get('id'):
                    all_actors.setdefault(el.get('id'), []).append(el)
    buildable = set()
    for L in dep:
        for f in glob.glob(str(L) + '/base.sc2data/gamedata/abildata.xml'):
            for ab in ET.parse(f).getroot():
                if ab.tag == 'CAbilBuild':
                    buildable |= {i.get('Unit') for i in ab.iter('InfoArray') if i.get('Unit')}
    done_ids = set()
    for el in root:
        aid = el.get('id')
        recs = all_actors.get(aid, [])
        unit = next((r.get('unitName') for r in reversed(recs) if r.get('unitName')), None)
        if el.tag != 'CActorUnit' or not unit or aid in done_ids:
            continue
        done_ids.add(aid)
        # 같은 ID의 모든 층 레코드를 최신 것부터 넣고, 부모는 어느 층이든 지정된 값을 따라간다.
        chain, cur, seen = [], aid, set()
        while cur in all_actors and cur not in seen:
            seen.add(cur)
            chain.extend(reversed(all_actors[cur]))
            cur = next((r.get('parent') for r in reversed(all_actors[cur]) if r.get('parent')), None)
        single = {}
        for a in chain:  # 자식 값이 우선
            for tag in ('PortraitModel', 'PlacementModel', 'BuildModel', 'Model'):
                c = a.find(tag)
                if c is not None and tag not in single:
                    single[tag] = c.get('value', '')
            c = a.find('EventDataFootprint')
            if c is not None and c.get('Model') and 'Footprint' not in single:
                single['Footprint'] = c.get('Model')
        for tag, v in single.items():
            # 발자국 모델은 원작에도 없는 경우가 많아 제외. 건설·배치 모델은 실제로 지을 수 있는 유닛만 본다.
            if tag == 'Footprint' or (tag in ('BuildModel', 'PlacementModel') and unit not in buildable):
                continue
            v = v.replace('##unitName##', unit)
            if v and '##' not in v and v not in models:
                fail(f'{name} 액터 {aid}: {tag} {v} 모델 없음')
        own = set(map(id, all_actors[aid]))
        for a in chain:
            if id(a) in own:
                continue
            for o in a.iter('On'):
                s = o.get('Send', '')
                if '##unitName##' not in s and '##unitName##' not in o.get('Terms', ''):
                    continue
                for x in re.findall(r'(?<![A-Za-z])Create ([A-Za-z0-9_@#]+)', s.replace('##unitName##', unit)):
                    if x not in actors and x not in KNOWN_EVENTS:
                        fail(f'{name} 액터 {aid}: 상속 이벤트 Create {x} 대상 없음')

    # 유닛이 가진 무기·능력·행동 연결이 실제로 있는지 (0.3.25 피닉스 사도: 무기 Adept 없음 → 공격 못 함)
    kinds = {'WeaponArray': 'weapondata.xml', 'AbilArray': 'abildata.xml', 'BehaviorArray': 'behaviordata.xml'}
    for el in ET.parse(m / 'base.sc2data/gamedata/unitdata.xml').getroot():
        if el.tag != 'CUnit':
            continue
        for tag, fn in kinds.items():
            for a in el.findall(tag):
                link = a.get('Link')
                if link and a.get('removed') != '1' and link not in ids.get(fn, set()) and link not in KNOWN_LINKS:
                    fail(f'{name} 유닛 {el.get("id")}: {tag} {link} 정의 없음')
                turret = a.get('Turret') if tag == 'WeaponArray' else None
                if turret and turret not in ids.get('turretdata.xml', set()):
                    # 0.3.29 원시 벌레: 포탑 NydusCanalAttacker가 없어 공격 못 함
                    fail(f'{name} 유닛 {el.get("id")}: 무기 포탑 {turret} 정의 없음')

    # 이식 유닛의 종족이 빠지면 기본 종족 Neut가 된다 (0.3.4 이식에서 원시 감시자·일벌레 종족이 빠짐, 짓는 중 안 보임 원인 후보)
    base_units = records([S / x for x in DEPS], 'unitdata.xml')
    src_units = records([S / x for x in ALL_SRC], 'unitdata.xml')
    for el in ET.parse(m / 'base.sc2data/gamedata/unitdata.xml').getroot():
        i = el.get('id')
        if el.tag != 'CUnit' or el.get('parent') or i in base_units or el.find('Race') is not None:
            continue
        if any(s.find('Race') is not None for s in src_units.get(i, [])):
            fail(f'{name} 유닛 {i}: 원본에 있는 종족(Race)이 빠짐')

    # 사령관 레벨 잠금은 이 모드에 없다 (사용자 확정 2026-10-17). 진급 레벨은 자치령 용병(RMK_…Veterancy)에만 있다.
    for f in glob.glob(str(m) + '/base.sc2data/gamedata/*.xml'):
        for x in sorted(set(re.findall(r'"(\w+Level\d\d)"', Path(f).read_text(encoding='utf-8')))):
            if COMMANDER_LEVEL.match(x):
                fail(f'{name} {Path(f).name}: 사령관 레벨 {x} 남음 (레벨 잠금 버튼·요구조건 제거)')

    script = (m / 'mapscript.galaxy').read_text(encoding='utf-8')
    # Galaxy: 함수는 정의나 앞선 선언 뒤에서만 부를 수 있다 (0.3.28 초안에서 gf_m3_Workers 호출이 정의보다 앞섰다).
    first_decl = {}
    for mm in re.finditer(r'^(?:static\s+)?[A-Za-z_][\w\[\]]*\s+(g[ft]_\w+)\s*\([^)]*\)\s*[;{]', script, re.M):
        first_decl.setdefault(mm.group(1), mm.start())
    for fname, pos in first_decl.items():
        call = re.search(r'(?<![\w"])' + re.escape(fname) + r'\s*\(', script)
        if call and call.start() < pos:
            line = script.count('\n', 0, call.start()) + 1
            fail(f'{name} 스크립트: {fname}를 선언 전에 부름 ({line}줄)')
    for x in re.findall(r'CreateModelAtPoint\("([A-Za-z0-9_]*Build)"', script):
        fail(f'{name} 스크립트가 고치/건설 모델 {x}를 땅에 띄움 (협동전 건설 방식으로)')


def main():
    z = Path(sys.argv[1])
    print('ZIP', z)
    if z.name != 'RaynorMercs_WoL_CCM.zip': fail('파일 이름이 RaynorMercs_WoL_CCM.zip이 아님')
    with zipfile.ZipFile(z) as zf, tempfile.TemporaryDirectory() as t:
        if zf.testzip() is not None: fail('ZIP CRC 오류')
        ver = re.search(rb'^version=(\S+)', zf.read('metadata.txt'), re.M).group(1).decode()
        print('version', ver)
        if not ver.startswith('0.'): fail(f'버전 {ver}: 완성 전에는 0.x')
        zf.extractall(t)
        for name in MAPS:
            check_map(Path(t), name)
    print('결과:', '통과' if not fails else f'실패 {len(fails)}개 — 배포하지 않는다')
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
