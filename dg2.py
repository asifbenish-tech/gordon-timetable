import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
old='''    for subj,per in NEED.items():
        if per[g]==0: continue
        v=[x[(c,s,subj,t)] for s in HSLOTS for (sj,t) in pairs[c] if sj==subj and (c,s,subj,t) in x]
        m.Add(sum(v)==per[g])'''
new='''    for subj,per in NEED.items():
        if per[g]==0: continue
        v=[x[(c,s,subj,t)] for s in HSLOTS for (sj,t) in pairs[c] if sj==subj and (c,s,subj,t) in x]
        sh=m.NewIntVar(0,per[g],f"sh{c}{subj}"); miss[(c,subj)]=sh
        m.Add(sum(v)+sh==per[g])'''
assert old in src
s=src.replace(old,new).replace('free={}','miss={}\nfree={}',1)
s=s.replace('m.Minimize(400*sum(vend.values())','m.Minimize(9000*sum(miss.values())+400*sum(vend.values())')
s=s.replace('    print("filled:"','''    io.open("dg2.txt","w",encoding="utf-8").write(chr(10).join(
        f"{c} | {sj} | חסר {sol.Value(v)}" for (c,sj),v in sorted(miss.items()) if sol.Value(v)) or "none")
    print("filled:"''')
io.open("_dg2.py","w",encoding="utf-8").write(s)
r=subprocess.run(["python3","_dg2.py"],capture_output=True,text=True)
print([l for l in r.stdout.splitlines() if 'status' in l or 'filled' in l])
