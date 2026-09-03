# -*- coding: utf-8 -*-
"""approve.py - מאשר את הפתרון הנוכחי כמערכת המפורסמת.

   מעתיק sol_J.json / sol_hat.json ל-baseline_J.json / baseline_hat.json.
   ה-baseline הוא מה שהפותר מנסה לשמור עליו (יציבות): כל ריצה עתידית
   תזיז כמה שפחות תאים ממנו. לכן מריצים את זה *רק* אחרי שהמנהל אישר
   את המערכת ולפני הדחיפה - לא כחלק מהצינור הרגיל.
   הרצה: python approve.py
"""
import io, json, shutil, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from data2 import CLASSES, SLOTS
from hdata import HCLASSES, HSLOTS

def _diff(prev, cur, classes, slots):
    n = 0
    for c in classes:
        for (d, h) in slots:
            if prev.get(c, {}).get(f"{d},{h}") != cur.get(c, {}).get(f"{d},{h}"): n += 1
    return n

for side, src, dst, classes, slots in (("יסודי", "sol_J.json", "baseline_J.json", CLASSES, SLOTS),
                                      ("חטיבה", "sol_hat.json", "baseline_hat.json", HCLASSES, HSLOTS)):
    cur = json.load(io.open(src, encoding="utf-8"))
    try: prev = json.load(io.open(dst, encoding="utf-8"))
    except FileNotFoundError: prev = {}
    n = _diff(prev, cur, classes, slots)
    shutil.copyfile(src, dst)
    print(f"{side}: baseline עודכן ({n} תאים שונים מהקודם)")
print("מכאן הפותר ישמור על המערכת הזו. לדחוף ל-master כדי לפרסם.")
