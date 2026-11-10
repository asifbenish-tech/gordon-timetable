# -*- coding: utf-8 -*-
"""jun_excel.py - אקסל חטיבה בלבד להצעה: גיליון שינויים + כיתות החטיבה + מערכות מורי החטיבה.
   נבנה מנתוני הלוח (viewer.html) של ההצעה ושל המפורסם - אותו מקור שהלוח מציג, ולכן
   תמיד תואם אותו. השינויים מחושבים ישירות מול הלוח המפורסם.
   שימוש: python jun_excel.py <viewer הצעה> <viewer מפורסם> <פלט.xlsx> <כותרת>"""
import io, json, re, sys, collections
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

PV, BV, OUT, TITLE = sys.argv[1:5]
load = lambda p: json.loads(re.search(r"^const DATA=(\{.*\});?$", io.open(p, encoding="utf-8").read(), re.M).group(1))
D, B = load(PV), load(BV)
DN = D["days"]
F = lambda **k: Font(name="Arial", **k)
fill = lambda c: PatternFill("solid", fgColor=c)
TH = Side(style="thin", color="A6A6A6")
BO = Border(left=TH, right=TH, top=TH, bottom=TH)
_ds = Side(style="mediumDashed", color="C55A11")
DUTYF = Border(left=_ds, right=_ds, top=_ds, bottom=_ds)
DUTY_TXT = "★ סידור חדר אוכל"
CEN = Alignment(horizontal="center", vertical="center", wrap_text=True)
RIGHT = Alignment(horizontal="right", vertical="center", wrap_text=True)
HDR, OFF, HOME, MAG, PE, FRI = fill("DDEBF7"), fill("F2F2F2"), fill("E2EFDA"), fill("EDE4F5"), fill("FFF2CC"), fill("FCE4D6")
CHG, HOLE, SED = fill("FFEB3B"), fill("FF9999"), fill("FFF2A8")
TEACH = ("חטיבה", "יסודי", "מגמות")
skey = lambda kk: tuple(map(int, kk.split(",")))


def ctext(v):
    if not v or v.get("k") == "off": return ""
    t, s = v.get("t") or "", v.get("s") or ""
    if v.get("k") == "mag" and t == "מגמות": return "מגמות – " + s.replace(" · ", " / ")
    return f"{t} – {s}" if t and s else (t or s)


def setc(ws, r, c, val, font=None, f=None, al=CEN):
    cell = ws.cell(row=r, column=c, value=val)
    cell.font = font or F(size=10); cell.alignment = al; cell.border = BO
    if f: cell.fill = f
    return cell


def grid_header(ws, r):
    setc(ws, r, 1, "שעה", F(bold=True), HDR)
    for d in range(6): setc(ws, r, 2 + d, DN[d], F(bold=True), HDR)


def tl(DD, t, d, h):
    return " / ".join(sorted(e[3] for e in DD["teachers"].get(t, []) if e[1] == d and e[2] == h and e[0] in TEACH))


# ---- שינויים מול המפורסם ----
DIFF, TDIFF = {}, {}
for c in D["jun"]:
    for k in sorted(set(D["jun"][c]["cells"]) | set(B["jun"][c]["cells"]), key=skey):
        a, b = ctext(B["jun"][c]["cells"].get(k)), ctext(D["jun"][c]["cells"].get(k))
        if a != b: DIFF.setdefault(c, {})[k] = {"was": a or "—"}
for t in sorted(set(D["teachers"]) | set(B["teachers"])):
    for d in range(6):
        for h in range(1, 9):
            a, b = tl(B, t, d, h), tl(D, t, d, h)
            if a != b: TDIFF.setdefault(t, {})[f"{d},{h}"] = {"was": a or "—"}
ELEM_CHG = sum(1 for c in D["elem"] for k in set(D["elem"][c]["cells"]) | set(B["elem"][c]["cells"])
               if (D["elem"][c]["cells"].get(k) or {}).get("t") != (B["elem"][c]["cells"].get(k) or {}).get("t"))
DUTY = {c: (D["jun"][c].get("duty"), B["jun"][c].get("duty")) for c in D["jun"]}
tch = sorted(TDIFF)

wb = Workbook(); wb.remove(wb.active)

# ---------- גיליון שינויים ----------
ws = wb.create_sheet("שינויים"); ws.sheet_view.rightToLeft = True
ws["A1"] = TITLE; ws["A1"].font = F(bold=True, size=14)
ws["A2"] = ("הצעה - לא מפורסם. השינוי נוגע לחטיבה בלבד" + ("; ביסודי אין שינוי" if not ELEM_CHG else f"; ביסודי {ELEM_CHG} תאים") +
            ". תאים שהשתנו מסומנים בצהוב בכל הגיליונות, עם מה שהיה קודם. סידור חדר האוכל מסומן ★ ובמסגרת כתומה.")
