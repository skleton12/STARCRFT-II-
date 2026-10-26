#!/usr/bin/env python3
"""0.5.1 -> 0.5.2: 레드스톤 첫 시험 보고 4가지 수정 (사용자 2026-10-25·26).

1) 사신(죽음의 우두머리, MercReaper) 업그레이드 (5번):
   - 원작 업그레이드는 원래 사신의 무기·효과 ID(P38ScytheGuassPistol)만 바꿔서 이식한 용병 사신에 안 닿았다.
     보병 공격·방어(부모 TerranInfantryWeapons/Armors, 단계 아이콘), U-238 탄(사거리 +1·경장갑 +3),
     니트로 추진기(ReaperSpeed, 속도)를 MercReaper에도 건다. G-4 집속탄은 같은 D8Charge 능력이라 이미 따라간다.
   - 용병 사신 명령 카드에 원작 U-238 탄 표시(무기고에서 샀을 때)를 붙인다.
   - 무기고에서 안 산 사신 기술은 병영 기술실에서 연구 (4장 규칙): U-238 탄·G-4 집속탄, 100/100·60초 (시험값),
     사신 생산이 해금됐을 때만 보인다 (RMR_ReaperUnlocked). 샀거나 연구 중이면 버튼이 안 나온다.
2) 동맹 군사 건물을 기지에서 더 멀리 (3·4·5번): 광물 반대쪽 16→13→10칸, 좌우 35·70도까지 자리를 찾고
   기지 중심에서 9칸 안에는 짓지 않는다. 5번은 용암 때문에 높이 9.5 위에만 짓는다. 자리가 없을 때만 예전처럼 기지 둘레.
3) 5번 시작 동맹 일꾼: 정화자 탐사정 1기, 원시저그 원시 일벌레 1기 (사용자 확정 2026-10-26). 일벌레 무료 보충도 1기까지.
4) 무기고 업그레이드 아이콘 2개 (4·5번): 원작 표시와 같은 업그레이드를 세는 모드 표시(RMP_)를 뺀다
   (망치 경호대 동역학 충격완화복, 악마의 개 곰발톱 분사기·강철 장갑판). 충격탄은 무기고 구매(Jackhammer) 표시가 있으면
   모드 표시를 숨긴다. 이지스 근위대처럼 원작 표시가 없는 유닛은 그대로.

Usage: python3 tools/build_v052.py <0.5.1 zip> <new output zip>
"""
import argparse, copy, re, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35
from build_v041 import merge

OLD, NEW = b'version=0.5.1', b'version=0.5.2'
M5 = 'TTosh01.SC2Map/'
GD = 'base.sc2data/gamedata/'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'
ICON_MAPS = ['TTychus01', 'TTosh01']
AWAY_MAPS = ['TRaynor03', 'TTychus01', 'TTosh01']
SAFE_H = 9.5

W, E = 'MercReaperP38ScytheGuassPistol', 'MercReaperP38ScytheGuassPistol'
LV = lambda kind, n: f'Assets\\Textures\\btn-upgrade-terran-infantry{kind}level{n}.dds'
UPGRADES = (
    f'<Catalog><CUpgrade id="TerranInfantryWeapons"><EffectArray Reference="Effect,{E},Amount" Value="1" />'
    f'<EffectArray Reference="Weapon,{W},Level" Value="1" /></CUpgrade>'
    '<CUpgrade id="TerranInfantryArmors"><EffectArray Reference="Unit,MercReaper,LifeArmor" Value="1" />'
    '<EffectArray Reference="Unit,MercReaper,LifeArmorLevel" Value="1" /></CUpgrade>'
    + ''.join(f'<CUpgrade id="TerranInfantryWeaponsLevel{n}"><EffectArray Operation="Set" Reference="Weapon,{W},Icon" Value="{LV("weapons", n)}" /></CUpgrade>'
              f'<CUpgrade id="TerranInfantryArmorsLevel{n}"><EffectArray Operation="Set" Reference="Actor,MercReaper,LifeArmorIcon" Value="{LV("armor", n)}" /></CUpgrade>'
              for n in (1, 2, 3))
    + f'<CUpgrade id="ReaperU238Rounds"><AffectedUnitArray value="MercReaper" /><EffectArray Reference="Weapon,{W},Range" Value="1.000000" />'
    f'<EffectArray Reference="Effect,{E},AttributeBonus[Light]" Value="3.000000" /></CUpgrade>'
    '<CUpgrade id="ReaperSpeed"><AffectedUnitArray value="MercReaper" /><EffectArray Reference="Unit,MercReaper,Speed" Value="0.886700" /></CUpgrade>'
    '<CUpgrade id="ClusterBomb"><AffectedUnitArray value="MercReaper" /></CUpgrade>'
    '<CUpgrade id="RMR_ReaperUnlocked"><Race value="Terr" /></CUpgrade></Catalog>')
