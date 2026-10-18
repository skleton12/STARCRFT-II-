#!/usr/bin/env python3
"""Build CCM 0.4.17 from 0.4.16: 레이너가 보병 공격·방어 업그레이드를 마치면 동맹도 같은 단계 (사용자 지시 2026-10-18).

3·4번 맵. 레이너(1)의 보병 무기·장갑 단계(공학 연구소 원작 연구, 히페리온 울트라 커패시터·바나듐 장갑판 판도 포함)를 따라
  정화자 → ProtossGroundWeaponsLevelN / ProtossGroundArmorsLevelN
  원시저그 → DehakaPrimalWeaponsLevelN / DehakaPrimalArmorLevelN (협동전 원시 공격·원시 갑피)
같은 단계까지 2초마다 채운다 (이미 있으면 다시 주지 않음).
데이터: 협동전·공허 업그레이드에서 이 맵에 있는 동맹 유닛·무기·효과 항목만 골라 넣는다. 정화자 파수병·동력기 방어력은 직접 +1씩.

Usage: python3 tools/build_v0417.py <0.4.16 zip> <new output zip>
"""
import argparse, copy, os, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / 'source'
OLD, NEW = b'version=0.4.16', b'version=0.4.17'
LAYERS = ['void.sc2mod', 'voidmulti.sc2mod', 'starcoop/starcoop.sc2mod']
MAPS = {'TRaynor03': (10, 11, 'bool gt_m3_Tick_Func (bool testConds,bool runActions) {', '    gf_m3_Skin(11);\n'),
        'TTychus01': (8, 9, 'bool gt_m4_Tick_Func (bool testConds,bool runActions) {', '    gf_m4_Mercs();\n')}
KO = {f'Upgrade/Name/DehakaPrimalWeaponsLevel{i}': f'원시 공격 - {i}단계 /// Primal Attacks Level {i}' for i in (1, 2, 3)}
KO.update({f'Upgrade/Name/DehakaPrimalArmorLevel{i}': f'원시 갑피 - {i}단계 /// Primal Carapace Level {i}' for i in (1, 2, 3)})
SYNC = '''void gf_rmUpSync (int pp,int pz) {
    int w;
    int a;
    int i;
    string n;
    // Allies match Raynor's infantry weapon/armor levels (user 2026-10-18). Never given twice.
    w=0;
    a=0;
    for (i=1;i<=3;i+=1) {
        n=IntToString(i);
        if (TechTreeUpgradeCount(1,"TerranInfantryWeaponsLevel"+n,c_techCountCompleteOnly)+TechTreeUpgradeCount(1,"TerranInfantryWeaponsUltraCapacitorsLevel"+n,c_techCountCompleteOnly)>0) { w=i; }
        if (TechTreeUpgradeCount(1,"TerranInfantryArmorsLevel"+n,c_techCountCompleteOnly)+TechTreeUpgradeCount(1,"TerranInfantryArmorsVanadiumPlatingLevel"+n,c_techCountCompleteOnly)>0) { a=i; }
    }
    for (i=1;i<=3;i+=1) {
        n=IntToString(i);
        if (i<=w && TechTreeUpgradeCount(pp,"ProtossGroundWeaponsLevel"+n,c_techCountCompleteOnly)==0) { TechTreeUpgradeAddLevel(pp,"ProtossGroundWeaponsLevel"+n,1); }
        if (i<=w && TechTreeUpgradeCount(pz,"DehakaPrimalWeaponsLevel"+n,c_techCountCompleteOnly)==0) { TechTreeUpgradeAddLevel(pz,"DehakaPrimalWeaponsLevel"+n,1); }
        if (i<=a && TechTreeUpgradeCount(pp,"ProtossGroundArmorsLevel"+n,c_techCountCompleteOnly)==0) { TechTreeUpgradeAddLevel(pp,"ProtossGroundArmorsLevel"+n,1); }
        if (i<=a && TechTreeUpgradeCount(pz,"DehakaPrimalArmorLevel"+n,c_techCountCompleteOnly)==0) { TechTreeUpgradeAddLevel(pz,"DehakaPrimalArmorLevel"+n,1); }
    }
}

'''


