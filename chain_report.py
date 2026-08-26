# -*- coding: utf-8 -*-
"""משווה שני פתרונות ומציג את שרשראות השינויים.
שימוש: python chain_report.py old_sol_J.json old_sol_hat.json
(משווה מול sol_J.json / sol_hat.json הנוכחיים)"""
import io, json, sys, collections
from data2 import CLASSES, SLOTS, DAY_NAMES
from hdata import HCLASSES, HSLOTS

def tof(v): return v.split(" – ")[1] if " – " in v else (v or None)

oldE = json.load(io.open(sys.argv[1] if len(sys.argv)>1 else "prev_sol_J.json", encoding="utf-8"))
oldH = json.load(io.open(sys.argv[2] if len(sys.argv)>2 else "prev_sol_hat.json", encoding="utf-8"))
newE = json.load(io.open("sol_J.json", encoding="utf-8"))
newH = json.load(io.open("sol_hat.json", encoding="utf-8"))

moves = []          # (teacher, side, class, day, hour, old, new)
for c in CLASSES:
    for (d,h) in SLOTS:
        a,b = oldE[c][f"{d},{h}"], newE[c][f"{d},{h}"]
        if a!=b: moves.append(("יסודי",c,d,h,a or "—",b or "—"))
for c in HCLASSES:
    for (d,h) in HSLOTS:
        a,b = oldH[c][f"{d},{h}"], newH[c][f"{d},{h}"]
        if a!=b: moves.append(("חטיבה",c,d,h,a or "—",b or "—"))

by_teacher = collections.defaultdict(list)
for side,c,d,h,a,b in moves:
    ta = tof(a) if side=="חטיבה" else (a if a!="—" else None)
    tb = tof(b) if side=="חטיבה" else (b if b!="—" else None)
    for t in {ta,tb}-{None,"—"}:
        by_teacher[t].append((side,c,d,h,a,b))

out=[f"סה\"כ {len(moves)} משבצות השתנו, {len(by_teacher)} מורים מעורבים",""]
for t in sorted(by_teacher, key=lambda k:-len(by_teacher[k])):
    lst=by_teacher[t]
    out.append(f"◆ {t} ({len(lst)} שינויים):")
    for side,c,d,h,a,b in sorted(lst,key=lambda z:(z[2],z[3])):
        out.append(f"   [{side}] {c} | {DAY_NAMES[d]} ש{h}: {a}  ->  {b}")
    out.append("")
io.open("chain_report.txt","w",encoding="utf-8").write("\n".join(out))
print(f"{len(moves)} שינויים, {len(by_teacher)} מורים -> chain_report.txt")
