#!/usr/bin/env python3
"""0.4.71 -> 0.4.72: 두 전투 안정제를 둘 다 연구할 수 있게 하고 효과를 나눈다 (4번, 사용자 2026-10-23 "둘 다 연구, 효과 나눔").

이전(0.4.45/0.4.47): 자날판과 협동전판이 택일이고, 협동전판도 치료 속도·에너지 효율만 바꿔 자날판과 사실상 같았다.
지금:
  자날판 StabilizerMedPacks (1페이지) — 치료 속도·에너지 효율 (원작 값 그대로).
  협동전판 RMC_StabilizerCoop (2페이지) — 레이너 협동전 전투 안정제의 나머지 두 효과만:
    기계 유닛 치료 (용병 의무관 치료 대상에 기계 포함, 플레이어 1만)
    치료받는 동안 받는 피해 25% 감소 (협동전 RaynorMedicSafeguardMastery 의 -0.25, 0.5초 버프를 치료 주기 0.25초마다 갱신).
  치료 속도·에너지 효율은 협동전판에서 뺐다(겹침 없음). 서로 숨기던 조건을 없애 둘 다 연구할 수 있다.
비용·시간(100/100·60초 시험값)과 무기고 구매 처리는 그대로.

Usage: python3 tools/build_v0472.py <0.4.71 zip> <new output zip>
"""
import argparse, copy, re, zipfile
from pathlib import Path
from build_v0464 import LOCALES, update_lines

M4 = 'TTychus01.SC2Map/'
GD = M4 + 'base.sc2data/gamedata/'
OLD, NEW = b'version=0.4.71', b'version=0.4.72'
MECH = 'Ground,Visible;Self,Enemy,Air,Structure,Missile,UnderConstruction,Dead,Hidden,Invulnerable'


def sub1(t, a, b):
    assert t.count(a) == 1, a
    return t.replace(a, b)


def append(t, extra):
    i = t.rindex('</Catalog>')
    return t[:i] + extra + t[i:]


def nodes(d):
    t = d.decode('utf-8')
    t = sub1(t, '<OperandArray value="RMA_StabilizerMedPacksNotQueued" />\n    <OperandArray value="RMC_StabilizerCoopNotQueued" />',
             '<OperandArray value="RMA_StabilizerMedPacksNotQueued" />') if '<OperandArray value="RMA_StabilizerMedPacksNotQueued" />\n    <OperandArray value="RMC_StabilizerCoopNotQueued" />' in t else t
    for show, keep, drop in [('RMA_StabilizerMedPacksShow', 'RMA_StabilizerMedPacksNotQueued', 'RMC_StabilizerCoopNotQueued'),
                             ('RMC_StabilizerCoopShow', 'RMC_StabilizerCoopNotQueued', 'RMA_StabilizerMedPacksNotQueued')]:
        m = re.search(rf'<CRequirementAnd id="{show}">.*?</CRequirementAnd>', t, re.S)
        b = re.sub(rf'\s*<OperandArray value="{drop}" />', '', m.group(0))
        assert f'value="{keep}"' in b and drop not in b
        t = t[:m.start()] + b + t[m.end():]
    assert 'id="RMC_StabilizerCoopDone"' not in t
    t = append(t, '<CRequirementCountUpgrade id="RMC_StabilizerCoopDone"><Count Link="RMC_StabilizerCoop" State="CompleteOnly" /></CRequirementCountUpgrade>')
    return t.encode('utf-8')


def reqs(d):
    t = d.decode('utf-8')
    return append(t, '<CRequirement id="RMC_HaveStabilizerCoopReq"><NodeArray index="Use" Link="RMC_StabilizerCoopDone" /></CRequirement>').encode('utf-8')


def validators(d):
    t = d.decode('utf-8')
    return append(t, '<CValidatorPlayerRequirement id="RMC_HaveStabilizerCoop"><WhichPlayer Value="Caster" /><Find value="1" />'
                     '<Value value="RMC_HaveStabilizerCoopReq" /></CValidatorPlayerRequirement>').encode('utf-8')


def upgrades(d):
    t = d.decode('utf-8')
    m = re.search(r'<CUpgrade id="RMC_StabilizerCoop">.*?</CUpgrade>', t, re.S)
    b = re.sub(r'\s*<EffectArray [^>]*MercMedicHeal[^>]*/>', '', m.group(0))
    assert 'EffectArray' not in b
    return (t[:m.start()] + b + t[m.end():]).encode('utf-8')


