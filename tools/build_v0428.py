#!/usr/bin/env python3
"""Build CCM 0.4.28 from 0.4.27: 4번 고용소 불곰 = 멩스크 협동전 이지스 근위대 (MarauderMengsk).

사용자 지시 (2026-10-19): 고용소에서 고용하는 불곰만 멩스크 불곰으로 (병영 망치 경호대·불곰 연구는 그대로).
  - 협동전 MarauderMengsk를 이식한다 (port_units --with-mengsk). 사령관 레벨 잠금·근위대 진급·통치력·마스터 힘은 이식하지 않는다
    (CLAUDE.md 3-1 레벨 규칙). 능력치·무기(PunisherGrenadesMengsk)는 협동전 그대로.
  - 원작 고용소 자리(Train4, 0행 2열 '망치 경호대')에 이지스 근위대 2명. 쿨다운·충전·가격은 원작 망치 경호대 고용을 따른다.
    3번 코랄의 후예처럼 계약 없이 쓸 수 있다 (State Available).
  - 유닛 비용 표기는 망치 경호대(125/25), 인구는 2로 맞춘다 (모드 변경, 시험값; 협동전 근위대는 125/350·인구 4).

Usage: python3 tools/build_v0428.py <0.4.27 zip> <new output zip>
"""
import argparse, copy, re, subprocess, sys, tempfile, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD, NEW = b'version=0.4.27', b'version=0.4.28'
M4 = 'TTychus01.SC2Map'
DROP = 'Veteran|Veterancy|MengskLevel|MarauderMengskAbsorb|MarauderMengskShrapnel|AttackSpeedBoost|SOASuperShield|RoyalGuard|CasterLevel|ImperialMandate'
KO = {
    'Button/Name/HireHammerSecurities': '이지스 근위대 /// Aegis Guard',
    'Button/Tooltip/HireHammerSecurities': '이지스 근위대 용병 2명을 요청합니다.<n/><n/>자치령 근위대의 중돌격 보병입니다. /// Request 2 Aegis Guard mercenaries.<n/><n/>Dominion Royal Guard heavy assault infantry.',
}
BASIC = ('<CardLayouts><LayoutButtons Face="Move" Type="AbilCmd" AbilCmd="move,Move" Row="0" Column="0" />'
         '<LayoutButtons Face="Stop" Type="AbilCmd" AbilCmd="stop,Stop" Row="0" Column="1" />'
         '<LayoutButtons Face="MoveHoldPosition" Type="AbilCmd" AbilCmd="move,HoldPos" Row="0" Column="2" />'
         '<LayoutButtons Face="MovePatrol" Type="AbilCmd" AbilCmd="move,Patrol" Row="0" Column="3" />'
         '<LayoutButtons Face="Attack" Type="AbilCmd" AbilCmd="attack,Execute" Row="0" Column="4" /></CardLayouts>')


def sub1(t, a, b, flags=0):
    t2, n = re.subn(a, b, t, count=1, flags=flags)
    assert n == 1, a
    return t2


def edit(gd):
    p = gd / 'unitdata.xml'; t = p.read_text('utf-8')
    m = re.search(r'<CUnit id="MarauderMengsk">.*?</CUnit>', t, re.S)
    u = m.group(0)
    u = sub1(u, r'\s*<EffectArray index="Create" value="MengskVeteranTrigger" />', '')
    u = sub1(u, r'<CardLayouts>.*?</CardLayouts>', BASIC, re.S)
    u = sub1(u, r'<CostResource index="Vespene" value="350" />', '<CostResource index="Vespene" value="25" />')
    u = sub1(u, r'<Food value="-4" />', '<Food value="-2" />')
    t = t[:m.start()] + u + t[m.end():]
    t = sub1(t, r'(<CUnit id="MercCompound">\s*<CardLayouts index="0">)',
             r'\1<LayoutButtons Face="HireHammerSecurities" Type="AbilCmd" AbilCmd="SummonMercenaries,Train4" Row="0" Column="2" />')
    p.write_text(t, 'utf-8')
    p = gd / 'abildata.xml'; t = p.read_text('utf-8')
    t = sub1(t, r'<InfoArray index="Train4">\s*<Button State="Suppressed" />\s*</InfoArray>',
             '<InfoArray index="Train4"><Unit index="0" value="MarauderMengsk" /><Unit index="1" value="MarauderMengsk" />'
             '<Button DefaultButtonFace="HireHammerSecurities" State="Available" Requirements="" /></InfoArray>')
    p.write_text(t, 'utf-8')
    p = gd / 'buttondata.xml'; t = p.read_text('utf-8')
    t = sub1(t, r'\s*<TooltipAppender Validator="HaveMasteryMengskRoyalGuardCost"[^>]*/>', '')
    t = t.replace('</Catalog>', '<CButton id="HireHammerSecurities"><Icon value="Assets\\Textures\\btn-unit-terran-maraudermengsk.dds" />'
                  '<AlertIcon value="Assets\\Textures\\btn-unit-terran-maraudermengsk.dds" /></CButton></Catalog>')
    p.write_text(t, 'utf-8')
    p = gd / 'actordata.xml'; t = p.read_text('utf-8')
    for s in ('Marauder_Land', 'Marauder_Death', 'Marauder_Death_NP'):
        t = sub1(t, r'\s*<On Terms="[^"]*" Send="Create ' + s + '" />', '')
    p.write_text(t, 'utf-8')


def build(source, output):
    sys.path.insert(0, str(HERE))
    import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev, tempfile.TemporaryDirectory() as tmp:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        names, infos = prev.namelist(), prev.infolist()
        prev.extractall(tmp)
        root = Path(tmp)
        subprocess.run([sys.executable, str(HERE / 'port_units.py'), str(root / M4), '--liberty-base', '--with-mengsk',
                        '--skip-existing', f'--drop={DROP}', 'MarauderMengsk'], check=True, stdout=subprocess.DEVNULL)
        (root / M4 / 'ported_shared_refs.txt').unlink(missing_ok=True)
        edit(root / M4 / 'base.sc2data/gamedata')
        ko = root / M4 / 'kokr.sc2data/localizeddata/gamestrings.txt'
        text = ko.read_bytes().decode('utf-8')
        nl = '\r\n' if '\r\n' in text else '\n'
        lines, done = text.split(nl), set()
        for i, line in enumerate(lines):
            k = line.split('=', 1)[0]
            if k in KO: lines[i] = f'{k}={KO[k]}'; done.add(k)
        while lines and lines[-1] == '': lines.pop()
        lines += [f'{k}={v}' for k, v in KO.items() if k not in done] + ['']
        ko.write_bytes(nl.join(lines).encode('utf-8'))
        ko.write_bytes(V35.fix_kokr(ko.read_bytes(), {}, V35.english_sources())[0])
        V35.gate('kokr', ko.read_bytes())
        for loc in V35.OTHER_LOCALES:
            (root / M4 / f'{loc}.sc2data/localizeddata/gamestrings.txt').write_bytes(V35.other_locale(ko.read_bytes()))
        (root / 'metadata.txt').write_bytes((root / 'metadata.txt').read_bytes().replace(OLD, NEW))
        files = sorted(str(p.relative_to(root)).replace('\\', '/') for p in root.rglob('*') if p.is_file())
        extra = [f for f in files if f not in names]
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in infos: out.writestr(copy.copy(info), (root / info.filename).read_bytes())
                for f in extra: out.writestr(f, (root / f).read_bytes())
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in names:
                    if not n.startswith(M4 + '/') and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, 'new files:', extra)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
