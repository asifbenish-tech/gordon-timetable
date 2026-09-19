# -*- coding: utf-8 -*-
import io,os,sys,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
shutil.copy("solveH.py","_q"); B=io.open("solveH.py",encoding="utf-8").read()
def t(n,f):
    io.open("solveH.py","w",encoding="utf-8").write(f(B))
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="55"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    print(n+": "+("INFEASIBLE" if "INFEASIBLE" in o else ("ERR" if r.returncode else "FEASIBLE")))
    shutil.copy("_q","solveH.py")
t("ט: חדר אוכל רק בש7 (ש6 שיעור)", lambda s:s.replace('    for _h in (6,7): m.Add(free[(_c9,(4,_h))]==1)','    m.Add(free[(_c9,(4,7))]==1)'))
t("בלי חדר אוכל ז+ח בש6", lambda s:s.replace('    if GRADE[c] in "זח": m.Add(free[(c,(2,6))]==1)',''))
t("בלי פין חינוך ש5", lambda s:s.replace('    if _v5: m.Add(sum(_v5)==1)','    pass'))
t("בלי חלוקת נעמי/אלי", lambda s:s.replace('        if _v: m.Add(sum(_v)>=1)','        pass'))

print("--- מקור הבעיה: hdata או solveH? ---")
import io as _io
HD=_io.open("hdata.py",encoding="utf-8").read()
shutil.copy("hdata.py","_qh")
def th(n,fh,fd):
    _io.open("solveH.py","w",encoding="utf-8").write(fh(B))
    _io.open("hdata.py","w",encoding="utf-8").write(fd(HD))
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="55"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    print(n+": "+("INFEASIBLE" if "INFEASIBLE" in o else ("ERR" if r.returncode else "FEASIBLE")))
    shutil.copy("_q","solveH.py"); shutil.copy("_qh","hdata.py")
noNew=lambda s:(s.replace('    if _v5: m.Add(sum(_v5)==1)','    pass')
                 .replace('    for _h in (6,7): m.Add(free[(_c9,(4,_h))]==1)','    pass')
                 .replace('    if GRADE[c] in "זח": m.Add(free[(c,(2,6))]==1)','')
                 .replace('        if _v: m.Add(sum(_v)>=1)','        pass')
                 .replace('    _lastT=5 if GRADE[c] in "זח" else 6                # ז+ח: ש6 חדר אוכל','    _lastT=6'))
th("בלי כל החדשים (solveH), hdata חדש", noNew, lambda s:s)
th("בלי כל החדשים + POOL ישן", noNew, lambda s:s.replace('"רב מלל":{"ז":["נעמי","אלי","שיר"],"ח":["נעמי","אלי","מאמי"],"ט":["נעמי","תמיר"]},','"רב מלל":{"ז":["נעמי","תמיר","אלי","שיר"],"ח":["נעמי","תמיר","אלי","מאמי"],"ט":["נעמי","תמיר","אלי"]},'))
th("בלי כל החדשים + העשרה חזרה", noNew, lambda s:s.replace('"העשרה טכנולוגית":{"ז":0,"ח":0,"ט":0},','"העשרה טכנולוגית":{"ז":1,"ח":0,"ט":0},'))
