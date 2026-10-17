#!/usr/bin/env python3
"""다른 캠페인·협동전 데이터에서 유닛을 1번 미션 맵 데이터로 옮긴다.

맵이 이미 가진 데이터(기본 층: core, 자날 캠페인, 자날 스토리)는 복사하지 않는다.
나머지 층에서 시작 유닛이 참조하는 엔트리를 따라가며 모으고, 같은 ID가 여러 층에 있으면
낮은 층 정의 뒤에 높은 층의 수정 내용을 이어 붙여 하나로 합친다 (게임의 층 덮어쓰기와 같은 순서).

맵에 나오는 유닛(해병, 바이킹, 레이너 등)과 그 데이터는 보호 목록으로 막아 절대 덮어쓰지 않는다.
협동전 성장 체계(마스터 힘, 위신, 돌연변이 등)는 따라가지 않고, 그쪽을 가리키는 배열 항목은 지운다.

사용법: python3 tools/port_units.py 출력맵폴더 유닛ID [유닛ID ...]
"""
import os, re, sys, copy
import xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'source')

def gd(*p):
    return os.path.join(S, *p, 'base.sc2data', 'gamedata')

# 맵이 종속성으로 이미 가진 층
BASE_LAYERS = [gd('core.sc2mod'), gd('liberty.sc2campaign'), gd('libertystory.sc2campaign')]
# 복사 원본 층 (낮은 순 → 높은 순)
COPY_LAYERS = [
    ('swarm.sc2mod', gd('swarm.sc2mod')),
    ('void.sc2mod', gd('void.sc2mod')),
    ('voidmulti.sc2mod', gd('voidmulti.sc2mod')),
    ('swarm.sc2campaign', gd('swarm.sc2campaign')),
    ('void.sc2campaign', gd('void.sc2campaign')),
    ('starcoop', gd('starcoop', 'starcoop.sc2mod')),
]
# 따라가지 않는 협동전 성장·돌연변이 체계
# EmergencyMedivac: 협동전 용병 투하 연출(용병 의무관에 딸려 옴). 끊긴 참조만 남겨서 따라가지 않음 (2026-10-15)
SKIP_RE = re.compile(r'Mastery|Prestige|Mutator|Talent|AllUnitBehaviorController|CommanderLevel|Commander[A-Z][a-z]+Level|Amon|EmergencyMedivac|Alarak|^VoidStalkerBlinkShieldRestore$|^ZagaraVoidCoopBroodlingIncubation$')
TOKEN_RE = re.compile(r'[A-Za-z_][A-Za-z0-9_@]*')
# 이보다 많은 엔트리가 참조하는 공용 엔트리는 따라가지 않는다 (시작 유닛 이름이 든 것은 예외)
SHARED_LIMIT = 6
# 공용이어도 따라갈 이름 (사령관 전용 데이터)
EXTRA_KEEP = ['Fenix']

# 카탈로그별로 어디까지 따라갈지. 키에 없는 카탈로그는 아예 복사하지 않는다.
# 대사·사령관 목록·스킨처럼 여러 유닛이 같이 쓰는 묶음이 참조를 폭발시키기 때문이다.
GAMEPLAY = {'unitdata.xml', 'abildata.xml', 'effectdata.xml', 'behaviordata.xml', 'weapondata.xml',
            'validatordata.xml', 'requirementdata.xml', 'requirementnodedata.xml', 'upgradedata.xml',
            'buttondata.xml', 'actordata.xml', 'modeldata.xml', 'sounddata.xml', 'moverdata.xml',
            'footprintdata.xml', 'turretdata.xml', 'accumulatordata.xml', 'targetsortdata.xml',
            'targetfinddata.xml', 'alertdata.xml'}
