#!/usr/bin/env python3
"""0.8.8 -> 0.8.9: 공학 연구소 강화 벙커 연구 (사용자 2026-11-23 "까치날개 했는데 공학 연구소에 150 추가되고 거기에 자가재생 업글 어디감(자가재생업글은 보급벙커 포함)").

maps 3~8: 히페리온 연구실 저그 1단계에서 까치날개 포탑(ShrikeTurret)을 골랐으면 공학 연구소 첫 화면 (2,2)에
[강화 벙커 연구](단축키 F)가 나온다. 연구하면 원작 강화 벙커 업그레이드(FortifiedBunkerCarapace) 자체를 얻는다:
일반 벙커·보급 벙커 생명력 +150(0.6.2), 피해 없이 5초 뒤 초당 5 회복(0.8.3), 효과 아이콘(0.8.4), 건설 버튼 외형.
연구실에서 강화 벙커를 골랐으면 버튼 없음 (0.8.2 울트라 축전기·바나듐 장갑과 같은 방식). 모드에서 재설계한 미션 내 연구,
150/150·90초 시험값, 한 번만. 한 파일 안 기존 정의에 합침(두 번 정의 금지).

maps 4~8 동맹 연구 건물 능력 (사용자 2026-11-23 "플토는 시간 가속 저그는 ... 스투코프 능력 건물 감염 시키면 공생충 나오는거"):
  - 정화자 대의회 [시간 가속](C): 레이너 건물 하나에 20초 동안 생산·연구·재사용 대기 1.5배 (원작 시간 증폭 효과값), 재사용 40초.
  - 데하카의 굴 [건물 감염](E): 스투코프 협동전 '건물 감염'을 단순화. 적 건물이면 20초 동안 능력(생산) 정지,
    내 건물이면 초당 생명력 25 회복. 어느 쪽이든 2초마다 레이너 소유 공생충(자날 Broodling, 원작 수명) 2기가 나온다. 재사용 90초.
  스투코프 원본 유닛·연출은 이식하지 않고 자날 공생충을 쓴다. 모드에서 재설계한 능력, 수치 시험값. Game not run.

Usage: python3 tools/build_v089.py <0.8.8 zip> <new output zip>
"""
import argparse, copy, re, zipfile, xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.8.8', b'version=0.8.9'
MS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01']
LANGS = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
G = '.SC2Map/base.sc2data/gamedata/'
B, UPG, INFO, ROW, COL, HK = 'RM8_FortBunker', 'FortifiedBunkerCarapace', 'Research29', 2, 2, 'F'
ALLY = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01']
IC_C, IC_I = r'Assets\Textures\btn-ability-protoss-chronoboost.dds', r'Assets\Textures\btn-ability-zerg-stukov-infeststructure.dds'
A_ABIL = (f'<CAbilEffectTarget id="RM9_Chrono"><Effect index="0" value="RM9_ChronoAB" /><Cost><Cooldown TimeUse="40" /></Cost>'
          f'<TargetFilters value="Structure;Ally,Neutral,Enemy,Missile,Stasis,Dead,Hidden,Invulnerable,UnderConstruction" /><Range value="500" /><Arc value="360" />'
          f'<CmdButtonArray index="Execute" DefaultButtonFace="RM9_Chrono" /></CAbilEffectTarget>\n'
          f'<CAbilEffectTarget id="RM9_Infest"><Effect index="0" value="RM9_InfestSet" /><Cost><Cooldown TimeUse="90" /></Cost>'
          f'<TargetFilters value="Structure,Visible;Neutral,Heroic,Missile,Stasis,UnderConstruction,Dead,Hidden,Invulnerable" /><Range value="500" /><Arc value="360" />'
          f'<CmdButtonArray index="Execute" DefaultButtonFace="RM9_Infest" /></CAbilEffectTarget>\n')
