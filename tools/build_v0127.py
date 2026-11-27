#!/usr/bin/env python3
"""0.12.6 -> 0.12.7: 용병 공방업 누락 보정 (사용자 2026-11-27 "내쪽 용병들 업그레이드 않되있는 경우 있던데 파악좀해줘").

데이터 조사(층별 업그레이드 EffectArray 합치기, 부모 상속 포함)로 확인한 누락:
  - 스키비의 천사(MercMedic): 2~12번(10번 탈옥 제외) 보병 장갑 1~3단계·바나듐판 1~3단계에 줄이 없음 → 장갑 업그레이드를 못 받음.
  - 코랄의 후예(RMK_MarineMengsk): 1·2번 맵에 보병 무기·장갑(및 울트라 축전기·바나듐판) 줄이 없음.
  나머지 레이너 용병은 모두 연결돼 있음.
보정: 다른 용병과 같은 줄을 맵 데이터에 넣는다 — 부모 TerranInfantryWeapons/Armors(단계마다 상속)와
울트라 축전기판(공속 +0.05 포함)·바나듐판(생명력 ×1.05 포함). 맵에 이미 정의가 있으면 첫 정의 안에 넣고, 없으면 부분 정의를 새로 만든다.
Game not run.

Usage: python3 tools/build_v0127.py <0.12.6 zip> <new output zip>
"""
import argparse, copy, re, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

OLD, NEW = b'version=0.12.6', b'version=0.12.7'
G = '.SC2Map/base.sc2data/gamedata/upgradedata.xml'
MEDIC_MAPS = ['TRaynor02', 'TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04']
RMK_MAPS = ['TRaynor01', 'TRaynor02']


def ea(ref, val, op=None):
    o = f' Operation="{op}"' if op else ''
    return f'<EffectArray{o} Reference="{ref}" Value="{val}" />'


def armor_lines(u):
    return [ea(f'Unit,{u},LifeArmor', 1), ea(f'Unit,{u},LifeArmorLevel', 1)]


def vp_lines(u):
    return armor_lines(u) + [ea(f'Unit,{u},LifeMax', '1.05', 'Multiply'), ea(f'Unit,{u},LifeStart', '1.05', 'Multiply')]


RMK_W = [ea('Effect,RMK_MarineMengskGaussRifleDamage,Amount', 1), ea('Effect,RMK_MarineMengskGaussRifleDamageUpgrade,Amount', 1),
         ea('Weapon,RMK_MarineMengskGaussRifle,Level', 1)]
RMK_UC = RMK_W + [ea('Weapon,RMK_MarineMengskGaussRifle,RateMultiplier', '0.05')]


def add_lines(t, uid, lines, m):
    """Put lines into the first non-self-closing definition of uid in this file, or append a partial definition."""
    mm = re.search(r'<CUpgrade\b[^>]*\bid="%s"(?:[^>]*[^/])?>' % uid, t)
    body = '\n'.join('        ' + l for l in lines) + '\n'
    if mm:
        end = t.index('</CUpgrade>', mm.end())
        blk = t[mm.end():end]
        for l in lines:
            ref = re.search(r'Reference="([^"]+)"', l).group(1)
            assert f'Reference="{ref}"' not in blk, (m, uid, ref)
        return t[:end] + body + '    ' + t[end:]
    k = t.rindex('</Catalog>')
    return t[:k] + f'    <CUpgrade id="{uid}">\n{body}    </CUpgrade>\n' + t[k:]


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in sorted(set(MEDIC_MAPS) | set(RMK_MAPS)):
            k = m + G; t = files[k].decode('utf-8')
            plan = {}
            if m in MEDIC_MAPS:
                plan.setdefault('TerranInfantryArmors', []).extend(armor_lines('MercMedic'))
                for n in (1, 2, 3):
                    plan.setdefault(f'TerranInfantryArmorsVanadiumPlatingLevel{n}', []).extend(vp_lines('MercMedic'))
            if m in RMK_MAPS:
                plan.setdefault('TerranInfantryWeapons', []).extend(RMK_W)
                plan.setdefault('TerranInfantryArmors', []).extend(armor_lines('RMK_MarineMengsk'))
                for n in (1, 2, 3):
                    plan.setdefault(f'TerranInfantryWeaponsUltraCapacitorsLevel{n}', []).extend(RMK_UC)
                    plan.setdefault(f'TerranInfantryArmorsVanadiumPlatingLevel{n}', []).extend(vp_lines('RMK_MarineMengsk'))
            for uid, lines in plan.items():
                t = add_lines(t, uid, lines, m)
            E.fromstring(t.encode('utf-8'))
            files[k] = t.encode('utf-8'); changed.add(k)
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
