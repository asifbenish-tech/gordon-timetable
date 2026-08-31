# -*- coding: utf-8 -*-
"""outCURRICULUM.py - מפיק 'תוכניות לימודים.pdf': טבלת השעות לכל שכבה,
   בדיוק כפי שהיא רשומה באתר הניהול (app_data/..._curriculum.json).
   הנתונים מוצגים כמות שהם; הסקריפט רק מסדר אותם לטבלה ומסמן פערים
   מול מספר השעות שיש בפועל במערכת.
   הרצה: python outCURRICULUM.py
"""
import json, io, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from data2 import DAY_HOURS
from hdata import HDAY

YEAR = "2026-2027"
CUR = json.load(io.open(f"app_data/v10_{YEAR}_curriculum.json", encoding="utf-8"))["value"]
WK, HWK = sum(DAY_HOURS), sum(HDAY)

HOUSES = [("בית א", ["א", "ב", "ג"], WK, "בית א'"),
          ("בית ב", ["ד", "ה", "ו"], WK, "בית ב'"),
          ("בית ג", ["ז", "ח", "ט"], HWK, "בית ג'")]

def short(name, suffix):
    """מקצר את שם המקצוע לתצוגה: השיוך לבית כבר מופיע בכותרת הטבלה."""
    n = (name or "").strip()
    for s in (suffix, suffix.rstrip("'"), "שכבת ג'"):
        if n.endswith(" " + s): return n[: -len(s) - 1].strip()
    return n or "(שם ריק)"

esc = lambda z: str(z).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
blocks, notes = [], []

for title, grades, target, suffix in HOUSES:
    rows, order = {}, []
    for g in grades:
        for it in CUR.get(g, []):
            k = short(it.get("s"), suffix)
            if k not in rows: rows[k] = {}; order.append(k)
            rows[k][g] = it.get("h", 0)
    # מיון: לפי סך השעות בשכבות הבית, מהגבוה לנמוך
    order.sort(key=lambda k: -sum(rows[k].get(g, 0) for g in grades))
    body = ""
    for k in order:
        cells = ""
        for g in grades:
            v = rows[k].get(g)
            if v is None:   cells += '<td class="na">—</td>'
            elif v == 0:    cells += '<td class="zero">0</td>'
            else:           cells += f"<td>{v}</td>"
        body += f'<tr><td class="sub">{esc(k)}</td>{cells}</tr>'
    tot = "".join(
        f'<td class="{"ok" if sum(rows[k].get(g,0) for k in order)==target else "bad"}">'
        f'{sum(rows[k].get(g,0) for k in order)}</td>' for g in grades)
    heads = "".join(f"<th>{g}׳</th>" for g in grades)
    blocks.append(
        f'<h2>{esc(title)} <small>— {target} שעות שבועיות במערכת</small></h2>'
        f'<table><thead><tr><th class="sub">מקצוע</th>{heads}</tr></thead>'
        f'<tbody>{body}</tbody>'
        f'<tfoot><tr><td class="sub">סה״כ</td>{tot}</tr></tfoot></table>')
    for g in grades:
        s = sum(rows[k].get(g, 0) for k in order)
        if s != target:
            notes.append(f"שכבה {g}׳: {s} שעות בתוכנית מול {target} במערכת "
                         f"({'עודף ' + str(s-target) if s > target else 'חסרות ' + str(target-s)}).")
blank = [g for g in CUR for it in CUR[g] if not (it.get("s") or "").strip()]
if blank: notes.append("בשכבה " + "׳, ".join(blank) + "׳ יש שורה ללא שם מקצוע — כנראה רשומה שנוצרה בטעות באתר.")
zeros = sorted({short(it.get("s"), "") for g in CUR for it in CUR[g] if not it.get("h")})
if zeros: notes.append("מקצועות הרשומים עם 0 שעות: " + " · ".join(z for z in zeros if z != "(שם ריק)") + ".")

HTML = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>
@page {{ size: A4; margin: 14mm 12mm; }}
* {{ box-sizing: border-box; margin: 0; }}
body {{ font: 13px/1.45 'Noto Sans Hebrew','Segoe UI',Arial,sans-serif; direction: rtl; color:#22303D; }}
h1 {{ font-size: 21px; text-align:center; }}
.sub0 {{ text-align:center; color:#6B7A88; font-size:11.5px; margin:2px 0 14px; }}
h2 {{ font-size: 15px; margin: 14px 0 6px; color:#0E6E66; }}
h2 small {{ font-weight:400; color:#6B7A88; font-size:11px; }}
table {{ border-collapse:collapse; width:100%; page-break-inside:avoid; margin-bottom:4px; }}
th,td {{ border:1px solid #C9C4B8; padding:3.5px 6px; text-align:center; font-size:12px; }}
th {{ background:#0E6E66; color:#fff; }}
td.sub, th.sub {{ text-align:right; width:42%; }}
tbody tr:nth-child(even) td {{ background:#FAF9F6; }}
td.na {{ color:#B9B3A6; }}
td.zero {{ color:#B3261E; font-weight:700; }}
tfoot td {{ background:#EFECE4; font-weight:700; }}
tfoot td.ok {{ color:#0E6E66; }}
tfoot td.bad {{ color:#B3261E; }}
.notes {{ border:1px solid #EAD3A2; background:#FBEFD8; border-radius:6px;
          padding:8px 12px; margin-top:14px; font-size:11.5px; page-break-inside:avoid; }}
.notes b {{ display:block; margin-bottom:4px; }}
.notes li {{ margin:2px 0; }}
.foot {{ margin-top:10px; color:#6B7A88; font-size:10.5px; text-align:center; }}
</style></head><body>
<h1>תוכניות לימודים — בית חינוך ע״ש א.ד גורדון</h1>
<div class="sub0">שנת {esc(YEAR)} · שעות שבועיות לכל שכבה, כפי שרשום באתר הניהול</div>
{''.join(blocks)}
<div class="notes"><b>לתשומת לב</b><ul>{''.join('<li>'+esc(n)+'</li>' for n in notes)}</ul></div>
<div class="foot">— אין נתון · <span style="color:#B3261E">0</span> = רשום בתוכנית עם אפס שעות ·
שם המקצוע מוצג בלי השיוך לבית, שכבר מופיע בכותרת הטבלה</div>
</body></html>"""

io.open("תוכניות לימודים.html", "w", encoding="utf-8").write(HTML)
try:
    from playwright.sync_api import sync_playwright
    exe = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
    with sync_playwright() as p:
        br = p.chromium.launch(**({"executable_path": exe} if os.path.exists(exe) else {}))
        pg = br.new_page(); pg.set_content(HTML, wait_until="load")
        pg.pdf(path="תוכניות לימודים.pdf", format="A4", print_background=True)
        br.close()
    print(f"תוכניות לימודים.pdf נוצר, {os.path.getsize('תוכניות לימודים.pdf')//1024} KB")
except Exception as e:
    print("PDF לא נוצר:", e)
