#!/usr/bin/env python3
"""Build CCM 0.3.3 from 0.3.2: mission 3 ally buildings/workers use co-op looks.

User rule (2026-10-17): 정화자 = 피닉스 협동전 정화자 외형, 원시저그 = 데하카 협동전 원시 외형 (유닛·건물·일꾼).
Mission 3 enemies are Zerg, so models are swapped only on ally-owned units: the script gives
players 10/11 structures and workers a hidden marker behavior and the actor swaps the model.
Model definitions are copied from the co-op data (coop/fenix, coop/dehaka) without sound events.

Usage: python3 tools/build_v033.py <0.3.2 zip> <new output zip>
"""
import argparse
import copy
import re
import zipfile
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD, NEW = b'version=0.3.2', b'version=0.3.3'
M3 = 'TRaynor03.SC2Map/'
GD = M3 + 'base.sc2data/gamedata/'
MARK = 'RM3_AllySkin'
# actor -> co-op model (source commander)
SWAP = {
    'Nexus': ('Nexus_Purifier_COOP', 'fenix'),
    'Gateway': ('Gateway_Purifier_COOP', 'fenix'),
    'Assimilator': ('Assimilator_Purifier_COOP', 'fenix'),
    'AssimilatorRich': ('Assimilator_Purifier_COOP', 'fenix'),
    'Probe': ('Probe_Purifier_Collection', None),  # defined in Liberty.SC2Mod
    'Hatchery': ('DehakaHatchery', 'dehaka'),
    'SpawningPool': ('DehakaBarracks', 'dehaka'),
    'Extractor': ('DehakaPrimalExtractor', 'dehaka'),
    'ExtractorRich': ('DehakaPrimalExtractor', 'dehaka'),
    'Drone': ('Drone_Primal_Collection', 'dehaka'),
}

SKIN_FUNC = '''void gf_m3_Skin (int p) {
    unitgroup g;
    unit u;
    int i;
    // Ally-only co-op look; enemy Zerg keep the normal models.
    g=UnitGroup(null,p,RegionEntireMap(),UnitFilter(0,0,0,(1 << (c_targetFilterUnderConstruction - 32))),0);
    i=UnitGroupCount(g,c_unitCountAll);
    for (;i>0;i-=1) {
        u=UnitGroupUnit(g,i);
        if (!UnitHasBehavior2(u,"RM3_AllySkin")) { UnitBehaviorAdd(u,"RM3_AllySkin",u,1); }
    }
}

bool gt_m3_Tick_Func (bool testConds,bool runActions) {'''
OLD_HALL = '    CatalogFieldValueSet(c_gameCatalogActor,"Hatchery","Model",11,"RM3_PrimalHallModel");\n'
TICK_CALL = '    gf_m3_Attack(10);\n'


def coop_model(ident, commander):
    d = (ROOT / 'coop' / commander / 'gamedata' / 'modeldata.xml').read_text(encoding='utf-8')
    m = re.search(r'<CModel id="%s"[^>]*?(?:/>|>.*?</CModel>)' % re.escape(ident), d, re.S)
    el = E.fromstring(m[0])
    for child in list(el):
        if child.tag in ('Events', 'LowQualityModel', 'PlanetPanelCamera', 'TechPurchaseCamera', 'UnitGlossaryCamera'): el.remove(child)
    return E.tostring(el, encoding='unicode')


def models(data):
    text = data.decode('utf-8')
    add = ''
    for ident, src in sorted({v for v in SWAP.values() if v[1]}):
        assert f'<CModel id="{ident}"' not in text, ident
        add += coop_model(ident, src)
    return text.replace('</Catalog>', add + '</Catalog>', 1).encode('utf-8')


def actors(data):
    text = data.decode('utf-8')
    add = ''.join(f'<CActorUnit id="{a}"><On Terms="Behavior.{MARK}.On" Send="ModelSwap {m}" /></CActorUnit>'
                  for a, (m, _) in SWAP.items())
    return text.replace('</Catalog>', add + '</Catalog>', 1).encode('utf-8')


def behaviors(data):
    text = data.decode('utf-8')
    assert MARK not in text
    add = f'<CBehaviorBuff id="{MARK}"><InfoFlags index="Hidden" value="1" /></CBehaviorBuff>'
    return text.replace('</Catalog>', add + '</Catalog>', 1).encode('utf-8')


def script(data):
    text = data.decode('utf-8')
    head = 'bool gt_m3_Tick_Func (bool testConds,bool runActions) {'
    assert text.count(head) == 1 and text.count(OLD_HALL) == 1 and text.count(TICK_CALL) == 1
    text = text.replace(head, SKIN_FUNC, 1)
    text = text.replace(OLD_HALL, '', 1)
    text = text.replace(TICK_CALL, '    gf_m3_Skin(10);\n    gf_m3_Skin(11);\n' + TICK_CALL, 1)
    return text.encode('utf-8')


FIX = {GD + 'modeldata.xml': models, GD + 'actordata.xml': actors,
       GD + 'behaviordata.xml': behaviors, M3 + 'mapscript.galaxy': script,
       'metadata.txt': lambda d: d.replace(OLD, NEW)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    data = prev.read(info.filename)
                    if info.filename in FIX:
                        data = FIX[info.filename](data)
                        if info.filename.endswith('.xml'): E.fromstring(data)
                    out.writestr(copy.copy(info), data)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for name in prev.namelist():
                    if name not in FIX: assert out.read(name) == prev.read(name), name
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
