import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
CAP='            if v: m.Add(sum(v)<=2)'
# צבי לא מלמד מתמטיקה בז ביום פעיל של הדר -> אין יום עם 3 מתמטיקה
add='''for _c in [c for c in HCLASSES if GRADE[c]=="ז"]:
    for _d in range(5):
        for _h in range(1,HDAY[_d]+1):
            _k=(_c,(_d,_h),"מתמטיקה","צבי")
            if _k in x: m.Add(x[_k]+hd_act[_d]<=1)
'''
s=src.replace('# ארז: רביעי + חמישי', add+'# ארז: רביעי + חמישי')
io.open("_tz.py","w",encoding="utf-8").write(s)
r=subprocess.run(["python3","_tz.py"],capture_output=True,text=True)
st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
print("צבי לא ביום של הדר ->",st)
