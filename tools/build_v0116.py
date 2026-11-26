#!/usr/bin/env python3
"""0.11.5 -> 0.11.6: 발할라 창고 침투대 무기고 구매 반영 (사용자 2026-11-26 "침투조 왜 무기고 능력이 없지 스팀팩이 없던데").

원인: 히페리온 무기고 구매를 미션 연구로 바꾸는 처리(자극제 MarineStimpack → RM3_Stim1, 충격탄 → PunisherGrenades,
전투 방패 → 미션 연구 막음)가 호위 단계 시작(gf_m11_Start)에만 있었다. 전쟁광 자극제(RM4_MercStimpack)는 RM3_Stim1이
있어야 쓸 수 있어 창고 단계엔 자극제가 없었다. 같은 처리를 gf_m11_Armory로 떼어 모드 초기화 끝(인트로 전)에도 부른다
(한 번만 올라가게 MaxI(0,1-현재) 그대로라 두 번 불러도 겹치지 않음). Game not run.
Usage: python3 tools/build_v0116.py <0.11.5 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.11.5', b'version=0.11.6'
SP = 'THorner03.SC2Map/mapscript.galaxy'
LINES = ('    if (TechTreeUpgradeCount(1,"JackhammerConcussionGrenades",c_techCountCompleteOnly)>0) { TechTreeUpgradeAddLevel(1,"PunisherGrenades",MaxI(0,1-TechTreeUpgradeCount(1,"PunisherGrenades",c_techCountCompleteOnly))); }\n'
         '    // Hyperion armory purchases count as the matching mission research (no re-buy, no double effect).\n'
         '    if (TechTreeUpgradeCount(1,"MarineStimpack",c_techCountCompleteOnly)>0) { TechTreeUpgradeAddLevel(1,"RM3_Stim1",MaxI(0,1-TechTreeUpgradeCount(1,"RM3_Stim1",c_techCountCompleteOnly))); }\n'
         '    if (TechTreeUpgradeCount(1,"CombatShield",c_techCountCompleteOnly)>0) { TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",3),false); }\n')


def script(t):
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    start = 'void gf_m11_Start () {\n'
    assert t.count(LINES) == 1 and t.count(start) == 1 and t.index(start) < t.index(LINES)
    t = t.replace(LINES, '    gf_m11_Armory();\n')
    t = t.replace(start, '// 0.11.6: armory purchases -> mission research, also before the warehouse intro (user 2026-11-26).\n'
                  'void gf_m11_Armory () {\n' + LINES + '}\n\n' + start)
    a = '    gf_m11_RaidMercs();\n'
    assert t.count(a) == 1
    t = t.replace(a, a + '    gf_m11_Armory();\n')
    return t.replace('\n', '\r\n') if crlf else t


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as o:
                for info in prev.infolist():
                    d = prev.read(info.filename)
                    if info.filename == 'metadata.txt': d = d.replace(OLD, NEW)
                    elif info.filename == SP: d = script(d.decode('utf-8')).encode('utf-8')
                    o.writestr(copy.copy(info), d, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        except BaseException:
            out.unlink(missing_ok=True); raise


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
