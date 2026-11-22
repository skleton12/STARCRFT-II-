#!/usr/bin/env python3
"""0.6.72 -> 0.6.73 (user 2026-11-22 "군수 기술실에 아무것도 없는 아이콘", "첫번째 두번이였나 세번째", "지금고쳐").

Maps 4-7: the Factory Tech Lab / Tech Reactor still showed the original buttons of FactoryTechLabResearch
Research1 (SiegeTech, 0,1), Research2 (HighCapacityBarrels, 0,0) and Research4 (campaign Ares 'CharonBoosters', 0,2)
as empty icons. Their buttons get the always-false Show requirement RM4_HideOriginal (0.4.54 way) and the script also
disallows those commands. The mod research (Research5-7) is untouched. Game not run.

Usage: python3 tools/build_v0673.py <0.6.72 zip> <new output zip>
"""
import argparse, copy, sys, zipfile
from pathlib import Path

OLD, NEW = b'version=0.6.72', b'version=0.6.73'
MAPS = ('TTychus01', 'TTosh01', 'THanson01', 'TTosh02')
ABIL = 'base.sc2data/gamedata/abildata.xml'
HEAD = '<CAbilResearch id="FactoryTechLabResearch">'
HIDE = ''.join(f'<InfoArray index="Research{n}"><Button Requirements="RM4_HideOriginal" /></InfoArray>' for n in (1, 2, 4))
S_OLD = '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",3),false);\n'
S_NEW = ('    // 0.6.73: original Factory Tech Lab buttons (siege tech, barrels, campaign Ares) hidden and blocked.\n'
         '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",0),false);\n'
         '    TechTreeAbilityAllow(1,AbilityCommand("FactoryTechLabResearch",1),false);\n' + S_OLD)


def build(src, out):
    if out.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(src) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {k: prev.read(k) for k in prev.namelist()}
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        changed = {'metadata.txt'}
        for m in MAPS:
            p = f'{m}.SC2Map/{ABIL}'
            t = files[p].decode('utf-8')
            assert t.count(HEAD) == 1 and 'id="RM4_HideOriginal"' in files[f'{m}.SC2Map/base.sc2data/gamedata/requirementdata.xml'].decode('utf-8')
            files[p] = t.replace(HEAD, HEAD + HIDE).encode('utf-8'); changed.add(p)
            p = f'{m}.SC2Map/mapscript.galaxy'
            raw = files[p].decode('utf-8'); nl = '\r\n' if '\r\n' in raw else '\n'; t = raw.replace('\r\n', '\n')
            assert t.count(S_OLD) == 1, m
            files[p] = t.replace(S_OLD, S_NEW).replace('\n', nl).encode('utf-8'); changed.add(p)
        with zipfile.ZipFile(out, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            for info in prev.infolist():
                i = copy.copy(info); i.compress_type = zipfile.ZIP_DEFLATED
                z.writestr(i, files[info.filename], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        with zipfile.ZipFile(out) as z:
            assert z.testzip() is None and z.namelist() == prev.namelist()
            for k in prev.namelist():
                if k not in changed: assert z.read(k) == prev.read(k), k
    print(out)


if __name__ == '__main__':
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument('src', type=Path); a.add_argument('out', type=Path)
    x = a.parse_args(); build(x.src, x.out)
