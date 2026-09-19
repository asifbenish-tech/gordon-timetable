# -*- coding: utf-8 -*-
"""חיתוך: מנטרל בלוק אילוצים אחד (בין כותרות #) בכל פעם, על הגרסה המלאה."""
import io,os,sys,subprocess,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
FULL=io.open("_asm",encoding="utf-8").read()
lines=FULL.split("\n")
# בלוקים = קטעים שמתחילים בשורת '# ' ברמת שמאל, אחרי שורה 95 (יצירת משתנים)
marks=[i for i,l in enumerate(lines) if l.startswith("# ") and i>95]
marks.append(len(lines))
blocks=[(marks[i],marks[i+1],lines[marks[i]][2:60]) for i in range(len(marks)-1)]
def neutral(a,b):
    out=lines[:a]
    for l in lines[a:b]:
        st=l.strip()
        if st.startswith("m.Add") or st.startswith("if _") and "m.Add" in l or ": m.Add" in l:
            out.append(re.sub(r'(\s*)','\1',l).replace("m.Add","(lambda *z: None)").replace("(lambda *z: None)Assumption","m.AddAssumption"))
        else: out.append(l)
    return "\n".join(out+lines[b:])
def run2(n,s,tl="60"):
    io.open("solveH.py","w",encoding="utf-8").write(s)
    r0=subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    if r0.returncode: return "GEN-ERR"
    os.environ["TL"]=tl
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    m=re.search(r"status:\s*(\w+)",o)
    return m.group(1) if m else "ERR"
for a,b,name in blocks:
    if b-a<2: continue
    st=run2(name,neutral(a,b))
    print(f"{name}: {st}")
    if st=="FEASIBLE": print("  ^^^ הבלוק הזה חוסם!")
