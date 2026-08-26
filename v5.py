import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
NOG='''for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(free[(c,(d,h))], free[(c,(d,h+1))])'''
SH='        if k in x: m.Add(x[k]==(1 if s2==(5,2) else 0))'
tests={
 "חלונות מותרים בשישי בלבד": src.replace(NOG, NOG.replace("for d in range(6):","for d in range(5):")),
 "שירה בשעה 1": src.replace(SH,'        if k in x: m.Add(x[k]==(1 if s2==(5,1) else 0))'),
 "שירה בשעה 3": src.replace(SH,'        if k in x: m.Add(x[k]==(1 if s2==(5,3) else 0))'),
 "שירה בשעה 4": src.replace(SH,'        if k in x: m.Add(x[k]==(1 if s2==(5,4) else 0))'),
}
for name,s in tests.items():
    io.open("_v5.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python3","_v5.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:28s} -> {st}")
