#!/usr/bin/env python3
"""Build CCM 0.4.63 from 0.4.62: 정화자 유닛 전용 협동전 업그레이드는 그 유닛이 해금됐을 때만 (4번, 사용자 지시 2026-10-21).

사용자: "정화자는 업그레이드는 해금된 유닛들만 해금되게" — 선택 "유닛 전용 업그레이드".
레이너 해금 k (gf_m4_Unl, tools/build_v0442.py) 가 참이면 8번 정화자에게 그 유닛의 협동전 업그레이드를 한 번 준다.
해금 안 된 유닛의 업그레이드는 주지 않는다. 기본 유닛(사도)은 처음부터. 맵 데이터에 효과가 있는 것만 넣는다:
  항상     사도 그림자 생성 AdeptFenixShadeSpawn (피닉스 협동전 대의회)
  k2 거신  화염 광선 ColossusFireBeam (카락스), 열 창 사거리 ExtendedThermalLance
  k3 분열기 은폐 모듈 DisruptorCloak (피닉스)
  k4 신기루 위상 장갑 MiragePhaseArmor (카락스), 음이온 파동 수정 PhoenixRangeUpgrade (신기루 PhoenixPurifier 포함)
  k5 정찰기 사거리 FenixScoutWeaponRange (피닉스 함대 신호소)
  k7 폭풍함 분해 TempestDisintegration (카락스)
빼는 것: DisruptorSecondExplosion (피닉스 분열기 효과 FenixPurificationNovaCP 가 맵에 없음), VoidPhoenix*·VoidColossusFireBeam
  (공허 캠페인 선택지, 생산 유닛을 바꿈), 용사·영웅 전투복 전용. 선동자·불멸자·우주모함·보전기·동력기 연구
  (그림자 포, 수리 비행정, 보호장 강화, 교화 등)는 맵에 이식되지 않아 이번에 넣지 않는다.
틱마다 부르지만 업그레이드가 0일 때만 1을 더한다 (한 번만 적용).

Usage: python3 tools/build_v0463.py <0.4.62 zip> <new output zip>
"""
import argparse, copy, zipfile
from pathlib import Path

OLD, NEW = b'version=0.4.62', b'version=0.4.63'
SCRIPT = 'TTychus01.SC2Map/mapscript.galaxy'
GRANT = '''
// Purifier unit upgrades only for unlocked units (user 2026-10-21). k=-1 = always (base units).
void gf_m4_Grant (int k, string up) {
    if (k>=0 && !gf_m4_Unl(k)) { return; }
    if (TechTreeUpgradeCount(8,up,c_techCountQueuedOrBetter)==0) { TechTreeUpgradeAddLevel(8,up,1); }
}

void gf_m4_Unlocks () {'''
CALLS = '''            TechTreeAbilityAllow(9,AbilityCommand(merge[k],1),gf_m4_Unl(k));
        }
    }
    gf_m4_Grant(-1,"AdeptFenixShadeSpawn");
    gf_m4_Grant(2,"ColossusFireBeam");
    gf_m4_Grant(2,"ExtendedThermalLance");
    gf_m4_Grant(3,"DisruptorCloak");
    gf_m4_Grant(4,"MiragePhaseArmor");
    gf_m4_Grant(4,"PhoenixRangeUpgrade");
    gf_m4_Grant(5,"FenixScoutWeaponRange");
    gf_m4_Grant(7,"TempestDisintegration");
}'''


def script(d):
    t = d.decode('utf-8')
    a = '\nvoid gf_m4_Unlocks () {'
    assert t.count(a) == 1 and 'gf_m4_Grant' not in t
    t = t.replace(a, GRANT)
    b = '''            TechTreeAbilityAllow(9,AbilityCommand(merge[k],1),gf_m4_Unl(k));
        }
    }
}'''
    assert t.count(b) == 1
    t = t.replace(b, CALLS)
    return t.encode('utf-8')


FIX = {'metadata.txt': lambda d: d.replace(OLD, NEW), SCRIPT: script}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for n, fn in FIX.items(): files[n] = fn(files[n])
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in FIX: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
