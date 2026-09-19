# -*- coding: utf-8 -*-
import io,os,sys,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
shutil.copy("solveH.py","solveH.a6"); shutil.copy("make_unified.py","mu.a6")
BH=io.open("solveH.py",encoding="utf-8").read()
BM=io.open("make_unified.py",encoding="utf-8").read()
def test(name,fh=None,fm=None):
    io.open("solveH.py","w",encoding="utf-8").write(fh(BH) if fh else BH)
    io.open("make_unified.py","w",encoding="utf-8").write(fm(BM) if fm else BM)
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="60"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    print(name+": "+("INFEASIBLE" if "INFEASIBLE" in (r.stdout or "")+(r.stderr or "") else "FEASIBLE"))
    shutil.copy("solveH.a6","solveH.py"); shutil.copy("mu.a6","make_unified.py")
test("בלי סידור חדר אוכל", lambda s:s.replace('    m.Add(sum(duty[(c,d)] for d in range(5))==1)','    pass'))
test("בלי שיעור כפול תמיר-שישי", lambda s:s.replace('m.Add(sum(tjS.values())==1)','m.Add(sum(tjS.values())<=1)'))
test("בלי מיס-שישי==2", lambda s:s.replace('if _miss_fri: m.Add(sum(_miss_fri)==2)','if _miss_fri: m.Add(sum(_miss_fri)<=2)'))
test("בלי כפולים-ליבה", lambda s:s.replace('        if ps: m.Add(sum(ps)>=1)','        pass'))
test("בלי חלוקת נעמי-אלי בז/ח", lambda s:s.replace('        if _v: m.Add(sum(_v)>=1)','        pass'))
test("בלי parity", None, lambda s:s.replace('            m.Add(_tot[0]==_tot[_i]); _neq+=1','            _neq+=1'))
