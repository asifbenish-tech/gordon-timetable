import io, subprocess, itertools
src=io.open("solveH.py",encoding="utf-8").read()
B={
 "end-time":'''vend={}
for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            b=m.NewBoolVar(f"ve{c}{d}{h}"); m.Add(free[(c,(d,h))]<=b); vend[(c,d,h)]=b''',
 "no-gaps":'''for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(free[(c,(d,h))], free[(c,(d,h+1))])''',
 "eli>=12":'if _all_eli: m.Add(sum(_all_eli)>=12)',
 "eli-tanach":'if _tn: m.Add(sum(_tn)==2)',
 "eli-rm3":'if _rm: m.Add(sum(_rm)==3)',
 "shir-fri":'    if _v: m.Add(sum(_v)==1)',
 "hadar4+4":'    if _v: m.Add(sum(_v)==4)',
 "duty":'    m.Add(sum(duty[(c,d)] for d in range(5))==1)',
 "shira":'        if k in x: m.Add(x[k]==(1 if s2==(5,2) else 0))',
 "erez":'m.Add(sum(erz[3])+sum(erz[4])==8)',
 "tj":'m.Add(sum(tjS.values())==1)',
 "lit":'m.Add(sum(litS.values())==1)',
}
names=[k for k in B if B[k] in src]
missing=[k for k in B if B[k] not in src]
if missing: print("anchors missing:", missing)
for r in (1,2):
    hits=[]
    for combo in itertools.combinations(names,r):
        s=src
        for n in combo: s=s.replace(B[n],"pass  # abl")
        io.open("_x.py","w",encoding="utf-8").write(s)
        res=subprocess.run(["python3","_x.py"],capture_output=True,text=True)
        st=next((l.split(":",1)[1].strip() for l in res.stdout.splitlines() if l.startswith("status:")),"?")
        if st!="INFEASIBLE": hits.append((combo,st))
    for c,st in hits: print("FEASIBLE removing:", c, "->", st)
    if hits: break
    print(f"-- none at size {r} --")
