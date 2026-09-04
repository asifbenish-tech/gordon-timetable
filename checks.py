# -*- coding: utf-8 -*-
"""checks.py — סוללת בדיקות אוטומטית. רצה אחרי כל פתרון; נכשלת בקול אם כלל הופר."""
import io, json, collections, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from data2 import CLASSES, SLOTS, DAY_NAMES, DAYS_OFF2, HOMEROOM, FRIDAY_TEACHER
from hdata import HCLASSES, HSLOTS, HDAY, GRADE, NEED, HOFF, OVR

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

# 4. שישי יסודי = מחנך בלבד (למעט ההחלפה המתוכננת בין דני לתניה)
FRI_SWAP = {("ה דני", 3): "תניה", ("ה תניה", 3): "דני"}
for c in CLASSES:
    for h in range(1, 5):
        t = S[c][f"5,{h}"]
        if t and t != FRI_SWAP.get((c, h), FRIDAY_TEACHER.get(c, HOMEROOM[c])):
            errors.append(f"שישי {c} ש{h}: {t}")
# ההחלפה בשישי חייבת להיות הדדית - אחרת מורה נמצא/ת בשתי כיתות בו-זמנית
for (c, h), t in FRI_SWAP.items():
    if S[c][f"5,{h}"] != t:
        errors.append(f"החלפת שישי חסרה: {c} ש{h} אמור להיות {t}")

# 5. מורות תל"ן לא בכיתות
for c in CLASSES:
    for (d, h) in SLOTS:
        if S[c][f"{d},{h}"] in ("יעל", "חגית", "יפעת", "הילית", "מאמי"):
            errors.append(f'{S[c][f"{d},{h}"]} (תל"ן) בכיתה {c}')

# 6. קבצי הצד (הצטרפות מורה לשיעור של מורה אחר/ת, ותל"ן חצוי) מול הפתרון.
#    הקבצים האלה נכתבים בנפרד מ-sol_hat/sol_J, ולכן הם יכולים להתיישן מולם -
#    למשל כשמשחזרים חלק מהקבצים מגיט. אז התצוגה מציירת מורה בכיתה שבה הוא
#    בכלל לא נמצא, ובלי הבדיקה הזו זה עובר בשקט. (גלית הופיעה ככה בו-זמנית
#    בט תמיר וגם בז נעמי ברביעי ש1.)
def _busy_at(d, h):
    """מי מלמד/ת בשעה הזו, ובאיזו כיתה - מתוך הפתרון עצמו בלבד."""
    out = {}
    for c in CLASSES:
        t = S[c].get(f"{d},{h}")
        if t and t != 'תל"ן': out.setdefault(t, []).append(c)
    if h <= HDAY[d]:
        for c in HCLASSES:
            t = tof(H[c][f"{d},{h}"] or "")
            if t and t not in ("מגמות", "שרית + חסן", "חסר מורה"):
                out.setdefault(t, []).append(c)
    return out

def _side(fname, pick):
    try: raw = json.load(io.open(fname, encoding="utf-8"))
    except FileNotFoundError: return []
    out = []
    for k, v in raw.items():
        t = pick(v)
        if not t: continue
        c, s = k.split("|"); d, h = (int(x) for x in s.split(","))
        c = _CO_CLASS.get(c, c)
        out.append((fname, t, c, d, h))
    return out

_CO_CLASS = {"anna": "א אנה", "pnina": "א פנינה"}   # co_zofia3 משתמש בקיצורים
for fname, t, c, d, h in (
        _side("galit_erez.json", lambda v: v) +
        _side("zvi_hila.json", lambda v: v) +
        _side("co_zofia3.json", lambda v: "צופיה") +
        _side("tln_map.json", lambda v: v.split('חצי תל"ן ')[1].split(" · ")[0]
              if isinstance(v, str) and v.startswith("חצי") else None)):
    where = _busy_at(d, h).get(t, [])
    if [x for x in where if x != c]:
        errors.append(f"{t} {DAY_NAMES[d]} ש{h}: {fname} אומר {c}, "
                      f"אבל בפתרון הוא/היא ב{' + '.join(where)}")


if errors:
    print("!!! נכשלו " + str(len(errors)) + " בדיקות:")
    for e in errors[:12]: print("   ✗ " + e)
    sys.exit(1)
print("checks: הכל תקין ✔")