ws["A2"].font = F(size=10, italic=True)
r = 4
ws.cell(row=r, column=1, value="שינויים במערכות הכיתות").font = F(bold=True, size=12); r += 1
for i, h in enumerate(["כיתה", "יום", "שעה", "היה", "נהיה"]): setc(ws, r, 1 + i, h, F(bold=True), HDR)
r += 1
nch = 0
for c in D["jun"]:
    for k, dv in DIFF.get(c, {}).items():
        d, h = skey(k)
        now = ctext(D["jun"][c]["cells"].get(k)) or "—"
        for i, v in enumerate([c, DN[d], h, dv["was"], now]): setc(ws, r, 1 + i, v, al=RIGHT if i > 2 else CEN)
        ws.cell(row=r, column=5).fill = CHG; r += 1; nch += 1
r += 1
ws.cell(row=r, column=1, value="שינויים במערכות המורים").font = F(bold=True, size=12); r += 1
for i, h in enumerate(["מורה", "יום", "שעה", "היה", "נהיה"]): setc(ws, r, 1 + i, h, F(bold=True), HDR)
r += 1
for t in tch:
    for k in sorted(TDIFF[t], key=skey):
        d, h = skey(k)
        for i, v in enumerate([t, DN[d], h, tl(B, t, d, h) or "—", tl(D, t, d, h) or "—"]): setc(ws, r, 1 + i, v, al=RIGHT if i > 2 else CEN)
        ws.cell(row=r, column=5).fill = CHG; r += 1
r += 1
ws.cell(row=r, column=1, value="שעות לפי יום (מורים שהשתנו)").font = F(bold=True, size=12); r += 1
for i, h in enumerate(["מורה", ""] + DN + ["סה\"כ"]): setc(ws, r, 1 + i, h, F(bold=True), HDR)
r += 1


def perday(DD, t):
    cnt = [0] * 6
    for side, d, h, lbl in DD["teachers"].get(t, []):
        if side in TEACH: cnt[d] += 1
    return cnt


for t in tch:
    for tag, DD in (("לפני", B), ("אחרי", D)):
        p = perday(DD, t)
        for i, v in enumerate([t, tag] + p + [sum(p)]): setc(ws, r, 1 + i, v)
        if tag == "אחרי":
            q = perday(B, t)
            for d in range(6):
                if p[d] != q[d]: ws.cell(row=r, column=3 + d).fill = CHG
        r += 1
r += 1
e8 = lambda DD: [f"{c} {DN[int(k.split(',')[0])]}" for c, i in DD["jun"].items() for k, v in i["cells"].items() if k.endswith(",8") and (v or {}).get("s")]
ws.cell(row=r, column=1, value=f"שעה שמינית - לפני: {', '.join(e8(B)) or 'אין'} | אחרי: {', '.join(e8(D)) or 'אין'}").font = F(size=10, bold=True)
r += 2
ws.cell(row=r, column=1, value="סידור חדר אוכל - חטיבה (שעה 5, עם מחנך/ת הכיתה)").font = F(bold=True, size=12); r += 1
for i, h in enumerate(["כיתה", "יום", "שעה", "עם", "הערה"]): setc(ws, r, 1 + i, h, F(bold=True), HDR)
r += 1
for c in sorted(D["jun"], key=lambda cc: DN.index(DUTY[cc][0]) if DUTY[cc][0] in DN else 9):
    now, was = DUTY[c]
    who = (D["jun"][c]["cells"].get(f"{DN.index(now)},5") or {}).get("s", "") if now in DN else ""
    note = "" if now == was else f"שונה (היה: יום {was})"
    for i, v in enumerate([c, now or "—", 5, who, note]): setc(ws, r, 1 + i, v, al=RIGHT if i > 2 else CEN)
    if note:
        for i in (2, 5): ws.cell(row=r, column=i).fill = CHG
    r += 1
for col, w in zip("ABCDEFGHI", [12, 9, 7, 30, 30, 9, 9, 9, 9]): ws.column_dimensions[col].width = w

# ---------- כיתות החטיבה ----------
for c, info in D["jun"].items():
    ws = wb.create_sheet(c); ws.sheet_view.rightToLeft = True
    home = info.get("home") or ""
    ws["A1"] = f"{c}   (מחנך/ת: {home})" + (f"   ·   סידור חדר אוכל: {info['duty']}" if info.get("duty") else "")
    ws["A1"].font = F(bold=True, size=13); ws.merge_cells("A1:G1"); ws["A1"].alignment = CEN
    grid_header(ws, 2)
    dif = DIFF.get(c, {})
    dkey = f"{DN.index(info['duty'])},5" if info.get("duty") in DN else None
    for h in range(1, 9):
        setc(ws, 2 + h, 1, h, F(bold=True), HDR)
        for d in range(6):
            k = f"{d},{h}"; v = info["cells"].get(k)
            txt = ctext(v)
            if v is None or (v or {}).get("k") == "off": f = OFF
            elif v.get("k") == "hole" or (v.get("s") or "") == "חסר מורה": f = HOLE
            elif v.get("k") == "mag": f = MAG
            elif v.get("k") == "pe" or v.get("t") == "חינוך גופני": f = PE
            elif v.get("s") == home: f = HOME
            elif d == 5: f = FRI
            else: f = None
            if k == dkey: txt = (txt + "\n" if txt else "") + DUTY_TXT
            if k in dif:
                txt = (txt or "—") + f"\n(היה: {dif[k]['was']})"; f = CHG
            cell = setc(ws, 2 + h, 2 + d, txt, F(size=10, bold=k in dif or k == dkey), f)
            if k == dkey: cell.border = DUTYF
    ws.column_dimensions["A"].width = 7
    for col in "BCDEFG": ws.column_dimensions[col].width = 24
    for h in range(3, 11): ws.row_dimensions[h].height = 42
    ws.cell(row=12, column=1, value="מקרא: ירוק = מחנך/ת · סגול = מגמות · צהוב בהיר = חנ\"ג שכבתי · צהוב חזק = שינוי בהצעה · אפור = אין לימודים · ★ במסגרת כתומה = סידור חדר אוכל").font = F(size=9, italic=True)

