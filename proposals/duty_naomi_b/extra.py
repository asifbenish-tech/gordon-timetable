# סידור חדר אוכל חטיבה - ימים חדשים (במקום duty_days): נעמי רביעי, אסיף שלישי, השאר ללא שינוי
for _c, _d in {"ז נעמי": 3, "ט אסיף": 2, "ז אלי": 1, "ח גלית": 4, "ט תמיר": 0}.items():
    m.Add(duty[(_c, _d)] == 1)
# נעמי שומרת את שלישי ש5 עם כיתתה (גם בלי תורנות)
_v = [v for k, v in hx.items() if k[0] == "ז נעמי" and k[1] == (2, 5) and k[3] == "נעמי"]
m.Add(sum(_v) == 1)
print(f"חדר אוכל: נעמי רביעי, אסיף שלישי; נעמי בשלישי ש5 ({len(_v)} אפשרויות)")
# יום המגמות - רך: כל סטייה מהכלל המקורי עולה ביוקר (נעמי בשלישי ש5 נשמרת למעלה כחובה)
_pen = []
_pen.append(1 - sum(hx[k] for k in hx if k[0] == "ז נעמי" and k[1] == (2, 5) and k[2] == "חינוך"))
_pen.append(1 - sum(hx[k] for k in hx if k[0] == "ז אלי" and k[1] == (2, 5) and k[3] == "אלי"))
_pen.append(hfree[("ח גלית", (2, 5))] + sum(hx[k] for k in hx if k[0] == "ח גלית" and k[1] == (2, 5) and k[3] in ("גלית", "חסר מורה")))
for _c9 in T9:
    _pen.append(1 - sum(hx[k] for k in hx if k[0] == _c9 and k[1] == (4, 5) and k[2] == "חינוך"))
    for _hb in MAG_H["ט"].get("free_after", []): _pen.append(1 - hfree[(_c9, (4, _hb))])
OBJ_H = OBJ_H + 3000 * sum(_pen)