# (button id, upgrade, research index (1-based), row, col, hotkey, icon, ko name, en name, ko desc, en desc)
NOTE = (' 히페리온 무기고에서 사지 않았을 때 미션 안에서 연구합니다.', ' Researched in the mission when not bought at the Hyperion Armory.')
RESEARCH = [
    ('RMA_ReaperU238Rounds', 'ReaperU238Rounds', 18, 0, 4, 'U', 'Assets\\Textures\\btn-techupgrade-terran-u238rounds.dds',
     'U-238 탄', 'U-238 Rounds', '사신의 사거리가 1 늘고 경장갑 상대 피해가 3 늘어납니다.', 'Reapers gain +1 range and do an additional +3 damage to light armor.'),
    ('RMA_ClusterBomb', 'ClusterBomb', 19, 1, 1, 'G', 'Assets\\Textures\\btn-techupgrade-terran-d-8charges.dds',
     'G-4 집속탄', 'G-4 Clusterbomb', '사신이 넓은 폭발 범위의 대인 폭약을 던질 수 있습니다.', 'Anti-personnel charge with a large blast radius.'),
]

AWAY_FN = f'''
// 0.5.2: allies build army structures well off their base (user 2026-10-25 "멀찍이"): opposite the resources,
// 16 -> 13 -> 10 cells out and up to 70 degrees to either side, never within 9 of the base centre.
fixed gv_rmMinBuildH;

bool gf_rmTryAway (int p, string worker, string abil, int idx, string kind) {{
    unitgroup ore=UnitGroup(null,0,RegionCircle(gv_rmBasePt[p],12.0),UnitFilter((1 << c_targetFilterRawResource),0,0,0),0);
    unit w=gf_rmFreeWorker(p,worker);
    fixed ang;
    fixed d;
    int k;
    point spot;
    if (w==null) {{ return true; }}
    if (PlayerGetPropertyInt(p,c_playerPropMinerals)<UnitTypeGetCost(kind,c_unitCostMinerals)
        || PlayerGetPropertyInt(p,c_playerPropVespene)<UnitTypeGetCost(kind,c_unitCostVespene)) {{ return true; }}
    ang=RandomFixed(0.0,360.0);
    if (UnitGroupCount(ore,c_unitCountAll)>0) {{ ang=AngleBetweenPoints(UnitGroupCenterOfGroup(ore),gv_rmBasePt[p]); }}
    for (d=16.0;d>=10.0;d-=3.0) {{
        for (k=0;k<5;k+=1) {{
            spot=UnitTypePlacementFromPoint(kind,p,PointWithOffsetPolar(gv_rmBasePt[p],d,ang+IntToFixed(((k+1)/2)*35*(1-2*ModI(k,2)))),3.0);
            if (spot!=null && DistanceBetweenPoints(spot,gv_rmBasePt[p])>=9.0 && WorldHeight(c_heightMapGround,spot)>gv_rmMinBuildH) {{
                UnitIssueOrder(w,OrderTargetingPoint(AbilityCommand(abil,idx),spot),c_orderQueueReplace);
                return true;
            }}
        }}
    }}
    return false;
}}
'''
AWAY = [
    ('    return PointWithOffsetPolar(gv_rmBasePt[p],8.0,AngleBetweenPoints(UnitGroupCenterOfGroup(ore),gv_rmBasePt[p]));\n}\n',
     '    return PointWithOffsetPolar(gv_rmBasePt[p],14.0,AngleBetweenPoints(UnitGroupCenterOfGroup(ore),gv_rmBasePt[p]));\n}\n' + AWAY_FN),
    ('if (!gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gf_rmAwayPt(pp),6.0)) {', 'if (!gf_rmTryAway(pp,"Probe","ProtossBuild",1,"Pylon")) {'),
    ('{ gf_rmTryBuild(pp,"Probe","ProtossBuild",1,"Pylon",gf_rmAwayPt(pp),10.0); }', '{ gf_rmTryAway(pp,"Probe","ProtossBuild",1,"Pylon"); }'),
    ('if (!gf_rmTryBuild(pz,"DehakaDrone","DehakaDroneMorph",0,"DehakaBarracks",gf_rmAwayPt(pz),6.0)) {',
     'if (!gf_rmTryAway(pz,"DehakaDrone","DehakaDroneMorph",0,"DehakaBarracks")) {'),
    ('py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],20.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);',
     'py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],24.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32))),0);'),
    ('py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],20.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))),0);',
     'py=UnitGroup("Pylon",pp,RegionCircle(gv_rmBasePt[pp],24.0),UnitFilter(0,0,0,(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterUnderConstruction - 32))),0);'),
]
M5_SCRIPT = [
    # 3) one worker each (user 2026-10-26)
    ('    UnitCreate(2,"Probe",0,8,Point(45.0,81.0),270.0);\n    for (i=0;i<5;i+=1) {',
     '    UnitCreate(1,"Probe",0,8,Point(45.0,81.0),270.0);\n    for (i=0;i<1;i+=1) {'),
    ('if (have<2) {', 'if (have<1) {'),
    ('for (i=have;i<2;i+=1)', 'for (i=have;i<1;i+=1)'),
    # lava map: allied army structures only on high ground
    ('    gf_m5_Mercs();\n    PlayerSetColorIndex(8,2,true);', f'    gf_m5_Mercs();\n    gv_rmMinBuildH={SAFE_H};\n    PlayerSetColorIndex(8,2,true);'),
    # 1) reaper research when not bought at the armory
    ('    TechTreeUpgradeAllow(1,"RM4_Shrapnel",true);\n}',
     '    TechTreeUpgradeAllow(1,"RM4_Shrapnel",true);\n'
     '    // 0.5.2: reaper armory items not bought are researched in the mission (Barracks Tech Lab).\n'
     + ''.join(f'    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",{n - 1}),true);\n    TechTreeUpgradeAllow(1,"{up}",true);\n'
               for bid, up, n, *_ in RESEARCH)
     + '    TechTreeUpgradeAllow(1,"ReaperSpeed",true);\n'
     '    TechTreeUpgradeAllow(1,"RMR_ReaperUnlocked",true);\n'
     '    if (TechTreeUpgradeCount(1,"RMR_ReaperUnlocked",c_techCountQueuedOrBetter)==0 && TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",1))) {\n'
     '        TechTreeUpgradeAddLevel(1,"RMR_ReaperUnlocked",1);\n'
     '    }\n}'),
]


