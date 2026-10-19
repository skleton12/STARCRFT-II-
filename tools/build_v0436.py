#!/usr/bin/env python3
"""Diagnostic only: report effective live research state when selecting a Tech Lab."""
import argparse,copy,zipfile
from pathlib import Path
M='TTychus01.SC2Map/'
CODE='''bool gt_rmLabDiagnostic_Func (bool testConds, bool runActions) {
    unit u;
    string ty;
    string msg;
    int n;
    int i;
    string cmd;
    string path;
    if (!runActions) { return true; }
    u=EventUnit();
    ty=UnitGetType(u);
    if (ty!="BarracksTechLab" && ty!="TechLab" && ty!="BarracksTechReactor") { return true; }
    msg="0.4.36 / "+ty+" / custom="+IntToText(BoolToInt(UnitAbilityExists(u,"RM3_TechResearch")))+" / enabled="+IntToText(BoolToInt(UnitAbilityCheck(u,"RM3_TechResearch",true)));
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringExternal("Param/Value/RM_LabDiagHeader")+StringToText(msg));
    msg="unlock="+IntToText(TechTreeUpgradeCount(1,"RM4_HammerUnlocked",c_techCountCompleteOnly))+" / train="+IntToText(BoolToInt(TechTreeAbilityIsAllowed(1,AbilityCommand("BarracksTrain",3))));
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringExternal("Param/Value/RM_LabDiagGate")+StringToText(msg));
    msg="Concussive="+IntToText(TechTreeUpgradeCount(1,"PunisherGrenades",c_techCountCompleteOnly))+" / Suppression="+IntToText(TechTreeUpgradeCount(1,"RM4_Suppression",c_techCountCompleteOnly))+" / Shrapnel="+IntToText(TechTreeUpgradeCount(1,"RM4_Shrapnel",c_techCountCompleteOnly));
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringExternal("Param/Value/RM_LabDiagLevels")+StringToText(msg));
    msg="cmd6="+IntToText(BoolToInt(TechTreeAbilityIsAllowed(1,AbilityCommand("RM3_TechResearch",5))))+" / cmd7="+IntToText(BoolToInt(TechTreeAbilityIsAllowed(1,AbilityCommand("RM3_TechResearch",6))))+" / cmd9="+IntToText(BoolToInt(TechTreeAbilityIsAllowed(1,AbilityCommand("RM3_TechResearch",8))));
    UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringExternal("Param/Value/RM_LabDiagAllow")+StringToText(msg));
    n=CatalogFieldValueCount(c_gameCatalogUnit,ty,"CardLayouts[0].LayoutButtons",1);
    for (i=0;i<n;i+=1) {
        path="CardLayouts[0].LayoutButtons["+IntToText(i)+"]";
        cmd=CatalogFieldValueGet(c_gameCatalogUnit,ty,path+".AbilCmd",1);
        if (cmd=="RM3_TechResearch,Research6" || cmd=="RM3_TechResearch,Research7" || cmd=="RM3_TechResearch,Research9") {
            msg=cmd+" / row="+CatalogFieldValueGet(c_gameCatalogUnit,ty,path+".Row",1)+" / col="+CatalogFieldValueGet(c_gameCatalogUnit,ty,path+".Column",1);
            UIDisplayMessage(PlayerGroupSingle(1),c_messageAreaChat,StringExternal("Param/Value/RM_LabDiagCard")+StringToText(msg));
        }
    }
    return true;
}

'''
STRINGS={'Header':('기술실 진단: ','Tech Lab diagnostic: '),'Gate':('해금 상태: ','Unlock state: '),'Levels':('연구 단계: ','Research levels: '),'Allow':('연구 명령 허용: ','Research permissions: '),'Card':('버튼 연결: ','Button link: ')}
def script(d):
 text=d.decode();nl='\r\n' if '\r\n' in text else '\n';text=text.replace('\r\n','\n');a='void gf_m4_Init () {';assert text.count(a)==1;text=text.replace(a,CODE+a)
 a='    gf_m4_Mercs();\n    PlayerSetColorIndex(8,2,true);';assert text.count(a)==1;text=text.replace(a,'    t=TriggerCreate("gt_rmLabDiagnostic_Func");\n    TriggerAddEventUnitSelected(t,null,1,true);\n'+a)
 return text.replace('\n',nl).encode()
def build(source,output):
 assert not output.exists()
 with zipfile.ZipFile(source) as prev:
  assert b'version=0.4.35' in prev.read('metadata.txt').splitlines()
  with zipfile.ZipFile(output,'x') as out:
   for info in prev.infolist():
    n=info.filename;d=prev.read(n)
    if n=='metadata.txt':d=d.replace(b'version=0.4.35',b'version=0.4.36')
    elif n==M+'mapscript.galaxy':d=script(d)
    elif n.startswith(M) and n.endswith('/gamestrings.txt'):
     ko='/kokr.' in n
     d+= ('\n'+''.join('Param/Value/RM_LabDiag'+k+'='+((v[0]+' /// '+v[1]) if ko else v[1])+'\n' for k,v in STRINGS.items())).encode()
    out.writestr(copy.copy(info),d)
  with zipfile.ZipFile(output) as out:
   assert out.testzip() is None and out.namelist()==prev.namelist()
   for n in prev.namelist():
    if n not in ['metadata.txt',M+'mapscript.galaxy'] and not(n.startswith(M) and n.endswith('/gamestrings.txt')):assert prev.read(n)==out.read(n),n
 print(output)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args();build(a.source,a.output)
