import io, subprocess
from hdata import HOFF
base=io.open("hdata.py",encoding="utf-8").read()
variants={
 "רק גלית שני": base.replace('"תמיר":["רביעי"],','"תמיר":[],').replace('"מורה חיצוני":["שישי"]','"מורה חיצוני":[]'),
 "גלית + תמיר רביעי": base.replace('"מורה חיצוני":["שישי"]','"מורה חיצוני":[]'),
 "גלית + תמיר שלישי": base.replace('"תמיר":["רביעי"],','"תמיר":["שלישי"],').replace('"מורה חיצוני":["שישי"]','"מורה חיצוני":[]'),
 "גלית + חיצוני שישי": base.replace('"תמיר":["רביעי"],','"תמיר":[],'),
}
for name,src in variants.items():
    io.open("hdata.py","w",encoding="utf-8").write(src)
    r=subprocess.run(["python3","solveH.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:24s} -> {st}")
io.open("hdata.py","w",encoding="utf-8").write(base)
