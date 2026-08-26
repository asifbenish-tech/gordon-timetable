# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from data import *

DIDX = {n:i for i,n in enumerate(DAY_NAMES)}
NONFRI = [(d,h) for (d,h) in SLOTS if d != 5]
FRI    = [(d,h) for (d,h) in SLOTS if d == 5]

def blocked(t):
    b = set()
    for dn in DAYS_OFF.get(t,[]):
        for h in range(1,9): b.add((DIDX[dn],h))
    for s in UNAVAIL.get(t,[]): b.add(s)
    for s in EVENTS.get(t,[]):  b.add(s)
    return b

BLOCK = {t:blocked(t) for t in QUOTA}
# תל"ן availability = intersection of its pair, per class
def tln_block(c):
    b=set()
    for sub in TLN_PAIR[c]:
        for dn in TLN_OFF[sub]:
            for h in range(1,9): b.add((DIDX[dn],h))
        for s in TLN_UNAVAIL[sub]: b.add(s)
    return b
TB = {c:tln_block(c) for c in CLASSES}

# ---- Friday is deterministic (rule 1) ----
fixed = {}
for c in CLASSES:
    for s in FRI: fixed[(c,s)] = FRIDAY_TEACHER[c]

rem = {t:dict(v) for t,v in QUOTA.items()}
for (c,s),t in fixed.items(): rem[t][c] -= 1
for t in rem:
    for c in list(rem[t]):
        assert rem[t][c] >= 0, (t,c,rem[t][c])

m = cp_model.CpModel()
x = {}
for c in CLASSES:
    for t,q in rem.items():
        if c not in q or q[c]==0: continue
        blk = TB[c] if t=='תל"ן' else BLOCK[t]
        for s in NONFRI:
            if s in blk: continue
            x[(c,s,t)] = m.NewBoolVar(f"x_{c}_{s[0]}_{s[1]}_{t}")

# each non-Friday slot: exactly one teacher (allow empty w/ penalty)
empty = {}
for c in CLASSES:
    for s in NONFRI:
        cand = [x[(c,s,t)] for t in rem if (c,s,t) in x]
        e = m.NewBoolVar(f"e_{c}_{s}"); empty[(c,s)] = e
        m.Add(sum(cand) + e == 1)

# quotas (soft, slack both ways)
short, over = {}, {}
for t,q in rem.items():
    for c,n in q.items():
        if n == 0: continue
        cand = [x[(c,s,t)] for s in NONFRI if (c,s,t) in x]
        sh = m.NewIntVar(0,n,f"sh_{t}_{c}"); ov = m.NewIntVar(0,8,f"ov_{t}_{c}")
        short[(t,c)] = sh; over[(t,c)] = ov
        m.Add(sum(cand) + sh - ov == n)

# a teacher is in at most one class per slot
subs = collections.defaultdict(list)     # תל"ן sub-teacher -> classes
for c in CLASSES:
    for sub in TLN_PAIR[c]: subs[sub].append(c)
for s in NONFRI:
    for t in rem:
        if t == 'תל"ן': continue
        v = [x[(c,s,t)] for c in CLASSES if (c,s,t) in x]
        fx = sum(1 for c in CLASSES if fixed.get((c,s))==t)
        if v: m.Add(sum(v) <= 1 - fx)
    for sub,cs in subs.items():
        v = [x[(c,s,'תל"ן')] for c in cs if (c,s,'תל"ן') in x]
        if v: m.Add(sum(v) <= 1)

# פאני: never two consecutive hours in the same class (rule 8)
for c in CLASSES:
    for d in range(5):
        for h in range(1, DAY_HOURS[d]):
            a,b = (c,(d,h),"פאני"), (c,(d,h+1),"פאני")
            if a in x and b in x: m.Add(x[a] + x[b] <= 1)

# תל"ן: 2 hours; consecutive where required, same day otherwise
for c in CLASSES:
    pairs = []
    for d in range(5):
        for h in range(1, DAY_HOURS[d]):
            a,b = (c,(d,h),'תל"ן'), (c,(d,h+1),'תל"ן')
            if a in x and b in x:
                p = m.NewBoolVar(f"p_{c}_{d}_{h}")
                m.Add(x[a]+x[b] == 2).OnlyEnforceIf(p)
                pairs.append(p)
    if TLN_CONSEC[c] and pairs: m.Add(sum(pairs) == 1)

# אינס: 2 consecutive science hours on Tuesday in ה דני / ה תניה
for c in ("ה דני","ה תניה"):
    ps = []
    for h in range(1,6):
        a,b = (c,(2,h),"אינס"), (c,(2,h+1),"אינס")
        if a in x and b in x:
            p = m.NewBoolVar(f"q_{c}_{h}"); m.Add(x[a]+x[b]==2).OnlyEnforceIf(p); ps.append(p)
    if ps: m.Add(sum(ps) == 1)

# spread: teacher shouldn't exceed a sane daily load in one class
m.Minimize(1000*sum(empty.values()) + 100*sum(short.values()) + 100*sum(over.values()))
sol = cp_model.CpSolver(); sol.parameters.max_time_in_seconds = 240
sol.parameters.num_workers = 8
st = sol.Solve(m)
print("status:", sol.StatusName(st), "obj:", sol.ObjectiveValue() if st in (4,2) else None)

if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    out = {c:{} for c in CLASSES}
    for c in CLASSES:
        for s in SLOTS:
            if s in FRI: out[c][f"{s[0]},{s[1]}"] = fixed[(c,s)]
            else:
                who = [t for t in rem if (c,s,t) in x and sol.Value(x[(c,s,t)])]
                out[c][f"{s[0]},{s[1]}"] = who[0] if who else ""
    io.open("solution.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    probs=[]
    for (t,c),v in short.items():
        if sol.Value(v): probs.append(f"חסר {sol.Value(v)} ש' ל{t} ב{c}")
    for (t,c),v in over.items():
        if sol.Value(v): probs.append(f"עודף {sol.Value(v)} ש' ל{t} ב{c}")
    for (c,s),v in empty.items():
        if sol.Value(v): probs.append(f"משבצת ריקה {c} {DAY_NAMES[s[0]]} ש{s[1]}")
    io.open("problems.txt","w",encoding="utf-8").write("\n".join(probs) or "אין חריגות")
    print("problems:", len(probs))
