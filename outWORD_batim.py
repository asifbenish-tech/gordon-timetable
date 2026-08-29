# -*- coding: utf-8 -*-
"""outWORD_batim.py - שלושה קבצי וורד לפי בתים: א (א-ג), ב (ד-ו), ג (ז-ט).
   בכל קובץ: מערכות הכיתות של הבית + מערכות כל המורים שמלמדים בו.
   שימוש: python outWORD_batim.py   (דורש node + npm install docx)"""
import json, io, subprocess, sys, importlib.util
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

spec = importlib.util.spec_from_file_location("mv", "make_viewer.py")
mv = importlib.util.module_from_spec(spec); spec.loader.exec_module(mv)
from data2 import DAY_NAMES, DAY_HOURS, HOMEROOM, CLASSES
from hdata import HHOME, HDAY, HCLASSES

home_of = {}
for c, t in HOMEROOM.items(): home_of.setdefault(t, []).append(("elem", c))
for c, t in HHOME.items():    home_of.setdefault(t, []).append(("jun", c))
data = {
    "days": DAY_NAMES,
    "day_hours_elem": DAY_HOURS, "day_hours_jun": HDAY,
    "teachers": mv.teachers,
    "elem": {c: {"cells": v["cells"], "home": v["home"]} for c, v in mv.elem.items()},
    "jun":  {c: {"cells": v["cells"], "home": v["home"]} for c, v in mv.jun.items()},
    "home_of": home_of,
    "full_names": (lambda: (json.load(io.open("names_map.json", encoding="utf-8"))))() if __import__("os").path.exists("names_map.json") else {},
}
io.open("word_data.json", "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))

BATIM = [
    ("בית א", "כיתות א-ג", [c for c in CLASSES if c[0] in "אבג"]),
    ("בית ב", "כיתות ד-ו", [c for c in CLASSES if c[0] in "דהו"]),
    ("בית ג", "חטיבה ז-ט", list(HCLASSES)),
]

def house_teachers(classes):
    cset = set(classes)
    out = set()
    for t, evs in mv.teachers.items():
        for side, d, h, label in evs:
            cls = label.split(" · ")[0] if side == "חטיבה" else label
            if side in ("יסודי", "חטיבה", 'תל"ן', "מגמות") and cls in cset:
                out.add(t); break
    return sorted(out)

for name, grades, classes in BATIM:
    kind = "jun" if classes and classes[0] in HCLASSES else "elem"
    spec_obj = {
        "title": f"{name} ({grades}) – מערכות שעות",
        "subtitle": "מערכות הכיתות ואחריהן מערכות כל המורים המלמדים בבית. "
                    "◦ = סדירות (לא שעת הוראה). משבצת אדומה = חוסר, מחנך/ת הכיתה נכנס/ת זמנית.",
        "classes": [[kind, c] for c in classes],
        "teachers": house_teachers(classes),
    }
    sp = f"word_spec_{name}.json"
    io.open(sp, "w", encoding="utf-8").write(json.dumps(spec_obj, ensure_ascii=False))
    out = f"מערכות {name}.docx"
    r = subprocess.run(["node", "make_word.js", "word_data.json", out, sp],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    print(r.stdout.strip() or r.stderr.strip())
    if r.returncode != 0: sys.exit("node נכשל - ודאו ש-node מותקן ושהרצתם npm install docx")
