# -*- coding: utf-8 -*-
"""outWORD.py - מפיק מסמך וורד: מערכות כל המורים + מערכת הכיתה אצל המחנכים.
   שימוש: python outWORD.py   (דורש node + חבילת docx: npm install docx)"""
import json, io, subprocess, sys, importlib.util
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

spec = importlib.util.spec_from_file_location("mv", "make_viewer.py")
mv = importlib.util.module_from_spec(spec); spec.loader.exec_module(mv)
from data2 import DAY_NAMES, DAY_HOURS, HOMEROOM
from hdata import HHOME, HDAY

home_of = {}
for c, t in HOMEROOM.items(): home_of.setdefault(t, []).append(("elem", c))
for c, t in HHOME.items():    home_of.setdefault(t, []).append(("jun", c))
out = {
    "days": DAY_NAMES,
    "day_hours_elem": DAY_HOURS, "day_hours_jun": HDAY,
    "teachers": mv.teachers,
    "elem": {c: {"cells": v["cells"], "home": v["home"]} for c, v in mv.elem.items()},
    "jun":  {c: {"cells": v["cells"], "home": v["home"]} for c, v in mv.jun.items()},
    "home_of": home_of,
}
io.open("word_data.json", "w", encoding="utf-8").write(json.dumps(out, ensure_ascii=False))
r = subprocess.run(["node", "make_word.js", "word_data.json", "מערכות שעות מורים.docx"],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
print(r.stdout or r.stderr)
if r.returncode != 0: sys.exit("node נכשל - ודאו ש-node מותקן ושהרצתם npm install docx")
