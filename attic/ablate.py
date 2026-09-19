import io, subprocess, re
src = io.open("solveH.py", encoding="utf-8").read()
BLOCKS = {
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
 "shira": '''        if k in x: m.Add(x[k]==(1 if s2==(5,2) else 0))''',
 "erez": '''m.Add(sum(erz[3])+sum(erz[4])==8)''',
 "asif-lang": '''        k=(c,(d,HDAY[d]),"שפה","אסיף")
        if k in x: m.Add(x[k]==0)''',
 "tj": '''m.Add(sum(tjS.values())>=1)''',
 "lit": '''m.Add(sum(litS.values())==1)''',
}
for name, blk in BLOCKS.items():
    if blk not in src:
        print(f"{name:12s} NOT-FOUND"); continue
    s = src.replace(blk, "pass  # ablated")
    io.open("_abl.py","w",encoding="utf-8").write(s)
    r = subprocess.run(["python","_abl.py"],capture_output=True,text=True)
    st = "?"
    for ln in r.stdout.splitlines():
        if ln.startswith("status:"): st = ln.split(":",1)[1].strip()
    print(f"{name:12s} -> {st}")
