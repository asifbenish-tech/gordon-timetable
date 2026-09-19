# -*- coding: utf-8 -*-
"""בודק כל שילוב של שעות מעגל שיח שלישי + ישיבת ניהול ומדווח כמה חוסרים יוצאים."""
import io, os, sys, json, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
TL = sys.argv[1] if len(sys.argv) > 1 else "70"
BASE = io.open("make_unified.py", encoding="utf-8").read()
MARK = "# שעות המעגלים משוחררות - הפותר בוחר את הטובות ביותר"
res = []
for cu in (1, 3, 5):
    for nh in (3, 5):
        if cu == nh: continue
        lock = ('for _h in range(1,7):\n'
                '    if ("u",_h) in blkh: m.Add(blkh[("u",_h)]==(1 if _h in (%d,%d) else 0))\n'
                'm.Add(nst[%d]==1)') % (cu, cu+1, 0 if nh == 3 else 1)
        io.open("make_unified.py", "w", encoding="utf-8").write(BASE.replace(MARK, lock))
        os.environ["TL"] = TL
        subprocess.run([sys.executable, "make_unified.py"], capture_output=True)
        r = subprocess.run([sys.executable, "solveALL.py"], capture_output=True,
                           text=True, encoding="utf-8", errors="replace")
        out = (r.stdout or "") + (r.stderr or "")
        tag = "מעגל %d-%d · ניהול %d-%d" % (cu, cu+1, nh, nh+1)
        if "INFEASIBLE" in out or r.returncode != 0:
            res.append((tag, None, None)); print(tag, "-> לא אפשרי"); continue
        subprocess.run([sys.executable, "fill2.py"], capture_output=True)
        S = json.load(io.open("sol_J.json", encoding="utf-8"))
        from data2 import CLASSES, SLOTS
        g = sum(1 for c in CLASSES for (d, h) in SLOTS if not S[c][str(d)+","+str(h)])
        H = json.load(io.open("sol_hat.json", encoding="utf-8"))
        from hdata import HCLASSES, HSLOTS
        gh = sum(1 for c in HCLASSES for (d, h) in HSLOTS
                 if (H[c][str(d)+","+str(h)] or "").endswith("חסר מורה"))
        res.append((tag, g, gh)); print(tag, "-> יסודי", g, "חטיבה", gh)
io.open("make_unified.py", "w", encoding="utf-8").write(BASE)
lines = ["שילוב | חוסרים יסודי | חוסרים חטיבה | סה\"כ"]
for tag, g, gh in sorted(res, key=lambda z: (999 if z[1] is None else z[1]+z[2])):
    lines.append("%s | %s | %s | %s" % (tag, "—" if g is None else g,
                 "—" if gh is None else gh, "לא אפשרי" if g is None else g+gh))
io.open("sweep.txt", "w", encoding="utf-8").write("\n".join(lines))
print("\n" + "\n".join(lines))
