#!/usr/bin/env python3
"""0.6.32 -> 0.6.33: 3번 피닉스(용기병) 음성·체력바·보호막 (사용자 2026-11-15).

사용자: "피닉스는 왜 말이 없고 그 체력이랑 보호막 않보이냐 그리고 보호막 다 꺼진체로 나오는데".
원인 (0.6.28 협동전 이식):
- 체력·보호막 바: 액터가 협동전 사령관 UI(Coop_UnitStatus/FenixHeroUnitEnergyStatusFrameTemplate)를 쓰고
  기본 상태바를 숨긴다. 그 UI는 맵에 없다 (0.4.66 이지스와 같은 문제) -> 기본 상태바로 되돌린다.
- 음성: 협동전에서 피닉스 목소리는 다른 액터(사령관 영웅)에 달려 있어 용기병 액터에는 대사 연결이 없다.
  공허 캠페인 피닉스 대사 Fenix_What/Yes/Attack/Ready/Pissed/Help(부모 ProtossAck_Void, 자날 층에 있음)를
  맵에 넣고 액터에 연결한다. 음량은 협동전 값.
- 보호막 0으로 시작: 유닛에 ShieldsStart가 없다 (협동전은 스크립트가 채움) -> ShieldsStart 500 (= 최대).
- 스킬이 안 나감: 태양 대포(Q)의 탄환 유닛 ChargedBuster, 솔라라이트 섬광탄(E)의 탄환 유닛
  FenixDragoonAirBomb(Upgraded)Weapon이 이식 때 공용 엔트리로 빠졌다 (0.4.67 이지스와 같은 유형).
- 같은 검사(check_release에 새로 넣음)로 다른 맵의 빠진 탄환 유닛도 찾았다: 원시 숙주 식충 알
  LocustMPEggA/BMissileWeapon(4~6번, 원시 숙주가 식충을 못 낳았을 수 있음), 한과 호너 폭격 HHBomberAreaBombMissile,
  쓰지 않는 데하카 섭취·노바 플라스마 탄환. 모든 미션 맵에 원본 층(군심·공허·협동전) 정의를 합쳐 넣는다.
- 끊긴 연결 전수 검사(실제로 쓰는 유닛에서 닿는 데이터만 따라감)로 추가 발견:
  원시 숙주가 낳는 식충 DehakaLocust·DehakaCreeperFlying(+비행형·무기·능력)이 4·5·6번에 없었다 -> port_units로 이식.
  원시 점화자 패시브 아이콘 조건 HaveDehakaGlevigRoachFireBreath(5·6번)가 없었다 -> 요구조건·노드·업그레이드 이식
  (연구하는 곳이 없어 아이콘은 숨겨진 채로 유지 = 원래 의도).
  나머지(쓰지 않는 영웅·사령관 흔적: 모선 소환, 정화 폭발, 카락스 시간 증폭 등)는 플레이에 닿지 않아 그대로.
- 스킬 버튼: R(무장 과충전) 칸 (2,3)에 협동전 패시브 아이콘 FenixDragoonChargeBusterPassive가 겹쳐 놓여 있었다 -> 패시브 줄 삭제.
  E(솔라라이트 섬광탄) 능력의 기본 버튼이 Q 모양(FenixDragoonChargedBuster)이었다 -> FenixDragoonAirBomb.
  과충전 상태 E의 본체 발사 동작 이벤트(FenixDragoonAirBombUpgradedCP)가 없었다 -> 일반 E와 같은 동작 연결.
  시작 기력 50 -> 100 (시험값, 시작부터 Q·E를 한 번씩 쓸 수 있게; Codex 플레이 검토).
게임 미실행.

Usage: python3 tools/build_v0633.py <0.6.32 zip> <new output zip>
"""
import argparse, copy, sys, tempfile, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OLD, NEW = b'version=0.6.32', b'version=0.6.33'
M = 'TRaynor03.SC2Map'
GD = 'base.sc2data/gamedata'
VO = ('What', 'Yes', 'Attack', 'Ready', 'Pissed', 'Help')


def once(t, a, b):
    assert t.count(a) == 1, a[:70]
    return t.replace(a, b)


