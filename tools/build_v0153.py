#!/usr/bin/env python3
"""0.15.2 -> 0.15.3: 레이너의 공성 전차 용병 = 협동전 멩스크 전차 (사용자 2026-11-28 "멩스크 전차로 바꿔야지").

공성 파괴단(자날 원작 용병) 대신 협동전 멩스크 사령관의 공성 전차(SiegeTankMengsk, 공성 모드 SiegeTankMengskSieged)를 쓴다.
코랄의 후예·이지스 근위대와 같은 기준(용병 = 협동전 멩스크 유닛). 군수 공장이 있는 10개 맵.
  - tools/port_units.py --with-mengsk로 이식. 사령관 성장(진급 행동·제국 명령·의무수송선 공수·레벨 잠금)은 따라가지 않는다.
  - 처음부터 3등급(0.4.68 규칙): 진급 3단계 합계를 박아 넣음 — 생명력 350+270=620, 장갑 1+3=4, 주는 피해 +75%(숨은 영구 버프),
    공성 사격 기절(3등급 능력)·넓은 폭발(정예) 항상 켬. 경험치 없음. 부활 장치(PreventDestroy) 끔.
  - 비용·인구는 자날 공성 전차와 같은 150/125·3 (시험값, 협동전 원본 150/425·6).
  - 차량 공방업(평소판·울트라 축전기·바나듐판 포함)과 대혼란 탄 등 공성 파괴단을 가리키는 모든 업그레이드 항목을
    멩스크 전차 무기·효과·유닛에 같은 값으로 붙인다. 충격포 폭발 범위 확장(RMC_TankSplash)은 멩스크 폭발 반경에도 +50%.
  - 스크립트의 "SiegeBreaker"/"SiegeBreakerSieged"(군수 공장 생산 바꿈·주기 바꿈·수송선 화물·해금 확인 등)를 멩스크 전차로.
  - 한국어 이름 '충격 사단'은 공식 번역 미확인.
Game not run. Usage: python3 tools/build_v0153.py <0.15.2 zip> <new output zip>
"""
import copy, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD, LOCS
from build_v092 import first, end_insert

OLD, NEW = b'version=0.15.2', b'version=0.15.3'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04', 'TTychus03', 'TTychus02']
SEEDS = ['SiegeTankMengsk', 'SiegeTankMengskSieged']
DROP = '--drop=Veterancy|ImperialMandate|Airlift|MengskVeteran|MengskLevel|ACGluescreen|Commander|Prestige|Mastery|MedivacMengsk'
BASE_UP = [HERE.parent / 'source/liberty.sc2mod/base.sc2data/gamedata/upgradedata.xml',
           HERE.parent / 'source/libertystory.sc2campaign/base.sc2data/gamedata/upgradedata.xml']
REF = [('Weapon,SiegeBreaker,', ['Weapon,SiegeTankMengsk,']),
       ('Effect,SiegeBreakerDamage,', ['Effect,SiegeTankMengskDamage,']),
       ('Unit,SiegeBreakerSieged,', ['Unit,SiegeTankMengskSieged,']),
       ('Unit,SiegeBreaker,', ['Unit,SiegeTankMengsk,']),
       ('Weapon,ArcliteShockCannon,', ['Weapon,SiegeTankMengskSieged,']),
       ('Effect,ArcliteShockCannonBlast,', ['Effect,SiegeTankMengskSiegedBlast,', 'Effect,SiegeTankMengskSiegedImprovedAoEBlast,']),
       ('Effect,ArcliteShockCannonDirected,', ['Effect,SiegeTankMengskSiegedDirected,', 'Effect,SiegeTankMengskSiegedImprovedAoEDirected,']),
       ('Effect,ArcliteShockCannonDummy,', ['Effect,SiegeTankMengskSiegedDummy,'])]
ELITE = ('<CBehaviorBuff id="RM15_TankElite"><BehaviorFlags index="Permanent" value="1" /><MaxStackCount value="1" />'
         '<InfoIcon value="Assets\\Textures\\btn-upgrade-terran-vehicleweaponslevel3.dds" /><Modification>'
         '<DamageDealtFraction index="Melee" value="0.75" /><DamageDealtFraction index="Ranged" value="0.75" />'
         '<DamageDealtFraction index="Splash" value="0.75" /></Modification></CBehaviorBuff>')
