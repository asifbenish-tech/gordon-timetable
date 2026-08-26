import io, subprocess
src=io.open("solveH.py",encoding="utf-8").read()
tests={
 "אלי>=8 במקום 12": src.replace('if _all_eli: m.Add(sum(_all_eli)>=12)','if _all_eli: m.Add(sum(_all_eli)>=8)'),
 "אלי>=10": src.replace('if _all_eli: m.Add(sum(_all_eli)>=12)','if _all_eli: m.Add(sum(_all_eli)>=10)'),
 "שיר 2 שעות במקום 3": src.replace('    if _v: m.Add(sum(_v)==1)','    if _v: m.Add(sum(_v)<=1)'),
 "אלי>=8 + שיר גמיש": src.replace('if _all_eli: m.Add(sum(_all_eli)>=12)','if _all_eli: m.Add(sum(_all_eli)>=8)').replace('    if _v: m.Add(sum(_v)==1)','    if _v: m.Add(sum(_v)<=1)'),
 "הדר 4+4 -> <=8": src.replace('    if _v: m.Add(sum(_v)==4)','    if _v: m.Add(sum(_v)<=4)'),
}
for name,s in tests.items():
    io.open("_r.py","w",encoding="utf-8").write(s)
    r=subprocess.run(["python3","_r.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:24s} -> {st}")