# 거꾸로 찾기에서 '지켜보는 대상'으로 볼 카탈로그
REVERSE_TARGET_FILES = {'weapondata.xml', 'effectdata.xml', 'unitdata.xml', 'abildata.xml', 'behaviordata.xml'}
# 빈 연결 채우기에서 복사할 카탈로그 (유닛·연출은 넣지 않는다: 상관없는 유닛을 끌고 오기 때문)
LEAF_FILES = {'abildata.xml', 'effectdata.xml', 'behaviordata.xml', 'weapondata.xml', 'validatordata.xml',
              'requirementdata.xml', 'requirementnodedata.xml', 'upgradedata.xml', 'buttondata.xml',
              'sounddata.xml', 'modeldata.xml', 'moverdata.xml'}
# 맵 쪽에 없는 종족은 맵에 있는 종족으로 바꾼다. 종족 데이터(PZrg)는 원시 저그 건물·일꾼 등을
# 줄줄이 가리켜 복사하면 빈 연결이 크게 늘어난다 (2026-10-14 확인)
RACE_REMAP = {'PZrg': 'Zerg'}
NO_UNIT = GAMEPLAY - {'unitdata.xml'}
EXPAND = {
    'unitdata.xml': NO_UNIT,                 # 유닛 → 다른 유닛은 따라가지 않음 (별칭·도감 연결 폭발 방지)
    'abildata.xml': GAMEPLAY,
    'effectdata.xml': GAMEPLAY,              # 효과가 소환하는 유닛은 따라간다
    'behaviordata.xml': GAMEPLAY,
    'weapondata.xml': GAMEPLAY,
    'validatordata.xml': {'validatordata.xml', 'behaviordata.xml', 'upgradedata.xml'},
    'requirementdata.xml': {'requirementnodedata.xml', 'upgradedata.xml'},
    'requirementnodedata.xml': {'requirementnodedata.xml', 'upgradedata.xml'},
    'actordata.xml': {'actordata.xml', 'modeldata.xml', 'sounddata.xml'},
    'accumulatordata.xml': {'accumulatordata.xml', 'validatordata.xml'},
    # 나머지(업그레이드, 버튼, 모델, 소리, 이동, 발자국, 포탑 …)는 여기서 멈춘다
}


def load_layer(path):
    out = defaultdict(list)  # (파일, ID) -> [요소]
    if not os.path.isdir(path):
        return out
    for fn in sorted(os.listdir(path)):
        if not fn.endswith('.xml'):
            continue
        try:
            root = ET.parse(os.path.join(path, fn)).getroot()
        except ET.ParseError:
            continue
        for el in root:
            if el.get('id'):
                out[(fn, el.get('id'))].append(el)
    return out