def sub1(t, a, b, n=1):
    assert t.count(a) == n, (a[:80], t.count(a))
    return t.replace(a, b)


def in_unit(t, unit, a, b):
    m = re.search(r'<CUnit id="' + unit + r'">.*?</CUnit>', t, re.S)
    body = m.group(0)
    assert body.count(a) == 1, (unit, a)
    return t[:m.start()] + body.replace(a, b) + t[m.end():]


def icons(files, m):
    p = f'{m}.SC2Map/{GD}'
    u = files[p + 'unitdata.xml'].decode('utf-8')
    u = in_unit(u, 'HammerSecurity', '<LayoutButtons Face="RMP_MarauderLifeBoost" Type="Passive" Requirements="RMP_HaveMarauderLifeBoost" Row="1" Column="3" />', '')
    for f in ('BearclawNozzles', 'FirebatJuggernautPlating'):
        u = in_unit(u, 'DevilDog', re.search(r'<LayoutButtons Face="RMP_%s"[^>]*/>' % f, u).group(0), '')
    files[p + 'unitdata.xml'] = u.encode('utf-8')
    r = files[p + 'requirementdata.xml'].decode('utf-8')
    r = sub1(r, '<CRequirement id="RMP_HavePunisherGrenades"><NodeArray index="Show" Link="RMP_DonePunisherGrenades" /></CRequirement>',
             '<CRequirement id="RMP_HavePunisherGrenades"><NodeArray index="Show" Link="RMP_ShowPunisherGrenades" /></CRequirement>')
    files[p + 'requirementdata.xml'] = r.encode('utf-8')
    n = files[p + 'requirementnodedata.xml'].decode('utf-8')
    n = sub1(n, '</Catalog>',
             '<CRequirementCountUpgrade id="RMP_ArmoryJackhammer"><Count Link="JackhammerConcussionGrenades" State="CompleteOnly" /></CRequirementCountUpgrade>'
             '<CRequirementNot id="RMP_NoArmoryJackhammer"><OperandArray index="0" value="RMP_ArmoryJackhammer" /></CRequirementNot>'
             '<CRequirementAnd id="RMP_ShowPunisherGrenades"><OperandArray value="RMP_DonePunisherGrenades" /><OperandArray value="RMP_NoArmoryJackhammer" /></CRequirementAnd>\n</Catalog>')
    files[p + 'requirementnodedata.xml'] = n.encode('utf-8')


