# -*- coding: utf-8 -*-
"""staff_private.py - מפיק גיליון פרטי צוות: שם מלא, ת"ז, תפקיד, אילוצים ושעות.

   הקובץ מכיל תעודות זהות ולכן הוא *לא* נכנס לגיט ולא מתפרסם בלוח -
   הלוח מתפרסם בכתובת ציבורית, וכל מה שמוטמע בו גלוי לכל מי שיש לו הקישור.
   הרצה: python staff_private.py   ->   'צוות - פרטים.xlsx'
"""
import json, io, sys, importlib.util
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

spec = importlib.util.spec_from_file_location("mv", "make_viewer.py")
mv = importlib.util.module_from_spec(spec); spec.loader.exec_module(mv)

def _load(path, default):
    try: return json.load(io.open(path, encoding="utf-8"))
    except Exception: return default

# ת"ז: מהאפליקציה + מהקובץ המקומי (שניהם מחוץ לגיט)
ids = {}
for name, v in _load("ids_local.json", {}).items():
    if not name.startswith("_"): ids[name] = list(v) if isinstance(v, list) else [v]
ALIAS = {"חסאן": "חסן"}
for t in _load("app_data/v10_2026-2027_teachers.json", {"value": []})["value"]:
    n = (t.get("name") or "").strip().split()
    if n and t.get("tz"):
        n = ALIAS.get(n[0], n[0])
        if t["tz"] not in ids.setdefault(n, []): ids[n].append(t["tz"])

ROLE = {e["n"]: e["r"] for e in _load("access_map.json", {}).values()}
HOUSE = {e["n"]: e.get("h") for e in _load("access_map.json", {}).values() if e.get("h")}
HNAME = {"A": "רכז/ת בית א", "B": "רכז/ת בית ב", "C": "רכז/ת בית ג"}
RNAME = {"admin": "הנהלה - רואה הכל", "coordinator": "רכז/ת בית", "teacher": "מורה"}

TR = {r["t"]: r for r in mv.TR}
UT = {u["t"]: u for u in mv.util}
names = sorted(set(TR) | set(UT), key=lambda t: -(UT.get(t, {}).get("q") or 0))

wb = openpyxl.Workbook(); ws = wb.active; ws.title = "צוות"
ws.sheet_view.rightToLeft = True
HEAD = ["שם מלא", "שם בלוח", 'ת"ז', "הרשאה בלוח", "ימים חופשיים", "מה מלמד/ת",
        "יסודי", "חטיבה", 'תל"ן', "מגמות", 'סה"כ', "מכסה", "נותר"]
thin = Side(style="thin", color="D9D9D9")
ws.append(HEAD)
for c in ws[1]:
    c.font = Font(bold=True, color="FFFFFF")
    c.fill = PatternFill("solid", fgColor="0E6E66")
    c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    c.border = Border(thin, thin, thin, thin)

for t in names:
    u, r = UT.get(t, {}), TR.get(t, {})
    role = HNAME.get(HOUSE.get(t)) if t in HOUSE else RNAME.get(ROLE.get(t), "— אין הרשאה —")
    ws.append([mv._FULLN.get(t, t), t, " · ".join(ids.get(t, [])) or "— חסרה —", role,
               r.get("off", ""), r.get("subj", ""),
               u.get("ye") or "", u.get("ch") or "", u.get("tl") or "", u.get("mg") or "",
               u.get("tot", ""), u.get("q", ""), u.get("left", "")])
    row = ws[ws.max_row]
    for c in row:
        c.border = Border(thin, thin, thin, thin)
        c.alignment = Alignment(horizontal="center" if c.column > 6 else "right", vertical="center")
    if u.get("left", 0) < 0:  row[12].font = Font(bold=True, color="B3261E")
    elif u.get("left") == 0:  row[12].font = Font(bold=True, color="0E6E66")
    if not ids.get(t):        row[2].font = Font(color="B3261E")

for i, w in enumerate([22, 12, 24, 20, 16, 46, 8, 8, 8, 8, 8, 8, 8], 1):
    ws.column_dimensions[get_column_letter(i)].width = w
ws.freeze_panes = "A2"
OUT = "צוות - פרטים.xlsx"
wb.save(OUT)
miss = [t for t in names if not ids.get(t)]
print(f"{OUT} נוצר: {len(names)} מורים, {len(names)-len(miss)} עם ת\"ז")
if miss: print('ללא ת"ז:', " · ".join(miss))
print("הקובץ מכיל תעודות זהות - אינו נכנס לגיט ואינו מתפרסם בלוח.")
