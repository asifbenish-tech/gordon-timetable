import io, subprocess
hd=io.open("hdata.py",encoding="utf-8").read()
tests={
 "צבי במתמטיקה ח": hd.replace('"מתמטיקה":{"ז":["הדר","צבי"],"ח":["מורה חיצוני"],"ט":["מורה חיצוני"]},','"מתמטיקה":{"ז":["הדר","צבי"],"ח":["מורה חיצוני","צבי"],"ט":["מורה חיצוני"]},'),
 "צבי בח+ט": hd.replace('"מתמטיקה":{"ז":["הדר","צבי"],"ח":["מורה חיצוני"],"ט":["מורה חיצוני"]},','"מתמטיקה":{"ז":["הדר","צבי"],"ח":["מורה חיצוני","צבי"],"ט":["מורה חיצוני","צבי"]},'),
}
for name,src in tests.items():
    io.open("hdata.py","w",encoding="utf-8").write(src)
    r=subprocess.run(["python3","solveH.py"],capture_output=True,text=True)
    st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
    print(f"{name:22s} -> {st}")
io.open("hdata.py","w",encoding="utf-8").write(hd)
