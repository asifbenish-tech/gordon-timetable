# -*- coding: utf-8 -*-
import io,os,sys,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
shutil.copy("solveH.py","solveH.a4")
BASE=io.open("solveH.py",encoding="utf-8").read()
def test(name,transform):
    io.open("solveH.py","w",encoding="utf-8").write(transform(BASE))
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="70"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    st="INFEASIBLE" if "INFEASIBLE" in (r.stdout or "")+(r.stderr or "") else "FEASIBLE"
    print(f"{name}: {st}")
    shutil.copy("solveH.a4","solveH.py")
test("בלי h5_pin", lambda s:s.replace('m.Add(hfree[("ח גלית",(0,5))]==0)','').replace('m.Add(hfree[("ח גלית",(4,5))]==0)',''))
test("בלי מינימום יומי ח", lambda s:s.replace('m.Add(sum(_occ)>=min(4,HDAY[_d]))','pass'))
test("בלי שישי מלא ח", lambda s:s.replace('    m.Add(hfree[("ח גלית",(5,_h))]==0)','    pass'))
test("בלי חינוך ש7 גלית", lambda s:s.replace('if _g7: m.Add(sum(_g7)==1)',''))
test("בלי מינימום אלי", lambda s:s.replace('if _all_eli: m.Add(sum(_all_eli)>=8)',''))
test("בלי תגבור==2", lambda s:s.replace('"תגבור":{"ז":0,"ח":2,"ט":0},','"תגבור":{"ז":0,"ח":2,"ט":0},'))
test("בלי אזרחות-tjS", lambda s:s.replace('m.Add(sum(tjS.values())==1)','m.Add(sum(tjS.values())<=1)'))
test("בלי חובת שישי אסיף>=2", lambda s:s.replace('if asif_fri: m.Add(sum(asif_fri)>=2)',''))

print("--- סבב 2: האילוץ של שלישי עצמו ---")
test("שלישי עד 6 רק לט", lambda s:s.replace('if d==2 and GRADE[c]=="ט": m.Add(hfree[(c,(d,h))]==0)   # ט: שלישי עד 6 חובה','if d==2 and GRADE[c]=="ט": m.Add(hfree[(c,(d,h))]==0)'))
test("בלי איסור חסר בשלישי", lambda s:s.replace('''for _k in [k for k in x if k[3]=="חסר מורה" and k[1][0]!=5]:
    m.Add(x[_k]==0)                               # חסר מורה: רק שישי ט אסיף''','''for _k in [k for k in x if k[3]=="חסר מורה" and k[1][0]!=5 and not (k[1][0]==2 and k[1][1] in (5,6))]:
    m.Add(x[_k]==0)'''))
test("בלי סנכרון-אלי-hebusy", lambda s:s.replace('''hebusy["אלי"].discard((HCM["שלישי"],5)); hebusy["אלי"].discard((HCM["שלישי"],6))
for _h5 in HSED["מעגלי שיח שני"]: hebusy["אלי"].add((HCM["שני"],_h5))''',''))