def protected_ids(map_dir):
    """맵 스크립트와 배치 유닛에 나오는 이름 전부 (덮어쓰기 금지)."""
    ids = set()
    with open(os.path.join(map_dir, 'mapscript.galaxy'), encoding='utf-8', errors='replace') as f:
        ids |= set(re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"', f.read()))
    for o in ET.parse(os.path.join(map_dir, 'objects')).getroot():
        if o.get('UnitType'):
            ids.add(o.get('UnitType'))
    return ids


def main():
    args = sys.argv[1:]
    # --liberty-base: 자날 기본 모드(Liberty.SC2Mod) 데이터도 '맵이 이미 가진 층'으로 본다 (2026-10-15, 2번 미션부터).
    # 이게 없으면 점멸·관문 생산 같은 기본 항목까지 군단·공허·협동전 판으로 복사해 덮어쓴다.
    # 1번 미션은 사용자 시험을 통과한 결과를 바꾸지 않으려고 이 옵션 없이 그대로 둔다.
    # --skip-existing: 맵에 이미 이식된 같은 ID는 건너뛴다 (앞선 이식분 재사용, 2026-10-17 3번 미션 데하카 건물)
    skip_existing = '--skip-existing' in args
    if skip_existing:
        args.remove('--skip-existing')
    if '--liberty-base' in args:
        args.remove('--liberty-base')
        BASE_LAYERS.append(gd('liberty.sc2mod'))
    # --drop=정규식: 이번 이식에서 따라가지 않을 ID (예: 데하카 알 생산·뿌리 들기·굴 건설). 해당 능력 버튼도 지운다
    global SKIP_RE
    drop = None
    for a in list(args):
        if a.startswith('--drop='):
            args.remove(a)
            drop = re.compile(a[len('--drop='):])
            SKIP_RE = re.compile(SKIP_RE.pattern + '|' + drop.pattern)
    map_dir, seeds = args[0], args[1:]
    base = defaultdict(set)
    for p in BASE_LAYERS:
        for (fn, i) in load_layer(p):
            base[i].add(fn)
    layers = [(name, load_layer(p)) for name, p in COPY_LAYERS]
    by_id = defaultdict(set)
    for _, lay in layers:
        for (fn, i) in lay:
            by_id[i].add(fn)
    protect = protected_ids(map_dir)

    def copyable(i):
        return i in by_id and i not in base and i not in protect and not SKIP_RE.search(i)

    def tokens(el):
        for node in el.iter():
            vals = list(node.attrib.values()) + ([node.text] if node.text and node.text.strip() else [])
            for v in vals:
                yield from TOKEN_RE.findall(v)

    # 각 ID를 참조하는 서로 다른 엔트리 수
    refcnt = defaultdict(set)
    for _, lay in layers:
        for key, els in lay.items():
            for el in els:
                for t in tokens(el):
                    if t != key[1] and t in by_id:
                        refcnt[t].add(key)
    # 시작 유닛 이름(또는 사령관 이름)이 든 엔트리와 시작 유닛이 직접 가진 것은 공용이어도 따라간다
    seed_re = re.compile('|'.join([re.escape(x) for x in seeds] + EXTRA_KEEP))
    seed_keys = set()
    shared = set()

    selected, queue = set(), []
    for s in seeds:
        if s not in by_id:
            sys.exit(f'{s}: 원본 층에 없음')
        for fn in by_id[s] & GAMEPLAY:
            selected.add((fn, s)); queue.append((fn, s)); seed_keys.add((fn, s))
    def expand():
        while queue:
            key = queue.pop()
            for _, lay in layers:
                for el in lay.get(key, []):
                    for t in tokens(el):
                        if not copyable(t):
                            continue
                        if len(refcnt[t]) > SHARED_LIMIT and not seed_re.search(t) and key not in seed_keys:
                            shared.add(t)
                            continue
                        for fn in by_id[t] & EXPAND.get(key[0], set()):
                            if (fn, t) not in selected:
                                selected.add((fn, t)); queue.append((fn, t))

    expand()

    # 거꾸로 찾기: 무기·효과·유닛·능력·행동을 지켜보다 반응하는 연출 액터 (공격 모션, 투사체, 포탑, 폭발 등).
    # 액터가 대상을 가리키는 구조라 위의 정방향 탐색으로는 못 찾는다 (2026-10-14 동맹 무기 연출 누락).
    # 유닛 액터(CActorUnit)는 같은 ID의 유닛을 고를 때 이미 따라오므로 제외한다
    watched = {i for fn, i in selected if fn in REVERSE_TARGET_FILES}
    rev = set()
    for _, lay in layers:
        for (fn, i), els in lay.items():
            if fn != 'actordata.xml' or (fn, i) in selected or not copyable(i):
                continue
            if any(el.tag == 'CActorUnit' for el in els):
                continue
            if any(t in watched for el in els for t in tokens(el)):
                rev.add((fn, i))
    for k in rev:
        selected.add(k); queue.append(k)
    expand()

    # 빈 연결 채우기: 고른 엔트리가 가리키는데 맵에도 기본 층에도 없는 것을 한 번 더 복사한다
    # (종족 PZrg처럼 공용이라 따라가지 않았지만 없으면 게임이 오류를 내는 것). 여기서는 더 따라가지 않는다
    leaves = set()
    for key in list(selected):
        for _, lay in layers:
            for el in lay.get(key, []):
                for t in tokens(el):
                    if copyable(t):
                        for fn in by_id[t] & LEAF_FILES:
                            if (fn, t) not in selected:
                                leaves.add((fn, t))
    selected |= leaves

    # 층 순서대로 합친다: 첫 정의를 복사하고, 다음 층 요소의 자식들을 이어 붙인다
    out_files = defaultdict(list)
    for fn, i in sorted(selected):
        merged = None
        for _, lay in layers:
            for el in lay.get((fn, i), []):
                if merged is None:
                    merged = copy.deepcopy(el)
                else:
                    for k, v in el.attrib.items():
                        merged.set(k, v)
                    for ch in el:
                        merged.append(copy.deepcopy(ch))
        for node in merged.iter('Race'):
            if node.get('value') in RACE_REMAP:
                node.set('value', RACE_REMAP[node.get('value')])
        # 따라가지 않은 체계를 가리키는 배열 항목은 지운다
        for parent in list(merged.iter()):
            for ch in list(parent):
                link = ch.get('Link') or ''
                if link and SKIP_RE.search(link):
                    parent.remove(ch)
                elif drop and drop.search((ch.get('AbilCmd') or '').split(',')[0] or '\0'):
                    parent.remove(ch)
        out_files[fn].append(merged)

    gdir = os.path.join(map_dir, 'base.sc2data', 'gamedata')
    os.makedirs(gdir, exist_ok=True)
    total = 0
    for fn, els in sorted(out_files.items()):
        p = os.path.join(gdir, fn)
        if os.path.exists(p):
            root = ET.parse(p).getroot()
            have = {e.get('id') for e in root}
            if skip_existing:
                els = [e for e in els if e.get('id') not in have]
            clash = [e.get('id') for e in els if e.get('id') in have]
            if clash:
                sys.exit(f'{fn}: 맵에 이미 있는 ID와 겹침 {clash[:5]}')
        else:
            root = ET.Element('Catalog')
        for e in els:
            root.append(e)
        ET.indent(root, space='    ')
        ET.ElementTree(root).write(p, encoding='utf-8', xml_declaration=True)
        total += len(els)
        print(f'  {fn:28} +{len(els)}')
    # 옮긴 엔트리의 한국어 문자열 (이름, 툴팁 등). 맵에 이미 있는 키는 건너뛴다
    ids = {i for _, i in selected}
    sp = os.path.join(map_dir, 'kokr.sc2data', 'localizeddata', 'gamestrings.txt')
    with open(sp, encoding='utf-8', newline='') as f:
        text = f.read()
    have = {l.split('=', 1)[0] for l in text.splitlines() if '=' in l}
    def read_strings(loc):
        out = {}
        for name, _ in COPY_LAYERS:
            root = os.path.join(S, *(['starcoop', 'starcoop.sc2mod'] if name == 'starcoop' else [name]))
            for fn in ('gamestrings.txt', 'objectstrings.txt'):
                q = os.path.join(root, f'{loc}.sc2data', 'localizeddata', fn)
                if not os.path.exists(q):
                    continue
                with open(q, encoding='utf-8-sig', errors='replace') as f:
                    for line in f:
                        if '=' in line:
                            k, v = line.rstrip('\r\n').split('=', 1)
                            out[k] = v  # 높은 층이 덮어씀
        return out

    ko, en = read_strings('kokr'), read_strings('enus')
    add = {}
    for k, v in ko.items():
        if k in have or not any(seg in ids for seg in k.split('/')[1:]):
            continue
        # 원본 맵 문자열 형식 '한국어 /// English'에 맞춘다
        if ' /// ' not in v and en.get(k) and en[k] != v:
            v = f'{v} /// {en[k]}'
        add[k] = v
    nl = '\r\n' if '\r\n' in text else '\n'
    if add:
        if not text.endswith(nl):
            text += nl
        text += ''.join(f'{k}={v}{nl}' for k, v in sorted(add.items()))
        with open(sp, 'w', encoding='utf-8', newline='') as f:
            f.write(text)
    print(f'거꾸로 찾은 연출 액터 {len(rev)}개, 빈 연결 채우기 {len(leaves)}개')
    print(f'총 {total}개 엔트리, 파일 {len(out_files)}개, 문자열 {len(add)}줄, 따라가지 않은 공용 엔트리 {len(shared)}개')
    with open(os.path.join(map_dir, 'ported_shared_refs.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(sorted(shared)) + '\n')


if __name__ == '__main__':
    main()