NAME = ('충격 사단', 'Shock Division')
STR = {
    'Unit/Name/SiegeTankMengsk': f'{NAME[0]} /// {NAME[1]}',
    'Button/Name/SiegeTankMengsk': f'{NAME[0]} /// {NAME[1]}',
    'Button/Name/RM_SiegeBreaker': f'{NAME[0]} /// {NAME[1]}',
    'Button/Tooltip/RM_SiegeBreaker': '멩스크 협동전 용병 공성 전차입니다. 처음부터 3등급(생명력 620·장갑 4·피해 +75%)이고, 공성 모드 포격이 지상 유닛을 기절시킵니다. /// Mengsk co-op mercenary siege tank. Rank 3 from the start (620 life, 4 armor, +75% damage); siege shots stun ground units.',
    'Button/Tooltip/SiegeTankMengsk': '멩스크 협동전 용병 공성 전차입니다. /// Mengsk co-op mercenary siege tank.',
    'Button/Name/SiegeModeMengsk': '공성 모드 /// Siege Mode',
    'Button/Tooltip/SiegeModeMengsk': '공성 모드로 바꿉니다. 사거리가 크게 늘고 범위 피해를 주지만 움직일 수 없습니다. /// Transforms into Siege Mode: long range and splash damage, but cannot move.',
    'Button/Name/UnsiegeMengsk': '전차 모드 /// Tank Mode',
    'Button/Tooltip/UnsiegeMengsk': '전차 모드로 돌아가 다시 움직일 수 있습니다. /// Returns to Tank Mode so the unit can move again.',
    'Button/Name/SiegeTankMengskStun': '충격 포격 /// Concussive Bombardment',
    'Button/Tooltip/SiegeTankMengskStun': '공성 모드 포격이 맞은 지상 유닛을 잠깐 기절시킵니다. 영웅 유닛은 느려집니다. 3등급 능력입니다. /// Siege shots briefly stun ground units hit. Heroic units are slowed instead. Rank 3 ability.',
    'Weapon/Name/SiegeTankMengsk': '90mm 포 /// 90mm Cannons',
    'Weapon/Name/SiegeTankMengskSieged': '충격포 /// Shock Cannon',
    'Behavior/Name/RM15_TankElite': '3등급 충격 사단 /// Rank 3 Shock Division',
    'Behavior/Tooltip/RM15_TankElite': '처음부터 3등급입니다. 주는 피해 +75%. 경험치 성장은 없습니다. /// Rank 3 from the start. +75% damage dealt. Does not gain experience.',
    'Behavior/Name/SiegeTankMengskStun': '기절 /// Stunned',
    'Behavior/Name/SiegeTankMengskSlowHeroic': '감속 /// Slowed',
}
HOT = {'SiegeModeMengsk': 'E', 'UnsiegeMengsk': 'D'}


def sub1(t, a, b):
    assert t.count(a) == 1, a[:90]
    return t.replace(a, b)


def mapped(ref):
    for old, news in REF:
        if ref.startswith(old):
            return [n + ref[len(old):] for n in news]
    return []


def base_upgrades():
    out = {}
    for p in BASE_UP:
        for el in E.parse(p).getroot():
            if el.tag != 'CUpgrade' or not el.get('id'): continue
            for ea in el.findall('EffectArray'):
                if mapped(ea.get('Reference', '')): out.setdefault(el.get('id'), []).append(dict(ea.attrib))
    return out


def unitfix(t):
    for uid in SEEDS:
        b = first(t, 'CUnit', uid); s = b.group(0)
        s = re.sub(r'\s*<EffectArray index="Create" value="MengskVeteranTrigger" />', '', s)
        s = re.sub(r'\s*<WeaponArray Link="90mmCannonsMengskLookAt"[^>]*/>', '', s)  # look-at weapon is not ported (shared)
        s = re.sub(r'\s*<TacticalAIThink value="[^"]*" />', '', s)  # AIThinkSiegeTank* is not in WoL
        s = re.sub(r'\s*<LayoutButtons Face="[^"]*(?:Veterancy|ImperialMandate|Airlift)[^"]*"[^>]*/>', '', s)
        s = s.replace('Face="SiegeTankMengskStun" Type="Passive" Requirements="HaveMengskVeterancySiegeTankMengskGELevel2"',
                      'Face="SiegeTankMengskStun" Type="Passive"')
        s = s.replace('<FlagArray index="PreventDestroy" value="1" />', '<FlagArray index="PreventDestroy" value="0" />')
        for tag, v in (('LifeStart', '620'), ('LifeMax', '620'), ('LifeArmor', '4'), ('Food', '-3')):
            s = re.sub(rf'<{tag} value="[^"]*" />', f'<{tag} value="{v}" />', s, count=1)
        s = s.replace('<CostResource index="Vespene" value="425" />', '<CostResource index="Vespene" value="125" />')
        assert 'MengskVeteranTrigger' not in s and 'Veterancy' not in s and '<LifeMax value="620" />' in s, uid
        s = s.replace('</CUnit>', '<BehaviorArray Link="RM15_TankElite" /><RankDisplay value="Never" /></CUnit>')
        t = t[:b.start()] + s + t[b.end():]
    return t


