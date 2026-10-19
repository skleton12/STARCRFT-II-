#!/usr/bin/env python3
"""Build CCM 0.4.26 from 0.4.25: 파편탄이 나가지 않던 것 (4번 TTychus01).

사용자 보고 (2026-10-19): 불곰 파편탄이 안 나옴.
  원인: 0.4.3 이름 바꾸기에서 검증기 id RM4_HaveIncapacitator가 그대로 남아, 파편 효과가 찾는
  RM4_HaveShrapnel이 정의되지 않았다 → 효과가 실행되지 않음. id를 RM4_HaveShrapnel로 고친다.
  또 파편 발사·명중 연출과 소리가 없었다 → 멩스크 협동전 MarauderMengskShrapnel 연출을 우리 효과에 연결한다.

Usage: python3 tools/build_v0426.py <0.4.25 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.25', b'version=0.4.26'
GD = 'TTychus01.SC2Map/base.sc2data/gamedata/'
MODELS = ('<CModel id="MarauderMengskShrapnelImpact" parent="ImpactFX"><Model value="Assets\\Effects\\Terran\\Nova_PenetratingShot_Impact\\Nova_PenetratingShot_Impact.m3" />'
          '<ScaleMax value="0.500000,0.500000,0.500000" /><ScaleMin value="0.500000,0.500000,0.500000" /></CModel>'
          '<CModel id="MarauderMengskShrapnelLaunch" parent="LaunchFX"><Model value="Assets\\COOP\\Mengsk\\Effects\\Marauder_Mengsk_COOP_Shrapnel\\Marauder_Mengsk_COOP_Shrapnel.m3" />'
          '<ScaleMax value="0.650000,0.650000,0.650000" /><ScaleMin value="0.650000,0.650000,0.650000" /></CModel>')
ACTORS = ('<CActorModel id="RM4_ShrapnelImpact" parent="ModelAnimationStyleOneShot"><On Terms="Effect.RM4_ShrapnelDamage.Start; At Target" Send="Create" />'
          '<Model value="MarauderMengskShrapnelImpact" /><Host Subject="_Selectable" /><HostSiteOps Ops="SOpAttachCenter" />'
          '<ModelFlags index="AllowHitTest" value="0" /><ModelFlags index="AutomateGlobalLoops" value="1" /></CActorModel>'
          '<CActorModel id="RM4_ShrapnelLaunch"><Flags index="SuppressSaveLoad" value="1" /><On Terms="Effect.RM4_ShrapnelSearch.Start; At Target" Send="Create" />'
          '<On Terms="ActorCreation" Send="$Birth" /><On Terms="AnimDone; AnimName Birth" Send="Destroy" /><Model value="MarauderMengskShrapnelLaunch" />'
          '<Host Subject="_Unit" /><HostSiteOps Ops="SOpAttachCenterSoft SOpForwardCasterPointInverted" HoldPosition="1" HoldRotation="1" />'
          '<ModelFlags index="AllowHitTest" value="0" /></CActorModel>'
          '<CActorSound id="RM4_ShrapnelSound" parent="SoundOneShot"><On Terms="Effect.RM4_ShrapnelSearch.Start; At Caster" Send="Create" />'
          '<Sound value="MarauderMengskShrapnel" /></CActorSound>')
SOUND = ('<CSound id="MarauderMengskShrapnel" parent="Combat">'
         + ''.join(f'<AssetArray File="Assets\\Sounds\\Hellfire_Shotgun_0{i}.wav" FacialGroup="" />' for i in range(1, 9))
         + '<Pitch value="-3.000000,0.000000" /><Volume value="-10.000000,-10.000000" /></CSound>')


def add(xml):
    def fn(d):
        assert d.rstrip().endswith(b'</Catalog>')
        i = d.rindex(b'</Catalog>')
        return d[:i] + xml.encode('utf-8') + d[i:]
    return fn


def validator(d):
    a, b = b'id="RM4_HaveIncapacitator"', b'id="RM4_HaveShrapnel"'
    assert d.count(a) == 1
    return d.replace(a, b)


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), GD + 'validatordata.xml': validator,
       GD + 'modeldata.xml': add(MODELS), GD + 'actordata.xml': add(ACTORS), GD + 'sounddata.xml': add(SOUND)}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        for n in FIX: assert n in prev.namelist(), n
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    out.writestr(copy.copy(info), FIX[info.filename](d) if info.filename in FIX else d)
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
                assert b'RM4_HaveIncapacitator' not in b''.join(out.read(n) for n in out.namelist() if n.startswith(GD))
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