def reaper(files):
    p = M5 + GD
    files[p + 'upgradedata.xml'] = merge(files[p + 'upgradedata.xml'], UPGRADES.encode('utf-8'))
    u = files[p + 'unitdata.xml'].decode('utf-8')
    u = in_unit(u, 'MercReaper', '<LayoutButtons Face="JetPack" Type="Passive" AbilCmd="255" Row="2" Column="1" />',
                '<LayoutButtons Face="JetPack" Type="Passive" AbilCmd="255" Row="2" Column="1" />'
                '<LayoutButtons Face="U238Rounds" Type="Passive" AbilCmd="255" Requirements="UseReaperU238Rounds" Row="2" Column="2" />')
    m = re.search(r'<CUnit id="BarracksTechLab">\s*<AbilArray[^>]*/>\s*<CardLayouts index="0">', u)
    u = u[:m.end()] + ''.join(f'<LayoutButtons Face="{bid}" Type="AbilCmd" AbilCmd="RM3_TechResearch,Research{n}" Row="{r}" Column="{c}" />'
                              for bid, up, n, r, c, *_ in RESEARCH) + u[m.end():]
    files[p + 'unitdata.xml'] = u.encode('utf-8')
    a = files[p + 'abildata.xml'].decode('utf-8')
    m = re.search(r'<CAbilResearch id="RM3_TechResearch">.*?</CAbilResearch>', a, re.S)
    for _, _, n, *_ in RESEARCH: assert f'index="Research{n}"' not in m.group(0)
    add = ''.join(f'<InfoArray index="Research{n}" Time="60" Upgrade="{up}"><Resource index="Minerals" value="100" />'
                  f'<Resource index="Vespene" value="100" /><Button DefaultButtonFace="{bid}" State="Available" Requirements="{bid}Learn" /></InfoArray>'
                  for bid, up, n, *_ in RESEARCH)
    a = a[:m.start()] + m.group(0).replace('</CAbilResearch>', add + '</CAbilResearch>') + a[m.end():]
    files[p + 'abildata.xml'] = a.encode('utf-8')
    b = files[p + 'buttondata.xml'].decode('utf-8')
    b = sub1(b, '</Catalog>', ''.join(f'<CButton id="{bid}"><Icon value="{icon}" /><Name value="Button/Name/{bid}" /><Tooltip value="Button/Tooltip/{bid}" />'
                                      f'<TooltipFlags index="ShowLevel" value="0" /></CButton>' for bid, up, n, r, c, hk, icon, *_ in RESEARCH) + '\n</Catalog>')
    files[p + 'buttondata.xml'] = b.encode('utf-8')
    r = files[p + 'requirementdata.xml'].decode('utf-8')
    r = sub1(r, '</Catalog>', ''.join(f'<CRequirement id="{bid}Learn"><NodeArray index="Show" Link="{bid}Show" /></CRequirement>' for bid, *_ in RESEARCH) + '\n</Catalog>')
    files[p + 'requirementdata.xml'] = r.encode('utf-8')
    nd = files[p + 'requirementnodedata.xml'].decode('utf-8')
    nd = sub1(nd, '</Catalog>', ''.join(
        f'<CRequirementCountUpgrade id="{bid}Queued"><Count Link="{up}" State="QueuedOrBetter" /></CRequirementCountUpgrade>'
        f'<CRequirementNot id="{bid}NotQueued"><OperandArray index="0" value="{bid}Queued" /></CRequirementNot>'
        f'<CRequirementCountUpgrade id="{bid}Gate"><Count Link="RMR_ReaperUnlocked" State="CompleteOnly" /></CRequirementCountUpgrade>'
        f'<CRequirementAnd id="{bid}Show"><OperandArray value="{bid}NotQueued" /><OperandArray value="{bid}Gate" /></CRequirementAnd>'
        for bid, up, *_ in RESEARCH) + '\n</Catalog>')
    files[p + 'requirementnodedata.xml'] = nd.encode('utf-8')
    ko = files[M5 + KO].decode('utf-8')
    nl = '\r\n' if '\r\n' in ko else '\n'
    add = []
    for bid, up, n, r, c, hk, icon, kn, en, kd, ed in RESEARCH:
        assert f'Button/Name/{bid}=' not in ko
        add += [f'Button/Name/{bid}={kn} /// {en}', f'Button/Tooltip/{bid}={kd}{NOTE[0]} /// {ed}{NOTE[1]}']
    files[M5 + KO] = (ko.rstrip('\r\n') + nl + nl.join(add) + nl).encode('utf-8')
    for loc in ['kokr'] + V35.OTHER_LOCALES:
        hp = f'{M5}{loc}.sc2data/localizeddata/gamehotkeys.txt'
        d = files[hp]
        t = d.decode('utf-8-sig')
        hn = '\r\n' if '\r\n' in t else '\n'
        t = t.rstrip('\r\n') + hn + hn.join(f'Button/Hotkey/{bid}={hk}' for bid, up, n, r, c, hk, *_ in RESEARCH) + hn
        files[hp] = t.encode('utf-8-sig' if d.startswith(b'\xef\xbb\xbf') else 'utf-8')


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for m in AWAY_MAPS:
            s = f'{m}.SC2Map/mapscript.galaxy'
            t = files[s].decode('utf-8')
            nl = '\r\n' if '\r\n' in t else '\n'
            t = t.replace('\r\n', '\n')
            for a, b in AWAY:
                t = sub1(t, a, b)
            if m == 'TTosh01':
                for a, b in M5_SCRIPT:
                    t = sub1(t, a, b)
            files[s] = t.replace('\n', nl).encode('utf-8')
        for m in ICON_MAPS: icons(files, m)
        reaper(files)
        V35.gate('kokr', files[M5 + KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M5}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[M5 + KO])
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        import xml.etree.ElementTree as ET
        for n, d in files.items():
            if n.endswith('.xml'): ET.fromstring(d)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n.startswith(('TRaynor01', 'TRaynor02')): assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
