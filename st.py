# -*- coding: utf-8 -*-
import io,os,sys,subprocess,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
B=io.open("_step1",encoding="utf-8").read()   # feasible base
def run2(n,s,tl="90"):
    io.open("solveH.py","w",encoding="utf-8").write(s)
    r0=subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    if r0.returncode: print(n+": GEN-ERR"); return
    os.environ["TL"]=tl
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    m=re.search(r"status:\s*(\w+)",o)
    print(n+": "+(m.group(1) if m else "ERR"))
def f_eli(s): return s.replace("def tblk(t):",'ebusy["אלי"].discard((CM["שלישי"],5))\ndef tblk(t):')
def f_tue(s):
    a='''for c in HCLASSES:
    for h in range(1,7): m.Add(free[(c,(2,h))]==0)     # שלישי מלא עד 6'''
    return s.replace(a,'''for c in HCLASSES:
    _lt=5 if GRADE[c] in "זח" else 6
    for h in range(1,_lt+1): m.Add(free[(c,(2,h))]==0)
    if GRADE[c] in "זח": m.Add(free[(c,(2,6))]==1)''')
A='# שירה בציבור: יום שישי שעה 2, כל החטיבה יחד באולם חדר האוכל'
def f_pinZ(s):
    return s.replace(A,'''for _cz in ("ז נעמי","ז אלי","ח גלית"):
    _v5=[x[k] for k in x if k[0]==_cz and k[1]==(2,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)

'''+A)
def f_thu(s):
    return s.replace(A,'''for _c9p in T9:
    _v5=[x[k] for k in x if k[0]==_c9p and k[1]==(4,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)
    for _hb in (6,7): m.Add(free[(_c9p,(4,_hb))]==1)

'''+A)
def f_hpool(s):
    a='''        if subj=="חינוך":
            pairs[c].append((subj,HHOME[c]))
            if c=="ז אלי": pairs[c].append((subj,"שיר"))'''
    return s.replace(a,a+'''
            if c=="ח גלית":
                pairs[c].append((subj,"נעמי")); pairs[c].append((subj,"אלי"))''')
run2("1 שלישי-קצר בלבד", f_tue(f_eli(f_hpool(B))))
run2("2 +פין ז/ח", f_pinZ(f_tue(f_eli(f_hpool(B)))))
run2("3 חמישי-ט בלבד", f_thu(f_hpool(B)))

print("--- מה בתוך שלישי-קצר שובר? ---")
def f_tue_noeat(s):
    a='''for c in HCLASSES:
    for h in range(1,7): m.Add(free[(c,(2,h))]==0)     # שלישי מלא עד 6'''
    return s.replace(a,'''for c in HCLASSES:
    _lt=5 if GRADE[c] in "זח" else 6
    for h in range(1,_lt+1): m.Add(free[(c,(2,h))]==0)''')
run2("1a שלישי-קצר בלי ריק-ש6", f_tue_noeat(f_eli(f_hpool(B))))
def f_tue_zonly(s):
    a='''for c in HCLASSES:
    for h in range(1,7): m.Add(free[(c,(2,h))]==0)     # שלישי מלא עד 6'''
    return s.replace(a,'''for c in HCLASSES:
    _lt=5 if GRADE[c]=="ז" else 6
    for h in range(1,_lt+1): m.Add(free[(c,(2,h))]==0)
    if GRADE[c]=="ז": m.Add(free[(c,(2,6))]==1)''')
run2("1b רק כיתות ז מקוצרות", f_tue_zonly(f_eli(f_hpool(B))))
def f_thu_noempty(s):
    return s.replace(A,'''for _c9p in T9:
    _v5=[x[k] for k in x if k[0]==_c9p and k[1]==(4,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)

'''+A)
run2("3a חמישי-ט רק פין (בלי ריק)", f_thu_noempty(f_hpool(B)))
