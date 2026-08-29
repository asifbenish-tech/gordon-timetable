# -*- coding: utf-8 -*-
"""go.py - ריצה מלאה בפקודה אחת: פותר -> מילוי חורים -> אקסל -> צופה.
   שימוש:  python go.py [שניות]     ברירת מחדל 90 שניות לפותר.
   הפותר מתחיל מהפתרון הקודם (warm start) ולכן מהיר."""
import subprocess, sys, os, time, io, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TL = sys.argv[1] if len(sys.argv) > 1 else "90"
os.environ["TL"] = TL
t0 = time.time()


def run(script, label):
    r = subprocess.run([sys.executable, script], capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    out = (r.stdout or "") + (r.stderr or "")
    tail = [l for l in (r.stdout or "").strip().split("\n") if l.strip()][-3:]
    print("  " + label + ": " + " | ".join(tail))
    if r.returncode != 0:
        print("\n!!! שגיאה ב-" + script + ":\n" + (r.stderr or "")[-1500:])
        sys.exit(1)
    return out


print("מריץ (מגבלת זמן " + TL + " שניות)...")
out = run("engine.py", "פותר")
if "INFEASIBLE" in out or "MODEL_INVALID" in out:
    print("\n!!! הפותר לא מצא פתרון - האילוצים סותרים. שום קובץ לא נדרס.")
    sys.exit(1)
run("fill2.py", "ממלא חורים")
run("checks.py", "בדיקות")
run("outGAPS.py", "אקסל")
run("make_viewer.py", "צופה")
run("outAPI.py", "timetable.json לאפליקציה")

S = json.load(io.open("sol_J.json", encoding="utf-8"))
from data2 import CLASSES, SLOTS, DAY_NAMES
g = [(c, DAY_NAMES[d], h) for c in CLASSES for (d, h) in SLOTS
     if not S[c][str(d) + "," + str(h)]]
msg = ["יסודי " + str(416 - len(g)) + "/416 · " + str(len(g)) +
       " חוסרים · " + str(int(time.time() - t0)) + " שניות"]
for c, d, h in g:
    msg.append("   " + c + " " + d + " ש" + str(h))
io.open("status.txt", "w", encoding="utf-8").write("\n".join(msg))
print("\n" + "\n".join(msg))
