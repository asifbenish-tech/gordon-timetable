import io, subprocess, itertools
src=io.open("solveH.py",encoding="utf-8").read()
B={
 "doubles":'        if ps: m.Add(sum(ps)>=1)',
 "duty":'    m.Add(sum(duty[(c,d)] for d in range(5))==1)',
 "tj":'m.Add(sum(tjS.values())==1)',
 "lit":'m.Add(sum(litS.values())==1)',
 "shir-fri":'    if _v: m.Add(sum(_v)==1)',
 "eli12":'if _all_eli: m.Add(sum(_all_eli)>=12)',
 "eli-tn":'if _tn: m.Add(sum(_tn)==2)',
 "eli-rm":'if _rm: m.Add(sum(_rm)==3)',
 "hadar-2days":'m.Add(sum(hd_act.values())==2)',
 "tirgul-tue":'        if _k in x and s2[0]!=2: m.Add(x[_k]==0)',
}
names=[k for k in B if B[k] in src]
print("anchors:",names)
for r in (1,2):
    hits=[]
    for combo in itertools.combinations(names,r):
        s=src
        for n in combo: s=s.replace(B[n],"pass  # abl")
        io.open("_y.py","w",encoding="utf-8").write(s)
        res=subprocess.run(["python3","_y.py"],capture_output=True,text=True)
        st=next((l.split(":",1)[1].strip() for l in res.stdout.splitlines() if l.startswith("status:")),"?")
        if st=="OPTIMAL": hits.append(combo)
    for c in hits: print("FEASIBLE removing:",c)
    if hits: break
    print(f"-- size {r}: none --")
