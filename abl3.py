# -*- coding: utf-8 -*-
import io,os,sys,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
shutil.copy("solveH.py","solveH.abl")
BASE=io.open("solveH.py",encoding="utf-8").read()
def test(name, transform):
    s=transform(BASE)
    io.open("solveH.py","w",encoding="utf-8").write(s)
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="80"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    st="INFEASIBLE" if "INFEASIBLE" in (r.stdout or "")+(r.stderr or "") else "FEASIBLE"
    print(f"{name}: {st}")
    shutil.copy("solveH.abl","solveH.py")
def no_eli(s): return s.replace('for _k in [k for k in x if k[0] in T9 and k[3]=="אלי"]:','for _k in []:')
def no_swap(s): return s.replace('m.Add(sum(_v)==0)          # תמיר יוצא מח גלית','m.Add(sum(_v)<=2)').replace('m.Add(sum(_v)==2)          # אלי נכנס במקומו','m.Add(sum(_v)<=2)')
def no_ovr(s): return s.replace('_ovr={("ט אסיף","חינוך"):4,("ט אסיף","מתמטיקה"):3}','_ovr={}').replace('''for _k in [k for k in x if k[0]==_MC and k[3]=="חסר מורה" and k[2]!="חינוך"]:
    m.Add(x[_k]==0)''','')
def no_naomi(s): return s.replace('    m.Add(sum(_v)==1)\n_v=[x[("ז נעמי"','    m.Add(sum(_v)<=1)\n_v=[x[("ז נעמי"')
def no_tj(s): return s.replace('m.Add(sum(tjS.values())==1)','m.Add(sum(tjS.values())<=1)')
def no_tnach(s): return s.replace('if _v9: m.Add(sum(_v9)==2)','')
test("בלי איסור אלי", no_eli)
test("בלי ההחלפה בח", no_swap)
test("בלי override חינוך/מתמטיקה", no_ovr)
test("בלי חובת ספרות נעמי", no_naomi)
test("בלי שיעור כפול תמיר", no_tj)
test("בלי תנך=תמיר בט אסיף", no_tnach)