def effectfix(t):
    b = first(t, 'CEffectEnumArea', 'SiegeTankMengskSiegedStunSearch')
    s = b.group(0); assert s.count('<ValidatorArray value="CasterLevelGTE2" />') == 1
    t = t[:b.start()] + s.replace('<ValidatorArray value="CasterLevelGTE2" />', '') + t[b.end():]
    b = first(t, 'CEffectEnumArea', 'SiegeTankMengskSiegedImprovedAoEStunSearch')
    s = b.group(0); assert s.count('<ValidatorArray value="CasterLevelGTE2" />') == 1  # Codex: the elite blast path also had it
    t = t[:b.start()] + s.replace('<ValidatorArray value="CasterLevelGTE2" />', '') + t[b.end():]
    b = first(t, 'CEffectSwitch', 'SiegeTankMengskSiegedSwitch')
    s = re.sub(r'<CaseArray Validator="CasterLevelGTE4" Effect="SiegeTankMengskSiegedImprovedAoESet"\s*/>', '', b.group(0))
    s = s.replace('<CaseDefault value="SiegeTankMengskSiegedSet" />', '<CaseDefault value="SiegeTankMengskSiegedImprovedAoESet" />')
    assert 'CasterLevelGTE4' not in s and 'ImprovedAoESet' in s
    return t[:b.start()] + s + t[b.end():]


def splash_refs(eff):
    refs = ''
    for i in ('SiegeTankMengskSiegedBlast', 'SiegeTankMengskSiegedImprovedAoEBlast'):
        b = first(eff, 'CEffectDamage', i)
        for k, m in enumerate(re.finditer(r'<AreaArray Radius="([\d.]+)"', b.group(0))):
            refs += f'<EffectArray Reference="Effect,{i},AreaArray[{k}].Radius" Value="{float(m.group(1)) * 0.5:g}" />'
    assert refs
    return refs


def upgrades(t, base, eff):
    have = {m.group(1) for m in re.finditer(r'<CUpgrade id="([^"]+)"', t)}
    ids = set(base)
    for m in re.finditer(r'<CUpgrade id="([^"]+)"[^>]*>(.*?)</CUpgrade>', t, re.S):
        if any(mapped(r) for r in re.findall(r'Reference="([^"]+)"', m.group(2))): ids.add(m.group(1))
    add_new = ''
    n = 0
    ids.discard('RMC_TankSplash')  # its Mengsk radii are added once by splash_refs (Codex: no double entry)
    for uid in sorted(ids):
        entries = list(base.get(uid, []))
        if uid in have:
            b = first(t, 'CUpgrade', uid)
            entries += [dict(re.findall(r'(\w+)="([^"]*)"', x)) for x in re.findall(r'<EffectArray ([^>]*?)/?>', b.group(0))]
        xml, seen = '', set()
        body = first(t, 'CUpgrade', uid).group(0) if uid in have else ''
        for ea in entries:
            for nr in mapped(ea.get('Reference', '')):
                key = (nr, ea.get('Operation', ''))
                if key in seen or f'Reference="{nr}"' in body: continue
                seen.add(key)
                op = f' Operation="{ea["Operation"]}"' if ea.get('Operation') else ''
                xml += f'<EffectArray{op} Reference="{nr}" Value="{ea.get("Value", "")}" />'
        if uid == 'MaelstromRounds':  # Codex: the Mengsk shot has no dummy; +40 goes on the primary-target hit
            for nr in ('Effect,SiegeTankMengskSiegedDirected,Amount', 'Effect,SiegeTankMengskSiegedImprovedAoEDirected,Amount'):
                if f'Reference="{nr}"' not in body: xml += f'<EffectArray Reference="{nr}" Value="40" />'
        if not xml: continue
        n += 1
        if uid in have:
            b = first(t, 'CUpgrade', uid); p = b.end() - len('</CUpgrade>')
            t = t[:p] + xml + t[p:]
        else:
            add_new += f'<CUpgrade id="{uid}">{xml}</CUpgrade>'
    b = first(t, 'CUpgrade', 'RMC_TankSplash'); p = b.end() - len('</CUpgrade>')
    t = t[:p] + '<AffectedUnitArray value="SiegeTankMengskSieged" />' + splash_refs(eff) + t[p:]
    if add_new: t = end_insert(t, add_new)
    assert n > 3, n
    return t


