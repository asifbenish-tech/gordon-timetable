import io, subprocess
src = io.open("solveH.py", encoding="utf-8").read()
B = {
 "end-time": '''for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            m.Add(free[(c,(d,h))]==0)''',
 "no-gaps": '''for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(free[(c,(d,h))], free[(c,(d,h+1))])''',
 "duty": '''    m.Add(sum(duty[(c,d)] for d in range(5))==1)''',
 "tj": '''m.Add(sum(tjS.values())>=1)''',
 "lit": '''m.Add(sum(litS.values())==1)''',
 "erez": '''m.Add(sum(erz[3])+sum(erz[4])==8)''',
 "hadar": '''m.Add(sum(hadar)<=8)''',
}
import itertools
names=list(B)
for r in (1,2):
    for combo in itertools.combinations(names,r):
        s=src
        ok=True
        for n in combo:
            if B[n] not in s: ok=False; break
            s=s.replace(B[n],"pass  # ablated")
        if not ok: continue
        io.open("_a.py","w",encoding="utf-8").write(s)
        res=subprocess.run(["python","_a.py"],capture_output=True,text=True)
        st=next((l.split(":",1)[1].strip() for l in res.stdout.splitlines() if l.startswith("status:")),"?")
        if st!="INFEASIBLE":
            print("FEASIBLE by removing:", combo, "->", st)
    print(f"-- done size {r} --")
