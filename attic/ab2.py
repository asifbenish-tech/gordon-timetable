# -*- coding: utf-8 -*-
import io,os,sys,subprocess,shutil
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
shutil.copy("solveH.py","_sh2"); shutil.copy("hdata.py","_hd2")
BH=io.open("solveH.py",encoding="utf-8").read(); BD=io.open("hdata.py",encoding="utf-8").read()
def t(name,fh=None,fd=None):
    io.open("solveH.py","w",encoding="utf-8").write(fh(BH) if fh else BH)
    io.open("hdata.py","w",encoding="utf-8").write(fd(BD) if fd else BD)
    subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    os.environ["TL"]="55"
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    print(name+": "+("INFEASIBLE" if "INFEASIBLE" in o else ("ERROR "+o[-200:] if r.returncode else "FEASIBLE")))
    shutil.copy("_sh2","solveH.py"); shutil.copy("_hd2","hdata.py")
noDiv=lambda s:s.replace('        if _v: m.Add(sum(_v)==2)','        pass')
noEdu=lambda s:s.replace('    if _k5 in x: m.Add(x[_k5]==1)','    pass')
noDine=lambda s:s.replace('    m.Add(hfree[(_cz,(2,6))]==1)','    pass').replace('    for _h in (6,7): m.Add(hfree[(_c9,(4,_h))]==1)','    pass')
t("בלי חלוקה + בלי חינוך-אחרי-מגמות", lambda s:noEdu(noDiv(s)))
t("בלי חלוקה + בלי חדר אוכל", lambda s:noDine(noDiv(s)))
t("בלי חינוך-אחרי + בלי חדר אוכל", lambda s:noDine(noEdu(s)))
t("בלי שלושתם", lambda s:noDine(noEdu(noDiv(s))))
t("בלי שלושתם + מעגל 5-6", lambda s:noDine(noEdu(noDiv(s))))

print("--- שינויי hdata ---")
t("חינוך חזרה ל-2,3,2", None, lambda s:s.replace('"חינוך":{"ז":3,"ח":4,"ט":2},   # כולל שיעור אחרי המגמות','"חינוך":{"ז":2,"ח":3,"ט":2},'))
t("POOL רב מלל חזרה (תמיר בז/ח)", None, lambda s:s.replace('"רב מלל":{"ז":["נעמי","אלי","שיר"],"ח":["נעמי","אלי"],"ט":["נעמי","תמיר"]},','"רב מלל":{"ז":["נעמי","תמיר","אלי","שיר"],"ח":["נעמי","תמיר","אלי","מאמי"],"ט":["נעמי","תמיר","אלי"]},'))
t("רב מלל 3,3,4", None, lambda s:s.replace('"רב מלל":{"ז":4,"ח":4,"ט":5},   # נעמי ספרות + אלי היסטוריה','"רב מלל":{"ז":3,"ח":3,"ט":4},'))
t("שניהם: חינוך 2,3,2 + רב מלל 3,3,4", None, lambda s:s.replace('"חינוך":{"ז":3,"ח":4,"ט":2},   # כולל שיעור אחרי המגמות','"חינוך":{"ז":2,"ח":3,"ט":2},').replace('"רב מלל":{"ז":4,"ח":4,"ט":5},   # נעמי ספרות + אלי היסטוריה','"רב מלל":{"ז":3,"ח":3,"ט":4},'))

print("--- החזרה מלאה של hdata ---")
def full_revert(s):
    s=s.replace('"רב מלל":{"ז":["נעמי","אלי","שיר"],"ח":["נעמי","אלי"],"ט":["נעמי","תמיר"]},','"רב מלל":{"ז":["נעמי","תמיר","אלי","שיר"],"ח":["נעמי","תמיר","אלי","מאמי"],"ט":["נעמי","תמיר","אלי"]},')
    s=s.replace('"חינוך":{"ז":3,"ח":4,"ט":2},   # כולל שיעור אחרי המגמות','"חינוך":{"ז":2,"ח":3,"ט":2},')
    s=s.replace('"העשרה טכנולוגית":{"ז":0,"ח":0,"ט":0},','"העשרה טכנולוגית":{"ז":1,"ח":0,"ט":0},')
    s=s.replace('"אלי":[(2,3),(2,4),(2,6),(4,3),(4,4),(3,6)],','"אלי":[(2,3),(2,4),(2,5),(2,6),(4,3),(4,4),(3,6)],')
    return s
def sh_revert(s):
    s=s.replace('''    _last=5 if GRADE[c] in "זח" else 6                 # ז+ח: חדר אוכל בש6
    for h in range(1,_last+1): m.Add(free[(c,(2,h))]==0)''','''    for h in range(1,7): m.Add(free[(c,(2,h))]==0)''')
    s=s.replace('    if _k5 in x: m.Add(x[_k5]==1)','    pass')
    s=s.replace('    m.Add(hfree[(_cz,(2,6))]==1)','    pass')
    s=s.replace('    for _h in (6,7): m.Add(hfree[(_c9,(4,_h))]==1)','    pass')
    s=s.replace('        if _v: m.Add(sum(_v)==2)','        pass')
    s=s.replace('for _t6 in ("אלי","גלית"):\n    hebusy[_t6].discard((HCM["שלישי"],5))   # מלמדים חינוך ש5, מעגל שיח ש6 בלבד\n','')
    return s
t("hdata מלא חזרה", sh_revert, full_revert)
