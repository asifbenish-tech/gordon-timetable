# -*- coding: utf-8 -*-
"""בודק שינויי-כלל מועמדים: כל אחד בריצה נפרדת, ומחזיר את מספר החוסרים."""
import io,os,sys,json,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
TL="130"
for f in ("data2.py","solveEI.py","sol_J.json","sol_hat.json","make_unified.py"):
    shutil.copy(f, f+".exp")
def run_and_count():
    os.environ["TL"]=TL
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    out=(r.stdout or "")+(r.stderr or "")
    if "INFEASIBLE" in out or r.returncode!=0: return None
    subprocess.run([sys.executable,"fill2.py"],capture_output=True)
    S=json.load(io.open("sol_J.json",encoding="utf-8"))
    from data2 import CLASSES,SLOTS
    return sum(1 for c in CLASSES for (d,h) in SLOTS if not S[c][f"{d},{h}"])
def restore():
    for f in ("data2.py","solveEI.py","sol_J.json","sol_hat.json","make_unified.py"):
        shutil.copy(f+".exp", f)
res={}
# E1: מעגל שיח של שני עובר לשעות 5-6
s=io.open("make_unified.py",encoding="utf-8").read()
s=s.replace('_hm=set(_SEDF["מעגלי שיח שני"])','_hm={5,6}')
io.open("make_unified.py","w",encoding="utf-8").write(s)
res["מעגל שני 5-6"]=run_and_count(); restore()
# E2: היום החופשי של דניאל עובר לרביעי
s=io.open("data2.py",encoding="utf-8").read()
s=s.replace('"דניאל":["שלישי"],','"דניאל":["רביעי"],')
io.open("data2.py","w",encoding="utf-8").write(s)
res["דניאל חופש ברביעי"]=run_and_count(); restore()
# E3: היום החופשי של דני עובר לרביעי
s=io.open("data2.py",encoding="utf-8").read()
s=s.replace('"דני":["שלישי"],','"דני":["רביעי"],')
io.open("data2.py","w",encoding="utf-8").write(s)
res["דני חופש ברביעי"]=run_and_count(); restore()
# E4: מרים - דרישת שכבות נמוכות יורדת מ-7 ל-5
s=io.open("solveEI.py",encoding="utf-8").read()
s=s.replace('m.Add(sum(_ml)>=7)','m.Add(sum(_ml)>=5)')
io.open("solveEI.py","w",encoding="utf-8").write(s)
res["מרים: 5 בנמוכות במקום 7"]=run_and_count(); restore()
lines=["ניסוי | חוסרים (בסיס: 7)"]
for k,v in sorted(res.items(),key=lambda z:(999 if z[1] is None else z[1])):
    lines.append(f"{k} | "+("לא אפשרי" if v is None else str(v)))
io.open("exper_out.txt","w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))

# ---- קומבו ----
res2={}
# C1: דניאל->רביעי + מעגל שני 5-6
s=io.open("data2.py",encoding="utf-8").read()
io.open("data2.py","w",encoding="utf-8").write(s.replace('"דניאל":["שלישי"],','"דניאל":["רביעי"],'))
s=io.open("make_unified.py",encoding="utf-8").read()
io.open("make_unified.py","w",encoding="utf-8").write(s.replace('_hm=set(_SEDF["מעגלי שיח שני"])','_hm={5,6}'))
res2["דניאל רביעי + מעגל שני 5-6"]=run_and_count(); restore()
# C2: גם דניאל וגם דני לרביעי
s=io.open("data2.py",encoding="utf-8").read()
s=s.replace('"דניאל":["שלישי"],','"דניאל":["רביעי"],').replace('"דני":["שלישי"],','"דני":["רביעי"],')
io.open("data2.py","w",encoding="utf-8").write(s)
res2["דניאל+דני שניהם רביעי"]=run_and_count(); restore()
lines=["קומבו | חוסרים"]
for k,v in res2.items(): lines.append(f"{k} | "+("לא אפשרי" if v is None else str(v)))
io.open("exper2.txt","w",encoding="utf-8").write("\n".join(lines))
print("\n".join(lines))
