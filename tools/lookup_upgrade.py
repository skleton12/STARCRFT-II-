#!/usr/bin/env python3
"""연구(CUpgrade) ID로 이름, 툴팁, 연구 비용, 효과를 원본 데이터에서 찾아 출력한다.

사용법: python3 tools/lookup_upgrade.py [--json] ID [ID ...]
"""
import os, re, sys, json
import xml.etree.ElementTree as ET
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODS = [
    ('starcoop', os.path.join(ROOT, 'source', 'starcoop', 'starcoop.sc2mod')),
    ('mengsk', os.path.join(ROOT, 'source', 'starcoop', 'commanders', 'arcturusmengsk.sc2mod')),
]


def load_strings(loc):
    s = {}
    for _, path in MODS:
        p = os.path.join(path, f'{loc}.sc2data', 'localizeddata', 'gamestrings.txt')
        if os.path.exists(p):
            with open(p, encoding='utf-8-sig', errors='replace') as f:
                for line in f:
                    if '=' in line:
                        k, v = line.rstrip('\r\n').split('=', 1)
                        s[k] = v
    return s


def clean(t):
    t = re.sub(r'<n/>', ' / ', t or '')
    return re.sub(r'<[^>]+>', '', t).strip()


def load(fn):
    out = defaultdict(list)
    for mod, path in MODS:
        p = os.path.join(path, 'base.sc2data', 'gamedata', fn)
        if os.path.exists(p):
            for el in ET.parse(p).getroot():
                if el.get('id'):
                    out[el.get('id')].append((mod, el))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    ko, en = load_strings('kokr'), load_strings('enus')
    upgrades, abils, buttons = load('upgradedata.xml'), load('abildata.xml'), load('buttondata.xml')

    # 연구 능력에서 업그레이드별 비용/시간/버튼 찾기
    research = defaultdict(list)
    for aid, items in abils.items():
        for mod, el in items:
            for info in el.iter('InfoArray'):
                up = info.get('Upgrade')
                if not up:
                    continue
                cost = {r.get('index'): r.get('value') for r in info.iter('Resource')}
                time = next((t.get('value') for t in info.iter('Time')), None)
                btn = next((b.get('DefaultButtonFace') for b in info.iter('Button') if b.get('DefaultButtonFace')), None)
                research[up].append(dict(abil=aid, mod=mod, slot=info.get('index'), cost=cost, time=time, button=btn))

    result = []
    for uid in args:
        r = dict(id=uid, found=uid in upgrades, mods=sorted({m for m, _ in upgrades.get(uid, [])}))
        r['name_ko'] = ko.get(f'Upgrade/Name/{uid}')
        r['name_en'] = en.get(f'Upgrade/Name/{uid}')
        effects = []
        for mod, el in upgrades.get(uid, []):
            for e in el.iter('EffectArray'):
                effects.append({k: v for k, v in e.attrib.items()})
            for tag in ('MaxLevel', 'Race', 'AffectedUnitArray'):
                for x in el.iter(tag):
                    r.setdefault(tag, []).append(x.get('value'))
        r['effects'] = effects
        r['research'] = research.get(uid, [])
        for rs in r['research']:
            b = rs.get('button')
            if b:
                rs['tooltip_ko'] = clean(ko.get(f'Button/Tooltip/{b}'))
                rs['button_name_ko'] = ko.get(f'Button/Name/{b}')
        result.append(r)

    if '--json' in sys.argv:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return
    for r in result:
        print(f"## {r['id']}  {r['name_ko'] or ''} / {r['name_en'] or ''}  {'' if r['found'] else '(데이터 없음)'} {r['mods']}")
        for rs in r['research']:
            print(f"  연구: {rs['abil']}[{rs['slot']}] 비용 {rs['cost']} 시간 {rs['time']} 버튼 {rs['button']}")
            if rs.get('tooltip_ko'):
                print(f"    툴팁: {rs['tooltip_ko'][:300]}")
        for e in r['effects'][:12]:
            print(f"  효과: {e}")
        if len(r['effects']) > 12:
            print(f"  ... 효과 {len(r['effects'])}개")


if __name__ == '__main__':
    main()
