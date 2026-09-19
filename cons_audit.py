# -*- coding: utf-8 -*-
"""cons_audit.py - האם האילוצים הרשומים מתאימים למה שקורה בפועל, בשני בתי הספר יחד?

   לכל מורה: הימים והשעות שבהם הוא/היא באמת מלמד/ת לפי המערכת המפורסמת
   (יסודי + חטיבה + מילויים + שישי ט + הצטרפות להילה + מגמות) מול DAYS_OFF2,
   UNAVAIL2/EVENTS2/HEV, TCONS ו-MAXDAYS. פער = או שהנתון שגוי, או שיש כלל
   במנוע שעוקף אותו - בשני המקרים כדאי לדעת לפני שבונים מערכות מחדש.
   שימוש: python cons_audit.py     (0 = הכל תואם)"""
import io, json, sys, collections
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from data import DAY_NAMES, DAY_HOURS
from data2 import DAYS_OFF2, UNAVAIL2, EVENTS2, TCONS, MAXDAYS, MAGAMA, CLASSES, SLOTS
from hdata import HCLASSES, HSLOTS, HDAY, HEV
import cons_sync

J = json.load(io.open("sol_J.json", encoding="utf-8")); H = json.load(io.open("sol_hat.json", encoding="utf-8"))
try: ZH = json.load(io.open("zvi_hila.json", encoding="utf-8"))
except Exception: ZH = {}
try: GE = json.load(io.open("galit_erez.json", encoding="utf-8"))
except Exception: GE = {}

teach = collections.defaultdict(set)      # מורה -> {(יום,שעה,תיאור)}
for c in CLASSES:
    for (d, h) in SLOTS:
        t = J[c].get(f"{d},{h}")
        if t and t != 'תל"ן': teach[t].add((d, h, f"{c}"))
for c in HCLASSES:
    for (d, h) in HSLOTS:
        v = H[c].get(f"{d},{h}") or ""
        if " – " not in v: continue
        sj, t = v.split(" – ", 1)
        for tt in t.split(" + "):
            if tt in ("מגמות", "חסר מורה", "שכבת ט יחד"): continue
            teach[tt].add((d, h, f"{c} · {sj}"))
try:
    for k, v in json.load(io.open("tln_map.json", encoding="utf-8")).items():   # תל"ן חצי-כיתה: המורות לא מופיעות ב-sol_J
        c, s = k.split("|"); d, h = map(int, s.split(","))
        names = [v.split('חצי תל"ן ')[1].split(" · ")[0]] if v.startswith('חצי תל"ן ') else v.split(" + ")
        for t in names: teach[t.strip()].add((d, h, f"{c} (תל\"ן)"))
except FileNotFoundError: pass
for k, t in list(ZH.items()) + list(GE.items()):
    c, s = k.split("|"); d, h = map(int, s.split(",")); teach[t].add((d, h, f"{c} (מצטרף/ת)"))
for (d, h), ts in MAGAMA.items():
    for t in ts: teach[t].add((d, h, "מגמות"))

rows = cons_sync.current()
issues = []
for t, slots in sorted(teach.items()):
    r = rows.get(t)
    if not r: continue
    days = {d for d, h, _ in slots}
    for dn in r["off"]:
        d = DAY_NAMES.index(dn)
        if d in days: issues.append((t, f"יום חופש רשום ({dn}) אבל מלמד/ת: " + ", ".join(sorted(x for dd, h, x in slots if dd == d)[:3])))
    for (d, h, what) in sorted(slots):
        if (d, h) in UNAVAIL2.get(t, []): issues.append((t, f"חסימה (UNAVAIL2) ב{DAY_NAMES[d]} ש{h} אבל מלמד/ת: {what}"))
        if (d, h) in EVENTS2.get(t, []) or (d, h) in HEV.get(t, []):
            if "מגמות" not in what and "מצטרף" not in what: issues.append((t, f"סדירות/ישיבה ב{DAY_NAMES[d]} ש{h} אבל מלמד/ת: {what}"))
        tc = TCONS.get(t, {})
        if h > tc.get("max_hour", 99): issues.append((t, f"מעבר ל-max_hour {tc['max_hour']}: {DAY_NAMES[d]} ש{h} {what}"))
        if h > tc.get("day_until", {}).get(d, 99): issues.append((t, f"מעבר ל-day_until {DAY_NAMES[d]}={tc['day_until'][d]}: ש{h} {what}"))
        if (d, h) in tc.get("no_slots", []): issues.append((t, f"חסימת TCONS ב{DAY_NAMES[d]} ש{h} אבל מלמד/ת: {what}"))
    if t in MAXDAYS and len(days - {5}) > MAXDAYS[t]: issues.append((t, f"MAXDAYS={MAXDAYS[t]} אבל עובד/ת {len(days - {5})} ימים"))
    tc = TCONS.get(t, {})
    if "max_days" in tc and len(days) > tc["max_days"]: issues.append((t, f"max_days={tc['max_days']} אבל עובד/ת {len(days)} ימים: " + ", ".join(DAY_NAMES[d] for d in sorted(days))))
    side_e = any(x for d, h, x in slots if x.split(" ")[0] in "אבגדהו" and " · " not in x); side_j = any(" · " in x or "מצטרף" in x for d, h, x in slots)
    if side_e and r["side"] == "jun": issues.append((t, "רשום/ה כמורה חטיבה בלבד אבל מלמד/ת ביסודי"))
    if side_j and r["side"] == "elem": issues.append((t, "רשום/ה כמורה יסודי בלבד אבל מלמד/ת בחטיבה"))
for t in rows:
    if t not in teach and t not in ("אבי קרן צבי",): issues.append((t, "ברשימת המורים אבל אין לו/ה שום שיעור במערכת המפורסמת"))
if issues:
    print(f"פערים בין האילוצים הרשומים למערכת בפועל: {len(issues)}")
    for t, msg in issues: print(f"  {t}: {msg}")
    sys.exit(1)
print("האילוצים הרשומים תואמים למערכת בפועל (יסודי + חטיבה)")
