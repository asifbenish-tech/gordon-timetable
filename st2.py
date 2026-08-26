# -*- coding: utf-8 -*-
import io,os,sys,subprocess,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
FULL=io.open("_asm",encoding="utf-8").read()
def run2(n,s,tl="90"):
    io.open("solveH.py","w",encoding="utf-8").write(s)
    r0=subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    if r0.returncode: print(n+": GEN-ERR"); return
    os.environ["TL"]=tl
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    m=re.search(r"status:\s*(\w+)",o)
    print(n+": "+(m.group(1) if m else "ERR"))
# הסרה סלקטיבית מהמכלול
run2("בלי ריק-ש6-שלישי", FULL.replace('    if GRADE[c] in "זח": m.Add(free[(c,(2,6))]==1)     # סוף יום המגמות',''))
run2("בלי ריק-חמישי-ט", FULL.replace('    for _hb in (6,7): m.Add(free[(_c9p,(4,_hb))]==1)','    pass'))
run2("בלי פין-חינוך-שלישי", FULL.replace('''for _cz in ("ז נעמי","ז אלי","ח גלית"):
    _v5=[x[k] for k in x if k[0]==_cz and k[1]==(2,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)''','pass'))
run2("בלי נוכחות-נעמי-אלי", FULL.replace('    if _vv: m.Add(sum(_vv)>=1)','    pass'))