A_EFF = ('<CEffectApplyBehavior id="RM9_ChronoAB"><Behavior value="RM9_Chrono" /></CEffectApplyBehavior>\n'
         '<CEffectSet id="RM9_InfestSet"><EffectArray value="RM9_InfestEnemyAB" /><EffectArray value="RM9_InfestFriendAB" /></CEffectSet>\n'
         '<CEffectApplyBehavior id="RM9_InfestEnemyAB"><Behavior value="RM9_InfestEnemy" /><ValidatorArray value="EnemyTarget" /></CEffectApplyBehavior>\n'
         '<CEffectApplyBehavior id="RM9_InfestFriendAB"><Behavior value="RM9_InfestFriend" /><ValidatorArray value="RM9_NotEnemy" /></CEffectApplyBehavior>\n'
         '<CEffectCreateUnit id="RM9_InfestBrood"><SpawnUnit value="Broodling" /><SpawnCount value="2" /><CreateFlags index="Placement" value="0" />'
         '<SpawnEffect value="BroodlingTimedLife" /><WhichLocation Value="TargetUnit" /><SpawnOwner Value="Caster" /></CEffectCreateUnit>\n')
A_BEH = (f'<CBehaviorBuff id="RM9_Chrono"><Alignment value="Positive" /><InfoIcon value="{IC_C}" /><Name value="Behavior/Name/RM9_Chrono" />'
         '<Tooltip value="Behavior/Tooltip/RM9_Chrono" /><TimeScaleSource Value="Global" /><Duration value="20" /><Modification>'
         + ''.join(f'<RateMultiplierArray index="{i}" value="1.5" />' for i in ('Charge', 'Cooldown', 'Morph', 'Progress', 'Queueable', 'Spawn', 'Creep'))
         + '</Modification><DisplayDuration index="Self" value="1" /><DisplayDuration index="Ally" value="1" /></CBehaviorBuff>\n'
         f'<CBehaviorBuff id="RM9_InfestEnemy"><Alignment value="Negative" /><InfoIcon value="{IC_I}" /><Name value="Behavior/Name/RM9_Infest" />'
         '<Tooltip value="Behavior/Tooltip/RM9_InfestEnemy" /><TimeScaleSource Value="Global" /><Duration value="20" /><Period value="2" />'
         '<PeriodicEffect value="RM9_InfestBrood" /><Modification><ModifyFlags index="DisableAbils" value="1" /></Modification>'
         '<DisplayDuration index="Self" value="1" /><DisplayDuration index="Enemy" value="1" /></CBehaviorBuff>\n'
         f'<CBehaviorBuff id="RM9_InfestFriend"><Alignment value="Positive" /><InfoIcon value="{IC_I}" /><Name value="Behavior/Name/RM9_Infest" />'
         '<Tooltip value="Behavior/Tooltip/RM9_InfestFriend" /><TimeScaleSource Value="Global" /><Duration value="20" /><Period value="2" />'
         '<PeriodicEffect value="RM9_InfestBrood" /><Modification><VitalRegenArray index="Life" value="25" /></Modification>'
         '<DisplayDuration index="Self" value="1" /></CBehaviorBuff>\n')
A_VAL = '<CValidatorUnitFilters id="RM9_NotEnemy"><Filters value="-;Enemy" /></CValidatorUnitFilters>\n'
A_BTN = (f'<CButton id="RM9_Chrono"><Icon value="{IC_C}" /><Name value="Button/Name/RM9_Chrono" /><Tooltip value="Button/Tooltip/RM9_Chrono" /></CButton>\n'
         f'<CButton id="RM9_Infest"><Icon value="{IC_I}" /><Name value="Button/Name/RM9_Infest" /><Tooltip value="Button/Tooltip/RM9_Infest" /></CButton>\n')
A_STR = {'Button/Name/RM9_Chrono': '시간 가속 /// Chrono Boost',
         'Button/Tooltip/RM9_Chrono': '레이너의 건물 하나의 생산·연구 속도를 20초 동안 50% 높입니다. 재사용 대기시간 40초. /// Increases one of Raynor\'s structures\' production and research speed by 50% for 20 seconds. Cooldown 40 seconds.',
         'Behavior/Name/RM9_Chrono': '시간 가속 /// Chrono Boost',
         'Behavior/Tooltip/RM9_Chrono': '생산·연구 속도 +50%. /// Production and research speed +50%.',
         'Button/Name/RM9_Infest': '건물 감염 /// Infest Structure',
         'Button/Tooltip/RM9_Infest': '건물 하나를 20초 동안 감염시킵니다. 2초마다 공생충 2기가 나옵니다. 적 건물은 능력을 쓰지 못하고, 아군 건물은 초당 생명력을 25 회복합니다. 재사용 대기시간 90초. /// Infests a structure for 20 seconds, spawning 2 Broodlings every 2 seconds. Enemy structures cannot use abilities; friendly structures regenerate 25 life per second. Cooldown 90 seconds.',
         'Behavior/Name/RM9_Infest': '건물 감염 /// Infest Structure',
         'Behavior/Tooltip/RM9_InfestEnemy': '감염됨: 능력을 쓸 수 없고 공생충이 나옵니다. /// Infested: cannot use abilities and spawns Broodlings.',
         'Behavior/Tooltip/RM9_InfestFriend': '감염됨: 초당 생명력 25 회복, 공생충이 나옵니다. /// Infested: regenerates 25 life per second and spawns Broodlings.'}
