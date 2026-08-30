# -*- coding: utf-8 -*-
"""outAPI.py - מייצר timetable.json: קובץ נתונים אחד, נקי ויציב, לאפליקציות חיצוניות.
   רץ אוטומטית בסוף go.py. את הקובץ מעתיקים לתיקיית public של אפליקציית הווב
   (Firebase Hosting) והאפליקציה עושה fetch('/timetable.json').

   סכמה:
     generated        - חותמת זמן ISO
     days             - שמות הימים (אינדקס 0=ראשון .. 5=שישי)
     elementary/junior- לכל כיתה: home (מחנך/ת), hours (שעות לכל יום), cells
     cells            - מפתח "יום,שעה" -> תא:
         t    - הטקסט הראשי (מורה ביסודי / מקצוע בחטיבה)
         s    - שורת משנה (מקצוע-משנה / שם מורה / הערה)
         k    - סוג: home=מחנך, tln=תל"ן, mag=מגמות/מרוכז, pe=ספורט שכבתי,
                fill=מילוי חלון, hole=חוסר (מחנך נכנס זמנית), off=אין לימודים
         co   - תוספת (צופיה מצטרפת / סידור חדר אוכל / זמני)
         away - המחנך/ת בחוץ (מפגשה / ישיבת מרכזי בית חינוך)
     teachers         - לכל מורה רשימת אירועים [side, day, hour, label]
                        side: יסודי / חטיבה / תל"ן / מגמות / סדירות
     sedirot          - מפגשות, ישיבת מרכזי בית חינוך, קבוצות
     holes            - רשימת החוסרים הפתוחים ביסודי (מכוסים זמנית ע"י המחנך)"""
import json, io, sys, importlib.util, datetime
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

spec = importlib.util.spec_from_file_location("mv", "make_viewer.py")
mv = importlib.util.module_from_spec(spec); spec.loader.exec_module(mv)
from data2 import DAY_NAMES, DAY_HOURS, HOMEROOM, CLASSES, SLOTS
from hdata import HHOME, HDAY, HCLASSES

S = json.load(io.open("sol_J.json", encoding="utf-8"))
SED = json.load(io.open("sed_J.json", encoding="utf-8"))
holes = [{"class": c, "day": d, "hour": h, "cover": HOMEROOM[c] + " (זמני)"}
         for c in CLASSES for (d, h) in SLOTS if not S[c][f"{d},{h}"]]

try:    NAMES = json.load(io.open("names_map.json", encoding="utf-8"))
except Exception: NAMES = {}
# מיפוי לזיהוי באפליקציה (school-gordon): התאמת כיתות ומורים למזהים של האתר
def _app_map():
    try:
        AC = json.load(io.open("app_data/v10_2026-2027_classes.json", encoding="utf-8"))["value"]
        AT = json.load(io.open("app_data/v10_2026-2027_teachers.json", encoding="utf-8"))["value"]
    except Exception:
        return {"classes": {}, "teachers": {}}
    alias = {"חסן": "חסאן"}   # שם בפותר -> שם באפליקציה
    cmap = {}
    for c in list(HOMEROOM) + list(HHOME.keys()):
        grade, home = c.split(" ", 1)
        first = alias.get(home, home).split()[0]
        for ac in AC:
            if ac.get("grade") == grade and (ac.get("name") or "").split()[0] == first:
                cmap[c] = {"app_id": ac["id"], "app_name": ac.get("name"), "grade": grade}
                break
    tmap = {}
    for t in set(list(HOMEROOM.values()) + list(HHOME.values())) | set(mv.teachers):
        first = alias.get(t, t)
        for at in AT:
            if (at.get("name") or "").strip().split()[0:1] == [first]:
                tmap[t] = {"app_id": at["id"], "full_name": " ".join(((at.get("name") or "") + " " + (at.get("lastName") or "")).split())}
                break
    return {"classes": cmap, "teachers": tmap}

