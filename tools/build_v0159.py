#!/usr/bin/env python3
"""0.15.8 -> 0.15.9: 시간 가속·건물 감염을 협동전처럼 화면 위 버튼으로 (사용자 2026-11-28 "그 시간 가속이랑 그 감염 … 왜 협동전처럼 위에 표시 않나오냐").
동맹 연구 건물(정화자 대의회·데하카의 굴)이 놓이면 동맹 지원 버튼 오른쪽에 [시간 가속](Ctrl+N)·[건물 감염](Ctrl+M) 아이콘 버튼과
남은 시간/충전 글자를 띄운다. 누르면 다음 지도 왼쪽 클릭 자리(3칸 안 가장 가까운 대상 건물)에 그 건물이 능력을 쓴다
(시간 가속: 레이너의 완성된 건물, 건물 감염: 레이너 또는 적 건물). 오른쪽 클릭 취소. 능력·대기·충전은 기존 데이터 그대로(건물 명령 카드에서도 계속 쓸 수 있음).
10개 공장 맵. Usage: build_v0159.py <0.15.8 zip> <out>"""
import copy, re, sys, zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_v035 as V35
from build_v062 import set_lines
OLD, NEW = b'version=0.15.8', b'version=0.15.9'
MAPS = ['TTychus01', 'TTosh01', 'THanson01', 'TTosh02', 'THorner01', 'THorner02', 'THorner03', 'THorner04', 'TTychus03', 'TTychus02']
STR = {
    'rmTop/Chrono': '시간 가속 Ctrl+N /// Chrono Ctrl+N',
    'rmTop/Infest': '감염 %s/3 Ctrl+M /// Infest %s/3 Ctrl+M',
    'rmTop/Wait': '%s초 /// %ss',
    'rmTop/AimC': '시간 가속할 레이너 건물을 왼쪽 클릭하세요. 오른쪽 클릭은 취소입니다. /// Left-click one of Raynor\'s structures to Chrono Boost. Right-click cancels.',
    'rmTop/AimI': '감염할 건물(레이너 또는 적 건물)을 왼쪽 클릭하세요. 오른쪽 클릭은 취소입니다. /// Left-click a structure (Raynor\'s or an enemy\'s) to infest. Right-click cancels.',
    'rmTop/NoTarget': '그 자리에 쓸 수 있는 건물이 없습니다. /// No valid structure there.',
    'rmTop/NotReady': '아직 쓸 수 없습니다. /// Not ready yet.',
}
FUNCS = r'''// 0.15.9: Chrono Boost / Infest Structure as top-bar buttons (like co-op), next to the ally support buttons.
int gv_rmTopDlg = c_invalidDialogId;
int[3] gv_rmTopBtn;
int[3] gv_rmTopLbl;
int gv_rmTopAim;
fixed gv_rmTopAimAt;

unit gf_rmTopCaster (int k) {
    string t = "RM7_Conclave";
    if (k == 2) { t = "RM7_DehakaDen"; }
    return UnitGroupUnit(UnitGroup(t, 1, RegionEntireMap(), UnitFilter(0, 0, 0, (1 << (c_targetFilterDead - 32))), 0), 1);
}

void gf_rmTopButton (int k, int x, string icon, string tip) {
    int img;
    DialogControlCreate(gv_rmTopDlg, c_triggerControlTypeLabel);
    gv_rmTopLbl[k] = DialogControlLastCreated();
    DialogControlSetSize(gv_rmTopLbl[k], PlayerGroupAll(), 110, 24);
    DialogControlSetPosition(gv_rmTopLbl[k], PlayerGroupAll(), c_anchorTopLeft, x - 20, 0);
    DialogControlCreate(gv_rmTopDlg, c_triggerControlTypeButton);
    gv_rmTopBtn[k] = DialogControlLastCreated();
    DialogControlSetSize(gv_rmTopBtn[k], PlayerGroupAll(), 64, 64);
    DialogControlSetPosition(gv_rmTopBtn[k], PlayerGroupAll(), c_anchorTopLeft, x, 26);
    DialogControlSetPropertyAsText(gv_rmTopBtn[k], c_triggerControlPropertyTooltip, PlayerGroupAll(), StringExternal(tip));
    DialogControlCreate(gv_rmTopDlg, c_triggerControlTypeImage);
    img = DialogControlLastCreated();
    DialogControlSetSize(img, PlayerGroupAll(), 52, 52);
    DialogControlSetPosition(img, PlayerGroupAll(), c_anchorTopLeft, x + 6, 32);
    DialogControlSetPropertyAsString(img, c_triggerControlPropertyImage, PlayerGroupAll(), icon);
    DialogControlSetPropertyAsInt(img, c_triggerControlPropertyImageType, PlayerGroupAll(), c_triggerImageTypeNormal);
}

void gf_rmTopAim (int k) {
    unit c = gf_rmTopCaster(k);
    if (c == null) { return; }
    gv_rmTopAim = k;
    gv_rmTopAimAt = GameGetMissionTime();
    if (k == 1) { UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaSubtitle, StringExternal("rmTop/AimC")); }
    else { UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaSubtitle, StringExternal("rmTop/AimI")); }
}

bool gt_rmTopBtn_Func (bool testConds, bool runActions) {
    if (!runActions) { return true; }
    if (EventDialogControl() == gv_rmTopBtn[1]) { gf_rmTopAim(1); }
    else if (EventDialogControl() == gv_rmTopBtn[2]) { gf_rmTopAim(2); }
    return true;
}

bool gt_rmTopKey_Func (bool testConds, bool runActions) {
    if (!runActions) { return true; }
    if (EventKeyPressed() == c_keyN) { gf_rmTopAim(1); }
    else if (EventKeyPressed() == c_keyM) { gf_rmTopAim(2); }
    return true;
}

bool gt_rmTopMouse_Func (bool testConds, bool runActions) {
    int k = gv_rmTopAim;
    point p;
    unitgroup g;
    unit c;
    unit t;
    if (!runActions || k == 0 || GameGetMissionTime() < gv_rmTopAimAt + 0.2) { return true; }
    gv_rmTopAim = 0;
    p = Point(EventMouseClickedPosXWorld(), EventMouseClickedPosYWorld());
    c = gf_rmTopCaster(k);
    if (c == null) { return true; }
    if (k == 1) {
        g = UnitGroup(null, 1, RegionCircle(p, 3.0), UnitFilter((1 << c_targetFilterStructure), 0, (1 << c_targetFilterMissile), (1 << (c_targetFilterStasis - 32)) | (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterUnderConstruction - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);
    }
    else {
        g = UnitGroup(null, 1, RegionCircle(p, 3.0), UnitFilter((1 << c_targetFilterStructure), 0, (1 << c_targetFilterMissile) | (1 << c_targetFilterHeroic), (1 << (c_targetFilterStasis - 32)) | (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterUnderConstruction - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0);
        UnitGroupAddUnitGroup(g, UnitGroupAlliance(1, c_unitAllianceEnemy, RegionCircle(p, 3.0), UnitFilter((1 << c_targetFilterStructure) | (1 << c_targetFilterVisible), 0, (1 << c_targetFilterMissile) | (1 << c_targetFilterHeroic), (1 << (c_targetFilterStasis - 32)) | (1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32)) | (1 << (c_targetFilterUnderConstruction - 32)) | (1 << (c_targetFilterInvulnerable - 32))), 0));
    }
    UnitGroupRemove(g, c);
    t = UnitGroupClosestToPoint(g, p);
    if (t == null) {
        UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaError, StringExternal("rmTop/NoTarget"));
        return true;
    }
    if (k == 1) {
        if (!UnitIssueOrder(c, OrderTargetingUnit(AbilityCommand("RM9_Chrono", 0), t), c_orderQueueReplace)) { UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaError, StringExternal("rmTop/NotReady")); }
    }
    else {
        if (!UnitIssueOrder(c, OrderTargetingUnit(AbilityCommand("RM9_Infest", 0), t), c_orderQueueReplace)) { UIDisplayMessage(PlayerGroupSingle(1), c_messageAreaError, StringExternal("rmTop/NotReady")); }
    }
    return true;
}

bool gt_rmTopCancel_Func (bool testConds, bool runActions) {
    if (!runActions) { return true; }
    gv_rmTopAim = 0;
    return true;
}

bool gt_rmTopTimer_Func (bool testConds, bool runActions) {
    unit c;
    fixed cd;
    int left;
    if (!runActions || gv_rmTopDlg == c_invalidDialogId) { return true; }
    c = gf_rmTopCaster(1);
    cd = 0.0;
    if (c != null) { cd = UnitGetCooldown(c, "Abil/RM9_Chrono"); }
    if (cd > 0.0) { DialogControlSetPropertyAsText(gv_rmTopLbl[1], c_triggerControlPropertyText, PlayerGroupAll(), TextReplaceWord(StringExternal("rmTop/Wait"), StringToText("%s"), IntToText(CeilingI(cd)), c_stringReplaceAll, c_stringCase)); }
    else { DialogControlSetPropertyAsText(gv_rmTopLbl[1], c_triggerControlPropertyText, PlayerGroupAll(), StringExternal("rmTop/Chrono")); }
    c = gf_rmTopCaster(2);
    left = 0;
    if (c != null) { left = 3 - CeilingI(UnitGetChargeUsed(c, "Abil/RM9_Infest")); }
    if (left < 0) { left = 0; }
    DialogControlSetPropertyAsText(gv_rmTopLbl[2], c_triggerControlPropertyText, PlayerGroupAll(), TextReplaceWord(StringExternal("rmTop/Infest"), StringToText("%s"), IntToText(left), c_stringReplaceAll, c_stringCase));
    return true;
}

void gf_rmTopUI () {
    trigger t;
    if (gv_rmTopDlg != c_invalidDialogId) { return; }
    DialogCreate(200, 96, c_anchorTop, 250, 4, false);
    gv_rmTopDlg = DialogLastCreated();
    DialogSetImageVisible(gv_rmTopDlg, false);
    gf_rmTopButton(1, 24, "Assets\\Textures\\btn-ability-protoss-chronoboost.dds", "Button/Tooltip/RM9_Chrono");
    gf_rmTopButton(2, 112, "Assets\\Textures\\btn-ability-zerg-stukov-infeststructure.dds", "Button/Tooltip/RM9_Infest");
    DialogSetVisible(gv_rmTopDlg, PlayerGroupSingle(1), true);
    t = TriggerCreate("gt_rmTopBtn_Func");
    TriggerAddEventDialogControl(t, 1, c_invalidDialogControlId, c_triggerControlEventTypeClick);
    t = TriggerCreate("gt_rmTopKey_Func");
    TriggerAddEventKeyPressed(t, 1, c_keyN, true, c_keyModifierStateExclude, c_keyModifierStateRequire, c_keyModifierStateExclude);
    TriggerAddEventKeyPressed(t, 1, c_keyM, true, c_keyModifierStateExclude, c_keyModifierStateRequire, c_keyModifierStateExclude);
    t = TriggerCreate("gt_rmTopMouse_Func");
    TriggerAddEventMouseClicked(t, 1, c_mouseButtonLeft, true);
    t = TriggerCreate("gt_rmTopCancel_Func");
    TriggerAddEventMouseClicked(t, 1, c_mouseButtonRight, true);
    t = TriggerCreate("gt_rmTopTimer_Func");
    TriggerAddEventTimePeriodic(t, 0.5, c_timeGame);
}

'''
START = 'bool gt_rm7Tick_Func (bool testConds, bool runActions) {'
RUN = '    if (!runActions) { return true; }\n'
CALL = '    if (gv_rm7Placed) { gf_rmTopUI(); }\n'


