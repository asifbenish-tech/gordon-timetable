import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
NOG='''for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(free[(c,(d,h))], free[(c,(d,h+1))])'''
SOFT='''vgap={}
for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            b=m.NewBoolVar(f"vg{c}{d}{h}"); vgap[(c,d,h)]=b
            m.Add(free[(c,(d,h))] <= free[(c,(d,h+1))] + b)'''
assert NOG in src
s=src.replace(NOG,SOFT)
s=s.replace('m.Minimize(400*sum(vend.values())','m.Minimize(5000*sum(vgap.values())+400*sum(vend.values())')
s=s.replace('    print("filled:"','''    io.open("gapv.txt","w",encoding="utf-8").write(chr(10).join(
        f"חלון: {c} {DAY_NAMES[d]} אחרי ש{h}" for (c,d,h),v in sorted(vgap.items()) if sol.Value(v)) or "אין")
    print("filled:"''')
io.open("_sg.py","w",encoding="utf-8").write(s)
r=subprocess.run(["python3","_sg.py"],capture_output=True,text=True)
print([l for l in r.stdout.splitlines() if 'status' in l or 'filled' in l])
