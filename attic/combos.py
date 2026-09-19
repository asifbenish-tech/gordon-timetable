import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
HARD_GAP='''for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(free[(c,(d,h))], free[(c,(d,h+1))])'''
SOFT_GAP='''vgap={}
for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            b=m.NewBoolVar(f"vg{c}{d}{h}"); vgap[(c,d,h)]=b
            m.Add(free[(c,(d,h))] <= free[(c,(d,h+1))] + b)'''
tests={
 "tj==1, גם שישי פטור מחלונות": src.replace("for d in range(6):","for d in range(5):",1),
 "tj==1, מעגל שיח נעמי? בלי duty": src.replace("    m.Add(sum(duty[(c,d)] for d in range(5))==1)","    pass"),
 "tj==1, בלי erez 4+4": src.replace("m.Add(sum(erz[3])+sum(erz[4])==8)","pass"),
 "tj==1, בלי lit": src.replace("m.Add(sum(litS.values())==1)","pass"),
 "tj==1, בלי כפולים": src.replace('''        if ps:
            dv=m.NewBoolVar(f"dblmiss{c}{subj}")
            m.Add(sum(ps)+dv>=1); viol_dbl[(c,subj)]=dv''','        pass') if 'dblmiss' in src else None,
}
# core-doubles block variant
if "if ps: m.Add(sum(ps)>=1)" in src:
    tests["tj==1, בלי כפולים"]=src.replace("if ps: m.Add(sum(ps)>=1)","pass")
for name,s in tests.items():
    if s is None or s==src: print(f"{name:34s} -> (anchor missing)"); continue
    io.open("_c.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python","_c.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:34s} -> {st}")
