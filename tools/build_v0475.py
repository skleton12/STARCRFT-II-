#!/usr/bin/env python3
"""0.4.74 -> 0.4.75: 코랄의 후예 '자기 가속 탄약'(레일건) 오류 구 수정, 흰 반구 진단 제거 (3·4번).

사용자 진단(0.4.70 진단판 + 관찰, 2026-10-23): 코랄의 후예가 레일건처럼 생긴 능력을 쓸 때 흰 오류 구가 생긴다.
원인: 탄환 유닛 RMK_MagrailMunitionMissileMengsk 의 이동기 WarHoundWeapon 이 군단의 심장 mod(swarm.sc2mod)에만 있고
이 맵들의 의존성(Liberty)에는 없다 → 탄환이 날아가지 못하고 그 자리에 남는다. 게다가 탄환·발사·명중 액터도 없어 오류 구로 보인다.
수정: swarm.sc2mod 의 WarHoundWeapon 이동기 정의를 맵에 옮기고, 원작 노바 레일건(MagrailMunition) 액터 구조를 복제 —
  CActorMissile RMK_MagrailMunitionInvisibleMissile (unitName=RMK 탄환, 모델 Invisible)
  CActorAction RMK_MagrailMunition (발사 MagrailMunition_Launch, 명중 MagrailMunition_Impact, 소리 RailGun_*)
모델·소리 정의가 없는 맵(1~3번)에는 4번 맵의 정의를 그대로 옮긴다. 1·2번은 코랄의 후예 정의만 있지만 같이 고친다. 0.4.70 진단 스크립트는 뺀다.

Usage: python3 tools/build_v0475.py <0.4.74 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.74', b'version=0.4.75'
ACTORS = ('<CActorMissile id="RMK_MagrailMunitionInvisibleMissile" parent="GenericAttackMissile" unitName="RMK_MagrailMunitionMissileMengsk">'
          '<Model value="Invisible" /></CActorMissile>'
          '<CActorAction id="RMK_MagrailMunition" parent="GenericAttack" effectImpact="RMK_MagrailMunitionsMengskDamage" '
          'effectLaunch="RMK_MagrailMunitionsMengskLaunchMissile"><BeamScope value="Caster" />'
          '<ImpactMap index="None" Model="MagrailMunition_Impact" Sound="RailGun_Impact" />'
          '<LaunchAssets Model="MagrailMunition_Launch" Sound="RailGun_Launch" />'
          '<LaunchAttachQuery Methods="SetC 0" /></CActorAction>')
MOVER = ('<CMoverMissile id="WarHoundWeapon" parent="MissileDefault"><MotionPhases index="0"><Driver value="Guidance" />'
         '<Acceleration value="3200" /><MaxSpeed value="40" /><ClearanceAcceleration value="75" /><ActorTracking value="Actual" />'
         '<Outro value="-1" /><RotationLaunchActorType value="LaunchToTarget" /><YawPitchRoll value="719.2968" /></MotionPhases></CMoverMissile>')
COPY = {'modeldata': ['MagrailMunition_Impact', 'MagrailMunition_Launch'],
        'sounddata': ['RailGun_Impact', 'RailGun_Launch']}


def block(t, i):
    m = re.search(rf'<(C\w+) id="{i}"[^>]*?(?:/>|>.*?</\1>)', t, re.S)
    return m.group(0) if m else None


def append(t, extra):
    i = t.rindex('</Catalog>')
    return t[:i] + extra + t[i:]


def strip_diag(t):
    a = t.index('\n// 0.4.70 diagnostic: white dome near mercenaries.')
    b = t.index('\nvoid gf_m4_Init () {', a)
    t = t[:a] + t[b:]
    t, n = re.subn(r'    t=TriggerCreate\("gt_m4_DomeDiag_Func"\);\n(?:    TriggerAddEventUnitBehaviorChange\(t,null,"[^"]+",c_unitBehaviorChange\w+\);\n)+', '', t)
    assert n == 1 and 'DomeDiag' not in t
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        src = {k: files[f'TTychus01.SC2Map/base.sc2data/gamedata/{k}.xml'].decode('utf-8') for k in COPY}
        changed = {'metadata.txt'}
        for m in ['TRaynor01', 'TRaynor02', 'TRaynor03', 'TTychus01']:
            g = f'{m}.SC2Map/base.sc2data/gamedata/'
            a = files[g + 'actordata.xml'].decode('utf-8')
            assert 'RMK_MagrailMunitionInvisibleMissile' not in a and 'id="RMK_MagrailMunitionMissileMengsk"' in files[g + 'unitdata.xml'].decode('utf-8')
            files[g + 'actordata.xml'] = append(a, ACTORS).encode('utf-8'); changed.add(g + 'actordata.xml')
            mv = files[g + 'moverdata.xml'].decode('utf-8')
            assert 'id="WarHoundWeapon"' not in mv
            files[g + 'moverdata.xml'] = append(mv, MOVER).encode('utf-8'); changed.add(g + 'moverdata.xml')
            for k, ids in COPY.items():
                t = files[g + k + '.xml'].decode('utf-8'); add = ''
                for i in ids:
                    if block(t, i) is None:
                        b = block(src[k], i); assert b, i; add += b
                if add:
                    files[g + k + '.xml'] = append(t, add).encode('utf-8'); changed.add(g + k + '.xml')
        s = 'TTychus01.SC2Map/mapscript.galaxy'
        files[s] = strip_diag(files[s].decode('utf-8')).encode('utf-8'); changed.add(s)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output, sorted(changed))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
