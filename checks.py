# -*- coding: utf-8 -*-
"""checks.py — סוללת בדיקות אוטומטית. רצה אחרי כל פתרון; נכשלת בקול אם כלל הופר."""
import io, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from data2 import CLASSES, SLOTS, DAY_NAMES, DAYS_OFF2, HOMEROOM, FRIDAY_TEACHER
from hdata import HCLASSES, HSLOTS, HDAY, GRADE, NEED, HOFF

S = json.load(io.open("sol_J.json", encoding="utf-8"))
H = json.load(io.open("sol_hat.json", encoding="utf-8"))
def tof(v): return v.split(" – ")[1] if " – " in v else None
def sof(v): return v.split(" – ")[0] if " – " in v else None

errors = []

# 1. כפילויות מורים והפרות ימי חופש
for (d, h) in SLOTS:
    seen = {}
    for c in CLASSES:
        t = S[c][f"{d},{h}"]
        if t and t != 'תל"ן':
            if t in seen: errors.append(f"כפילות {t} {DAY_NAMES[d]} ש{h}")
            seen[t] = 1
            if DAY_NAMES[d] in DAYS_OFF2.get(t, []): errors.append(f"{t} ביום חופש {DAY_NAMES[d]}")
    if h <= HDAY[d]:
        for c in HCLASSES:
            t = tof(H[c][f"{d},{h}"] or "")
            if t and t in seen and t not in ("מגמות", "שרית + חסן", "חסר מורה"):
                errors.append(f"{t} יסודי+חטיבה {DAY_NAMES[d]} ש{h}")
            if t and t not in ("מגמות", "שרית + חסן", "חסר מורה") and DAY_NAMES[d] in HOFF.get(t, []):
                errors.append(f"{t} (חטיבה) ביום חופש {DAY_NAMES[d]}")

# 2. תוכניות לימודים חטיבה
OVR = {("ט אסיף", "חינוך"): 3, ("ט אסיף", "מתמטיקה"): 5, ("ט תמיר", "חינוך"): 3}
for c in HCLASSES:
    g = GRADE[c]
    cnt = collections.Counter(sof(H[c][f"{d},{h}"]) for (d, h) in HSLOTS if H[c][f"{d},{h}"])
    for subj, per in NEED.items():
        want = OVR.get((c, subj), per[g])
        if cnt.get(subj, 0) != want:
            errors.append(f"{c}: {subj} {cnt.get(subj,0)}/{want}")

# 3. חלונות בחטיבה
for c in HCLASSES:
    for d in range(6):
        seen2 = False
        for h in range(1, HDAY[d] + 1):
            if not H[c][f"{d},{h}"]: seen2 = True
            elif seen2: errors.append(f"חלון {c} {DAY_NAMES[d]} ש{h}")

# 4. שישי יסודי = מחנך בלבד
for c in CLASSES:
    for h in range(1, 5):
        t = S[c][f"5,{h}"]
        if t and t != FRIDAY_TEACHER.get(c, HOMEROOM[c]):
            errors.append(f"שישי {c} ש{h}: {t}")

# 5. מורות תל"ן לא בכיתות
for c in CLASSES:
    for (d, h) in SLOTS:
        if S[c][f"{d},{h}"] in ("יעל", "חגית", "יפעת", "הילית", "מאמי"):
            errors.append(f'{S[c][f"{d},{h}"]} (תל"ן) בכיתה {c}')

if errors:
    print("!!! נכשלו " + str(len(errors)) + " בדיקות:")
    for e in errors[:12]: print("   ✗ " + e)
    sys.exit(1)
print("checks: הכל תקין ✔")
