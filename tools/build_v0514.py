#!/usr/bin/env python3
"""0.5.13 -> 0.5.14: 동맹 이름 '컴퓨터 8/9' 수정 (사용자 2026-10-27 "너가 잘못 만든 거다, 어부지리 맵에선 잘 나왔다").

원인: 맵 문자열 MapInfo/PlayerNN/Name의 NN은 플레이어 번호가 아니라 mapinfo 플레이어 레코드의 순서다.
블리자드 레드스톤(TTosh01) 원본은 레코드가 0,1,2,4,5,6번뿐이라(3·7번 없음, 그래서 원본 Player03 '저그 군단' = 4번 저그,
Player04 '토시의 대원' = 5번, Player05 '스완의 무기고' = 6번), 뒤에 붙인 8·9번 동맹은 6·7번째 레코드다.
이름은 Player08/09에만 넣어서 6·7번째 이름이 없어 게임이 '컴퓨터 8/9'로 보였다. 어부지리는 1~7번이 다 있어 순서=번호였다.
1·2번 미션도 레코드가 0~5번 + 8·9번이라 같은 문제였다 (1번은 원본 Player06/07 '행위자'·'80 레벨 정예 타우렌 족장'이 동맹에 붙음,
2번은 Player07이 '원시 저그'(띄어 씀)).

수정: TRaynor01·TRaynor02·TTosh01에서 MapInfo/Player06/Name=정화자, Player07/Name=원시저그를 12개 언어 문자열과
문서 헤더(DocumentHeader) 둘 다에 넣는다 (기존 Player08/09 줄은 남겨 둠). check_release가 레코드 순서로 동맹 이름을 검사한다.

Usage: python3 tools/build_v0514.py <0.5.13 zip> <new output zip>
"""
import argparse, copy, struct, zipfile
from pathlib import Path

OLD, NEW = b'version=0.5.13', b'version=0.5.14'
MAPS = ['TRaynor01', 'TRaynor02', 'TTosh01']
LOCS = 'kokr dede enus eses esmx frfr itit plpl ptbr ruru zhcn zhtw'.split()
HEADER_LOCALES = ['SUne', 'RFrf', 'EDed', 'SEse', 'XMse', 'URur', 'RKok', 'NChz', 'WThz', 'LPlp', 'TIti', 'RBtp']
NAMES = {'MapInfo/Player06/Name': ('정화자', 'Purifiers'), 'MapInfo/Player07/Name': ('원시저그', 'Primal Zerg')}


def set_strings(raw, ko):
    t = raw.decode('utf-8-sig')
    bom = raw.startswith(b'\xef\xbb\xbf')
    nl = '\r\n' if '\r\n' in t else '\n'
    lines = t.replace('\r\n', '\n').rstrip('\n').split('\n')
    idx = {l.split('=', 1)[0]: i for i, l in enumerate(lines) if '=' in l}
    for k, (k_ko, en) in NAMES.items():
        v = f'{k}={k_ko} /// {en}' if ko else f'{k}={en}'
        if k in idx: lines[idx[k]] = v
        else: lines.append(v)
    out = ('\n'.join(lines) + '\n').replace('\n', nl).encode('utf-8')
    return (b'\xef\xbb\xbf' if bom else b'') + out


def set_header(d):
    marker = b'Campaigns/LibertyStory.SC2Campaign\x00'
    p = d.index(marker) + len(marker)
    n = struct.unpack('<I', d[p:p + 4])[0]
    q = p + 4
    ents = []
    for _ in range(n):
        kl = struct.unpack('<H', d[q:q + 2])[0]; k = d[q + 2:q + 2 + kl]; loc = d[q + 2 + kl:q + 6 + kl]
        vl = struct.unpack('<H', d[q + 6 + kl:q + 8 + kl])[0]; v = d[q + 8 + kl:q + 8 + kl + vl]
        ents.append([k, loc, v]); q += 8 + kl + vl
    assert q == len(d), (q, len(d))
    have = {(k, loc): e for e in ents for k, loc in [(e[0], e[1])]}
    for key, (ko, en) in NAMES.items():
        for loc in HEADER_LOCALES:
            v = (ko if loc == 'RKok' else en).encode('utf-8')
            kb, lb = key.encode(), loc.encode()
            if (kb, lb) in have: have[(kb, lb)][2] = v
            else: ents.append([kb, lb, v])
    body = b''.join(struct.pack('<H', len(k)) + k + loc + struct.pack('<H', len(v)) + v for k, loc, v in ents)
    return d[:p] + struct.pack('<I', len(ents)) + body


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        changed = {'metadata.txt'}
        for m in MAPS:
            for l in LOCS:
                n = f'{m}.SC2Map/{l}.sc2data/localizeddata/gamestrings.txt'
                files[n] = set_strings(files[n], l == 'kokr'); changed.add(n)
            n = f'{m}.SC2Map/documentheader'
            files[n] = set_header(files[n]); changed.add(n)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out:
                assert out.testzip() is None and out.namelist() == prev.namelist()
                for n in prev.namelist():
                    if n not in changed: assert out.read(n) == prev.read(n), n
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
