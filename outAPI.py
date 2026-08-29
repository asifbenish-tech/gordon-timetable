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
out = {
    "generated": datetime.datetime.now().isoformat(timespec="seconds"),
    "days": DAY_NAMES,
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
io.open("timetable.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False, indent=1))
print("timetable.json נוצר,", len(out["elementary"]) + len(out["junior"]), "כיתות,", len(out["teachers"]), "מורים")
