#!/usr/bin/env python3
"""0.11.4 -> 0.11.5: 발할라 창고 침투대도 용병 (사용자 2026-11-26 "침투할때 마린이 전쟁광이 아님").

0.11.1은 창고 단계 해병·의무관을 원본 그대로 뒀다: 원작이 습격대를 InitGlobals에서 묶음(gv_raynorsRaidingForce)으로
잡아 패배 판정·중간 연출에 쓰는데, 유닛을 바꾸면 묶음이 비기 때문. 이제 모드 초기화 끝(gt_m11_InitT, 인트로 전)에
습격대 지역(RegionFromId 8)의 레이너 해병 → 전쟁광, 의무관 → 용병 의무관으로 바꾸고 묶음을 새 유닛으로 다시 잡는다
(원작 생성 필터 그대로). 체력 비율은 ReplaceUnit(OldUnitsRelative)로 유지, 용병 의무관 에너지는 원작처럼 100%. 호위 단계 이후는 기존 주기 처리 그대로.
Game not run. Usage: python3 tools/build_v0115.py <0.11.4 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.11.4', b'version=0.11.5'
SP = 'THorner03.SC2Map/mapscript.galaxy'
FILT = 'UnitFilter(0, 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))), 0)'
FN = f'''// 0.11.5 (user 2026-11-26): the warehouse raiding force is mercenaries too; the original group is rebuilt with the new units.
void gf_m11_RaidMercs () {{
    unitgroup g = UnitGroup(null, 1, RegionFromId(8), {FILT};
    unit u;
    int i;
    for (i = UnitGroupCount(g, c_unitCountAll); i > 0; i -= 1) {{
        u = UnitGroupUnit(g, i);
        if (UnitGetType(u) == "Marine") {{ libNtve_gf_ReplaceUnit(u, "WarPig", libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }}
        else if (UnitGetType(u) == "Medic") {{ libNtve_gf_ReplaceUnit(u, "MercMedic", libNtve_ge_ReplaceUnitOptions_OldUnitsRelative); }}
    }}
    gv_raynorsRaidingForce = UnitGroup(null, gv_p01_USER, RegionFromId(8), {FILT};
    // like the original Init 03 for Medics: full energy
    for (i = UnitGroupCount(gv_raynorsRaidingForce, c_unitCountAll); i > 0; i -= 1) {{
        u = UnitGroupUnit(gv_raynorsRaidingForce, i);
        if (UnitGetType(u) == "MercMedic") {{ UnitSetPropertyFixed(u, c_unitPropEnergyPercent, 100.0); }}
    }}
}}

'''


def script(t):
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    a = 'bool gt_m11_InitT_Func (bool testConds, bool runActions) {\n    if (!runActions) { return true; }\n    gf_m11_Init();\n'
    assert t.count(a) == 1 and t.count('gv_raynorsRaidingForce = UnitGroup(null, gv_p01_USER, RegionFromId(8), ' + FILT + ';') == 1
    assert t.index('unitgroup gv_raynorsRaidingForce;') < t.index(a)
    t = t.replace(a, FN + a + '    gf_m11_RaidMercs();\n')
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
