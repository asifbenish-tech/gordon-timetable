import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
tests={
 "הדר 4+4, 3 מתמטיקה גם בשלישי": src.replace(
   '            if v: m.Add(sum(v)<= (3 if (subj=="מתמטיקה" and GRADE[c]=="ז" and d==1) else 2))',
   '            if v: m.Add(sum(v)<= (3 if (subj=="מתמטיקה" and GRADE[c]=="ז" and d in (1,2)) else 2))'),
 "הדר 4+3": src.replace('    if _v: m.Add(sum(_v)==4)','    if _v: m.Add(sum(_v)>=3)'),
 "הדר 4+4 + 3 אנגלית ברביעי": src.replace(
   '            if v: m.Add(sum(v)<= (3 if (subj=="מתמטיקה" and GRADE[c]=="ז" and d==1) else 2))',
   '            if v: m.Add(sum(v)<= (3 if ((subj=="מתמטיקה" and GRADE[c]=="ז" and d==1) or (subj=="אנגלית" and GRADE[c]=="ז" and d==3)) else 2))'),
}
for name,s in tests.items():
    io.open("_hh.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python3","_hh.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:32s} -> {st}")
