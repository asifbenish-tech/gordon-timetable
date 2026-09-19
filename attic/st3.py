# -*- coding: utf-8 -*-
import io,os,sys,subprocess,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
FULL=io.open("_asm",encoding="utf-8").read()
def run2(n,s,tl="80"):
    io.open("solveH.py","w",encoding="utf-8").write(s)
    r0=subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    if r0.returncode: print(n+": GEN-ERR"); return
    os.environ["TL"]=tl
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    m=re.search(r"status:\s*(\w+)",o)
    print(n+": "+(m.group(1) if m else "ERR"))
# ריק רק ש6 (ולא ש7); ריק רק ש7
run2("ט ריק רק ש7", FULL.replace('    for _hb in (6,7): m.Add(free[(_c9p,(4,_hb))]==1)','    m.Add(free[(_c9p,(4,7))]==1)'))
run2("ט ריק רק ש6", FULL.replace('    for _hb in (6,7): m.Add(free[(_c9p,(4,_hb))]==1)','    m.Add(free[(_c9p,(4,6))]==1)'))
# ריק לכיתה אחת בלבד
run2("ריק רק בט תמיר", FULL.replace('''for _c9p in T9:
    _v5=[x[k] for k in x if k[0]==_c9p and k[1]==(4,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)
    for _hb in (6,7): m.Add(free[(_c9p,(4,_hb))]==1)''','''for _c9p in T9:
    _v5=[x[k] for k in x if k[0]==_c9p and k[1]==(4,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)
for _hb in (6,7): m.Add(free[("ט תמיר",(4,_hb))]==1)'''))
