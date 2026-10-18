#!/usr/bin/env python3
"""Build CCM 0.4.9 from 0.4.8: 모드·이식 버튼 단축키 (사용자 요청 2026-10-18 "단축키 넣기").

모드가 만든 버튼(RM*)과 협동전에서 옮긴 버튼은 단축키 문자열(Button/Hotkey/<버튼>)이 맵에 없어서 키가 먹지 않았다.
각 맵에 <언어>.sc2data/localizeddata/gamehotkeys.txt를 넣는다 (12개 언어 같은 내용).
  - 이식 버튼: 원본(협동전·군심·공허) 단축키 파일의 값. RMK_/RM21_ 복제본은 원래 이름의 값.
  - 모드 버튼: 원작 자리에 맞춘 값 (아래 MOD). 자날 기본 층에 이미 있는 버튼은 건드리지 않는다.

Usage: python3 tools/build_v049.py <0.4.8 zip> <new output zip>
"""
import argparse, copy, glob, os, zipfile
import xml.etree.ElementTree as E
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD, NEW = b'version=0.4.8', b'version=0.4.9'
MAPS = ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']
LOCALES = ['kokr', 'enus', 'dede', 'eses', 'esmx', 'frfr', 'itit', 'plpl', 'ptbr', 'ruru', 'zhcn', 'zhtw']
MOD = {  # 기술실: 자극제 T, 전투 방패 C, 레이저 조준 L, 충격탄·억제탄 G, 자기가속 M, 파편탄 R
    'RM3_Stim1': 'T', 'RM3_Stim2': 'T', 'RM3_Stim3': 'T', 'RM3_Shield': 'C', 'RM3_Laser': 'L',
    'RM4_Concussive': 'G', 'RM4_Suppression': 'G', 'RM4_Magrail': 'M', 'RM4_Shrapnel': 'R',
    # 공학 연구소: 보급 벙커 해금 U, 건물 장갑 N. SCV 보급 벙커 건설 Y. 고용소 코랄의 후예 K.
    # 코랄의 후예: 멩스크 자극제(자극제 3단계 버튼) T, 자기가속 탄약 U (협동전 MagrailMunitions 값)
    'RMK_MarineMengskAttackSpeedBoost': 'T', 'RMK_MagrailMunitionsMengsk': 'U',
    'RM3_SupplyBunker': 'U', 'RM3_Armor': 'N', 'RM3_BuildSupplyBunker': 'Y', 'RM3_HireKorhal': 'K',
}


def source_keys():
    keys = {}
    for f in sorted(glob.glob(str(ROOT / 'source/**/gamehotkeys.txt'), recursive=True)):
        for line in open(f, encoding='utf-8-sig', errors='replace'):
            k, sep, v = line.rstrip('\r\n').partition('=')
            if sep and k.startswith('Button/Hotkey/'):
                v = v.split('///')[-1].strip()
                if v: keys.setdefault(k, v)
    return keys


def base_buttons():
    ids = set()
    for layer in ('core.sc2mod', 'liberty.sc2mod', 'liberty.sc2campaign', 'libertystory.sc2campaign'):
        f = ROOT / 'source' / layer / 'base.sc2data/gamedata/buttondata.xml'
        if f.exists(): ids |= {e.get('id') for e in E.parse(f).getroot() if e.tag == 'CButton'}
    return ids


def hotkeys(buttons, keys, base):
    out = {}
    for b in E.fromstring(buttons):
        bid = b.get('id')
        if b.tag != 'CButton' or not bid or bid in base: continue
        hk = b.find('Hotkey')
        name = hk.get('value') if hk is not None and hk.get('value') else f'Button/Hotkey/{bid}'
        stripped = 'Button/Hotkey/' + bid.split('_', 1)[1] if bid.startswith(('RMK_', 'RM21_')) else None
        v = keys.get(name) or (keys.get(stripped) if stripped else None) or MOD.get(bid)
        if v: out[name] = v
    return out


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    keys, base = source_keys(), base_buttons()
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert not any('gamehotkeys' in n.lower() for n in prev.namelist())
        add = {}
        for m in MAPS:
            hk = hotkeys(prev.read(f'{m}.SC2Map/base.sc2data/gamedata/buttondata.xml'), keys, base)
            missing = [k for k in MOD if f'Button/Hotkey/{k}' not in hk and k.encode() in prev.read(f'{m}.SC2Map/base.sc2data/gamedata/buttondata.xml')]
            assert not missing, (m, missing)
            text = ''.join(f'{k}={v}\r\n' for k, v in sorted(hk.items())).encode('utf-8')
            for loc in LOCALES: add[f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamehotkeys.txt'] = text
            print(m, len(hk), 'hotkeys')
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), d.replace(OLD, NEW) if info.filename == 'metadata.txt' else d)
                for n, d in sorted(add.items()): out.writestr(n, d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
