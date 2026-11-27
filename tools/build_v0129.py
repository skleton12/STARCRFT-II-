#!/usr/bin/env python3
"""0.12.8 -> 0.12.9: 코덱스 검토(0.12.4~0.12.7) 반영 (사용자 2026-11-27 "검사 코덱스에게 맡겨").

maps 3~9·11·12:
  1. (높음) 연구 건물을 못 짓는 임무 대비: 고르지 않은 쪽 연구(열화탄·나노탄환·보병 공방업 4·5단계 해금·무법자 장비)를
     공학 연구소 연구실 메뉴(RML1)에도 다시 둔다 — 유령 사관학교·무기고 버튼은 그대로(같은 연구 명령).
  2. (높음) 원작은 완료 임무 9개에 공방업 2단계, 16개에 3단계를 허용해 4·5단계까지 못 갈 수 있다:
     보병 공방업 4·5단계(RMPL_Inf45)가 있으면 공학 연구소 보병 2·3단계(일반·울트라 축전기·바나듐판) 명령을 허용.
  3. (높음) 원작 유닛 생산 차단을 명령 차단(1초마다) 대신 유닛 금지로: 약탈자·헤라클레스·밤까마귀·과학선 TechTreeUnitAllow false
     (명령 차단도 그대로 둠). 0.12.8 코랄 과학선 2기는 스크립트가 직접 만들어서 상관없음.
  4. (중간) 스키비의 천사가 미션 안 바나듐 장갑(RM8_VP_Infantry1~3) 생명력 ×1.05를 못 받던 것.
  5. (중간) 열화탄·나노탄환·무법자 장비에서 일꾼(SCV) 제외, 열화탄·나노탄환은 무기 피해(근접·원거리·범위)만.
  6. (낮음) 보병 4·5단계 업그레이드에 이름·LeaderLevel 지정.
남은 지적(이번에 안 함): 미션 중 치트로 연구실 상태가 바뀌는 경우의 회수, 히페리온 연구실 아이콘·영상.
Game not run.

Usage: python3 tools/build_v0129.py <0.12.8 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.12.8', b'version=0.12.9'
MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
G = '.SC2Map/base.sc2data/gamedata/'


def one(t, tag, i):
    m = list(re.finditer(r'<%s id="%s"[^>]*>.*?</%s>' % (tag, i, tag), t, re.S)); assert len(m) == 1, (tag, i, len(m))
    return m[0]


def patch_unit(t, m):
    e = one(t, 'CUnit', 'EngineeringBay'); body = e.group(0)
    c = re.search(r'<CardLayouts CardId="RML1">(.*?)</CardLayouts>', body, re.S); assert c, m
    for cell in ('Row="1" Column="1"', 'Row="0" Column="2"'): assert cell not in c.group(1), (m, cell)
    add = ('            <LayoutButtons Face="RML_P41" Type="AbilCmd" AbilCmd="RML_Research,Research5" Row="0" Column="2" />\n'
           '            <LayoutButtons Face="RML_P42" Type="AbilCmd" AbilCmd="RML_Research,Research6" Row="0" Column="2" />\n'
           '            <LayoutButtons Face="RML_Z31" Type="AbilCmd" AbilCmd="RML_Research,Research10" Row="1" Column="1" />\n'
           '            <LayoutButtons Face="RML_Z32" Type="AbilCmd" AbilCmd="RML_Research,Research11" Row="1" Column="1" />\n')
    body = body[:c.end(1)] + add + body[c.end(1):]
    return t[:e.start()] + body + t[e.end():]


def patch_up(t, m):
    for k, lv in (('W4', 4), ('W5', 5), ('A4', 4), ('A5', 5)):
        e = one(t, 'CUpgrade', f'RMPL_Inf{k}')
        b = e.group(0); assert '<LeaderLevel' not in b and '<Name ' not in b
        b = b.replace('<Alert value="ResearchComplete" />', f'<Alert value="ResearchComplete" />\n        <Name value="Upgrade/Name/RMPL_Inf{k}" />\n        <LeaderLevel value="{lv}" />', 1)
        t = t[:e.start()] + b + t[e.end():]
    for n in (1, 2, 3):
        e = one(t, 'CUpgrade', f'RM8_VP_Infantry{n}'); b = e.group(0)
        assert 'Unit,MercMedic,' not in b, (m, n)
        add = ('        <EffectArray Operation="Multiply" Reference="Unit,MercMedic,LifeMax" Value="1.05" />\n'
               '        <EffectArray Operation="Multiply" Reference="Unit,MercMedic,LifeStart" Value="1.05" />\n    ')
        k = b.rindex('</CUpgrade>'); b = b[:k].rstrip(' ') + add + b[k:]
        t = t[:e.start()] + b + t[e.end():]
    return t


def patch_script(t):
    def rep(a, b):
        nonlocal t
        assert t.count(a) == 1, a[:80]
        t = t.replace(a, b)
    # 3. unit bans next to the command bans
    rep('    TechTreeAbilityAllow(1, AbilityCommand("StarportTrain", 6), false);\n',
        '    TechTreeAbilityAllow(1, AbilityCommand("StarportTrain", 6), false);\n'
        '    // 0.12.9 (Codex review): ban the units too, a campaign re-apply can re-allow the train commands\n'
        '    TechTreeUnitAllow(1, "Predator", false);\n    TechTreeUnitAllow(1, "Hercules", false);\n'
        '    TechTreeUnitAllow(1, "Raven", false);\n    TechTreeUnitAllow(1, "ScienceVessel", false);\n'
        '    // 0.12.9: lab Infantry Upgrades 4-5 also opens infantry levels 2-3 (the campaign gates them on 9 / 16 missions)\n'
        '    if (TechTreeUpgradeCount(1, "RMPL_Inf45", c_techCountCompleteOnly) > 0) {\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 3), true);\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 4), true);\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 7), true);\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 8), true);\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 11), true);\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 12), true);\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 14), true);\n'
        '        TechTreeAbilityAllow(1, AbilityCommand("EngineeringBayResearch", 15), true);\n'
        '    }\n')
    # 5. workers out; weapon damage only
    rep('    if (UnitTypeTestAttribute(st, c_unitAttributeStructure)) { return true; }\n',
        '    if (UnitTypeTestAttribute(st, c_unitAttributeStructure)) { return true; }\n'
        '    if (!UnitFilterMatch(s, 1, UnitFilter(0, 0, (1 << c_targetFilterWorker), 0))) { return true; }\n')
    rep('    TriggerAddEventUnitDamaged(gt_rmZ3Hit, null, c_unitDamageTypeAny, c_unitDamageEither, null);\n',
        '    TriggerAddEventUnitDamaged(gt_rmZ3Hit, null, c_unitDamageTypeMelee, c_unitDamageEither, null);\n'
        '    TriggerAddEventUnitDamaged(gt_rmZ3Hit, null, c_unitDamageTypeRanged, c_unitDamageEither, null);\n'
        '    TriggerAddEventUnitDamaged(gt_rmZ3Hit, null, c_unitDamageTypeSplash, c_unitDamageEither, null);\n')
    rep('(1 << c_targetFilterStructure) | (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32))), 0);\n    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {\n        u = UnitGroupUnit(g, i);\n        if (UnitBehaviorCount(u, "RMPL_GearBuff") == 0)',
        '(1 << c_targetFilterStructure) | (1 << c_targetFilterMissile) | (1 << c_targetFilterWorker), (1 << (c_targetFilterDead - 32))), 0);\n    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {\n        u = UnitGroupUnit(g, i);\n        if (UnitBehaviorCount(u, "RMPL_GearBuff") == 0)')
    return t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            for f, fn in (('unitdata.xml', patch_unit), ('upgradedata.xml', patch_up)):
                k = m + G + f; t = fn(files[k].decode('utf-8'), m); E.fromstring(t.encode('utf-8'))
                files[k] = t.encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in raw else '\n'
            files[k] = patch_script(raw.replace('\r\n', '\n')).replace('\n', nl).encode('utf-8'); changed.add(k)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
                for info in prev.infolist():
                    z.writestr(copy.copy(info), files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as z:
                assert z.testzip() is None and z.namelist() == prev.namelist()
                for k in prev.namelist():
                    if k not in changed: assert z.read(k) == prev.read(k), k
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
