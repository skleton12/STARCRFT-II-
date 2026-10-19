#!/usr/bin/env python3
"""0.4.30 -> 0.4.31: explicitly allow custom research commands after campaign tech restrictions.

The XML button/upgrade allow flags alone are not the runtime ability-command allow state.
Keep the existing research prerequisites, costs, effects and card positions. Reapply the
command permissions from the existing init/tick hook; suppress the original research
commands so that the original first-row Concussive Shells cannot bypass the custom chain.
Gameplay confirmation is still required.
"""
import argparse
import copy
import zipfile
from pathlib import Path

OLD = b'version=0.4.30'
NEW = b'version=0.4.31'
MAP = 'TTychus01.SC2Map/'
ANCHOR = 'void gf_m4_Mercs () {\n'
PERMISSIONS = '''    // 0.4.31: runtime command permissions are separate from upgrade permissions.
    // Show/Use requirements still gate each research, so this does not unlock future units.
    TechTreeUpgradeAllow(1,"RM4_HammerUnlocked",true);
    if (TechTreeUpgradeCount(1,"RM4_HammerUnlocked",c_techCountQueuedOrBetter)==0 &&
        (TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",3)) ||
         TechTreeUnitCount(1,"HammerSecurity",c_techCountCompleteOnly)>0)) {
        TechTreeUpgradeAddLevel(1,"RM4_HammerUnlocked",1);
    }
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",5),true);
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",6),true);
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",7),true);
    TechTreeAbilityAllow(1,AbilityCommand("RM3_TechResearch",8),true);
    TechTreeAbilityAllow(1,AbilityCommand("BarracksTechLabResearch",0),false);
    TechTreeAbilityAllow(1,AbilityCommand("BarracksTechLabResearch",1),false);
    TechTreeAbilityAllow(1,AbilityCommand("BarracksTechLabResearch",2),false);
'''


def script(data):
    text = data.decode('utf-8')
    nl = '\r\n' if '\r\n' in text else '\n'
    text = text.replace('\r\n', '\n')
    assert text.count(ANCHOR) == 1
    text = text.replace(ANCHOR, ANCHOR + PERMISSIONS)
    return text.replace('\n', nl).encode('utf-8')


def build(source, output):
    if output.exists():
        raise FileExistsError(output)
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        assert len(set(prev.namelist())) == len(prev.namelist())
        with zipfile.ZipFile(output, 'x') as out:
            for info in prev.infolist():
                data = prev.read(info.filename)
                if info.filename == MAP + 'mapscript.galaxy':
                    data = script(data)
                elif info.filename == 'metadata.txt':
                    data = data.replace(OLD, NEW)
                out.writestr(copy.copy(info), data)
        with zipfile.ZipFile(output) as out:
            assert out.testzip() is None and out.namelist() == prev.namelist()
            for name in prev.namelist():
                if name not in (MAP + 'mapscript.galaxy', 'metadata.txt'):
                    assert prev.read(name) == out.read(name), name
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    args = p.parse_args()
    build(args.source, args.output)