def script(t):
    t = t.replace('"SiegeBreakerSieged"', '"SiegeTankMengskSieged"').replace('"SiegeBreaker"', '"SiegeTankMengsk"')
    assert '"SiegeBreaker' not in t
    return t


def build(src, out):
    out = Path(out); assert not out.exists()
    base = base_upgrades()
    with zipfile.ZipFile(src) as z, tempfile.TemporaryDirectory() as tmp:
        assert OLD in z.read('metadata.txt').splitlines()
        root = Path(tmp); rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        before = {}
        for M in MAPS:
            for n in z.namelist():
                if n.startswith(M + '.SC2Map/'): z.extract(n, root)
            m = root / f'{M}.SC2Map'; gd = m / 'base.sc2data/gamedata'
            before.update({str(p.relative_to(root)).replace('\\', '/'): p.read_bytes() for p in m.rglob('*') if p.is_file()})
            subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(m), '--liberty-base', '--skip-existing', '--with-mengsk', DROP, *SEEDS],
                           check=True, stdout=subprocess.DEVNULL)
            (m / 'ported_shared_refs.txt').unlink(missing_ok=True)
            u = gd / 'unitdata.xml'; u.write_text(unitfix(u.read_text('utf-8')), 'utf-8')
            e = gd / 'effectdata.xml'; e.write_text(effectfix(e.read_text('utf-8')), 'utf-8')
            v = gd / 'validatordata.xml'; vt = v.read_text('utf-8')
            b = first(vt, 'CValidatorCombine', 'CanUseSiegeTankMengskRangeBonus')  # airlift check was a commander unlock
            s = b.group(0).replace('<CombineArray value="MedivacMengskSiegeTankAirliftLevelGTE2" />', '').replace('<CombineArray value="CasterLevelGTE3" />', '<CombineArray value="IsSiegeTankMengskSieged" />')
            assert 'Airlift' not in s; v.write_text(vt[:b.start()] + s + vt[b.end():], 'utf-8')
            bh = gd / 'behaviordata.xml'; bt = bh.read_text('utf-8'); assert 'RM15_TankElite' not in bt; bh.write_text(end_insert(bt, ELITE), 'utf-8')
            up = gd / 'upgradedata.xml'; up.write_text(upgrades(up.read_text('utf-8'), base, e.read_text('utf-8')), 'utf-8')
            sp = m / 'mapscript.galaxy'; sp.write_bytes(script(sp.read_bytes().decode('utf-8-sig')).encode('utf-8'))
            ko = m / KO; kb = set_lines(ko.read_bytes(), STR); V35.gate('kokr', kb); ko.write_bytes(kb)
            for loc in V35.OTHER_LOCALES:
                (m / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(kb))
            for loc in LOCS:
                q = m / f'{loc}.sc2data/localizeddata/gamehotkeys.txt'
                q.write_bytes(set_lines(q.read_bytes(), {f'Button/Hotkey/{k}': v for k, v in HOT.items()}))
            for f in gd.glob('*.xml'): E.parse(f)
            for p in m.rglob('*'):
                if not p.is_file(): continue
                k = str(p.relative_to(root)).replace('\\', '/')
                if before.get(k) != p.read_bytes(): rep[k] = p.read_bytes()
        new = sorted(k for k in rep if k not in z.namelist())
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
                for k in new:
                    zi = zipfile.ZipInfo(k, (2026, 11, 28, 0, 0, 0)); zi.external_attr = 0o644 << 16
                    w.writestr(zi, rep[k], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out, len(rep), 'changed,', len(new), 'new')


if __name__ == '__main__': build(*sys.argv[1:])
