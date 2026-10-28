#!/usr/bin/env python3
"""0.5.20 -> 0.5.21: 레드스톤 동맹 지원 5단계 (사용자 2026-10-28).

사용자: "지원군도 5단계 형식으로 만들어줘" → 대상 동맹 지원, "연구실 단계 올라가면 자동으로 올라감 — 저그 1단계면 원시저그 +1단계",
효과 "병력 수 증가, 유닛 종류 강화".
- 단계 = 히페리온 연구실에서 산 연구 수 (0~5). 프로토스 연구 → 정화자 지원, 저그 연구 → 원시저그 지원.
  (libCamp 연구 상태 Purchased, 임무 시작 때 한 번 센다)
- 단계마다 지원 묶음에 한 기씩 더 (시험값). 단계로 더해진 유닛은 동맹 돈을 쓰지 않는다 (연구 보상). 인구 100 상한에는 센다.
  정화자: 1 군단병 / 2 선동자 / 3 피닉스 사도 / 4 거신 / 5 폭풍함
  원시저그: 1 원시 저글링 2 / 2 라바사우르스 / 3 원시 점화자 / 4 원시 울트라리스크 / 5 티라노조르
- 화면 위 지원 버튼 글자에 단계 표시 ("정화자 Ctrl+V 3단계"). 묶음 최대 12 → 16기.

Usage: python3 tools/build_v0521.py <0.5.20 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.5.20', b'version=0.5.21'
M5 = 'TTosh01.SC2Map/'
S = M5 + 'mapscript.galaxy'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'

TIER = r'''// 0.5.21 (user 2026-10-28): support tier = Hyperion lab research bought (Protoss -> Purifiers, Zerg -> Primal Zerg), 0-5.
int[16] gv_m5_tier;
int[16] gv_m5_supPaid;

int gf_m5_Tier (int p) {
    int i;
    int r;
    int n=0;
    int cat=libCamp_ge_StoryResearchCategory_ResearchCategoryProtoss;
    if (p==9) { cat=libCamp_ge_StoryResearchCategory_ResearchCategoryZerg; }
    for (i=libCamp_gv_TSC_RESEARCH_FIRST;i<=libCamp_gv_TSC_RESEARCH_LAST;i+=1) {
        r=libCamp_gv_tS_ResearchID[i];
        if (libCamp_gf_StoryResearchCategory(r)==cat && libCamp_gf_StoryResearchStateCheck(r,libCamp_ge_StoryResearchState_ResearchStatePurchased)) { n+=1; }
    }
    return MinI(n,5);
}

void gf_m5_SupAdd (int p, string kind) {'''

SCRIPT = [
    ('string[16][12] gv_m5_supKind;\npoint[16][12] gv_m5_supAt;\n', 'string[16][16] gv_m5_supKind;\npoint[16][16] gv_m5_supAt;\n'),
    ('void gf_m5_SupAdd (int p, string kind) {', TIER),
    ('    if (gv_m5_supN[p]>=12) { return; }\n', '    if (gv_m5_supN[p]>=16) { return; }\n'),
    ('        if (n>0) { gf_m5_SupAdd(p,extra[ModI(gv_m5_supTurn,n)]); }\n        return;\n',
     '        if (n>0) { gf_m5_SupAdd(p,extra[ModI(gv_m5_supTurn,n)]); }\n'
     '        // Tier units (free, trial): 1 Legionnaire, 2 Instigator, 3 Fenix Adept, 4 Colossus, 5 Tempest.\n'
     '        gv_m5_supPaid[p]=gv_m5_supN[p];\n'
     '        if (gv_m5_tier[p]>=1) { gf_m5_SupAdd(p,"ZealotPurifier"); }\n'
     '        if (gv_m5_tier[p]>=2) { gf_m5_SupAdd(p,"StalkerPurifier"); }\n'
     '        if (gv_m5_tier[p]>=3) { gf_m5_SupAdd(p,"AdeptFenix"); }\n'
     '        if (gv_m5_tier[p]>=4) { gf_m5_SupAdd(p,"ColossusPurifier"); }\n'
     '        if (gv_m5_tier[p]>=5) { gf_m5_SupAdd(p,"TempestPurifier"); }\n'
     '        return;\n'),
    ('    if (gf_m5_Unl(3)) { gf_m5_SupAdd(p,"DehakaUltraliskLevel2"); }\n}\n',
     '    if (gf_m5_Unl(3)) { gf_m5_SupAdd(p,"DehakaUltraliskLevel2"); }\n'
     '    // Tier units (free, trial): 1 zergling x2, 2 Ravasaur, 3 Primal Igniter, 4 Primal Ultralisk, 5 Tyrannozor.\n'
     '    gv_m5_supPaid[p]=gv_m5_supN[p];\n'
     '    if (gv_m5_tier[p]>=1) { gf_m5_SupAdd(p,"DehakaZerglingLevel2"); gf_m5_SupAdd(p,"DehakaZerglingLevel2"); }\n'
     '    if (gv_m5_tier[p]>=2) { gf_m5_SupAdd(p,"DehakaRavasaur"); }\n'
     '    if (gv_m5_tier[p]>=3) { gf_m5_SupAdd(p,"DehakaRoachLevel3"); }\n'
     '    if (gv_m5_tier[p]>=4) { gf_m5_SupAdd(p,"DehakaUltraliskLevel2"); }\n'
     '    if (gv_m5_tier[p]>=5) { gf_m5_SupAdd(p,"DehakaUltraliskLevel3"); }\n'
     '}\n'),
    ('    for (i=0;i<gv_m5_supN[p];i+=1) {\n        m+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostMinerals);\n        g+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostVespene);\n        food+=gf_m5_UnitFood(gv_m5_supKind[p][i]);\n    }\n',
     '    for (i=0;i<gv_m5_supN[p];i+=1) {\n'
     '        // 0.5.21: tier units are free (lab research reward); they still count toward the supply cap.\n'
     '        if (i<gv_m5_supPaid[p]) {\n'
     '            m+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostMinerals);\n'
     '            g+=UnitTypeGetCost(gv_m5_supKind[p][i],c_unitCostVespene);\n'
     '        }\n'
     '        food+=gf_m5_UnitFood(gv_m5_supKind[p][i]);\n    }\n'),
    ('    gv_m5_callAbil[9]="RM5_PrimalSupport";\n',
     '    gv_m5_callAbil[9]="RM5_PrimalSupport";\n    gv_m5_tier[8]=gf_m5_Tier(8);\n    gv_m5_tier[9]=gf_m5_Tier(9);\n'),
    ('        DialogControlSetPropertyAsText(gv_m5_callLblP[p],c_triggerControlPropertyText,PlayerGroupAll(),name);\n',
     '        DialogControlSetPropertyAsText(gv_m5_callLblP[p],c_triggerControlPropertyText,PlayerGroupAll(),\n'
     '            name+StringToText(" ")+TextReplaceWord(StringExternal("rm5/CallTier"),StringToText("%s"),IntToText(gv_m5_tier[p]),c_stringReplaceAll,c_stringCase));\n'),
]
TWICE = [('    string[12] kind;\n    point[12] at;\n    actor[12] fx;\n', '    string[16] kind;\n    point[16] at;\n    actor[16] fx;\n')]

ADD = ['rm5/CallTier=%s단계 /// Tier %s']


def sub(t, pairs, n=1):
    for a, b in pairs:
        assert t.count(a) == n, (t.count(a), a)
        t = t.replace(a, b)
    return t


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        t = files[S].decode('utf-8')
        nl = '\r\n' if '\r\n' in t else '\n'
        t = sub(t.replace('\r\n', '\n'), SCRIPT)
        t = sub(t, TWICE, 2)
        files[S] = t.replace('\n', nl).encode('utf-8')
        ko = files[M5 + KO].decode('utf-8-sig')
        knl = '\r\n' if '\r\n' in ko else '\n'
        for a in ADD: assert a.split('=', 1)[0] + '=' not in ko, a
        files[M5 + KO] = (ko.rstrip('\r\n') + knl + knl.join(ADD) + knl).encode('utf-8')
        V35.gate('kokr', files[M5 + KO])
        for loc in V35.OTHER_LOCALES:
            files[f'{M5}{loc}.sc2data/localizeddata/gamestrings.txt'] = V35.other_locale(files[M5 + KO])
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if not n.startswith(M5) and n != 'metadata.txt': assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
