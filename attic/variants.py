import io, subprocess
src = io.open("solveH.py", encoding="utf-8").read()
END = '''for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            m.Add(free[(c,(d,h))]==0)'''
V = {
 "A: שלישי עד 5 במקום 6": END.replace("last = 6 if d==2 else min(5,HDAY[d])","last = min(5,HDAY[d])"),
 "B: סיום מ-5 ל-4":        END.replace("min(5,HDAY[d])","min(4,HDAY[d])").replace("last = 6 if d==2 else","last = 6 if d==2 else"),
 "C: פטור לשישי בלבד מהסיום": END,
}
# C needs no-gaps tweak instead
NOG='''for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(free[(c,(d,h))], free[(c,(d,h+1))])'''
NOG_FRI=NOG.replace("for d in range(6):","for d in range(5):")

tests = {
 "A: שלישי עד 5": (END, V["A: שלישי עד 5 במקום 6"], None, None),
 "B: סיום מינימלי 4": (END, V["B: סיום מ-5 ל-4"], None, None),
 "C: חלונות מותרים בשישי": (None, None, NOG, NOG_FRI),
 "D: A + חלונות בשישי": (END, V["A: שלישי עד 5 במקום 6"], NOG, NOG_FRI),
}
for name,(o1,n1,o2,n2) in tests.items():
    s=src
    if o1 and o1 in s: s=s.replace(o1,n1)
    elif o1: print(name,"-> anchor1 missing"); continue
    if o2 and o2 in s: s=s.replace(o2,n2)
    elif o2: print(name,"-> anchor2 missing"); continue
    io.open("_v.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python","_v.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:28s} -> {st}")
