# -*- coding: utf-8 -*-
"""עקיפות נתונים להצעות (propose.py). OVERRIDES=<קובץ json> עם מפתחות
   "data" / "data2" / "hdata"; כל אחד = {שם משתנה: ערך}. מילון מתמזג
   (מפתח קיים מוחלף, חדש נוסף, ערך null מוחק); כל דבר אחר מוחלף.
   מפתחות "א|ב" הופכים לזוג (למשל OVR: "ט אסיף|חינוך"), מפתחות ספרתיים
   ל-int (day_until: {"1":4}), ורשימות [יום,שעה] לזוגות ((1,3) ולא [1,3] -
   אחרת בדיקת 'in' נכשלת בשקט). מנגנון להצעות בלבד - לא לפרסום."""
import io, json, os

def _conv(v):
    if isinstance(v, dict):
        out = {}
        for k, x in v.items():
            if isinstance(k, str) and "|" in k: k = tuple(k.split("|"))
            elif isinstance(k, str) and k.lstrip("-").isdigit(): k = int(k)
            out[k] = _conv(x)
        return out
    if isinstance(v, list):
        if len(v) == 2 and all(isinstance(a, int) for a in v): return tuple(v)
        return [_conv(a) for a in v]
    return v

def apply(g, section):
    p = os.environ.get("OVERRIDES")
    if not p: return
    ov = json.load(io.open(p, encoding="utf-8")).get(section) or {}
    for name, val in ov.items():
        val = _conv(val)
        cur = g.get(name)
        if isinstance(cur, dict) and isinstance(val, dict):
            for k, x in val.items():
                if x is None: cur.pop(k, None)
                elif isinstance(cur.get(k), dict) and isinstance(x, dict): cur[k].update(x)
                else: cur[k] = x
        else:
            g[name] = val
    if ov: print(f"OVERRIDES[{section}]: {', '.join(ov)}")
