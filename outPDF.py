# -*- coding: utf-8 -*-
"""outPDF.py - מפיק את מסמכי המערכות כ-PDF (עברית, RTL, צבעים כמו בלוח):
     מערכות שעות מורים.pdf                - כל המורים + מערכת הכיתה אצל מחנכים
     מערכות בית א/ב/ג.pdf                 - כיתות הבית + מורי הבית
   דורש: pip install playwright  (משתמש בכרום; בענן הדפדפן כבר מותקן)
   שימוש: python outPDF.py [all|batim|teachers]"""
import json, io, os, sys, importlib.util
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

spec = importlib.util.spec_from_file_location("mv", "make_viewer.py")
mv = importlib.util.module_from_spec(spec); spec.loader.exec_module(mv)
from data2 import DAY_NAMES, DAY_HOURS, HOMEROOM, CLASSES
from hdata import HHOME, HDAY, HCLASSES

try: FULL = {k: v for k, v in json.load(io.open("names_map.json", encoding="utf-8")).items() if v}
except Exception: FULL = {}
fn = lambda t: FULL.get(t, t)
home_of = {}
for c, t in HOMEROOM.items(): home_of.setdefault(t, []).append(("elem", c))
for c, t in HHOME.items():    home_of.setdefault(t, []).append(("jun", c))

CSS = """
@page { size: A4; margin: 12mm 10mm; }
* { box-sizing: border-box; margin: 0; }
body { font: 13px/1.4 'Noto Sans Hebrew','Segoe UI',Arial,sans-serif; direction: rtl; color: #22303D; }
h1 { font-size: 24px; text-align: center; margin: 4px 0 2px; }
.sub { text-align: center; color: #6B7A88; font-size: 11px; margin-bottom: 10px; }
h2 { font-size: 17px; margin: 8px 0 6px; }
h3 { font-size: 15px; text-align: center; color: #0E6E66; margin: 6px 0 10px; }
table { border-collapse: collapse; width: 100%; page-break-inside: avoid; }
th, td { border: 1px solid #C9C4B8; padding: 4px 3px; text-align: center; font-size: 11.5px; }
th { background: #EFECE4; }
td .s { display: block; color: #6B7A88; font-size: 9.5px; }
td .co { display: block; color: #0E6E66; font-size: 9.5px; font-weight: 700; }
td .aw { display: block; color: #8A6D3B; font-size: 9px; font-style: italic; }
.k-home { background: #E3EEF7; } .k-tln { background: #E4F0DF; }
.k-mag { background: #E7E6F4; } .k-pe { background: #FBEFD8; }
.k-fill { background: #D7EEF2; font-weight: 700; }
.k-hole { background: #FBE4E1; color: #990000; font-weight: 700; }
.k-off { background: #F4F2EC; }
.sed { background: #F6F4EE; color: #6B7A88; font-style: italic; }
.pagebreak { page-break-before: always; }
.legend { font-size: 10px; color: #6B7A88; text-align: center; margin: 6px 0 12px; }
"""