out = {
    "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    "days": DAY_NAMES,
    "app_map": _app_map(),
    "full_names": {k: v for k, v in NAMES.items() if v},   # שם פרטי -> שם מלא (מתוך names_map.json)
    "elementary": {c: {"home": v["home"], "hours": DAY_HOURS, "cells": v["cells"]}
                   for c, v in mv.elem.items()},
    "junior": {c: {"home": v["home"], "hours": HDAY, "cells": v["cells"]}
               for c, v in mv.jun.items()},
    "teachers": mv.teachers,
    "sedirot": {
        "מפגשה (מעגלי שיח) - שני": {"hours": SED["מעגלי שיח שני"], "who": SED["קבוצת שני"]},
        "מפגשה (מעגלי שיח) - שלישי": {"hours": SED["מעגלי שיח שלישי"], "who": SED["קבוצת שלישי"]},
        "ישיבת מרכזי בית חינוך - שלישי": {"hours": SED["ישיבת ניהול שלישי"],
                                          "who": ["לייה", "שרית", "יערה", "צופיה", "אסיף", "אלי"]},
        "אסיפת צוות - ראשון": {"hours": [6, 7], "who": ["כל המורים"]},
    },
    "holes": holes,
}

# ---- רשימה שטוחה ואחידה: כל שיעור עם מקצוע, מורה ומזהי האפליקציה ----
_AM = out["app_map"]
def _norm(level, cls, key, cell):
    d, h = map(int, key.split(","))
    k = cell.get("k") or ""
    t = cell.get("t") or ""
    sub = cell.get("s") or ""
    if level == "junior":
        subject, teacher = t, sub
        if k == "mag": teacher = ""
    else:                                   # יסודי: t = שם המורה
        teacher, subject = t, ""
        if k == "tln":
            subject, teacher = 'תל"ן', t.replace('תל"ן · ', "")
        elif k == "half":
            subject, teacher = "שיעור (½ כיתה) + תל\"ן (½ כיתה)", t
        elif k == "hole":
            subject, teacher = "", t
        elif sub and sub != "חצי כיתה":
            subject = sub
    if not teacher and not subject: return None
    return {
        "level": level, "class": cls,
        "class_app_id": (_AM["classes"].get(cls) or {}).get("app_id"),
        "day": d, "day_name": DAY_NAMES[d], "hour": h,
        "subject": subject, "teacher": teacher,
        "teacher_app_id": (_AM["teachers"].get(teacher) or {}).get("app_id"),
        "kind": k or "regular",
        "note": cell.get("co") or "",
        "temporary": k == "hole",
    }
lessons = []
for lvl, src in (("elementary", out["elementary"]), ("junior", out["junior"])):
    for cls, info in src.items():
        for key, cell in info["cells"].items():
            r = _norm(lvl, cls, key, cell)
            if r: lessons.append(r)
lessons.sort(key=lambda z: (z["level"], z["class"], z["day"], z["hour"]))
out["lessons"] = lessons

# ---- index: רשימת המערכות שאפשר למשוך (לתפריט בחירה באפליקציה) ----
_HOUSES = [("A", "בית א", "כיתות א-ג", [c for c in CLASSES if c[0] in "אבג"]),
           ("B", "בית ב", "כיתות ד-ו", [c for c in CLASSES if c[0] in "דהו"]),
           ("C", "בית ג", "חטיבה ז-ט", list(HCLASSES))]
_FN = out["full_names"]
index = [{"id": "all", "type": "all", "label": f"כל המערכות ({len(lessons)} שיעורים)",
          "count": len(lessons)}]
for hk, hname, hgrades, hcls in _HOUSES:
    n = sum(1 for L in lessons if L["class"] in hcls)
    index.append({"id": f"house:{hk}", "type": "house", "label": f"{hname} ({hgrades})",
                  "classes": hcls, "count": n})
for lvl, src in (("elementary", out["elementary"]), ("junior", out["junior"])):
    for cls in src:
        index.append({"id": f"class:{cls}", "type": "class", "label": f"כיתה {cls}",
                      "level": lvl, "class": cls,
                      "app_id": (_AM["classes"].get(cls) or {}).get("app_id"),
                      "count": sum(1 for L in lessons if L["class"] == cls)})
for t in sorted(out["teachers"]):
    index.append({"id": f"teacher:{t}", "type": "teacher",
                  "label": "מורה: " + _FN.get(t, t), "teacher": t,
                  "app_id": (_AM["teachers"].get(t) or {}).get("app_id"),
                  "count": sum(1 for L in lessons if L["teacher"] == t)})
out["index"] = index
io.open("timetable.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("timetable.json נוצר,", len(out["elementary"]) + len(out["junior"]), "כיתות,", len(out["teachers"]), "מורים")
