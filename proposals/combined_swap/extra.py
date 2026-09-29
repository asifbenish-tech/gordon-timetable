# החלפה ישירה דליה <-> דניאל (בקשת המנהל 29.09): בשתי שעות שבהן שניהם עם הכיתה שלהם,
# דליה עוברת לג דניאל ודניאל לג דליה, באותה שעה. שום מורה אחר לא זז - כל שאר היסודי קפוא.
import json as _j, io as _io
_B = _j.load(_io.open("baseline_J.json", encoding="utf-8"))
_A, _N = "ג דליה", "ג דניאל"
_EXCL = {(1, 1), (2, 6)}          # תל"ן חצי-כיתה עם דליה (שני ש1 גם חווה)
_cand = [s for s in NONFRI if s not in _EXCL
         and _B[_A].get(f"{s[0]},{s[1]}") == "דליה" and _B[_N].get(f"{s[0]},{s[1]}") == "דניאל"]
_sw = []
for s in _cand:
    b = m.NewBoolVar(f"swapDD_{s}"); _sw.append(b)
    for c, t_home, t_other in ((_A, "דליה", "דניאל"), (_N, "דניאל", "דליה")):
        if (c, s, t_other) in x: m.Add(x[(c, s, t_other)] == b)
        else: m.Add(b == 0)
        if (c, s, t_home) in x: m.Add(x[(c, s, t_home)] == 1 - b)
m.Add(sum(_sw) == 2)
_AT = [(1, 5), (2, 1)]            # השעות שנבחרו: שני ש5 ושלישי ש1 (זהה בכל ההצעות)
for s, b in zip(_cand, _sw): m.Add(b == (1 if s in _AT else 0))
# כל שאר היסודי קפוא על המפורסם (כל כיתה, כל שעה) - חוץ מהמשבצות שמוחלפות
_cs = {(_A, s) for s in _cand} | {(_N, s) for s in _cand}
_nf = 0
for k, v in x.items():
    c, s, t = k
    if (c, s) in _cs: continue
    if _B.get(c, {}).get(f"{s[0]},{s[1]}") == t: m.Add(v == 1); _nf += 1
print(f"החלפה דליה/דניאל: {len(_cand)} שעות אפשריות, 2 נבחרות; {_nf} תאים קפואים")