def behaviors(d):
    t = d.decode('utf-8')
    mod = ''.join(f'<DamageTakenFraction index="{k}" value="0.75" />' for k in ['Melee', 'Ranged', 'Spell', 'Splash'])
    return append(t, '<CBehaviorBuff id="RMC_StabilizerGuard"><Duration value="0.5" /><MaxStackCount value="1" />'
                     '<InfoIcon value="Assets\\Textures\\btn-upgrade-raynor-stabilizermedpacks.dds" />'
                     f'<Modification>{mod}</Modification></CBehaviorBuff>').encode('utf-8')


def effects(d):
    t = d.decode('utf-8')
    t = sub1(t, '<CEffectSet id="MercMedicHealPeriodicSet">\n    <EffectArray value="MercMedicHealExtraDelay1" />',
             '<CEffectSet id="MercMedicHealPeriodicSet">\n    <EffectArray value="MercMedicHealExtraDelay1" />\n    <EffectArray value="RMC_StabilizerGuardAB" />')
    return append(t, '<CEffectApplyBehavior id="RMC_StabilizerGuardAB"><ValidatorArray value="RMC_HaveStabilizerCoop" />'
                     '<Behavior value="RMC_StabilizerGuard" /></CEffectApplyBehavior>').encode('utf-8')


def script(d):
    t = d.decode('utf-8')
    a = 'void gf_m4_Icons () {\n'
    t = sub1(t, a, a + '    // 0.4.72: co-op Stabilizer Medpacks lets Raynor\'s medics heal mechanical units.\n'
             '    if (!gv_m4_mechHeal && TechTreeUpgradeCount(1,"RMC_StabilizerCoop",c_techCountCompleteOnly)>0) {\n'
             f'        CatalogFieldValueSet(c_gameCatalogAbil,"MercMedicHeal","TargetFilters",1,"{MECH}");\n'
             '        gv_m4_mechHeal=true;\n    }\n')
    t = sub1(t, '\n// 0.4.71: research/upgrade info icons', '\nbool gv_m4_mechHeal;\n\n// 0.4.71: research/upgrade info icons')
    return t.encode('utf-8')


STRINGS = {
    'Behavior/Name/RMC_StabilizerGuard': '전투 안정제 보호 /// Stabilizer Protection',
    'Behavior/Tooltip/RMC_StabilizerGuard': '치료받는 동안 받는 피해가 25% 감소합니다. /// Takes 25% less damage while being healed.',
    'Button/Tooltip/RMC_StabilizerCoop': '용병 의무관이 기계 유닛도 치료하고, 치료받는 유닛은 받는 피해가 25% 감소합니다. 자날판 전투 안정제(치료 속도·에너지 효율)와 함께 연구할 수 있습니다. /// Medics can heal mechanical units, and healed units take 25% less damage. Stacks with the Wings of Liberty Stabilizer Medpacks (healing speed and energy efficiency).',
}


def build(source, output):
    if output.exists(): raise ValueError('Output must be new')
    with zipfile.ZipFile(source) as prev:
        assert prev.testzip() is None and OLD in prev.read('metadata.txt').splitlines()
        files = {n: prev.read(n) for n in prev.namelist()}
        for f, fn in [('requirementnodedata', nodes), ('requirementdata', reqs), ('validatordata', validators),
                      ('upgradedata', upgrades), ('behaviordata', behaviors), ('effectdata', effects)]:
            files[GD + f + '.xml'] = fn(files[GD + f + '.xml'])
        files[M4 + 'mapscript.galaxy'] = script(files[M4 + 'mapscript.galaxy'])
        for loc in ('kokr',) + LOCALES:
            path = M4 + loc + '.sc2data/localizeddata/gamestrings.txt'
            values = STRINGS if loc == 'kokr' else {k: v.split(' /// ', 1)[1] for k, v in STRINGS.items()}
            files[path] = update_lines(files[path], values)
        files['metadata.txt'] = files['metadata.txt'].replace(OLD, NEW)
        for n in files:
            if n != 'metadata.txt' and not n.startswith(M4): assert files[n] == prev.read(n), n
        try:
            with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED) as out:
                for info in prev.infolist(): out.writestr(copy.copy(info), files[info.filename])
            with zipfile.ZipFile(output) as out: assert out.testzip() is None
        except BaseException:
            output.unlink(missing_ok=True); raise
    print(output)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path); p.add_argument('output', type=Path)
    a = p.parse_args(); build(a.source, a.output)