def sounds_xml():
    void = {e.get('id'): e for e in E.parse(ROOT / 'source/void.sc2campaign' / GD / 'sounddata.xml').getroot()}
    coop = {e.get('id'): e for e in E.parse(ROOT / 'source/starcoop/starcoop.sc2mod' / GD / 'sounddata.xml').getroot()}
    out = ''
    for k in VO:
        sid = f'Fenix_{k}'
        e = copy.deepcopy(void[sid])
        assert e.get('parent') in ('ProtossAck_Void', 'ProtossReady', 'ProtossPissed', 'ProtossHelp'), sid
        vol = coop[sid].find('Volume')
        if vol is not None:
            for old in e.findall('Volume'): e.remove(old)
            e.append(copy.deepcopy(vol))
        e.tail = None
        out += E.tostring(e, encoding='unicode')
    return out


AMMO_LAYERS = ['swarm.sc2mod', 'void.sc2mod', 'voidmulti.sc2mod', 'swarm.sc2campaign', 'void.sc2campaign',
               'starcoop/starcoop.sc2mod']
DEP_LAYERS = ['core.sc2mod', 'liberty.sc2mod', 'liberty.sc2campaign', 'libertystory.sc2campaign']
MISSION_MAPS = ('TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01')


def missing_ammo_units(gd):
    dep = set()
    for L in DEP_LAYERS:
        f = ROOT / 'source' / L / GD / 'unitdata.xml'
        if f.exists(): dep |= {e.get('id') for e in E.parse(f).getroot()}
    have = {e.get('id') for e in E.parse(gd / 'unitdata.xml').getroot()}
    need = []
    for e in E.parse(gd / 'effectdata.xml').getroot():
        a = e.find('AmmoUnit')
        if e.tag == 'CEffectLaunchMissile' and a is not None and a.get('value') and a.get('value') not in have | dep:
            if a.get('value') not in need: need.append(a.get('value'))
    out = ''
    for uid in need:
        merged = None
        for L in AMMO_LAYERS:
            f = ROOT / 'source' / L / GD / 'unitdata.xml'
            for e in E.parse(f).getroot():
                if e.get('id') != uid: continue
                if merged is None:
                    merged = copy.deepcopy(e)
                else:
                    for c in e: merged.append(copy.deepcopy(c))
        assert merged is not None, uid
        merged.tail = None
        out += E.tostring(merged, encoding='unicode')
    return need, out


def merged_record(fname, rid):
    merged = None
    for L in AMMO_LAYERS:
        f = ROOT / 'source' / L / GD / fname
        if not f.exists(): continue
        for e in E.parse(f).getroot():
            if e.get('id') != rid: continue
            if merged is None: merged = copy.deepcopy(e)
            else:
                for c in e: merged.append(copy.deepcopy(c))
    return merged


def missing_movers(gd, unit_xml):
    dep = set()
    for L in DEP_LAYERS:
        f = ROOT / 'source' / L / GD / 'moverdata.xml'
        if f.exists(): dep |= {e.get('id') for e in E.parse(f).getroot()}
    f = gd / 'moverdata.xml'
    have = {e.get('id') for e in E.parse(f).getroot()} if f.exists() else set()
    out, need = '', []
    for u in E.fromstring('<C>' + unit_xml + '</C>'):
        mv = u.find('Mover')
        if mv is not None and mv.get('value') not in have | dep and mv.get('value') not in need:
            need.append(mv.get('value'))
    for mid in need:
        r = merged_record('moverdata.xml', mid)
        assert r is not None, mid
        r.tail = None
        out += E.tostring(r, encoding='unicode')
    return need, out


LOCUST_MAPS = ('TTychus01', 'TTosh01', 'THanson01')
LOCUST_SEEDS = ['DehakaLocust', 'DehakaCreeperFlying']
LOCUST_DROP = ('FenixMojo|FenixWarbringer|FenixCommander|FenixChampion|FenixPurificationNova|^SOA|Vorazun|DehakaMurvar|'
               'DehakaGlevig|AllUnitBehaviorController')
