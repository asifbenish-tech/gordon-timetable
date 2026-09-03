# -*- coding: utf-8 -*-
"""outDIFF.py - מציג שינוי מוצע על המערכות עצמן: כל כיתה וכל מורה שהשתנו,
   עם סימון של כל תא שזז (לפני ← אחרי). זה מה שהמנהל רואה לפני אישור.

   שימוש: python outDIFF.py <data_before.json> <data_after.json> [שם הקובץ]
   הקלט הוא ה-DATA של הלוח (כפי שמוטבע ב-viewer.html) בשני המצבים.
   פלט: 'שינויים מוצעים.html' + 'שינויים מוצעים.pdf'
"""
import json, io, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from data2 import DAY_HOURS
from hdata import HDAY

A = json.load(io.open(sys.argv[1], encoding="utf-8"))
B = json.load(io.open(sys.argv[2], encoding="utf-8"))
OUT = sys.argv[3] if len(sys.argv) > 3 else "שינויים מוצעים"
DAYS = B["days"]
esc = lambda z: str(z).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def cell_text(c):
    if not c: return ""
    t = c.get("t", ""); s = c.get("s", ""); co = c.get("co", "")
    return t + (f" · {s}" if s else "") + (f" ({co})" if co else "")

def grid(title, sub, hours, get_before, get_after):
    """טבלה אחת; get_* מחזירים טקסט לתא (d,h). מחזיר (html, מספר תאים שזזו) או None."""
    changed = 0; rows = ""
    for h in range(1, max(hours) + 1):
        tds = ""
        for d in range(6):
            if h > hours[d]: tds += '<td class="off"></td>'; continue
            a, b = get_before(d, h), get_after(d, h)
            if a == b:
                tds += f'<td>{esc(b)}</td>'
            else:
                changed += 1
                tds += (f'<td class="chg"><span class="old">{esc(a) or "—"}</span>'
                        f'<span class="arrow">←</span><span class="new">{esc(b) or "—"}</span></td>')
        rows += f"<tr><th>{h}</th>{tds}</tr>"
    if not changed: return None
    head = "".join(f"<th>{d}</th>" for d in DAYS)
    return (f'<section><h2>{esc(title)} <small>{esc(sub)} · {changed} '
            f'{"תא זז" if changed == 1 else "תאים זזו"}</small></h2>'
            f'<table><thead><tr><th>שעה</th>{head}</tr></thead><tbody>{rows}</tbody></table></section>'), changed

blocks, total = [], 0
# ---- כיתות ----
for side, hours in (("elem", DAY_HOURS), ("jun", HDAY)):
    for cls in B.get(side, {}):
        ca, cb = A.get(side, {}).get(cls, {}).get("cells", {}), B[side][cls].get("cells", {})
        r = grid(cls, "מערכת הכיתה", hours,
                 lambda d, h: cell_text(ca.get(f"{d},{h}")), lambda d, h: cell_text(cb.get(f"{d},{h}")))
        if r: blocks.append(r[0]); total += r[1]
# ---- מורים ----
FN = B.get("full_names", {})
def ev_map(evs):
    m = {}
    for side, d, h, lbl in evs:
        m.setdefault((d, h), []).append(lbl)
    return {k: " + ".join(v) for k, v in m.items()}
for t in sorted(set(A.get("teachers", {})) | set(B.get("teachers", {}))):
    ea, eb = ev_map(A.get("teachers", {}).get(t, [])), ev_map(B.get("teachers", {}).get(t, []))
    if ea == eb: continue
    hrs = [7, 7, 7, 7, 7, 4]
    r = grid(FN.get(t, t), "המערכת האישית", hrs,
             lambda d, h: ea.get((d, h), ""), lambda d, h: eb.get((d, h), ""))
    if r: blocks.append(r[0])

HTML = f"""<!doctype html><html lang="he" dir="rtl"><head><meta charset="utf-8"><style>
@page {{ size: A4 landscape; margin: 10mm 9mm; }}
* {{ box-sizing: border-box; margin: 0; }}
body {{ font: 12px/1.35 'Noto Sans Hebrew','Segoe UI',Arial,sans-serif; direction: rtl; color:#22303D; }}
h1 {{ font-size: 19px; text-align:center; }}
.sub0 {{ text-align:center; color:#6B7A88; font-size:11px; margin:2px 0 6px; }}
.legend {{ text-align:center; font-size:11px; margin-bottom:10px; }}
.legend .chg {{ display:inline-block; padding:2px 8px; border-radius:4px; }}
section {{ page-break-inside: avoid; margin-bottom: 14px; }}
h2 {{ font-size: 14.5px; margin: 0 0 4px; color:#0E6E66; }}
h2 small {{ font-weight:400; color:#6B7A88; font-size:10.5px; }}
table {{ border-collapse:collapse; width:100%; }}
th,td {{ border:1px solid #C9C4B8; padding:3px 4px; text-align:center; font-size:10.5px; height:26px; }}
th {{ background:#EFECE4; font-weight:700; }}
tbody th {{ width:34px; }}
td {{ color:#5A6570; }}
td.off {{ background:#F4F2EC; }}
td.chg {{ background:#FFF3C4; border:2px solid #E0A800; color:#22303D; }}
.old {{ text-decoration: line-through; color:#B3261E; }}
.arrow {{ margin: 0 5px; color:#6B7A88; }}
.new {{ font-weight:700; color:#0E6E66; }}
.foot {{ margin-top:8px; color:#6B7A88; font-size:10px; text-align:center; }}
</style></head><body>
<h1>שינויים מוצעים — טרם אושרו</h1>
<div class="sub0">מול המערכת המפורסמת ({esc(A.get('built',''))}) · {len(blocks)} מערכות מושפעות · {total} תאים בכיתות</div>
<div class="legend"><span class="chg" style="background:#FFF3C4;border:2px solid #E0A800">
<span class="old">לפני</span> <span class="arrow">←</span> <span class="new">אחרי</span></span> &nbsp; תא ללא סימון = ללא שינוי</div>
{''.join(blocks) if blocks else '<p style="text-align:center;color:#6B7A88">אין הבדלים.</p>'}
<div class="foot">המורים ממשיכים לראות את המערכת המפורסמת עד לאישור.</div>
</body></html>"""

io.open(OUT + ".html", "w", encoding="utf-8").write(HTML)
try:
    from playwright.sync_api import sync_playwright
    exe = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
    with sync_playwright() as p:
        br = p.chromium.launch(**({"executable_path": exe} if os.path.exists(exe) else {}))
        pg = br.new_page(); pg.set_content(HTML, wait_until="load")
        pg.pdf(path=OUT + ".pdf", format="A4", landscape=True, print_background=True)
        br.close()
    print(f"{OUT}.pdf נוצר: {len(blocks)} מערכות, {os.path.getsize(OUT + '.pdf')//1024} KB")
except Exception as e:
    print("PDF לא נוצר:", e)