# ---------- מורי החטיבה ----------
ws = wb.create_sheet("מורי החטיבה"); ws.sheet_view.rightToLeft = True
ws["A1"] = "מערכות מורי החטיבה (כל מי שמלמד/ת בחטיבה; המערכת המלאה, כולל יסודי)"; ws["A1"].font = F(bold=True, size=13)
teachers = sorted(t for t, ev in D["teachers"].items() if any(e[0] == "חטיבה" for e in ev))
teachers = [t for t in tch if t in teachers] + [t for t in teachers if t not in tch]   # מי שהשתנה - ראשון
util = {u["t"]: u for u in D["util"]}
order = list(D["elem"]) + list(D["jun"])
r = 3
for t in teachers:
    ev = D["teachers"][t]; td = TDIFF.get(t, {})
    tduty = {f"{DN.index(i['duty'])},5" for c2, i in D["jun"].items() if i.get("home") == t and i.get("duty") in DN
             and (i["cells"].get(f"{DN.index(i['duty'])},5") or {}).get("s") == t}
    u = util.get(t)
    full = (D.get("full_names") or {}).get(t)
    setc(ws, r, 1, t + (f" ({full})" if full and full != t else ""), F(bold=True, size=12, color="FFFFFF"), fill("305496"), RIGHT)
    ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=3)
    info = (f"משובץ/ת {u['tot']} מתוך {u['q']} שעות" if u else "") + ("   ·   השתנה בהצעה" if td else "")
    setc(ws, r, 4, info, F(bold=bool(td), size=10), CHG if td else None, RIGHT)
    ws.merge_cells(start_row=r, start_column=4, end_row=r, end_column=7)
    r += 1; grid_header(ws, r); r += 1
    by = collections.defaultdict(list)
    for side, d, h, lbl in ev: by[(d, h)].append((side, lbl))
    for h in range(1, 9):
        setc(ws, r, 1, h, F(bold=True), HDR)
        for d in range(6):
            items = by.get((d, h), [])
            txt = " / ".join(("◦ " if s == "סדירות" else "") + l + (" (יסודי)" if s == "יסודי" else "") for s, l in items)
            f = SED if items and all(s == "סדירות" for s, _ in items) else (MAG if any(s == "מגמות" for s, _ in items) else None)
            k = f"{d},{h}"
            if k in tduty: txt = (txt + "\n" if txt else "") + DUTY_TXT
            if k in td:
                txt = (txt or "—") + f"\n(היה: {td[k]['was']})"; f = CHG
            cell = setc(ws, r, 2 + d, txt, F(size=9, bold=k in td or k in tduty), f)
            if k in tduty: cell.border = DUTYF
        r += 1
    cnt = collections.Counter(); subj = collections.defaultdict(collections.Counter)
    for side, d, h, lbl in ev:
        if side not in ("חטיבה", "יסודי"): continue
        cl = lbl.split(" · ")[0]; cnt[cl] += 1
        if " · " in lbl: subj[cl][lbl.split(" · ")[1].split(" (")[0]] += 1
    parts = [f"{cl}: {n}" + (" (" + ", ".join(f"{s} {m}" for s, m in subj[cl].items()) + ")" if subj[cl] else "")
             for cl, n in sorted(cnt.items(), key=lambda kv: order.index(kv[0]) if kv[0] in order else 99)]
    setc(ws, r, 1, "שעות לפי כיתה:", F(bold=True, size=9), None, RIGHT)
    setc(ws, r, 2, "   ·   ".join(parts), F(size=9), None, RIGHT)
    ws.merge_cells(start_row=r, start_column=2, end_row=r, end_column=7)
    ws.row_dimensions[r].height = 30
    r += 2
ws.column_dimensions["A"].width = 14
for col in "BCDEFG": ws.column_dimensions[col].width = 28

wb.save(OUT)
print(f"נשמר: {OUT} | שינויים בכיתות: {nch} | יסודי: {ELEM_CHG} | מורים: {len(teachers)} ({', '.join(teachers)})")
