import io, subprocess
base=io.open("hdata.py",encoding="utf-8").read()
tests={
 "רק תמיר שלישי":  base.replace('"גלית":["שני"],','"גלית":[],'),
 "רק גלית שני":    base.replace('"תמיר":["שלישי"],','"תמיר":[],'),
 "גלית חמישי":     base.replace('"גלית":["שני"],','"גלית":["חמישי"],').replace('"תמיר":["שלישי"],','"תמיר":[],'),
 "שניהם + גלית חמישי": base.replace('"גלית":["שני"],','"גלית":["חמישי"],'),
}
for name,src in tests.items():
    io.open("hdata.py","w",encoding="utf-8").write(src)
    r=subprocess.run(["python3","solveH.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:24s} -> {st}")
io.open("hdata.py","w",encoding="utf-8").write(base)
