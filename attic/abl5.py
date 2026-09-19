# -*- coding: utf-8 -*-
import io,os,sys,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
shutil.copy("solveH.py","solveH.a5"); shutil.copy("make_unified.py","mu.a5")
BH=io.open("solveH.py",encoding="utf-8").read()
BM=io.open("make_unified.py",encoding="utf-8").read()
def test(name,fh=None,fm=None):
    io.open("solveH.py","w",encoding="utf-8").write(fh(BH) if fh else BH)
    io.open("make_unified.py","w",encoding="utf-8").write(fm(BM) if fm else BM)
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="70"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    print(name+": "+("INFEASIBLE" if "INFEASIBLE" in (r.stdout or "")+(r.stderr or "") else "FEASIBLE"))
    shutil.copy("solveH.a5","solveH.py"); shutil.copy("mu.a5","make_unified.py")
test("בלי הביתה-שלישי ז+ח", lambda s:s.replace('m.Add(hfree[(c,(d,h))]==1); continue','pass; continue'))
test("בלי הביתה-חמישי ט", lambda s:s.replace('        m.Add(hfree[(_c9,(4,_h))]==1)','        pass'))
test("בלי חלוקת רב מלל חדשה", lambda s:s.replace('        if _v: m.Add(sum(_v)>=1)','        pass'))
test("בלי תמיר==3", lambda s:s.replace('m.Add(sum(_v)==3)','m.Add(sum(_v)<=3)'))
test("בלי async caps", None, lambda s:s.replace('-_ASYNC.get(t,0)',''))
test("בלי duty", lambda s:s.replace('    m.Add(sum(duty[(c,d)] for d in range(5))==1)','    pass'))
test("בלי parity", None, lambda s:s.replace('            m.Add(_tot[0]==_tot[_i]); _neq+=1','            _neq+=1'))
