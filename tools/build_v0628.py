#!/usr/bin/env python3
"""0.6.27 -> 0.6.28: 3번 피닉스 영웅(용기병)·멀티샷 표기 (사용자 2026-11-14).

1. 3번 제로 아워(TRaynor03)에 협동전 피닉스 용기병(FenixDragoon)을 플레이어(레이너)가 조종하는 영웅으로 넣는다.
   사용자: "3번째 맵에 피닉스 영웅 추가해야되 드라군으로", "플레이어가 조종하고 죽으면 그냥 죽는거임".
   - 시작 때 레이너 사령부 (97.5,33.5) 옆 (100,38)에 1기. 부활 없음 (협동전 PreventDestroy 끔).
   - 협동전 피닉스 전투복은 사령관 스크립트로 기력을 얻는다(SuppressEnergyRegen). 그 스크립트가 없으므로
     기력 자연 회복을 켜고 시작 기력 50 (시험값). 능력: 태양 대포(Q)·솔라라이트 섬광탄(E)·무장 과충전(R), 협동전 수치 그대로.
     무장 과충전은 협동전 데이터에서 주석 처리된 주기 초기화(0.25초)를 켜서 10초 동안 Q·E 대기시간이 계속 없게 한다.
   - 'Raynor 유닛은 모두 용병' 규칙(CLAUDE.md 3장)의 사용자 지시 예외.
   - 단축키는 협동전 gamehotkeys 값으로 12개 언어 gamehotkeys.txt에 넣는다.
3. 동맹 지원 병력 증원 (사용자 "동맹 병력도 좀더 추가해야됨"): 3·5·6번 [정화자 지원]·[원시저그 지원] 묶음에
   무료로 정화자 군단병 2·피닉스 사도 1, 원시저그 원시 저글링 2·바퀴 1 추가 (시험값). 5·6번 묶음 상한 20 -> 24.
   4번은 동맹이 건물에서 직접 생산하는 방식이라 이번에는 그대로.
2. 멀티샷(RM6_Multishot) 표기: 연구하면 전쟁광·코랄의 후예 무기 표시가 'x2'로 보이도록 DisplayAttackCount = 2
   (사용자 "멀티샷 그거 표기가 않되는데", "attack: 2 뭐 이렇게 나와야"). 실제 효과(맞은 적 근처 1기 추가)는 그대로. 3·4·5·6번.

Usage: python3 tools/build_v0628.py <0.6.27 zip> <new output zip>
"""
import argparse, copy, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.6.27', b'version=0.6.28'
M3 = 'TRaynor03.SC2Map'
MULTI_MAPS = ('TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')
LOCALES = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
DROP = 'FenixMojo|FenixWarbringer|FenixCommander|FenixChampion|FenixPurificationNova|^SOA|AllUnitBehaviorController'
FENIX_POS = (100.0, 38.0)
ENERGY_START = 50           # trial
ENERGY_REGEN = 1.0          # trial (energy per second)

