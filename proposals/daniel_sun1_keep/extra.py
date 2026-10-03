# כל מורה שומר את מספר השעות שלו בכל כיתה כמו במפורסם - רק *מתי* משתנה.
import json as _j, io as _io, collections as _co
_B = _j.load(_io.open("baseline_J.json", encoding="utf-8"))
_cnt = _co.Counter((c, t) for c, row in _B.items() for k, t in row.items()
                   if (c, tuple(map(int, k.split(","))), t) in x)   # רק תאים שהמנוע מחליט עליהם
_vars = _co.defaultdict(list)
for (c, s, t), v in x.items(): _vars[(c, t)].append(v)
for (c, t), vs in _vars.items():
    if t == 'תל"ן' or c not in ("ג דניאל", "ג דליה", "ג לייה", "ו שרית"): continue
    m.Add(sum(vs) == _cnt.get((c, t), 0))
print(f"שימור שעות מורה-כיתה: {len(_vars)} זוגות")