def class_table(kind, c):
    info = (mv.elem if kind == "elem" else mv.jun)[c]
    hours = DAY_HOURS if kind == "elem" else HDAY
    H = max(hours)
    rows = ["<tr><th>שעה</th>" + "".join(f"<th>{d}</th>" for d in DAY_NAMES) + "</tr>"]
    for h in range(1, H + 1):
        tds = [f"<th>{h}</th>"]
        for d in range(6):
            if h > hours[d]: tds.append('<td class="k-off"></td>'); continue
            cc = info["cells"].get(f"{d},{h}", {"t": ""})
            cls = f' class="k-{cc["k"]}"' if cc.get("k") else ""
            inner = cc.get("t", "")
            if cc.get("s"): inner += f'<span class="s">{cc["s"]}</span>'
            if cc.get("co"): inner += f'<span class="co">{cc["co"]}</span>'
            if cc.get("away"): inner += f'<span class="aw">({cc["away"]})</span>'
            tds.append(f"<td{cls}>{inner}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return "<table>" + "".join(rows) + "</table>"

def teacher_table(t):
    ev = mv.teachers.get(t, [])
    per, sed_only = {}, {}
    for side, d, h, label in ev:
        key = (d, h)
        txt = ("◦ " + label) if side == "סדירות" else label + ("" if side in ("יסודי", "חטיבה") else f" ({side})")
        sed_only[key] = sed_only.get(key, True) and side == "סדירות"
        per[key] = (per[key] + " · " + txt) if key in per else txt
    rows = ["<tr><th>שעה</th>" + "".join(f"<th>{d}</th>" for d in DAY_NAMES) + "</tr>"]
    for h in range(1, 8):
        tds = [f"<th>{h}</th>"]
        for d in range(6):
            v = per.get((d, h), "")
            cls = ' class="sed"' if v and sed_only.get((d, h)) else ""
            tds.append(f"<td{cls}>{v}</td>")
        rows.append("<tr>" + "".join(tds) + "</tr>")
    return "<table>" + "".join(rows) + "</table>"

LEGEND = ('כחול=מחנך/ת · ירוק=תל"ן · סגול=מגמות/מרוכז · צהוב=ספורט שכבתי · '
          'תכלת=מילוי · אדום=חוסר (מחנך/ת נכנס/ת זמנית) · ◦=סדירות (לא שעת הוראה)')

def doc_teachers():
    parts = [f"<h1>מערכות שעות מורים – בית חינוך ע\"ש א.ד גורדון</h1>",
             f'<div class="legend">{LEGEND}</div>']
    for i, t in enumerate(sorted(mv.teachers, key=lambda z: z)):
        homes = home_of.get(t, [])
        note = " — מחנך/ת " + ", ".join(c for _, c in homes) if homes else ""
        parts.append(f'<div{" class=pagebreak" if i else ""}><h2>{fn(t)}{note}</h2>{teacher_table(t)}')
        for kind, c in homes:
            parts.append(f"<h2 style='margin-top:14px'>מערכת כיתה {c}</h2>{class_table(kind, c)}")
        parts.append("</div>")
    return "".join(parts)

def doc_house(name, grades, classes):
    kind = "jun" if classes and classes[0] in HCLASSES else "elem"
    cset = set(classes)
    tset = set()
    for t, evs in mv.teachers.items():
        for side, d, h, label in evs:
            cls = label.split(" · ")[0] if side == "חטיבה" else label
            if side in ("יסודי", "חטיבה", 'תל"ן') and cls in cset: tset.add(t); break
    parts = [f"<h1>{name} ({grades}) – מערכות שעות</h1>",
             f'<div class="legend">{LEGEND}</div>', "<h3>מערכות הכיתות</h3>"]
    for i, c in enumerate(classes):
        info = (mv.elem if kind == "elem" else mv.jun)[c]
        parts.append(f'<div{" class=pagebreak" if i else ""}><h2>כיתה {c}   (מחנך/ת: {fn(info["home"])})</h2>{class_table(kind, c)}</div>')
    parts.append('<div class="pagebreak"><h3>מערכות המורים</h3></div>')
    for i, t in enumerate(sorted(tset)):
        homes = home_of.get(t, [])
        note = " — מחנך/ת " + ", ".join(c for _, c in homes) if homes else ""
        parts.append(f'<div{" class=pagebreak" if i else ""}><h2>{fn(t)}{note}</h2>{teacher_table(t)}</div>')
    return "".join(parts)

DOCS = {"מערכות שעות מורים": doc_teachers()}
for name, grades, classes in [("מערכות בית א", "כיתות א-ג", [c for c in CLASSES if c[0] in "אבג"]),
                              ("מערכות בית ב", "כיתות ד-ו", [c for c in CLASSES if c[0] in "דהו"]),
                              ("מערכות בית ג", "חטיבה ז-ט", list(HCLASSES))]:
    DOCS[name] = doc_house(name.replace("מערכות ", ""), grades, classes)

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright לא מותקן - מדלג על PDF (pip install playwright)"); sys.exit(0)
exe = "/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None
with sync_playwright() as p:
    kw = {"executable_path": exe} if exe else {}
    browser = p.chromium.launch(**kw)
    page = browser.new_page()
    for name, body in DOCS.items():
        page.set_content(f"<!doctype html><html lang='he' dir='rtl'><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>", wait_until="load")
        page.pdf(path=f"{name}.pdf", format="A4", print_background=True)
        print(f"{name}.pdf נוצר, {os.path.getsize(name + '.pdf')//1024} KB")
    browser.close()