STRINGS = {
    'Unit/Name/FenixDragoon': '피닉스 /// Fenix',
    'Unit/Name/FenixDragoonAttackMissile': '피닉스 용기병 공격 미사일 /// Fenix Dragoon Attack Missile',
    'Unit/Name/ChargedBusterUpgraded': '강화 태양 대포 /// Charged Buster Upgraded',
    'Weapon/Name/FenixDragoon': '위상 분열기 /// Phase Disruptor',
    'Abil/Name/ChargeBuster': '무장 과충전 /// Arsenal Overcharge',
    'Abil/Name/ChargedBuster': '태양 대포 /// Solar Cannon',
    'Abil/Name/FenixDragoonAirBomb': '솔라라이트 섬광탄 /// Solarite Flare',
    'Abil/Name/FenixDragoonArsenalOvercharge': '무장 과충전 /// Arsenal Overcharge',
    'Button/Name/FenixDragoonAirBomb': '솔라라이트 섬광탄 /// Solarite Flare',
    'Button/Name/FenixDragoonArsenalOvercharge': '무장 과충전 /// Arsenal Overcharge',
    'Button/Name/FenixDragoonChargeBuster': '무장 과충전 /// Arsenal Overcharge',
    'Button/Name/FenixDragoonChargeBusterPassive': '과충전! /// Overcharged!',
    'Button/Name/FenixDragoonChargedBuster': '태양 대포 /// Solar Cannon',
    'Button/Tooltip/FenixDragoonAirBomb': '공중에서 터지는 섬광탄을 쏘아 적 공중 유닛에게 <d ref="Effect,FenixDragoonAirBombAirDamage,Amount"/>의 피해를 줍니다. /// Fires an air-bursting flare that deals <d ref="Effect,FenixDragoonAirBombAirDamage,Amount"/> damage to enemy air units.',
    'Button/Tooltip/FenixDragoonAirBombCharged': '<n><n><c val="F0FD02">과충전!</c> 무장 과충전 중에는 재사용 대기시간 없이 쓸 수 있습니다. /// <n><n><c val="F0FD02">Overcharged!</c> Can be cast without cooldown while Arsenal Overcharge is active.',
    'Button/Tooltip/FenixDragoonArsenalOvercharge': '무장 과충전을 켜면 <d ref="Behavior,ChargeBuster,Duration"/>초 동안 피해를 주는 능력의 재사용 대기시간이 없어집니다. /// Activating Arsenal Overcharge causes your damaging abilities to have no cooldown for <d ref="Behavior,ChargeBuster,Duration"/> seconds.',
    'Button/Tooltip/FenixDragoonChargeBusterBase': '무장 과충전을 켜면 <d ref="Behavior,ChargeBuster,Duration"/>초 동안 피해를 주는 능력의 재사용 대기시간이 없어집니다. /// Activating Arsenal Overcharge causes your damaging abilities to have no cooldown for <d ref="Behavior,ChargeBuster,Duration"/> seconds.',
    'Button/Tooltip/FenixDragoonChargeBusterCooldown': '재사용 대기시간: 120<n><n> /// Cooldown: 120<n><n>',
    'Button/Tooltip/FenixDragoonChargeBusterPassive': '무장 과충전 중에는 피해를 주는 능력을 재사용 대기시간 없이 쓸 수 있습니다. /// Your damaging abilities can be cast without cooldown while Arsenal Overcharge is active.',
    'Button/Tooltip/FenixDragoonChargedBuster': '관통하는 광선을 쏘아 경로에 있는 모든 적 지상 유닛에게 <d ref="Effect,ChargedBusterDamage,Amount"/>의 피해를 줍니다. /// Fires a piercing beam that deals <d ref="Effect,ChargedBusterDamage,Amount"/> damage to all enemy ground units in its path.',
    'Button/Tooltip/FenixDragoonChargedBusterCharged': '<n><n><c val="F0FD02">과충전!</c> 무장 과충전 중에는 재사용 대기시간 없이 쓸 수 있습니다. /// <n><n><c val="F0FD02">Overcharged!</c> Can be cast without cooldown while Arsenal Overcharge is active.',
}
HOTKEYS = {
    'Button/Hotkey/FenixDragoonChargedBuster': 'Q',
    'Button/Hotkey/FenixDragoonAirBomb': 'E',
    'Button/Hotkey/FenixDragoonArsenalOvercharge': 'R',
    'Button/Hotkey/FenixDragoonChargeBuster': 'R',
}

SPAWN_ANCHOR = '    TriggerExecute(gt_Init03Units, true, true);\n'
SPAWN = SPAWN_ANCHOR + ('    // 0.6.28 (user 2026-11-14): Fenix (Dragoon) hero for the player, no revive.\n'
                        '    UnitCreate(1, "FenixDragoon", 0, 1, Point(%.1f, %.1f), 270.0);\n' % FENIX_POS)

SUP_MAPS = {'TRaynor03': 'm3c', 'TTosh01': 'm5', 'THanson01': 'm6'}
SUP_P = '        gf_{x}_SupAdd(p,"ZealotPurifier");\n        gf_{x}_SupAdd(p,"ZealotPurifier");\n        gf_{x}_SupAdd(p,"AdeptFenix");\n'
SUP_Z = '    gf_{x}_SupAdd(p,"DehakaZerglingLevel2");\n    gf_{x}_SupAdd(p,"DehakaZerglingLevel2");\n    gf_{x}_SupAdd(p,"DehakaRoachLevel2");\n'


def support(m, x, t):
    paid8 = '\n        gv_{x}_supPaid[p]=gv_{x}_supN[p];\n'.format(x=x)
    paid9 = '\n    gv_{x}_supPaid[p]=gv_{x}_supN[p];\n'.format(x=x)
    assert t.count(paid8) == 1 and t.count(paid9) == 1, m
    t = t.replace(paid8, paid8 + '        // 0.6.28: +3 free per group (user 2026-11-14, trial).\n' + SUP_P.format(x=x))
    t = t.replace(paid9, paid9 + '    // 0.6.28: +3 free per group (user 2026-11-14, trial).\n' + SUP_Z.format(x=x))
    if x != 'm3c':
        t = once(t, f'string[16][20] gv_{x}_supKind;', f'string[16][24] gv_{x}_supKind;')
        t = once(t, f'point[16][20] gv_{x}_supAt;', f'point[16][24] gv_{x}_supAt;')
        t = once(t, f'    if (gv_{x}_supN[p]>=20) {{ return; }}', f'    if (gv_{x}_supN[p]>=24) {{ return; }}')
        loc = '    string[20] kind;\n    point[20] at;\n    actor[20] fx;\n'
        assert t.count(loc) == 2, m
        t = t.replace(loc, loc.replace('[20]', '[24]'))
    return t


