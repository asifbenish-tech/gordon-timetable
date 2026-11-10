# אין שעה שמינית באף כיתה (גם לא בח בשני) - מורה לא מלמד 8 שעות רצוף (חוזר מנכ"ל)
for k in hfree:
    if k[1][1] == 8 and k[1][0] < 5: m.Add(hfree[k] == 1)

# כיתות ז: בשלישי לא אחרי ש6
for _c in ("ז אלי", "ז נעמי"):
    for _h in (7, 8):
        if (_c, (2, _h)) in hfree: m.Add(hfree[(_c, (2, _h))] == 1)
# היסודי פתוח, אבל בלי חוסרים חדשים: כל משבצת שמאוישת היום נשארת מאוישת (לא בהכרח באותו מורה)
import json as _j, io as _io
_B = _j.load(_io.open("baseline_J.json", encoding="utf-8"))
_bys = {}
for (_c, _s, _t), _v in x.items(): _bys.setdefault((_c, _s), []).append(_v)
_n = 0
for _c, _row in _B.items():
    for _k, _t in _row.items():
        _s = tuple(map(int, _k.split(",")))
        if _t and (_c, _s, _t) in x: m.Add(sum(_bys[(_c, _s)]) >= 1); _n += 1
print(f"יסודי: {_n} משבצות חייבות להישאר מאוישות")
