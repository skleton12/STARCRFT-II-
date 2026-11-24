#!/usr/bin/env python3
"""0.9.5 -> 0.9.6 (사용자 2026-11-24 "탈리스가 움직이다 마는 버그", "공생충 저거 원래 표식 같은거 나오지 않나 건물 오염되는").

(1) 3~9번 피닉스 용사 탈리스(FenixTalisAdept): 협동전 전술 AI 함수 AIThinkFenixTalisAdept가 자날 라이브러리에 없다
    (다른 이식 유닛은 모두 자날에 있는 함수). 그 줄을 지운다 — 탈리스는 일반 사도처럼 엔진·스크립트 명령만 따른다.
    check_release가 '정의 없는 전술 AI 함수'를 검사한다. 원인 후보 제거이며 게임 확인 필요.
(2) 4~9번 건물 감염(RM9_InfestEnemy/Friend): 자날 감시군주 오염(Contaminate)과 같은 감염 연출 모델
    (ContaminateModel = Infestation.m3)과 소리를 건물에 붙인다 (새 액터 RM9_InfestFX·RM9_InfestSound). Game not run.

Usage: python3 tools/build_v096.py <0.9.5 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.9.5', b'version=0.9.6'
TALIS_MAPS = ['TRaynor03', 'TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02']
ABIL_MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02']
G = '{}.SC2Map/base.sc2data/gamedata/{}'
FX = (b'<CActorModel id="RM9_InfestFX" parent="ModelAddition"><Model value="ContaminateModel" /><AutoScaleFactor value="0.500000" />'
      b'<Inherits index="TintColor" value="0" /><AcceptedHostedPropTransfers index="BaseModelScale" value="0" />'
      b'<Remove Terms="ActorOrphan" Send="Destroy" />'
      b'<On Terms="Behavior.RM9_InfestEnemy.On" Send="Create" /><On Terms="Behavior.RM9_InfestFriend.On" Send="Create" />'
      b'<On Terms="Behavior.RM9_InfestEnemy.Off" Send="AnimBracketStop BSD" /><On Terms="Behavior.RM9_InfestFriend.Off" Send="AnimBracketStop BSD" />'
      b'<On Terms="ActorOrphan" Send="AnimBracketStop BSD" /><HostSiteOps Ops="SOpAttachCenterSoft" /></CActorModel>'
      b'<CActorSound id="RM9_InfestSound" parent="SoundOneShot"><Sound value="Corruptor_CorruptionImpact" />'
      b'<On Terms="Behavior.RM9_InfestEnemy.On" Send="Create" /><On Terms="Behavior.RM9_InfestFriend.On" Send="Create" /></CActorSound>\n</Catalog>')


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in TALIS_MAPS:
            k = G.format(m, 'unitdata.xml'); t = files[k]
            n = len(re.findall(rb'\s*<TacticalAIThink value="AIThinkFenixTalisAdept"\s*/>', t))
            assert n == 1, (m, n)
            files[k] = re.sub(rb'\s*<TacticalAIThink value="AIThinkFenixTalisAdept"\s*/>', b'', t); changed.add(k)
        for m in ABIL_MAPS:
            k = G.format(m, 'actordata.xml'); t = files[k].rstrip()
            assert b'RM9_InfestFX' not in t and t.endswith(b'</Catalog>')
            files[k] = t[:-len(b'</Catalog>')] + FX + b'\n'; changed.add(k)
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
    print(out, len(changed))


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