def map_ids(z, m):
    ids = set()
    for n in z.namelist():
        if n.startswith(f'{m}.SC2Map/base.sc2data/gamedata/') and n.endswith('.xml'):
            ids |= {e.get('id') for e in E.fromstring(z.read(n)) if e.get('id')}
    return ids


def entries(uid, ids):
    out = []
    for L in LAYERS:
        f = SRC / L / 'base.sc2data/gamedata/upgradedata.xml'
        if not f.exists(): continue
        for e in E.parse(f).getroot():
            if e.get('id') != uid: continue
            for c in e:
                if c.tag == 'EffectArray':
                    p = c.get('Reference', '').split(',')
                    if len(p) >= 2 and p[1] in ids: out.append(copy.deepcopy(c))
                elif c.tag == 'AffectedUnitArray' and c.get('value') in ids:
                    out.append(copy.deepcopy(c))
    return out


def upgrades(d, ids):
    root = E.fromstring(d)
    have = {e.get('id') for e in root}
    for lv in (1, 2, 3):
        for kind, own in (('Weapons', False), ('Armors', True)):
            uid = f'ProtossGroundWeaponsLevel{lv}' if kind == 'Weapons' else f'ProtossGroundArmorsLevel{lv}'
            assert uid not in have
            rec = E.SubElement(root, 'CUpgrade', id=uid)
            for c in entries(uid, ids): rec.append(c)
            if own:
                for u in ('ZealotPurifier', 'RM21_Energizer'):
                    if u in ids:
                        E.SubElement(rec, 'AffectedUnitArray', value=u)
                        E.SubElement(rec, 'EffectArray', Reference=f'Unit,{u},LifeArmor', Value='1')
        for kind in ('Weapons', 'Armor'):
            uid = f'DehakaPrimal{kind}Level{lv}'
            assert uid not in have
            rec = E.SubElement(root, 'CUpgrade', id=uid)
            E.SubElement(rec, 'Race', value='Zerg')
            for c in entries(uid, ids): rec.append(c)
            assert len(rec) > 3, uid
    return E.tostring(root, encoding='utf-8', xml_declaration=True)


def script(d, pp, pz, tick, after):
    crlf = b'\r\n' in d
    t = d.decode('utf-8').replace('\r\n', '\n')
    assert t.count(tick) == 1 and 'gf_rmUpSync' not in t
    t = t.replace(tick, SYNC + tick)
    i = t.index(tick); j = t.index(after, i) + len(after)
    t = t[:j] + f'    gf_rmUpSync({pp},{pz});\n' + t[j:]
    return (t.replace('\n', '\r\n') if crlf else t).encode('utf-8')


def strings(d, V35):
    text = d.decode('utf-8'); nl = '\r\n' if '\r\n' in text else '\n'
    lines = [l for l in text.split(nl) if l.split('=', 1)[0] not in KO]
    while lines and lines[-1] == '': lines.pop()
    return nl.join(lines + [f'{k}={v}' for k, v in KO.items()] + ['']).encode('utf-8')


def build(source, output):
    import sys; sys.path.insert(0, str(HERE)); import build_v035 as V35
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for m, (pp, pz, tick, after) in MAPS.items():
            ids = map_ids(prev, m)
            up = f'{m}.SC2Map/base.sc2data/gamedata/upgradedata.xml'
            files[up] = upgrades(files[up], ids)
            sp = f'{m}.SC2Map/mapscript.galaxy'
            files[sp] = script(files[sp], pp, pz, tick, after)
            ko = f'{m}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'
            files[ko] = strings(files[ko], V35)
            V35.gate('kokr', files[ko])
            changed |= {up, sp, ko}
            for loc in V35.OTHER_LOCALES:
                k = f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'
                files[k] = V35.other_locale(files[ko]); changed.add(k)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
