# אילוצים נוספים להצעת "הילה מדעים" - רץ בתוך המנוע (m, x, hx, hfree, HCLASSES, OBJ_H זמינים)
_h=[k for k in hx if k[3]=="הילה"]
_s0=[hx[k] for k in _h if k[1][0]==0]
if _s0: m.Add(sum(_s0)>=3); m.Add(sum(_s0)<=5)          # ראשון: 3-5 שעות
for _d in range(5):                                       # עד 6 שעות ביום
    _v=[hx[k] for k in _h if k[1][0]==_d]
    if _v: m.Add(sum(_v)<=6)
for _c9 in ("ט תמיר","ט אסיף"):                            # בדיוק 4 מתמטיקה בכל כיתת ט (השאר = שישי עם צבי)
    _v=[hx[k] for k in _h if k[0]==_c9 and k[2]=="מתמטיקה"]
    if _v: m.Add(sum(_v)==4)
for _c in HCLASSES:                                       # שעה שמינית: רק ח גלית בשני, ובקנס
    for _d in range(5):
        if (_c,(_d,8)) in hfree:
            if (_c,_d)==("ח גלית",1): OBJ_H = OBJ_H + 400*hfree[(_c,(_d,8))].Not()
            else: m.Add(hfree[(_c,(_d,8))]==1)
for _k in [k for k in hx if k[0]=="ט אסיף" and k[2]=="מדעים" and k[3]=="חסר מורה"]:
    m.Add(hx[_k]==0)                                      # מדעים בט אסיף = שיעור אמיתי, לא שעת "חסר מורה" של שישי
