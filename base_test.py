import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
hd=io.open("hdata.py",encoding="utf-8").read()
# מודל בסיסי: בלי אילוצי אלי/שיר/הדר האחרונים
b=src
b=b.replace('if _all_eli: m.Add(sum(_all_eli)>=12)','pass')
b=b.replace('if _tn: m.Add(sum(_tn)==2)','pass')
b=b.replace('if _rm: m.Add(sum(_rm)==3)','pass')
b=b.replace('    if _v: m.Add(sum(_v)==1)','    pass')
b=b.replace('    if _v: m.Add(sum(_v)==4)','    pass')
combos={
 "בסיס בלבד (בלי ימי חופש חדשים)": (hd.replace('"גלית":["שני"],','"גלית":[],').replace('"תמיר":["שלישי"],','"תמיר":[],'), b),
 "בסיס + גלית שני": (hd.replace('"תמיר":["שלישי"],','"תמיר":[],'), b),
 "בסיס + תמיר שלישי": (hd.replace('"גלית":["שני"],','"גלית":[],'), b),
 "בסיס + שניהם": (hd, b),
}
for name,(h,s) in combos.items():
    io.open("hdata.py","w",encoding="utf-8").write(h)
    io.open("_b.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python3","_b.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:34s} -> {st}")
io.open("hdata.py","w",encoding="utf-8").write(hd)
