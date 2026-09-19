# -*- coding: utf-8 -*-
import io,os,sys,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
shutil.copy("solveH.py","_sh"); shutil.copy("hdata.py","_hd")
BH=io.open("solveH.py",encoding="utf-8").read()
BD=io.open("hdata.py",encoding="utf-8").read()
def t(name,fh=None,fd=None):
    io.open("solveH.py","w",encoding="utf-8").write(fh(BH) if fh else BH)
    io.open("hdata.py","w",encoding="utf-8").write(fd(BD) if fd else BD)
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="55"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    print(name+": "+("INFEASIBLE" if "INFEASIBLE" in o else ("ERROR" if r.returncode else "FEASIBLE")))
    shutil.copy("_sh","solveH.py"); shutil.copy("_hd","hdata.py")
t("בלי פין חינוך אחרי מגמות", lambda s:s.replace('    if _k5 in x: m.Add(x[_k5]==1)','    pass'))
t("בלי חדר אוכל (ריק)", lambda s:s.replace('    m.Add(hfree[(_cz,(2,6))]==1)','    pass').replace('    for _h in (6,7): m.Add(hfree[(_c9,(4,_h))]==1)','    pass'))
t("ספרות/היסטוריה >=1 במקום ==2", lambda s:s.replace('        if _v: m.Add(sum(_v)==2)','        if _v: m.Add(sum(_v)>=1)'))
t("רב מלל ט=4", None, lambda s:s.replace('"רב מלל":{"ז":4,"ח":4,"ט":5},','"רב מלל":{"ז":4,"ח":4,"ט":4},'))
t("חינוך ט=1", None, lambda s:s.replace('"חינוך":{"ז":3,"ח":4,"ט":2},','"חינוך":{"ז":3,"ח":4,"ט":1},'))
t("בלי תגבור", None, lambda s:s.replace('"תגבור":{"ז":0,"ח":2,"ט":0},','"תגבור":{"ז":0,"ח":0,"ט":0},'))

print("--- סבב 2 ---")
t("בלי overrides ט אסיף", lambda s:s.replace('_ovr={("ט אסיף","חינוך"):4,("ט אסיף","מתמטיקה"):3}','_ovr={}'))
t("בלי miss_fri==2", lambda s:s.replace('if _miss_fri: m.Add(sum(_miss_fri)==2)','if _miss_fri: m.Add(sum(_miss_fri)<=2)'))
t("בלי חינוך-בלבד לחסר", lambda s:s.replace('''for _k in [k for k in x if k[0]==_MC and k[3]=="חסר מורה" and k[2]!="חינוך"]:
    m.Add(x[_k]==0)''',''))
t("בלי _a6 (חינוך אסיף ש6)", lambda s:s.replace('if _a6: m.Add(sum(_a6)>=1)',''))
t("בלי parity מקבילות", lambda s:s, None)
t("בלי h5_pin ח גלית", lambda s:s.replace('m.Add(hfree[("ח גלית",(0,5))]==0)','').replace('m.Add(hfree[("ח גלית",(4,5))]==0)',''))
t("בלי מינימום יומי ח", lambda s:s.replace('m.Add(sum(_occ)>=min(4,HDAY[_d]))','pass'))