MULTI_OLD = '<EffectArray Reference="Effect,RM6_MultiSearchRMK,AreaArray[0].Radius" Value="4" /></CUpgrade>'
MULTI_NEW = ('<EffectArray Reference="Effect,RM6_MultiSearchRMK,AreaArray[0].Radius" Value="4" />'
             '<EffectArray Operation="Set" Reference="Weapon,KelmorianMinerGaussRifle,DisplayAttackCount" Value="2" />'
             '<EffectArray Operation="Set" Reference="Weapon,RMK_MarineMengskGaussRifle,DisplayAttackCount" Value="2" /></CUpgrade>')


def once(t, a, b):
    assert t.count(a) == 1, a[:80]
    return t.replace(a, b)


def fenix_unit(gd):
    p = gd / 'unitdata.xml'
    t = p.read_text('utf-8')
    s = t.index('<CUnit id="FenixDragoon">'); e = t.index('</CUnit>', s)
    u = t[s:e]
    u = once(u, '<FlagArray index="PreventDestroy" value="1" />', '<FlagArray index="PreventDestroy" value="0" />')
    u = once(u, '<BehaviorArray Link="SuppressEnergyRegen" />', '')
    u = once(u, '<EnergyMax value="500" />',
             f'<EnergyMax value="500" />\n        <EnergyStart value="{ENERGY_START}" />\n        <EnergyRegenRate value="{ENERGY_REGEN}" />')
    p.write_text(t[:s] + u + t[e:], 'utf-8')
    # Arsenal Overcharge: the co-op buff only clears Q/E cooldowns once (InitialEffect); its periodic reset is
    # commented out in the co-op data. Turn it on so the tooltip ('no cooldown for 10 s') holds (Codex play review).
    b = gd / 'behaviordata.xml'
    bt = b.read_text('utf-8')
    old = '<InitialEffect value="ChargeBusterCooldownSet" />\n        <Duration value="10" />'
    b.write_text(once(bt, old, old + '\n        <Period value="0.25" />\n        <PeriodicEffect value="ChargeBusterCooldownSet" />'), 'utf-8')


def add_lines(path, items):
    raw = path.read_bytes().decode('utf-8-sig')
    nl = '\r\n' if '\r\n' in raw else '\n'
    keys = {l.split('=', 1)[0] for l in raw.splitlines() if '=' in l}
    add = [f'{k}={v}' for k, v in items.items() if k not in keys]
    out = raw.rstrip('\r\n') + nl + nl.join(add) + nl if add else raw
    path.write_bytes(out.encode('utf-8'))
    return len(add)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        m3 = root / M3
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(m3), '--liberty-base', '--skip-existing',
                        f'--drop={DROP}', 'FenixDragoon'], check=True, stdout=subprocess.DEVNULL)
        (m3 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        gd = m3 / 'base.sc2data/gamedata'
        fenix_unit(gd)
        sp = m3 / 'mapscript.galaxy'
        sp.write_text(once(sp.read_text('utf-8'), SPAWN_ANCHOR, SPAWN), 'utf-8')
        for m, x in SUP_MAPS.items():
            q = root / f'{m}.SC2Map/mapscript.galaxy'
            raw = q.read_bytes().decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'
            q.write_bytes(support(m, x, raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'))
        ko = m3 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        print('strings', add_lines(ko, STRINGS))
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (m3 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        for loc in LOCALES:
            print(loc, 'hotkeys', add_lines(m3 / f'{loc}.sc2data/localizeddata/gamehotkeys.txt', HOTKEYS))
        for m in MULTI_MAPS:
            up = root / f'{m}.SC2Map/base.sc2data/gamedata/upgradedata.xml'
            up.write_text(once(up.read_text('utf-8'), MULTI_OLD, MULTI_NEW), 'utf-8')
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra: out.writestr(f, (root / f).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if n == 'metadata.txt' or n.startswith(M3 + '/') or n.endswith(('upgradedata.xml', 'mapscript.galaxy')): continue
                    assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, 'new files:', extra)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
