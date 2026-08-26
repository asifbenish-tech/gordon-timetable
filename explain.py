# -*- coding: utf-8 -*-
"""explain.py — מזריק assumptions לכל בלוק אילוצים ב-solveALL ומדפיס את הליבה הסותרת."""
import io, re, sys, subprocess
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

src = io.open("solveALL.py", encoding="utf-8").read()

wrapper = '''
_SECT = {"cur": "init"}
_LITS = {}
_ORIG_ADD = m.Add
def _add2(ct):
    c = _ORIG_ADD(ct)
    lit = _LITS.get(_SECT["cur"])
    if lit is None:
        lit = m.NewBoolVar("assume_%d" % len(_LITS))
        _LITS[_SECT["cur"]] = lit
    try:
        c.OnlyEnforceIf(lit)
    except Exception:
        pass
    return c
m.Add = _add2
'''

i = src.index("m=cp_model.CpModel()")
j = i + len("m=cp_model.CpModel()")
src = src[:j] + wrapper + src[j:]

# תווית לכל כותרת בלוק
out = []
for ln in src.split("\n"):
    out.append(ln)
    if ln.startswith("# ") and len(ln) > 4:
        label = ln[2:48].replace('"', "'").replace("\\", "")
        out.append('_SECT["cur"] = "%s"' % label)
src = "\n".join(out)

# פתרון עם assumptions + ליבה
a = "st=sol.Solve(m)"
assert a in src
src = src.replace(a, '''m.ClearAssumptions()
m.AddAssumptions(list(_LITS.values()))
st=sol.Solve(m)
if sol.StatusName(st)=="INFEASIBLE":
    _idx=set(sol.SufficientAssumptionsForInfeasibility())
    _names=[k for k,v in _LITS.items() if v.Index() in _idx]
    import io as _io
    _io.open("core.txt","w",encoding="utf-8").write("\\n".join(_names))
    print("CORE:", len(_names), "blocks")
''', 1)

io.open("solveEXP.py", "w", encoding="utf-8").write(src)
print("explain built")
