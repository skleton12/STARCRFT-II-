#!/usr/bin/env python3
"""0.11.2 -> 0.11.3: 발할라(THorner03) "타이커스가 적·바로 기지로" 보고 (사용자 2026-11-25).

정적 검사로 확정 원인은 못 찾음. 두 증상은 원작 초기화(gt_Init02Players의 1·2 동맹, gt_IntroSequence 창고 인트로)가
통째로 안 돌 때 함께 나온다. 모드 쪽 런타임 오류가 원작 흐름을 끊지 못하게 막는다:
- InitMap: 모드 초기화(연구실·벌처·기술실·벙커 등 주기 트리거 등록)를 InitGlobals()/InitTriggers() 뒤로 옮김.
- gt_Initialization: gf_m11_Init()을 별도 트리거 스레드(완료 대기)로 실행 → 오류가 나도 인트로는 실행.
- 호위 단계 시작(gf_m11_Start)과 gf_m11_Init 끝에서 레이너(1)↔타이커스(2) 동맹·시야·밀치기를 다시 설정.
그 밖에 찾은 버그:
- 원작 Init02Players가 3~8번을 빨강·광물/가스 5000으로 → 8번은 이제 정화자 동맹. 3~7번 + 원래 8번(이제 11번)으로.
- 동맹 적 탐색(gf_m11_Enemies/EnemyBase)이 2~6번만 봐서 7·10·11번 적을 못 봄 → 3~11번(IsEnemy로 거름).
Game not run.
Usage: python3 tools/build_v0113.py <0.11.2 zip> <new output zip>"""
import copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.11.2', b'version=0.11.3'
SP = 'THorner03.SC2Map/mapscript.galaxy'


def rep(t, a, b, n=1):
    assert t.count(a) == n, (t.count(a), a[:80])
    return t.replace(a, b)


def script(t):
    crlf = '\r\n' in t
    t = t.replace('\r\n', '\n')
    mod_init = ('    gf_rmLabInit();\n'
                '    gt_m11_OvFollow = TriggerCreate("gt_m11_OvFollow_Func");\n'
                '    TriggerAddEventTimePeriodic(gt_m11_OvFollow, 2.0, c_timeGame);\n'
                '    gf_rm9MinesInit();\n    gf_rm9Lab2Init();\n    gf_rm9Z2Init();\n    gf_rm8BunkerInit();\n    gf_rm8LabInit();\n')
    t = rep(t, '    AchievementsDisable(1);\n' + mod_init + '    InitGlobals();\n    InitTriggers();\n}',
            '    AchievementsDisable(1);\n    InitGlobals();\n    InitTriggers();\n'
            '    // 0.11.3: mod set-up after the original triggers are registered (a mod error cannot stop them).\n' + mod_init + '}')
    ally12 = ('    libNtve_gf_SetAlliance(1,2,libNtve_ge_AllianceSetting_AllyWithSharedVision);\n'
              '    libNtve_gf_SetAlliance(2,1,libNtve_ge_AllianceSetting_AllyWithSharedVision);\n'
              '    PlayerSetAlliance(1,c_allianceIdPushable,2,true);\n')
    # gf_m11_Init in its own thread (waits; an error there does not stop the intro).
    t = rep(t, '    libCamp_gf_PurchaseStorymodeTech();\n    gf_m11_Init();\n',
            '    libCamp_gf_PurchaseStorymodeTech();\n    TriggerExecute(TriggerCreate("gt_m11_InitT_Func"), false, true);\n')
    t = rep(t, 'bool gt_Initialization_Func (bool testConds, bool runActions) {',
            '// 0.11.3: mod init in a separate thread; Raynor (1) and Tychus (2) stay allies.\n'
            'bool gt_m11_InitT_Func (bool testConds, bool runActions) {\n'
            '    if (!runActions) { return true; }\n    gf_m11_Init();\n' + ally12 + '    return true;\n}\n\n'
            'bool gt_Initialization_Func (bool testConds, bool runActions) {')
    t = rep(t, '    gv_m11_started=true;\n', '    gv_m11_started=true;\n' + ally12)
    # original colour/money loop 3..8 -> 3..7 and the moved Dominion infantry B (11); 8 is the Purifier ally.
    t = rep(t, '    const int auto317FADF5_ae = 8;', '    const int auto317FADF5_ae = 7;')
    t = rep(t, '        PlayerModifyPropertyInt(auto317FADF5_var, c_playerPropVespene, c_playerPropOperSetTo, 5000);\n    }\n',
            '        PlayerModifyPropertyInt(auto317FADF5_var, c_playerPropVespene, c_playerPropOperSetTo, 5000);\n    }\n'
            '    PlayerSetColorIndex(gv_p08_DOMINION_INFANTRY_B, 1, true);  // RM 0.11.3: moved from 8\n'
            '    PlayerModifyPropertyInt(gv_p08_DOMINION_INFANTRY_B, c_playerPropMinerals, c_playerPropOperSetTo, 5000);\n'
            '    PlayerModifyPropertyInt(gv_p08_DOMINION_INFANTRY_B, c_playerPropVespene, c_playerPropOperSetTo, 5000);\n')
    # ally enemy scans: all enemy slots 3..11.
    t = rep(t, '    e=UnitGroupEmpty();\n    for (p=2;p<=6;p+=1) {', '    e=UnitGroupEmpty();\n    for (p=3;p<=11;p+=1) {')
    t = rep(t, '    all=UnitGroupEmpty();\n    for (p=2;p<=6;p+=1) {', '    all=UnitGroupEmpty();\n    for (p=3;p<=11;p+=1) {')
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
            with zipfile.ZipFile(out) as o:
                assert o.testzip() is None
                for n in prev.namelist():
                    if n not in ('metadata.txt', SP): assert o.read(n) == prev.read(n), n
        except BaseException:
            out.unlink(missing_ok=True); raise


if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    build(Path(sys.argv[1]), Path(sys.argv[2]))