A_HK = {'Button/Hotkey/RM9_Chrono': 'C', 'Button/Hotkey/RM9_Infest': 'E'}
ICON = r'Assets\Textures\btn-building-terran-bunkerneosteel.dds'
NAME = ('강화 벙커 연구 /// Research Fortified Bunker', 'Research Fortified Bunker')
TIP = ('일반 벙커와 보급 벙커의 생명력이 150 늘어나고, 피해를 받지 않고 5초가 지나면 초당 5씩 생명력을 회복합니다. 연구실에서 까치날개 포탑을 골랐을 때만 연구할 수 있습니다.',
       'Bunkers and Supply Bunkers gain +150 life and regenerate 5 life per second after 5 seconds without taking damage. Available only if Shrike Turret was chosen in the lab.')
NODES = (f'    <CRequirementCountUpgrade id="{B}Shrike"><Count Link="ShrikeTurret" State="CompleteOnly" /></CRequirementCountUpgrade>\n'
         f'    <CRequirementCountUpgrade id="{B}Queued"><Count Link="{UPG}" State="QueuedOrBetter" /></CRequirementCountUpgrade>\n'
         f'    <CRequirementNot id="{B}NotQueued"><OperandArray index="0" value="{B}Queued" /></CRequirementNot>\n'
         f'    <CRequirementAnd id="{B}Show"><OperandArray value="{B}Shrike" /><OperandArray value="{B}NotQueued" /></CRequirementAnd>\n')
REQ = f'    <CRequirement id="{B}Learn"><NodeArray index="Show" Link="{B}Show" /><NodeArray index="Use" Link="{B}Show" /></CRequirement>\n'
BTN = (f'    <CButton id="{B}">\n        <Icon value="{ICON}" />\n        <Name value="Button/Name/{B}" />\n'
       f'        <Tooltip value="Button/Tooltip/{B}" />\n        <TooltipFlags index="ShowLevel" value="0" />\n    </CButton>\n')


def ALL_ALLY():
    return ALLY


