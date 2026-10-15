#!/usr/bin/env python3
"""자날 기본 모드(Liberty.SC2Mod)의 게임 데이터 XML을 source/에 받는다 (2번 미션 이식 기준층, port_units --liberty-base).

드라이브에서 받은 source/liberty.sc2mod는 행위자·모델·소리만 있어서, 나머지는 SC2Mapster/SC2GameData 공개 사본에서 받는다.
사본은 사용자 설치본과 버전이 다를 수 있다. 이미 있는 파일은 덮어쓰지 않는다.
"""
import os, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEST = os.path.join(ROOT, 'source', 'liberty.sc2mod', 'base.sc2data', 'gamedata')
URL = 'https://raw.githubusercontent.com/SC2Mapster/SC2GameData/master/mods/liberty.sc2mod/base.sc2data/GameData/{}.xml'
FILES = ['AbilData', 'EffectData', 'UnitData', 'WeaponData', 'BehaviorData', 'ValidatorData', 'RequirementData',
         'RequirementNodeData', 'UpgradeData', 'ButtonData', 'MoverData']


def main():
    os.makedirs(DEST, exist_ok=True)
    for f in FILES:
        out = os.path.join(DEST, f.lower() + '.xml')
        if os.path.exists(out):
            print('있음', out)
            continue
        with urllib.request.urlopen(URL.format(f), timeout=120) as r:
            open(out, 'wb').write(r.read())
        print('받음', out)


if __name__ == '__main__':
    main()
