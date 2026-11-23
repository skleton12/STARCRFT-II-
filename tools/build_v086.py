#!/usr/bin/env python3
"""0.8.5 -> 0.8.6: 동맹 지원 = 연구 점수 1점마다 유닛 추가 (사용자 2026-11-23 "1칸에 오를 때마다 유닛 추가해줘 예를 들면 프로토스는
군단병 1기 선동자 1기 이런식으로", "중간중간에 중장갑이나 비행유닛도 추가하는 방식으로").

maps 3~8. 0.6.75의 '연구실 단계(산 연구 수)마다 가벼운 유닛 2기'를 '히페리온 연구 점수 1점마다 1기'로 바꾼다 (무료, 시험값):
  - 점수 = libCamp_gf_StoryResearchPoints(프로토스 → 정화자, 저그 → 원시저그), 최대 25.
  - 정화자: 1점째 군단병, 2점째 선동자를 번갈아, 5점마다(5·10·15·20·25) 대신 중장갑·비행 1기
      4~8번: 불멸자 → 정찰기 → 거신 → 폭풍함 → 불멸자. 3번(TRaynor03)은 정화자 외형 중장갑이 없어 군단병·선동자만.
  - 원시저그: 저글링 2 → 바퀴 1 → 저글링 2 → 히드라 1을 돌고, 5점마다 대신
      4~8번: 원시 울트라 → 원시 뮤탈리스크 → 원시 숙주 → 원시 수호군주 → 티라노조르. 3번은 라바사우르스 2.
  원시저그 저글링은 원작처럼 2기 한 쌍(인구 1)으로 센다. 3번은 군단병 인구 계산을 2 → 3으로 바로잡음(코덱스).
  연구실 단계(산 연구 수)는 피닉스 용사·5단계 중장갑(0.6.76/0.6.77)에만 그대로 쓴다.
  무료분은 그대로 인구 120 남은 자리만큼만 붙는다(0.6.75). 묶음 칸 32 → 64 (25점이면 무료만 30기 넘게 나올 수 있음).
Game not run.

Usage: python3 tools/build_v086.py <0.8.5 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path

OLD, NEW = b'version=0.8.5', b'version=0.8.6'
MAPS = {'TRaynor03': ('m3c', 10, 11), 'TTychus01': ('m4', 8, 9), 'TTosh01': ('m5', 8, 9), 'THanson01': ('m6', 8, 9),
        'TTosh02': ('m7', 8, 9), 'THorner01': ('m8', 8, 9)}
P_HEAVY = ['Immortal', 'Scout', 'ColossusPurifier', 'TempestPurifier', 'Immortal']
Z_HEAVY = ['DehakaUltraliskLevel2', 'DehakaMutaliskLevel2', 'DehakaSwarmHost', 'DehakaGuardian', 'DehakaUltraliskLevel3']
MAX_POINTS = 25


def pts_fn(t, pp, pz):
    return (f'// 0.8.6 (user 2026-11-23): Hyperion lab research points (Protoss -> Purifiers, Zerg -> Primal Zerg), max {MAX_POINTS}.\n'
            f'int gf_{t}_Pts (int p) {{\n'
            f'    int cat=libCamp_ge_StoryResearchCategory_ResearchCategoryProtoss;\n'
            f'    if (p=={pz}) {{ cat=libCamp_ge_StoryResearchCategory_ResearchCategoryZerg; }}\n'
            f'    return MaxI(0,MinI(libCamp_gf_StoryResearchPoints(cat),{MAX_POINTS}));\n}}\n\n')


def loop(t, prot, heavy):
    a = f'gf_{t}_SupAdd(p,'
    if prot:
        hv = ''.join(f'                if (k=={(i + 1) * 5}) {{ {a}"{u}"); }}\n' for i, u in enumerate(heavy)) if heavy else ''
        five = (f'            if (ModI(k,5)==0) {{\n{hv}            }}\n            else ' if heavy else '            ')
        body = (f'{five}if (ModI(k,2)==1) {{ {a}"ZealotPurifier"); }}\n'
                f'            else {{ {a}"StalkerPurifier"); }}\n')
    else:
        if heavy:
            hv = ''.join(f'                if (k=={(i + 1) * 5}) {{ {a}"{u}"); }}\n' for i, u in enumerate(heavy))
        else:
            hv = f'                {a}"DehakaRavasaur"); {a}"DehakaRavasaur");\n'
        body = (f'            if (ModI(k,5)==0) {{\n{hv}            }}\n'
                f'            else if (ModI(k,4)==1 || ModI(k,4)==3) {{ {a}"DehakaZerglingLevel2"); {a}"DehakaZerglingLevel2"); }}\n'
                f'            else if (ModI(k,4)==2) {{ {a}"DehakaRoachLevel2"); }}\n'
                f'            else {{ {a}"DehakaHydraliskLevel2"); }}\n')
    return (f'        // 0.8.6: one free unit per lab research point (trial).\n'
            f'        for (k=1;k<=gf_{t}_Pts(p);k+=1) {{\n{body}        }}\n')


def patch(s, m, t, pp, pz):
    nl = '\r\n' if '\r\n' in s else '\n'
    s = s.replace('\r\n', '\n')
    heavy = m != 'TRaynor03'
    # tier light-unit lines (0.6.75) -> points loops
    lines = s.split('\n')
    pi = [i for i, l in enumerate(lines) if re.match(rf'\s*if \(gv_{t}_tier\[p\]>=[1-5]\) \{{ gf_{t}_SupAdd', l)]
    assert len(pi) == 10, (m, len(pi))
    p_block, z_block = pi[:5], pi[5:]
    assert p_block == list(range(p_block[0], p_block[0] + 5)) and z_block == list(range(z_block[0], z_block[0] + 5)), m
    assert 'Dehaka' not in ''.join(lines[i] for i in p_block) and 'Dehaka' in lines[z_block[0]], m
    new = lines[:p_block[0]] + [loop(t, True, P_HEAVY if heavy else None).rstrip('\n')] + lines[p_block[-1] + 1:z_block[0]] \
        + [loop(t, False, Z_HEAVY if heavy else None).rstrip('\n')] + lines[z_block[-1] + 1:]
    s = '\n'.join(new)
    # the SupFill function must declare k
    f = s.index(f'void gf_{t}_SupFill (int p) {{')
    body_end = s.index('\n}\n', f)
    assert '    int k;\n' in s[f:body_end], m
    # points function before SupFill
    s = s[:f] + pts_fn(t, pp, pz) + s[f:]
    # group slots 32 -> 64
    n = 0
    for a, b in ((f'string[16][32] gv_{t}_supKind;', f'string[16][64] gv_{t}_supKind;'),
                 (f'point[16][32] gv_{t}_supAt;', f'point[16][64] gv_{t}_supAt;'),
                 (f'if (gv_{t}_supN[p]>=32) {{ return; }}', f'if (gv_{t}_supN[p]>=64) {{ return; }}')):
        assert s.count(a) == 1, (m, a); s = s.replace(a, b)
    for a, b in (('    string[32] kind;\n', '    string[64] kind;\n'), ('    point[32] at;\n', '    point[64] at;\n'),
                 ('    actor[32] fx;\n', '    actor[64] fx;\n')):
        c = s.count(a); assert c >= 1, (m, a); n += c; s = s.replace(a, b)
    if m == 'TRaynor03':
        # Codex review: mission 3 counted the Legionnaire (Food 3) as 2, so a group could pass the 120 cap.
        x = '    if (kind=="DehakaZerglingLevel2") { return 1.0; }\n'
        assert s.count(x) == 1
        s = s.replace(x, x + '    if (kind=="ZealotPurifier") { return 3.0; }  // 0.8.6: Legionnaire Food 3\n')
    return s.replace('\n', nl), n


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m, (t, pp, pz) in MAPS.items():
            k = f'{m}.SC2Map/mapscript.galaxy'
            s, n = patch(files[k].decode('utf-8-sig'), m, t, pp, pz)
            print(m, 'local arrays widened:', n)
            files[k] = s.encode('utf-8'); changed.add(k)
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
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
