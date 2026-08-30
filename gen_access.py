# -*- coding: utf-8 -*-
"""gen_access.py - בונה את access_map.json: מפת גישה ללוח המערכות.
   קורא את תעודות הזהות של המורים מנתוני האפליקציה (app_data, שדה tz)
   ושומר רק גיבוב חד-כיווני (PBKDF2-SHA256, 100 אלף איטרציות) - שום ת"ז
   לא נשמרת גלויה בריפו או בדף. ההזדהות בלוח משווה גיבוב מול גיבוב.

   תפקידים: מחנכים מזוהים אוטומטית; רכזי בתים: לייה (בית א),
   שרית (בית ב), אלי (בית ג); מנהלים רואים הכל.
   שימוש: python pull_app.py && python gen_access.py"""
import json, hashlib, io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SALT = b"gordon-lohot-2026"
COORDINATORS = {"לייה": "A", "שרית": "B", "אלי": "C"}
ADMINS = {"אסיף", "דאפי", "חסן"}
ALIAS = {"חסאן": "חסן"}   # שם באפליקציה -> שם בפותר
# ת"ז שאינן באפליקציה נשמרות ב-ids_local.json, שאינו נכנס לגיט (הריפו ציבורי).
# מבנה: {"שם": ["תעודת זהות", ...]} - אפשר יותר מאחת לאותו אדם.
try:
    EXTRA_IDS = {k: (v if isinstance(v, list) else [v])
                 for k, v in json.load(io.open("ids_local.json", encoding="utf-8")).items()
                 if not k.startswith("_")}
except FileNotFoundError:
    EXTRA_IDS = {}
    print('אזהרה: ids_local.json חסר - מי שת"ז שלו/ה אינה באפליקציה לא ייכנס למפה')

def hid(idnum):
    idn = "".join(ch for ch in str(idnum) if ch.isdigit()).rjust(9, "0")
    return hashlib.pbkdf2_hmac("sha256", idn.encode(), SALT, 100000).hex()

T = json.load(io.open("app_data/v10_2026-2027_teachers.json", encoding="utf-8"))["value"]
ids = {k: list(v) for k, v in EXTRA_IDS.items()}
for t in T:      # ת"ז מהאפליקציה מתווספת ואינה דורסת - כך אף אחד לא מאבד גישה
    n = (t.get("name") or "").strip().split()[0] if (t.get("name") or "").strip() else None
    if n and t.get("tz"):
        n = ALIAS.get(n, n)
        if t["tz"] not in ids.setdefault(n, []): ids[n].append(t["tz"])

access = {}
for n, idlist in ids.items():
    role = "coordinator" if n in COORDINATORS else ("admin" if n in ADMINS else "teacher")
    e = {"n": n, "r": role}
    if role == "coordinator": e["h"] = COORDINATORS[n]
    for idn in idlist: access[hid(idn)] = e
io.open("access_map.json", "w", encoding="utf-8").write(json.dumps(access, ensure_ascii=False, indent=1))
roles = {e["n"]: e["r"] for e in access.values() if e["r"] != "teacher"}
missing = sorted({(t.get("name") or "").strip().split()[0] for t in T
                  if (t.get("name") or "").strip() and not t.get("tz")})
print(f"access_map.json: {len(access)} משתמשים | בעלי תפקיד: {roles}")
print("ללא ת\"ז באפליקציה (לא יוכלו להזדהות עד שתוזן):", " · ".join(missing))
