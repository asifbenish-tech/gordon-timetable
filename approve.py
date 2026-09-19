# -*- coding: utf-8 -*-
"""approve.py - מאשר את הפתרון הנוכחי כמערכת המפורסמת.

   מעתיק sol_J.json / sol_hat.json ל-baseline_J.json / baseline_hat.json.
   ה-baseline הוא מה שהפותר מנסה לשמור עליו (יציבות): כל ריצה עתידית
   תזיז כמה שפחות תאים ממנו. לכן מריצים את זה *רק* אחרי שהמנהל אישר
   את המערכת ולפני הדחיפה - לא כחלק מהצינור הרגיל.
   הרצה: python approve.py        (DRY=1 - רק מדפיס את היקף השינוי, בלי לעדכן)
   לפני הדריסה מודפס היקף ההשפעה: כמה תאים, אילו כיתות, אילו מורים, ומה
   השתנה בכל תא (היה ← נהיה) - כדי שהאישור יינתן על מה שבאמת זז.
"""
import io, json, os, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from data2 import CLASSES, SLOTS
from hdata import HCLASSES, HSLOTS

from data2 import DAY_NAMES
import collections

def _diff(prev, cur, classes, slots):
    """רשימת התאים השונים: (כיתה, יום, שעה, היה, נהיה)."""
    return [(c, d, h, prev.get(c, {}).get(f"{d},{h}") or "", cur.get(c, {}).get(f"{d},{h}") or "")
            for c in classes for (d, h) in slots
            if (prev.get(c, {}).get(f"{d},{h}") or "") != (cur.get(c, {}).get(f"{d},{h}") or "")]

def _impact(cells):
    """היקף ההשפעה - מה שהמנהל רואה לפני שה-baseline נדרס: כיתות, מורים, וכל תא."""
    if not cells: return ["  אין שינוי"]
    byc = collections.Counter(c for c, *_ in cells)
    ts = collections.Counter()
    for c, d, h, a, b in cells:
        for v in (a, b):
            for t in (v.split(" – ")[-1] if " – " in v else v).split(" + "):
                if t: ts[t] += 1
    out = ["  לפי כיתה: " + ", ".join(f"{c} {n}" for c, n in sorted(byc.items())),
           "  מורים מעורבים: " + ", ".join(f"{t} ({n})" for t, n in ts.most_common())]
    out += [f"    {c} | {DAY_NAMES[d]} ש{h}: {a or '—'}  ←  {b or '—'}" for c, d, h, a, b in sorted(cells)]
    return out

for side, src, dst, classes, slots in (("יסודי", "sol_J.json", "baseline_J.json", CLASSES, SLOTS),
                                      ("חטיבה", "sol_hat.json", "baseline_hat.json", HCLASSES, HSLOTS)):
    cur = json.load(io.open(src, encoding="utf-8"))
    try: prev = json.load(io.open(dst, encoding="utf-8"))
    except FileNotFoundError: prev = {}
    cells = _diff(prev, cur, classes, slots)
    print(f"{side}: {len(cells)} תאים שונים מה-baseline הקודם")
    print("\n".join(_impact(cells)))
    if not os.environ.get("DRY"): shutil.copyfile(src, dst)
# מפת התל"ן נשמרת גם היא - אחרת שעות החצי-כיתה זזות בכל הרצה מחדש
if os.environ.get("DRY"):
    print("DRY=1: ה-baseline לא עודכן.")
else:
    try:
        shutil.copyfile("tln_map.json", "baseline_tln.json")
        print('תל"ן: baseline_tln.json עודכן')
    except FileNotFoundError:
        print('tln_map.json חסר - אין בסיס לתל"ן')
    try:
        shutil.copyfile("co_zofia3.json", "baseline_co.json")   # שעות צופיה המקבילות - גם הן מיוצבות
        print('צופיה: baseline_co.json עודכן')
    except FileNotFoundError:
        print('co_zofia3.json חסר - אין בסיס לשעות צופיה')
    print("מכאן הפותר ישמור על המערכת הזו. לדחוף ל-master כדי לפרסם.")
