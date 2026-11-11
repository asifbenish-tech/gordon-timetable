# היסודי פתוח, אבל בלי חוסרים חדשים: כל משבצת שמאוישת היום נשארת מאוישת (לא בהכרח באותו מורה)
import json as _j, io as _io
_B = _j.load(_io.open("baseline_J.json", encoding="utf-8"))
_bys = {}
for (_c, _s, _t), _v in x.items(): _bys.setdefault((_c, _s), []).append(_v)
_n = 0
_NEWGAP = []
for _c, _row in _B.items():
    for _k, _t in _row.items():
        _s = tuple(map(int, _k.split(",")))
        if _t and (_c, _s) in _bys:   # גם אם המורה המקורי/ת כבר לא זמין/ה - רך: חוסר חדש עולה ביוקר
            _u = m.NewBoolVar(f"nogap_{_c}_{_k}"); m.Add(sum(_bys[(_c, _s)]) + _u >= 1); _NEWGAP.append(_u); _n += 1
print(f"יסודי: {_n} משבצות חייבות להישאר מאוישות")

OBJ_E = OBJ_E + 30000 * sum(_NEWGAP)
print('חוסרים חדשים אפשריים בקנס:', len(_NEWGAP))