def end_insert(data, add, what):
    i = data.rindex(b'</Catalog>'); assert data[i:].strip() == b'</Catalog>', what
    return data[:i] + add.encode() + data[i:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MS:
            k = m + G + 'abildata.xml'; s = files[k]
            a = list(re.finditer(rb'<CAbilResearch id="RM3_BayResearch">.*?</CAbilResearch>', s, re.S))
            assert len(a) == 1 and INFO.encode() not in a[0].group(0), m
            ins = (f'        <InfoArray index="{INFO}" Time="90" Upgrade="{UPG}">\n            <Resource index="Minerals" value="150" />\n'
                   f'            <Resource index="Vespene" value="150" />\n            <Button DefaultButtonFace="{B}" State="Available" Requirements="{B}Learn" />\n'
                   f'        </InfoArray>\n    ').encode()
            j = a[0].end() - len(b'</CAbilResearch>'); files[k] = s[:j] + ins + s[j:]; changed.add(k)
            k = m + G + 'unitdata.xml'; s = files[k]
            e = list(re.finditer(rb'<CUnit id="EngineeringBay"[^>]*>.*?</CUnit>', s, re.S)); assert len(e) == 1, m
            c0 = re.search(rb'<CardLayouts index="0">(.*?)</CardLayouts>', e[0].group(0), re.S)
            assert f'Row="{ROW}" Column="{COL}"'.encode() not in c0.group(1), m
            p = e[0].start() + c0.end(1)
            files[k] = s[:p] + f'            <LayoutButtons Face="{B}" Type="AbilCmd" AbilCmd="RM3_BayResearch,{INFO}" Row="{ROW}" Column="{COL}" />\n'.encode() + s[p:]
            changed.add(k)
            for f, add in (('buttondata.xml', BTN), ('requirementdata.xml', REQ), ('requirementnodedata.xml', NODES)):
                k = m + G + f; assert B.encode() not in files[k], k
                files[k] = end_insert(files[k], add, k); changed.add(k)
            for lang in LANGS:
                ko = lang == 'kokr'
                for fn, lines in (('gamestrings.txt', [f'Button/Name/{B}=' + (NAME[0] if ko else NAME[1]),
                                                       f'Button/Tooltip/{B}=' + (f'{TIP[0]} /// {TIP[1]}' if ko else TIP[1])]),
                                  ('gamehotkeys.txt', [f'Button/Hotkey/{B}={HK}'])):
                    k = f'{m}.SC2Map/{lang}.sc2data/localizeddata/{fn}'; d = files[k]
                    enl = b'\r\n' if b'\r\n' in d else b'\n'; assert B.encode() not in d, k
                    files[k] = d.rstrip(b'\r\n') + enl + enl.join(l.encode('utf-8') for l in lines) + enl; changed.add(k)
        for m in ALL_ALLY():
            for f, add in (('abildata.xml', A_ABIL), ('effectdata.xml', A_EFF), ('behaviordata.xml', A_BEH), ('buttondata.xml', A_BTN), ('validatordata.xml', A_VAL)):
                k = m + G + f; assert b'RM9_' not in files[k], k
                files[k] = end_insert(files[k], add, k); changed.add(k)
            k = m + G + 'unitdata.xml'; s = files[k].decode('utf-8')
            for uid, ab, rch in (('RM7_Conclave', 'RM9_Chrono', 'RM7_ConclaveResearch'), ('RM7_DehakaDen', 'RM9_Infest', 'RM7_DenResearch')):
                e = list(re.finditer(r'<CUnit id="%s">.*?</CUnit>' % uid, s, re.S)); assert len(e) == 1, (m, uid)
                b = e[0].group(0)
                b2 = b.replace(f'<AbilArray Link="{rch}" />', f'<AbilArray Link="{rch}" />\n        <AbilArray Link="{ab}" />', 1)
                c0 = re.search(r'<CardLayouts[^>]*>', b2); assert c0 and 'Row="0" Column="1"' not in b2, (m, uid)
                b2 = b2[:c0.end()] + f'\n            <LayoutButtons Face="{ab}" Type="AbilCmd" AbilCmd="{ab},Execute" Row="0" Column="1" />' + b2[c0.end():]
                assert b2 != b and b2.count('<AbilArray') == b.count('<AbilArray') + 1
                s = s[:e[0].start()] + b2 + s[e[0].end():]
            files[k] = s.encode('utf-8'); changed.add(k)
            k = m + '.SC2Map/mapscript.galaxy'; t = files[k]
            a = b'    TechTreeAbilityAllow(1,AbilityCommand("RM7_ConclaveResearch",0),true);'
            assert t.count(a) == 1, m
            t = t.replace(a, a + b'\r\n' * (b'\r\n' in t) + b'\n' * (b'\r\n' not in t)
                          + b'    TechTreeAbilityAllow(1,AbilityCommand("RM9_Chrono",0),true);' + (b'\r\n' if b'\r\n' in t else b'\n')
                          + b'    TechTreeAbilityAllow(1,AbilityCommand("RM9_Infest",0),true);')
            files[k] = t; changed.add(k)
            for lang in LANGS:
                ko = lang == 'kokr'
                for fn, dd in (('gamestrings.txt', A_STR), ('gamehotkeys.txt', A_HK)):
                    k = f'{m}.SC2Map/{lang}.sc2data/localizeddata/{fn}'; d = files[k]
                    enl = b'\r\n' if b'\r\n' in d else b'\n'
                    lines = [f'{x}=' + (v if ko or '///' not in v else v.split(' /// ', 1)[1]) for x, v in dd.items()]
                    files[k] = d.rstrip(b'\r\n') + enl + enl.join(l.encode('utf-8') for l in lines) + enl
        for k in changed:
            if k.endswith('.xml'): E.fromstring(files[k])
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
