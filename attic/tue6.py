import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
old='''vend={}
for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            b=m.NewBoolVar(f"ve{c}{d}{h}"); m.Add(free[(c,(d,h))]<=b); vend[(c,d,h)]=b'''
new='''vend={}
for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            if d==2: m.Add(free[(c,(d,h))]==0)
            else:
                b=m.NewBoolVar(f"ve{c}{d}{h}"); m.Add(free[(c,(d,h))]<=b); vend[(c,d,h)]=b'''
assert old in src
s=src.replace(old,new)
io.open("_t6.py","w",encoding="utf-8").write(s)
r=subprocess.run(["python3","_t6.py"],capture_output=True,text=True)
st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
print("שלישי עד 6 קשיח ->",st)
if st=="OPTIMAL": io.open("solveH.py","w",encoding="utf-8").write(s); print("applied")
