import io, subprocess
hd=io.open("hdata.py",encoding="utf-8").read()
sv=io.open("solveH.py",encoding="utf-8").read()
tests={
 "ארז עוזר באנגלית ח": hd.replace('"אנגלית":{"ז":["ארז"],"ח":["גלית"],"ט":["גלית"]},','"אנגלית":{"ז":["ארז"],"ח":["גלית","ארז"],"ט":["גלית"]},'),
 "ארז עוזר באנגלית ח+ט": hd.replace('"אנגלית":{"ז":["ארז"],"ח":["גלית"],"ט":["גלית"]},','"אנגלית":{"ז":["ארז"],"ח":["גלית","ארז"],"ט":["גלית","ארז"]},'),
 "צבי עוזר במתמטיקה ח+ט": hd.replace('"מתמטיקה":{"ז":["הדר","צבי"],"ח":["מורה חיצוני"],"ט":["מורה חיצוני"]},','"מתמטיקה":{"ז":["הדר","צבי"],"ח":["מורה חיצוני","צבי"],"ט":["מורה חיצוני","צבי"]},'),
}
for name,src in tests.items():
    io.open("hdata.py","w",encoding="utf-8").write(src)
    r=subprocess.run(["python3","solveH.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:26s} -> {st}")
io.open("hdata.py","w",encoding="utf-8").write(hd)