def script(raw):
    nl = '\r\n' if '\r\n' in raw else '\n'; s = raw.replace('\r\n', '\n')
    assert s.count(START) == 1 and 'gf_rmTopUI' not in s
    k = s.index(START); r = s.index(RUN, k) + len(RUN)
    assert r - k < 400
    s = s[:k] + FUNCS + s[k:r] + CALL + s[r:]
    return s.replace('\n', nl)


def build(src, out):
    out = Path(out); assert not out.exists()
    with zipfile.ZipFile(src) as z:
        assert OLD in z.read('metadata.txt').splitlines()
        rep = {'metadata.txt': z.read('metadata.txt').replace(OLD, NEW)}
        for m in MAPS:
            n = f'{m}.SC2Map/mapscript.galaxy'; rep[n] = script(z.read(n).decode('utf-8')).encode('utf-8')
            kn = f'{m}.SC2Map/kokr.sc2data/localizeddata/gamestrings.txt'; ko = set_lines(z.read(kn), STR); V35.gate('kokr', ko); rep[kn] = ko
            for loc in V35.OTHER_LOCALES: rep[f'{m}.SC2Map/{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(ko)
        try:
            with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as w:
                for i in z.infolist(): w.writestr(copy.copy(i), rep.get(i.filename, z.read(i.filename)), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
            with zipfile.ZipFile(out) as w: assert w.testzip() is None
        except BaseException:
            out.unlink(missing_ok=True); raise
    print(out)


if __name__ == '__main__': build(*sys.argv[1:])