LOCUST_STRINGS = {
    'Unit/Name/DehakaLocust': '원시 식충 /// Primal Locust',
    'Unit/Name/DehakaLocustFlying': '원시 식충 /// Primal Locust',
    'Unit/Name/DehakaCreeperFlying': '폭발성 식충 /// Explosive Creeper',
    'Unit/Name/LocustMPPrecursor': '식충 /// Locust',
    'Unit/Name/DehakaLocustWeapon': '원시 식충 무기 /// Primal Locust Weapon',
    'Weapon/Name/DehakaLocustMelee': '원시 식충 /// Primal Locust',
    'Weapon/Name/DehakaLocustFlyingSwoopWeapon': '급강하 /// Swoop',
    'Weapon/Name/DehakaCreeperSwoop': '급강하 /// Swoop',
    'Weapon/Name/DehakaCreeperSuicide': '폭발 /// Explode',
    'Weapon/Name/DehakaCreeperSuicideBuilding': '폭발 /// Explode',
    'Abil/Name/DehakaLocustFlyingMorphToGround': '착지 /// Land',
    'Abil/Name/DehakaLocustFlyingSwoopAttack': '급강하 /// Swoop',
    'Button/Name/DehakaLocustSwoop': '급강하 /// Swoop',
}
FIRE_MAPS = ('TTosh01', 'THanson01')
FIRE_RECORDS = (('requirementdata.xml', 'HaveDehakaGlevigRoachFireBreath'),
                ('requirementnodedata.xml', 'CountUpgradeDehakaGlevigRoachFireBreathCompleteOnly1237587109'),
                ('upgradedata.xml', 'DehakaGlevigRoachFireBreath'))


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        g = root / M / GD
        # actor: default status bars + voice
        p = g / 'actordata.xml'; t = p.read_text('utf-8')
        s = t.index('<CActorUnit id="FenixDragoon"'); e = t.index('</CActorUnit>', s)
        a = t[s:e]
        a = once(a, '<CustomUnitStatusFrame value="Coop_UnitStatus/FenixHeroUnitEnergyStatusFrameTemplate" />', '')
        a = once(a, '<StatusBarOn index="Custom" value="1" />', '')
        a = once(a, '<UnitFlags index="SuppressDefaultStatusBar" value="1" />', '')
        a = once(a, '<SoundArray index="Movement" value="Dragoon_MoveStart" />',
                 '<SoundArray index="Movement" value="Dragoon_MoveStart" />'
                 + ''.join(f'<SoundArray index="{k}" value="Fenix_{k}" />' for k in VO))
        p.write_text(t[:s] + a + t[e:], 'utf-8')
        # E air-bomb animation also for the overcharged branch (Codex play review)
        p = g / 'actordata.xml'; t = p.read_text('utf-8')
        s = t.index('<CActorUnit id="FenixDragoon"'); e = t.index('</CActorUnit>', s)
        a = t[s:e]
        assert 'FenixDragoonAirBombUpgradedCP' not in a and 'Effect.FenixDragoonAirBombCP.Start' in a
        a = a.replace('<SoundArray index="Movement" value="Dragoon_MoveStart" />',
                      '<On Terms="Effect.FenixDragoonAirBombUpgradedCP.Start" Send="AnimBracketStart AirBomb Cover,Start Cover Cover,End DontResetOnUnhide" />'
                      '<On Terms="Effect.FenixDragoonAirBombUpgradedCP.Stop" Send="AnimBracketStop AirBomb" />'
                      '<SoundArray index="Movement" value="Dragoon_MoveStart" />', 1)
        p.write_text(t[:s] + a + t[e:], 'utf-8')
        # E uses its own button face
        p = g / 'abildata.xml'; t = p.read_text('utf-8')
        s = t.index('<CAbilEffectTarget id="FenixDragoonAirBomb">'); e = t.index('</CAbilEffectTarget>', s)
        a = once(t[s:e], '<CmdButtonArray index="Execute" DefaultButtonFace="FenixDragoonChargedBuster" />',
                 '<CmdButtonArray index="Execute" DefaultButtonFace="FenixDragoonAirBomb" />')
        p.write_text(t[:s] + a + t[e:], 'utf-8')
        # unit: start with full shields
        p = g / 'unitdata.xml'; t = p.read_text('utf-8')
        s = t.index('<CUnit id="FenixDragoon">'); e = t.index('</CUnit>', s)
        u = once(t[s:e], '<ShieldsMax value="500" />', '<ShieldsMax value="500" />\n        <ShieldsStart value="500" />')
        u = once(u, '<LayoutButtons Face="FenixDragoonChargeBusterPassive" Type="Passive" Row="2" Column="3" />', '')
        u = once(u, '<EnergyStart value="50" />', '<EnergyStart value="100" />')
        p.write_text(t[:s] + u + t[e:], 'utf-8')
        # sounds
        p = g / 'sounddata.xml'; t = p.read_text('utf-8')
        assert 'id="Fenix_What"' not in t and t.count('</Catalog>') == 1
        p.write_text(t.replace('</Catalog>', sounds_xml() + '</Catalog>'), 'utf-8')
        changed_maps = {M}
        import subprocess
        sys.path.insert(0, str(HERE))
        import build_v035 as V35
        from build_v062 import set_lines, KO
        for mm in LOCUST_MAPS:
            d = root / f'{mm}.SC2Map'
            subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(d), '--liberty-base', '--skip-existing',
                            f'--drop={LOCUST_DROP}', *LOCUST_SEEDS], check=True, stdout=subprocess.DEVNULL)
            (d / 'ported_shared_refs.txt').unlink(missing_ok=True)
            ko = set_lines((d / KO).read_bytes(), LOCUST_STRINGS)
            (d / KO).write_bytes(ko)
            V35.gate('kokr', ko)
            for loc in V35.OTHER_LOCALES:
                (d / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko))
            gd = d / GD
            fp = gd / 'actordata.xml'; ft = fp.read_text('utf-8')
            if 'id="Locust_Land"' not in ft:
                r = merged_record('actordata.xml', 'Locust_Land'); r.tail = None
                fp.write_text(ft.replace('</Catalog>', E.tostring(r, encoding='unicode') + '</Catalog>'), 'utf-8')
            changed_maps.add(f'{mm}.SC2Map')
        for mm in FIRE_MAPS:
            gd = root / f'{mm}.SC2Map' / GD
            for fname, rid in FIRE_RECORDS:
                fp = gd / fname; ft = fp.read_text('utf-8')
                if f'id="{rid}"' in ft: continue
                r = merged_record(fname, rid)
                assert r is not None, rid
                if fname == 'requirementdata.xml':
                    for na in list(r.findall('NodeArray')):
                        if na.get('index') == 'Show': r.remove(na)   # commander-level Show node: no levels in this mod
                r.tail = None
                fp.write_text(ft.replace('</Catalog>', E.tostring(r, encoding='unicode') + '</Catalog>'), 'utf-8')
            changed_maps.add(f'{mm}.SC2Map')
        for mm in MISSION_MAPS:
            gd = root / f'{mm}.SC2Map' / GD
            need, xml = missing_ammo_units(gd)
            if need:
                p = gd / 'unitdata.xml'; t = p.read_text('utf-8')
                assert t.count('</Catalog>') == 1
                p.write_text(t.replace('</Catalog>', xml + '</Catalog>'), 'utf-8')
                changed_maps.add(f'{mm}.SC2Map')
                print(mm, 'ammo units added:', need)
                mneed, mxml = missing_movers(gd, xml)
                if mneed:
                    mp = gd / 'moverdata.xml'; mt = mp.read_text('utf-8')
                    assert mt.count('</Catalog>') == 1
                    mp.write_text(mt.replace('</Catalog>', mxml + '</Catalog>'), 'utf-8')
                    print(mm, 'movers added:', mneed)
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        for f in root.rglob('*.xml'): E.parse(f)
        try:
            files = sorted(str(q.relative_to(root)).replace('\\', '/') for q in root.rglob('*') if q.is_file())
            extra = [f for f in files if f not in names]
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra: out.writestr(f, (root / f).read_bytes())
            print('new files:', extra)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if n == 'metadata.txt' or any(n.startswith(c + '/') for c in changed_maps): continue
                    assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('source', type=Path); a.add_argument('output', type=Path)
    a = a.parse_args(); build(a.source, a.output)
