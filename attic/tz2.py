import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
anchor='''    _tot=[x[(_c,s,"מתמטיקה","הדר")] for s in HSLOTS if (_c,s,"מתמטיקה","הדר") in x]
    if _tot: m.Add(sum(_tot)==4)'''
add=anchor+'''
# צבי לא מלמד מתמטיקה בז ביום פעיל של הדר (מונע 3 מתמטיקה ביום)
for _c in [c for c in HCLASSES if GRADE[c]=="ז"]:
    for _d in range(5):
        for _h in range(1,HDAY[_d]+1):
            _k=(_c,(_d,_h),"מתמטיקה","צבי")
            if _k in x: m.Add(x[_k]+hd_act[_d]<=1)'''
assert anchor in src
s=src.replace(anchor,add)
io.open("_tz2.py","w",encoding="utf-8").write(s)
r=subprocess.run(["python3","_tz2.py"],capture_output=True,text=True)
st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
print("->",st)
if st=="OPTIMAL":
    io.open("solveH.py","w",encoding="utf-8").write(s)
    print("applied")
