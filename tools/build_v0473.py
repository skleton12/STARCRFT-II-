#!/usr/bin/env python3
"""0.4.72 -> 0.4.73: 연구 완료 표시를 명령 카드(오른쪽 아래) 패시브 아이콘으로 (4번, 사용자 2026-10-23).

사용자: "아이콘이 그 스팀팩 저거처럼 나오는 걸 생각했는데, 오른쪽 하단 거기". 0.4.71의 정보 칸 버프 아이콘 대신
명령 카드에 패시브 버튼(RMP_<업그레이드>)을 넣고, 그 업그레이드를 마쳤을 때만 보이게 한다(요구조건 Show = 완료 1 이상).
0.4.71 정보 칸 아이콘은 끈다(스크립트 호출 제거; 표시용 버프 정의는 남김). 협동전 안정제 기계 치료 처리는 그대로.
이미 원본 패시브가 있는 항목(보급 벙커 2종, 이지스 무력화탄, 거신·분열기·신기루·정찰기, 파수병 재구축)은 건드리지 않는다.
악마의 개는 맵에 정의가 없어 전쟁광·망치 경호대처럼 명령 카드 부분 덮어쓰기를 추가한다.

Usage: python3 tools/build_v0473.py <0.4.72 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines

M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
OLD, NEW = b'version=0.4.72', b'version=0.4.73'
T = 'Assets\\Textures\\'
# upgrade -> (icon, 'ko /// en', tooltip ko /// en)
UP = {
    'RM3_Shield': ('btn-techupgrade-terran-combatshield-color.dds', '전투 방패 /// Combat Shield', '최대 생명력 +10. /// +10 maximum life.'),
    'RM3_Laser': ('btn-upgrade-terran-hisecautotracking.dds', '레이저 조준 시스템 /// Laser Targeting System', '공격 사거리 증가. /// Increased attack range.'),
    'PunisherGrenades': ('btn-ability-terran-punishergrenade-color.dds', '충격탄 /// Concussive Shells', '공격이 적을 감속시킵니다. /// Attacks slow enemies.'),
    'RM4_Suppression': ('btn-ability-terran-superconcussive.dds', '억제탄 /// Suppression Shells', '대상 주변의 적도 감속시킵니다. /// Also slows enemies around the target.'),
    'RM4_Shrapnel': ('btn-upgrade-terran-explosiveshrapnelshells.dds', '파편탄 /// Shrapnel Shells', '공격이 대상 뒤 부채꼴로 파편 피해를 줍니다. /// Attacks deal shrapnel damage in a cone behind the target.'),
    'MarauderLifeBoost': ('btn-techupgrade-terran-kineticfoam.dds', '동역학 충격완화복 /// Kinetic Foam', '최대 생명력 증가. /// Increased maximum life.'),
    'StabilizerMedPacks': ('btn-techupgrade-terran-stabilizermedpacks.dds', '전투 안정제 /// Stabilizer Medpacks', '치료 속도가 빨라지고 에너지 효율이 좋아집니다. /// Faster healing and better energy efficiency.'),
    'RMC_StabilizerCoop': ('btn-upgrade-raynor-stabilizermedpacks.dds', '전투 안정제 (협동전) /// Stabilizer Medpacks (Co-op)', '기계 유닛도 치료하고, 치료받는 유닛은 받는 피해가 25% 감소합니다. /// Heals mechanical units; healed units take 25% less damage.'),
    'BearclawNozzles': ('btn-techupgrade-terran-bearclawnozzles.dds', '화염증폭기 /// Incinerator Gauntlets', '화염 공격 범위 증가. /// Increased flame attack area.'),
    'FirebatJuggernautPlating': ('btn-techupgrade-terran-juggernautplating.dds', '철인 장갑 /// Juggernaut Plating', '방어력 증가. /// Increased armor.'),
    'RMC_JuggernautCoop': ('btn-upgrade-raynor-juggernautplating.dds', '철인 장갑 (협동전) /// Juggernaut Plating (Co-op)', '협동전 철인 장갑 효과가 적용됩니다. /// Co-op Juggernaut Plating is active.'),
    'AdeptFenixShadeSpawn': ('btn-upgrade-protoss-fenix-adeptchampionshadespawn.dds', '사이오닉 투영 /// Psionic Projection', '공격할 때 그림자를 만듭니다. /// Spawns a shade when attacking.'),
    'TempestDisintegration': ('btn-ability-protoss-disintegration.dds', '분해 /// Disintegration', '분해 능력이 강화됩니다. /// Disintegration is upgraded.'),
    'Charge': ('btn-ability-protoss-charge-color.dds', '돌진 /// Charge', '적에게 돌진합니다. /// Charges at enemies.'),
}
# unit -> [(upgrade, row, col)]; existing cells checked in the map data (0.4.72).
CARDS = {
    'WarPig': [('RM3_Shield', 1, 0), ('RM3_Laser', 1, 1)],
    'RMK_MarineMengsk': [('RM3_Shield', 1, 1), ('RM3_Laser', 1, 3)],
    'HammerSecurity': [('PunisherGrenades', 1, 0), ('RM4_Suppression', 1, 1), ('RM4_Shrapnel', 1, 2), ('MarauderLifeBoost', 1, 3)],
    'MarauderMengsk': [('RM4_Shrapnel', 1, 1), ('MarauderLifeBoost', 1, 4)],
    'MercMedic': [('StabilizerMedPacks', 1, 0), ('RMC_StabilizerCoop', 1, 1)],
    'DevilDog': [('BearclawNozzles', 1, 0), ('FirebatJuggernautPlating', 1, 1), ('RMC_JuggernautCoop', 1, 2)],
    'AdeptFenix': [('AdeptFenixShadeSpawn', 1, 0)],
    'TempestPurifier': [('TempestDisintegration', 1, 0)],
    'ZealotPurifier': [('Charge', 2, 2)],
}


def append(t, extra):
    i = t.rindex('</Catalog>')
    return t[:i] + extra + t[i:]


def lb(up, r, c):
    return f'<LayoutButtons Face="RMP_{up}" Type="Passive" Requirements="RMP_Have{up}" Row="{r}" Column="{c}" />'


def units(d):
    t = d.decode('utf-8')
    for u, items in CARDS.items():
        btns = ''.join(lb(*x) for x in items)
        m = re.search(rf'<CUnit id="{u}"[^>]*>.*?</CUnit>', t, re.S)
        if m is None:
            assert u == 'DevilDog'
            t = append(t, f'<CUnit id="{u}"><CardLayouts>{btns}</CardLayouts></CUnit>')
            continue
        b = m.group(0)
        i = b.index('</CardLayouts>')
        t = t[:m.start()] + b[:i] + btns + b[i:] + t[m.end():]
    return t.encode('utf-8')


def buttons(d):
    t = d.decode('utf-8')
    return append(t, ''.join(f'<CButton id="RMP_{up}"><Icon value="{T}{icon}" /><Name value="Button/Name/RMP_{up}" />'
                             f'<Tooltip value="Button/Tooltip/RMP_{up}" /></CButton>' for up, (icon, _, _) in UP.items())).encode('utf-8')


def nodes(d):
    return append(d.decode('utf-8'), ''.join(f'<CRequirementCountUpgrade id="RMP_Done{up}"><Count Link="{up}" State="CompleteOnly" /></CRequirementCountUpgrade>'
                                             for up in UP)).encode('utf-8')


def reqs(d):
    return append(d.decode('utf-8'), ''.join(f'<CRequirement id="RMP_Have{up}"><NodeArray index="Show" Link="RMP_Done{up}" /></CRequirement>'
                                             for up in UP)).encode('utf-8')


def script(d):
    t = d.decode('utf-8')
    n = len(re.findall(r'    gf_m4_IconOne\([^\n]*\n', t))
    assert n > 20
    t = re.sub(r'    gf_m4_IconOne\(\d,"[^"]+","[^"]+","RMI_[^"]+"\);\n', '', t)
    assert 'gf_m4_IconOne(1' not in t and 'gv_m4_mechHeal=true' in t
    return t.encode('utf-8')


def strings():
    s = {}
    for up, (_, name, tip) in UP.items():
        s[f'Button/Name/RMP_{up}'] = name
        s[f'Button/Tooltip/RMP_{up}'] = tip
    return s


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for f, fn in [('unitdata', units), ('buttondata', buttons), ('requirementnodedata', nodes), ('requirementdata', reqs)]:
            files[GD + f + '.xml'] = fn(files[GD + f + '.xml'])
        files[M4 + 'mapscript.galaxy'] = script(files[M4 + 'mapscript.galaxy'])
        S = strings()
        for loc in ('kokr',) + LOCALES:
            path = M4 + loc + '.sc2data/localizeddata/gamestrings.txt'
            values = S if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in S.items()}
            files[path] = update_lines(files[path], values)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for n in files:
            if n != 'metadata.txt' and not n.startswith(M4): assert files[n] == prev.read(n), n
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
