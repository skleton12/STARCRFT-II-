#!/usr/bin/env python3
"""0.4.64 -> 0.4.65: mixed selection cleanup and royal guard shared kill XP.

Mission 4 only. Original Mengsk reference: LibCOMI CM_Mengsk_VeterancyEarned,
SC2GameData 6dd323aae4209a01f110719a00b4e8f7a88389bc: radius 15,
100 XP/supply, heroic zero-supply fallback 800, minimum 1/recipient,
global eligible guards fallback when none are nearby. No mastery/prestige.
"""
import argparse
import copy
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

M4 = 'TTychus01.SC2Map/'
SCRIPT = M4 + 'mapscript.galaxy'
BEHAVIOR = M4 + 'base.sc2data/gamedata/behaviordata.xml'
OLD, NEW = b'version=0.4.64', b'version=0.4.65'

SELECTION = '''// 0.4.65: keep controlled units in mixed selections; allied solo inspection remains possible.
bool gt_m4_PylonDrag_Func (bool testConds,bool runActions) {
    unitgroup sel;
    unitgroup excluded;
    unit u;
    int i;
    int owner;
    bool controlled;
    bool worker;
    if (!runActions) { return true; }
    sel=UnitGroupSelected(1);
    excluded=UnitGroupEmpty();
    controlled=false;
    i=UnitGroupCount(sel,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(sel,i);
        owner=UnitGetOwner(u);
        worker=(owner==8 && UnitGetType(u)=="Probe") || (owner==9 && UnitGetType(u)=="DehakaDrone");
        if (owner==1 || worker) { controlled=true; }
        else if (owner==8 || owner==9) { UnitGroupAdd(excluded,u); }
    }
    if (!controlled) { return true; }
    i=UnitGroupCount(excluded,c_unitCountAll);
    for (;i>0;i-=1) { UnitSelect(UnitGroupUnit(excluded,i),1,false); }
    return true;
}

'''

XP = '''// 0.4.65: Mengsk co-op kill XP sharing, adapted to player 1 and allies 8/9.
// Existing rank thresholds are unchanged. Native per-kill XP is disabled to avoid double credit.
bool gt_m4_GuardXP_Func (bool testConds,bool runActions) {
    unit dead;
    unit u;
    unitgroup army;
    unitgroup eligible;
    unitgroup nearby;
    int killer;
    int i;
    int count;
    string kind;
    string veterancy;
    fixed xp;
    if (!runActions) { return true; }
    dead=EventUnit();
    if (dead==null || EventUnitDamageDeathCheck(c_deathTypeRemove)) { return true; }
    killer=libNtve_gf_KillingPlayer();
    if (killer!=1 && killer!=8 && killer!=9) { return true; }
    if (!UnitFilterMatch(dead,1,UnitFilter(0,0,(1 << c_targetFilterPlayer) | (1 << c_targetFilterAlly) | (1 << c_targetFilterNeutral) | (1 << c_targetFilterStructure) | (1 << c_targetFilterRawResource) | (1 << c_targetFilterHarvestableResource) | (1 << c_targetFilterMissile) | (1 << c_targetFilterDestructible) | (1 << c_targetFilterItem) | (1 << c_targetFilterUncommandable),(1 << (c_targetFilterHallucination - 32))))) { return true; }
    xp=UnitTypeGetProperty(UnitGetType(dead),c_unitPropSuppliesUsed)*100.0;
    if (xp<=0.0 && UnitFilterMatch(dead,1,UnitFilter((1 << c_targetFilterHeroic),0,0,0))) { xp=800.0; }
    if (xp<=0.0) { return true; }
    army=UnitGroup(null,1,RegionEntireMap(),UnitFilter(0,0,0,0),0);
    eligible=UnitGroupEmpty();
    nearby=UnitGroupEmpty();
    i=UnitGroupCount(army,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(army,i);
        if (!UnitIsAlive(u)) { continue; }
        kind=UnitGetType(u);
        if (kind=="MarauderMengsk") { veterancy="RMK_MengskVeterancyMarauderMengsk"; }
        else if (kind=="RMK_MarineMengsk") { veterancy="RMK_MengskVeterancyMarineMengsk"; }
        else { continue; }
        if (!UnitHasBehavior2(u,veterancy) || UnitXPGetCurrentLevel(u,veterancy)>=4) { continue; }
        UnitGroupAdd(eligible,u);
        if (DistanceBetweenPoints(UnitGetPosition(u),UnitGetPosition(dead))<=15.0) { UnitGroupAdd(nearby,u); }
    }
    count=UnitGroupCount(nearby,c_unitCountAlive);
    if (count>0) { eligible=nearby; }
    else { count=UnitGroupCount(eligible,c_unitCountAlive); }
    if (count==0) { return true; }
    xp=MaxF(Round(xp/IntToFixed(count)),1.0);
    for (i=1;i<=count;i+=1) {
        u=UnitGroupUnit(eligible,i);
        if (UnitGetType(u)=="MarauderMengsk") { veterancy="RMK_MengskVeterancyMarauderMengsk"; }
        else { veterancy="RMK_MengskVeterancyMarineMengsk"; }
        UnitXPAddXP(u,veterancy,xp);
    }
    return true;
}

'''


def script(data):
    t = data.decode('utf-8')
    start = t.index('// 0.4.59: an allied (Purifier) Pylon')
    end = t.index('void gf_m4_Init () {', start)
    assert t[start:end].count('bool gt_m4_PylonDrag_Func') == 1
    t = t[:start] + SELECTION + XP + t[end:]
    marker = '    t=TriggerCreate("gt_m4_PylonDrag_Func");'
    assert t.count(marker) == 1
    return t.replace(marker, '    t=TriggerCreate("gt_m4_GuardXP_Func");\n'
                     '    TriggerAddEventUnitDied(t,null);\n' + marker).encode('utf-8')


def behaviors(data):
    root = E.fromstring(data)
    changed = []
    for e in root:
        if e.get('id') in ('RMK_MengskVeterancyMarineMengsk','RMK_MengskVeterancyMarauderMengsk'):
            xp = e.find("XPFraction[@index='Kills']")
            assert xp is not None and xp.get('value') == '1'
            xp.set('value','0')
            changed.append(e.get('id'))
    assert len(changed) == 2
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        changes = {'metadata.txt':prev.read('metadata.txt').replace(OLD,NEW),
                   SCRIPT:script(prev.read(SCRIPT)), BEHAVIOR:behaviors(prev.read(BEHAVIOR))}
        output.parent.mkdir(parents=True,exist_ok=True)
        try:
            with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():out.writestr(copy.copy(info),changes.get(info.filename,prev.read(info.filename)))
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist()==prev.namelist()
                for n in prev.namelist():
                    if n not in changes:assert out.read(n)==prev.read(n),n
        except BaseException:
            output.unlink(missing_ok=True)
            raise
    print(output)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();build(a.source,a.output)
