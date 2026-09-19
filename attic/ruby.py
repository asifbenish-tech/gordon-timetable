import io, subprocess
hd=io.open("hdata.py",encoding="utf-8").read()
sv=io.open("solveH.py",encoding="utf-8").read()
# רובי: שעות ליווי בכיתות ז ביום שלישי בלבד (דרך רב מלל)
h2=hd.replace('"רב מלל":{"ז":["נעמי","תמיר","אלי","שיר"],','"רב מלל":{"ז":["נעמי","תמיר","אלי","שיר","רובי"],')
if '"רובי"' not in hd.split("CAP=")[1].split("HOFF")[0]:
    h2=h2.replace('CAP={"שיר":4,','CAP={"רובי":6,"שיר":4,')
h2=h2.replace('"גלית":["שני"], "תמיר":["שלישי"],','"גלית":["שני"], "תמיר":["שלישי"], "רובי":["ראשון","שני","רביעי","חמישי","שישי"],')
s2=sv.replace('# ארז: רביעי + חמישי','''# רובי: רק בכיתות ז ביום שלישי ש5-6 (ליווי/תגבור)
for c in HCLASSES:
    for s2b in HSLOTS:
        _k=(c,s2b,"רב מלל","רובי")
        if _k in x and not (GRADE[c]=="ז" and s2b[0]==2 and s2b[1] in (5,6)): m.Add(x[_k]==0)

# ארז: רביעי + חמישי''')
io.open("hdata.py","w",encoding="utf-8").write(h2)
io.open("_rb.py","w",encoding="utf-8").write(s2)
r=subprocess.run(["python3","_rb.py"],capture_output=True,text=True)
st=next((l.split(":",1)[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")),"?")
print("עם רובי בשלישי 5-6 ->",st)
if st!="OPTIMAL":
    io.open("hdata.py","w",encoding="utf-8").write(hd)
else:
    io.open("solveH.py","w",encoding="utf-8").write(s2)
