#!/usr/bin/env python3
"""0.5.18 -> 0.5.19: 레드스톤 저그 기지 지원 — 기지가 부서지면 그 기지의 지원이 끊긴다 (사용자 2026-10-28).

사용자: "적들도 지원오게 해줄 수 있니? 단 그 지역에 적들 기지가 작살나면 그곳에서 오는 지원이 중지되는 걸로".
- 기지 = 시작할 때 있는 저그(2·4번) 부화장·번식지·군락 하나하나 (원본 배치 6곳). 그 건물이 살아 있는 동안만
  그 기지에서 지원이 온다. 부서지면 "이 지역의 저그 지원이 끊겼습니다" 안내 후 영영 멈춘다.
- 동맹 지원과 같은 박자 (시험값): 임무 4분에 첫 지원, 그 뒤 120초마다. 용암 분출 25초 전~가라앉을 때까지는 미룬다.
- 기지마다 낙하 주머니로 그 기지 둘레에 투하 (원본 미션에 나오는 저그 종류만, 7-1):
  저글링 2/3/4/4, 히드라리스크 0/1/1/2 (쉬움/보통/어려움/아주 어려움), 두 번에 한 번 번식지·군락에서 뮤탈리스크 0/0/1/1.
- 목적지: 레이너·동맹 병력이 어느 저그 기지 25칸 안에 있으면 그곳(이 기지에서 가장 가까운 침입자)을 도우러 가고,
  없으면 레이너 본진 (41.5,88.5)으로 공격 이동.

Usage: python3 tools/build_v0519.py <0.5.18 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build_v035 as V35

OLD, NEW = b'version=0.5.18', b'version=0.5.19'
M5 = 'TTosh01.SC2Map/'
S = M5 + 'mapscript.galaxy'
KO = 'kokr.sc2data/localizeddata/gamestrings.txt'

CODE = r'''// 0.5.19 (user 2026-10-28): Zerg bases send reinforcements too; a base whose Hatchery/Lair/Hive dies stops for good.
// Bases = the Zerg (2, 4) town halls at the start. First wave at 4:00, then every 120 s; held back around lava (trial).
unit[8] gv_m5_zBase;
bool[8] gv_m5_zDown;
int gv_m5_zBaseN;
fixed gv_m5_zNext;
int gv_m5_zWave;
bool gv_m5_zToldFirst;
int gv_m5_zN;
string[64] gv_m5_zKind;
point[64] gv_m5_zAt;
int[64] gv_m5_zOwn;
point[64] gv_m5_zGo;

void gf_m5_ZergBasesInit () {
    unitgroup g;
    unit u;
    int p;
    int i;
    string t;
    gv_m5_zBaseN=0;
    for (p=2;p<=4;p+=2) {
        g=UnitGroup(null,p,RegionEntireMap(),UnitFilter((1 << c_targetFilterStructure),0,0,(1 << (c_targetFilterDead - 32))),0);
        i=UnitGroupCount(g,c_unitCountAll);
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            t=UnitGetType(u);
            if ((t=="Hatchery" || t=="Lair" || t=="Hive") && gv_m5_zBaseN<8) {
                gv_m5_zBase[gv_m5_zBaseN]=u;
                gv_m5_zDown[gv_m5_zBaseN]=false;
                gv_m5_zBaseN+=1;
            }
        }
    }
    gv_m5_zNext=MaxF(240.0,GameGetMissionTime());
}

point gf_m5_ZTarget (point from) {
    unitgroup g;
    unit u;
    int b;
    int i;
    int p;
    fixed d;
    fixed bd;
    point best;
    // Help a base under attack first: the Raynor/ally unit near any live Zerg base that is closest to this base.
    best=null;
    bd=0.0;
    for (b=0;b<gv_m5_zBaseN;b+=1) {
        if (!UnitIsAlive(gv_m5_zBase[b])) { continue; }
        g=UnitGroupAlliance(2,c_unitAllianceEnemy,RegionCircle(UnitGetPosition(gv_m5_zBase[b]),25.0),
            UnitFilter(0,0,(1 << c_targetFilterMissile),(1 << (c_targetFilterDead - 32)) | (1 << (c_targetFilterHidden - 32))),0);
        i=UnitGroupCount(g,c_unitCountAll);
        for (;i>0;i-=1) {
            u=UnitGroupUnit(g,i);
            p=UnitGetOwner(u);
            if ((p!=1 && p!=8 && p!=9) || UnitGetType(u)=="RM5_AllyCaster") { continue; }
            d=DistanceBetweenPoints(from,UnitGetPosition(u));
            if (best==null || d<bd) { best=UnitGetPosition(u); bd=d; }
        }
    }
    if (best!=null) { return best; }
    return Point(41.5,88.5);
}

void gf_m5_ZAdd (int owner, string kind, int count, point c, point go) {
    int k;
    int t;
    point at;
    for (k=0;k<count && gv_m5_zN<64;k+=1) {
        at=c;
        for (t=0;t<8;t+=1) {
            at=PointWithOffsetPolar(c,RandomFixed(3.5,6.5),RandomFixed(0.0,360.0));
            if (PointPathingPassable(at)) { break; }
        }
        gv_m5_zKind[gv_m5_zN]=kind;
        gv_m5_zAt[gv_m5_zN]=at;
        gv_m5_zOwn[gv_m5_zN]=owner;
        gv_m5_zGo[gv_m5_zN]=go;
        gv_m5_zN+=1;
    }
}

bool gt_m5_ZWave_Func (bool testConds,bool runActions) {
    int n;
    int i;
    string[64] kind;
    point[64] at;
    int[64] own;
    point[64] go;
    actor[64] fx;
    if (!runActions || gv_gameOver) { return true; }
    n=gv_m5_zN;
    for (i=0;i<n;i+=1) {
        kind[i]=gv_m5_zKind[i];
        at[i]=gv_m5_zAt[i];
        own[i]=gv_m5_zOwn[i];
        go[i]=gv_m5_zGo[i];
        if (kind[i]!="Mutalisk") {
            fx[i]=libNtve_gf_CreateModelAtPoint("ZergDropPod",at[i]);
            ActorSend(fx[i],"AnimPlay Drop Birth NonLooping");
        }
    }
    // Units appear after the drop pod lands, like the Primal Zerg support (0.5.13).
    Wait(3.0,c_timeGame);
    for (i=0;i<n;i+=1) {
        if (gv_gameOver) { break; }
        UnitCreate(1,kind[i],0,own[i],at[i],270.0);
        UnitIssueOrder(UnitLastCreated(),OrderTargetingPoint(AbilityCommand("attack",0),go[i]),c_orderQueueReplace);
    }
    Wait(8.0,c_timeGame);
    for (i=0;i<n;i+=1) {
        if (fx[i]!=null) { ActorSend(fx[i],"Destroy"); }
    }
    return true;
}

void gf_m5_ZTick () {
    int b;
    int sent;
    unit hall;
    point c;
    point go;
    if (gv_m5_zBaseN==0 || gv_inCinematic) { return; }
    for (b=0;b<gv_m5_zBaseN;b+=1) {
        if (!gv_m5_zDown[b] && !UnitIsAlive(gv_m5_zBase[b])) {
            gv_m5_zDown[b]=true;
            UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/ZBaseDown"));
        }
    }
    if (GameGetMissionTime()<gv_m5_zNext || gf_m5_LavaSoon()) { return; }
    gv_m5_zNext=GameGetMissionTime()+120.0;
    gv_m5_zWave+=1;
    gv_m5_zN=0;
    sent=0;
    for (b=0;b<gv_m5_zBaseN;b+=1) {
        hall=gv_m5_zBase[b];
        if (!UnitIsAlive(hall)) { continue; }
        c=UnitGetPosition(hall);
        go=gf_m5_ZTarget(c);
        // Trial squad per base (Zerg types from the original mission only, rule 7-1).
        gf_m5_ZAdd(UnitGetOwner(hall),"Zergling",libNtve_gf_DifficultyValueInt(2,3,4,4),c,go);
        gf_m5_ZAdd(UnitGetOwner(hall),"Hydralisk",libNtve_gf_DifficultyValueInt(0,1,1,2),c,go);
        if (ModI(gv_m5_zWave,2)==0 && UnitGetType(hall)!="Hatchery") {
            gf_m5_ZAdd(UnitGetOwner(hall),"Mutalisk",libNtve_gf_DifficultyValueInt(0,0,1,1),c,go);
        }
        sent+=1;
    }
    if (sent==0 || gv_m5_zN==0) { return; }
    if (!gv_m5_zToldFirst) {
        gv_m5_zToldFirst=true;
        UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaSubtitle,StringExternal("rm5/ZFirst"));
    }
    TriggerExecute(TriggerCreate("gt_m5_ZWave_Func"),false,false);
}

bool gt_m5_Tick_Func (bool testConds,bool runActions) {'''

SCRIPT = [
    ('bool gt_m5_Tick_Func (bool testConds,bool runActions) {', CODE),
    ('    gf_m5_CallTick();\n    gf_rmAllyBases(8,9);\n', '    gf_m5_CallTick();\n    gf_m5_ZTick();\n    gf_rmAllyBases(8,9);\n'),
    ('    gf_m5_EnemyRules();\n    TriggerExecute(gt_m5_arrive,false,false);\n',
     '    gf_m5_EnemyRules();\n    gf_m5_ZergBasesInit();\n    TriggerExecute(gt_m5_arrive,false,false);\n'),
]

ADD = [
    'rm5/ZFirst=저그 기지에서 지원 병력이 투하됩니다. 부화장·번식지·군락을 파괴하면 그 기지의 지원이 끊깁니다. '
    '/// Zerg bases are dropping in reinforcements. Destroy a Hatchery, Lair or Hive to cut off that base\'s reinforcements.',
    'rm5/ZBaseDown=저그 기지 파괴 — 이 지역의 저그 지원이 끊겼습니다. /// Zerg base destroyed: reinforcements from this area have stopped.',
]


def sub(t, pairs):
    for a, b in pairs:
        assert t.count(a) == 1, a
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
