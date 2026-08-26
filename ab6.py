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
}
names=[k for k in B if B[k] in src]
hits=[]
for combo in itertools.combinations(names,2):
    s=src
    for n in combo: s=s.replace(B[n],"pass")
    io.open("_z.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python3","_z.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    if st=="OPTIMAL": hits.append(combo); print("FEASIBLE:",combo)
if not hits: print("שום זוג (בלי לגעת בתרגול-שלישי) לא פותר")
