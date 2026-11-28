#!/usr/bin/env python3
"""0.14.1 -> 0.14.2: 공성 전차 연구 (사용자 2026-11-28 "공성전차 업그레이드도 적용됨 협동전 연구 일부 포함해서").

군수 공장 기술실·기술 반응로 (군수 공장이 있는 4~9·11·12·14번), 0.9.2 벌처와 같은 방식(첫 정의 안에 합침):
  - 대혼란 탄 (MaelstromRounds, 자날 무기고: 공성 모드 포격이 대상에게 +40 추가 피해) (0,3) M
  - 성형 폭발 (SiegeTankShapedBlast, 자날 무기고: 공성 포격이 아군에게 주는 피해가 줄어듦) (0,4) H
    두 연구 모두 원작 업그레이드 그대로라 히페리온에서 샀으면 버튼이 숨고, 공성 파괴단(SiegeBreaker)에도 원작대로 적용된다.
  - [협동전 페이지] 충격포 폭발 범위 확장 (RMC_TankSplash, 협동전 SiegeTankSplashRadius 값: 공성 포격 범위 피해 반경 약 +50%) (0,1) D
    — 모드에서 재설계한 미션 내 연구. 성형 폭발을 연구했을 때 쓰는 적 피해 효과에도 같은 반경을 더한다(아군 피해 효과는 그대로).
  FactoryTechLabResearch Research14~16, 100/100·60초(시험값), 한 번만. 공성 전차 해금(FactoryTrain 1 또는 공성 전차·공성 파괴단 보유,
  1초마다 확인) 뒤에만 보인다(표시 업그레이드 RMA_TankUnlocked). 협동전 페이지 메뉴는 골리앗 또는 공성 전차 해금이면 보인다.
  한국어 이름 공식 번역 미확인. Game not run.

Usage: python3 tools/build_v0142.py <0.14.1 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v062 import set_lines, KO, GD, LOCS
from build_v092 import first, end_insert

OLD, NEW = b'version=0.14.1', b'version=0.14.2'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04', 'TTychus03']
NOTE = (' 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다.', ' Researched in the mission when not bought at the Hyperion Armory.')
COST = '<Resource index="Minerals" value="100" /><Resource index="Vespene" value="100" />'
# (button, upgrade, research index, card, row, col, hotkey, icon, name, tooltip)
ITEMS = [
    ('RMA_Maelstrom', 'MaelstromRounds', 14, '0', 0, 3, 'M', 'Assets\\Textures\\btn-techupgrade-terran-maelstromrounds.dds',
     ('대혼란 탄', 'Maelstrom Rounds'), ('공성 모드 공성 전차·공성 파괴단의 포격이 대상에게 피해를 40 더 줍니다.' + NOTE[0],
                                       'Sieged Siege Tanks and Siege Breakers deal +40 damage to the primary target.' + NOTE[1])),
    ('RMA_ShapedBlast', 'SiegeTankShapedBlast', 15, '0', 0, 4, 'H', 'Assets\\Textures\\btn-techupgrade-terran-shapedblast.dds',
     ('성형 폭발', 'Shaped Blast'), ('공성 모드 포격이 아군에게 주는 범위 피해가 크게 줄어듭니다.' + NOTE[0],
                                     'Siege mode splash deals greatly reduced damage to friendly units.' + NOTE[1])),
    ('RMC_TankSplash', 'RMC_TankSplash', 16, 'RMC2', 0, 1, 'D', 'Assets\\Textures\\btn-techupgrade-terran-ripwavemissiles.dds',
     ('충격포 폭발 범위 확장', 'Shock Cannon Splash Radius'),
     ('공성 모드 공성 전차·공성 파괴단의 범위 피해 반경이 약 50% 늘어납니다. (협동전 연구를 바탕으로 한 모드 연구)',
      'Increases the splash radius of sieged Siege Tanks and Siege Breakers by about 50%. (Mod research based on a co-op upgrade)')),
]
SPLASH = ''.join(f'<EffectArray Reference="Effect,{e},AreaArray[{i}].Radius" Value="{v}" />'
                 for e in ('CrucioShockCannonBlast', 'ArcliteShockCannonBlast', 'CrucioShockCannonEnemyDamage', 'ArcliteShockCannonEnemyDamage')
                 for i, v in ((0, '0.2343'), (1, '0.3906'), (2, '0.625')))
UPG = ('<CUpgrade id="RMA_TankUnlocked"><Race value="Terr" /><Flags index="UpgradeCheat" value="0" /></CUpgrade>'
       '<CUpgrade id="RMC_TankSplash"><Race value="Terr" /><Flags index="UpgradeCheat" value="0" /><MaxLevel value="1" />'
       '<Icon value="Assets\\Textures\\btn-techupgrade-terran-ripwavemissiles.dds" /><Name value="Upgrade/Name/RMC_TankSplash" />'
       '<Alert value="ResearchComplete" /><AffectedUnitArray value="SiegeTankSieged" /><AffectedUnitArray value="SiegeBreakerSieged" />'
       + SPLASH + '</CUpgrade>')
SCRIPT = ('// 0.14.2: siege tank research gate (Siege Tank unlocked or owned), checked every second.\n'
          'trigger gt_rm14Tank;\n\n'
          'bool gt_rm14Tank_Func (bool testConds, bool runActions) {\n'
          '    if (!runActions) { return true; }\n'
          '    if (TechTreeUpgradeCount(1, "RMA_TankUnlocked", c_techCountQueuedOrBetter) == 0 && (TechTreeAbilityIsAllowed(1, AbilityCommand("FactoryTrain", 1))\n'
          '        || UnitGroupCount(UnitGroup("SiegeTank", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) > 0\n'
          '        || UnitGroupCount(UnitGroup("SiegeTankSieged", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) > 0\n'
          '        || UnitGroupCount(UnitGroup("SiegeBreaker", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) > 0\n'
          '        || UnitGroupCount(UnitGroup("SiegeBreakerSieged", 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), c_unitCountAlive) > 0)) {\n'
          '        TechTreeUpgradeAddLevel(1, "RMA_TankUnlocked", 1);\n    }\n'
          '    return true;\n}\n\n'
          'void gf_rm14TankInit () {\n'
          '    if (gt_rm14Tank != null) { return; }\n'
          '    TechTreeUpgradeAllow(1, "RMA_TankUnlocked", true);\n'
          '    TechTreeUpgradeAllow(1, "MaelstromRounds", true);\n'
          '    TechTreeUpgradeAllow(1, "SiegeTankShapedBlast", true);\n'
          '    TechTreeUpgradeAllow(1, "RMC_TankSplash", true);\n'
          '    TechTreeAbilityAllow(1, AbilityCommand("FactoryTechLabResearch", 13), true);\n'
          '    TechTreeAbilityAllow(1, AbilityCommand("FactoryTechLabResearch", 14), true);\n'
          '    TechTreeAbilityAllow(1, AbilityCommand("FactoryTechLabResearch", 15), true);\n'
          '    gt_rm14Tank = TriggerCreate("gt_rm14Tank_Func");\n'
          '    TriggerAddEventTimePeriodic(gt_rm14Tank, 1.0, c_timeGame);\n}\n\n')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    strs, hk = {'Upgrade/Name/RMC_TankSplash': '충격포 폭발 범위 확장 /// Shock Cannon Splash Radius'}, {}
    btn = abil = req = node = ''
    cards = {'0': '', 'RMC2': ''}
    for bid, upg, n, card, r, c, key, icon, (nk, ne), (tk, te) in ITEMS:
        btn += (f'<CButton id="{bid}"><Icon value="{icon}" /><Name value="Button/Name/{bid}" /><Tooltip value="Button/Tooltip/{bid}" />'
                f'<Hotkey value="Button/Hotkey/{bid}" /><TooltipFlags index="ShowLevel" value="0" /></CButton>')
        abil += (f'<InfoArray index="Research{n}" Time="60" Upgrade="{upg}">{COST}<Button DefaultButtonFace="{bid}" State="Available" '
                 f'Requirements="{bid}Learn" /></InfoArray>')
        cards[card] += f'<LayoutButtons Face="{bid}" Type="AbilCmd" AbilCmd="FactoryTechLabResearch,Research{n}" Row="{r}" Column="{c}" />'
        req += f'<CRequirement id="{bid}Learn"><NodeArray index="Show" Link="{bid}Show" /><NodeArray index="Use" Link="{bid}Show" /></CRequirement>'
        node += (f'<CRequirementCountUpgrade id="{bid}Queued"><Count Link="{upg}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
                 f'<CRequirementNot id="{bid}NotQueued"><OperandArray index="0" value="{bid}Queued" /></CRequirementNot>'
                 f'<CRequirementAnd id="{bid}Show"><OperandArray value="{bid}NotQueued" /><OperandArray value="RMA_TankGate" /></CRequirementAnd>')
        strs[f'Button/Name/{bid}'] = f'{nk} 연구 /// Research {ne}'
        strs[f'Button/Tooltip/{bid}'] = f'{tk} /// {te}'
        hk[bid] = key
    node += ('<CRequirementCountUpgrade id="RMA_TankGate"><Count Link="RMA_TankUnlocked" State="CompleteOnly" /></CRequirementCountUpgrade>'
             '<CRequirementOr id="RMA14_CoopMenuOr"><OperandArray value="RMA_GoliathGate" /><OperandArray value="RMA_TankGate" /></CRequirementOr>')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            P = lambda f: f'{m}.SC2Map/{GD}{f}'
            t = files[P('unitdata.xml')].decode('utf-8')
            for u in ('FactoryTechLab', 'FactoryTechReactor'):
                b = first(t, 'CUnit', u)
                c0 = re.search(r'<CardLayouts index="0">(.*?)</CardLayouts>', b.group(0), re.S)
                assert 'Row="0" Column="3"' not in c0.group(1) and 'Row="0" Column="4"' not in c0.group(1), (m, u)
                p = b.start() + c0.end(1); t = t[:p] + cards['0'] + t[p:]
                b = first(t, 'CUnit', u)
                c2 = re.search(r'<CardLayouts CardId="RMC2">(.*?)</CardLayouts>', b.group(0), re.S)
                assert c2 and 'Row="0" Column="1"' not in c2.group(1), (m, u)
                p = b.start() + c2.end(1); t = t[:p] + cards['RMC2'] + t[p:]
            files[P('unitdata.xml')] = t.encode('utf-8')
            t = files[P('abildata.xml')].decode('utf-8')
            b = first(t, 'CAbilResearch', 'FactoryTechLabResearch')
            assert all(f'index="Research{n}"' not in b.group(0) for n in (14, 15, 16)), m
            p = b.end() - len('</CAbilResearch>'); files[P('abildata.xml')] = (t[:p] + abil + t[p:]).encode('utf-8')
            t = files[P('requirementdata.xml')].decode('utf-8')
            b = first(t, 'CRequirement', 'RMC_FactoryCoopMenuShow')
            a = '<NodeArray index="Show" Link="RMA_GoliathGate" />'
            assert b.group(0).count(a) == 1, m
            t = t[:b.start()] + b.group(0).replace(a, '<NodeArray index="Show" Link="RMA14_CoopMenuOr" />') + t[b.end():]
            files[P('requirementdata.xml')] = t.encode('utf-8')
            for f, x in (('buttondata.xml', btn), ('requirementdata.xml', req), ('requirementnodedata.xml', node), ('upgradedata.xml', UPG)):
                t = files[P(f)].decode('utf-8'); assert 'RMA_TankUnlocked' not in t and 'RMA_Maelstrom' not in t and 'RMA_TankGate' not in t, (m, f)
                files[P(f)] = end_insert(t, x).encode('utf-8')
            for f in ('unitdata.xml', 'abildata.xml', 'buttondata.xml', 'requirementdata.xml', 'requirementnodedata.xml', 'upgradedata.xml'):
                E.fromstring(files[P(f)]); changed.add(P(f))
            k = f'{m}.SC2Map/mapscript.galaxy'; t = files[k].decode('utf-8-sig'); nl = '\r\n' if '\r\n' in t else '\n'; t = t.replace('\r\n', '\n')
            a = 'void InitMap () {\n'; assert t.count(a) == 1; t = t.replace(a, SCRIPT + a)
            a = '    gf_rm9MinesInit();\n'; assert t.count(a) == 1, m; t = t.replace(a, a + '    gf_rm14TankInit();\n')
            files[k] = t.replace('\n', nl).encode('utf-8'); changed.add(k)
            k = f'{m}.SC2Map/{KO}'
            ko = set_lines(files[k], strs); V35.gate('kokr', ko); files[k] = ko; changed.add(k)
            for loc in V35.OTHER_LOCALES:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'; files[q] = V35.other_locale(ko); changed.add(q)
            for loc in LOCS:
                q = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'
                files[q] = set_lines(files[q], {f'Button/Hotkey/{b}': h for b, h in hk.items()}); changed.add(q)
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
