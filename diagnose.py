# -*- coding: utf-8 -*-
"""diagnose.py - כשהפותר נופל (INFEASIBLE): מריץ אוטומטית 'הרפיה אחת בכל פעם' ומדווח
   אילו הרפיות בודדות מחזירות פתרון. go.py מריץ את זה לבד אחרי INFEASIBLE (NODIAG=1 מבטל).
   הרצה ידנית: python diagnose.py [שניות לכל ניסוי, ברירת מחדל 45]
   הניסויים: כל חוק מדיניות ב-rules.py בנפרד (RULES_OFF), וכן כפתורי המנוע:
   בלי נעילות (PINS), בלי הקפאות (FREEZEJ/FREEZEH). הסביבה הנוכחית (PINS, RULES_OFF...) נשמרת."""
import io, os, subprocess, sys, concurrent.futures as cf
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import rules
TL = sys.argv[1] if len(sys.argv) > 1 else "45"
base = dict(os.environ); base["TL"] = TL; base["NODIAG"] = "1"
already_off = [i for i in base.get("RULES_OFF", "").split(",") if i]

def run(label, env):
    r = subprocess.run([sys.executable, "engine.py"], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    st = next((l.split("status:")[1].strip() for l in r.stdout.splitlines() if l.startswith("status:")), "ERROR")
    return label, st

jobs = []
for r in rules.RULES:
    if not r["active"] or r["id"] in already_off: continue
    e = dict(base); e["RULES_OFF"] = ",".join(already_off + [r["id"]])
    jobs.append((f"[{r['id']}] {r['name']}", e))
for k, lab in (("PINS", "בלי הנעילות (PINS)"), ("FREEZEJ", "בלי הקפאת היסודי"), ("FREEZEH", "בלי הקפאת החטיבה")):
    if base.get(k):
        e = dict(base); e.pop(k); jobs.append((lab, e))
print(f"אבחון: {len(jobs)} ניסויים, {TL} שניות כל אחד, 4 במקביל...")
ok, bad = [], []
with cf.ThreadPoolExecutor(max_workers=4) as ex:
    for label, st in ex.map(lambda j: run(*j), jobs):
        (ok if st in ("OPTIMAL", "FEASIBLE") else bad).append((label, st))
        print(f"  {'✔' if st in ('OPTIMAL','FEASIBLE') else '✗'} {label}: {st}")
print()
if ok:
    print("הרפיה אחת מספיקה - כל אחת מאלה לבדה מחזירה פתרון:")
    for label, _ in ok: print("   •", label)
else:
    print("אף הרפיה בודדת לא מספיקה. כנראה חשבון קיבולת (ראו 'קיבולת' בפלט הפותר, או python capacity.py),")
    print("או שילוב של כמה כללים. הצעד הבא: python diagnose.py עם RULES_OFF=<כלל> כדי לבדוק זוגות.")
