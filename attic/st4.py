# -*- coding: utf-8 -*-
import io,os,sys,subprocess,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
FULL=io.open("_asm",encoding="utf-8").read()
def run2(n,s,tl="70"):
    io.open("solveH.py","w",encoding="utf-8").write(s)
    r0=subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    if r0.returncode: print(n+": GEN-ERR"); return
    os.environ["TL"]=tl
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    m=re.search(r"status:\s*(\w+)",o)
    st=m.group(1) if m else "ERR"
    print(n+": "+st+("   <<< זה!" if st!="INFEASIBLE" else ""))
run2("בלי tjS-כפול", FULL.replace('m.Add(sum(tjS.values())==1)','m.Add(sum(tjS.values())<=1)'))
run2("בלי _a6", FULL.replace('if _a6: m.Add(sum(_a6)>=1)',''))
run2("בלי duty", FULL.replace('    m.Add(sum(duty[(c,d)] for d in range(5))==1)','    pass'))
run2("בלי miss_fri==2", FULL.replace('if _miss_fri: m.Add(sum(_miss_fri)==2)','if _miss_fri: m.Add(sum(_miss_fri)<=2)'))
run2("בלי גלית-ארז", FULL.replace('m.Add(sum(gj.values())==2)','m.Add(sum(gj.values())<=2)'))
run2("בלי כפולי-ליבה", FULL.replace('        if ps: m.Add(sum(ps)>=1)','        pass'))
run2("בלי אסיף-שישי>=2", FULL.replace('if asif_fri: m.Add(sum(asif_fri)>=2)',''))
run2("בלי שיר-3-בשישי", FULL.replace('    if _v: m.Add(sum(_v)==1)','    pass'))
