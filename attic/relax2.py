import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
CAP='            if v: m.Add(sum(v)<=2)'
tests={
 "אלי>=12 -> >=10": src.replace('if _all_eli: m.Add(sum(_all_eli)>=12)','if _all_eli: m.Add(sum(_all_eli)>=10)'),
 "אלי-תנך גמיש": src.replace('if _tn: m.Add(sum(_tn)==2)','if _tn: m.Add(sum(_tn)>=1)'),
 "אלי-רבמלל גמיש": src.replace('if _rm: m.Add(sum(_rm)==3)','if _rm: m.Add(sum(_rm)>=2)'),
 "הדר: 2+2 -> גמיש ביום": src.replace('        if _v: m.Add(sum(_v)==2*hd_act[d])','        if _v: m.Add(sum(_v)<=2*hd_act[d])'),
 "duty רך": src.replace('    m.Add(sum(duty[(c,d)] for d in range(5))==1)','    pass'),
 "sameday-cap-3-math": src.replace(CAP,'            if v: m.Add(sum(v)<= (3 if (subj=="מתמטיקה" and GRADE[c]=="ז") else 2))'),
}
for name,s in tests.items():
    if s==src: print(f"{name:26s} -> anchor missing"); continue
    io.open("_r2.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python3","_r2.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:26s} -> {st}")
