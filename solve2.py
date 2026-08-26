# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from data import *

DIDX={n:i for i,n in enumerate(DAY_NAMES)}
NONFRI=[s for s in SLOTS if s[0]!=5]; FRI=[s for s in SLOTS if s[0]==5]
F_CL=[c for c in CLASSES if c.startswith("ו ")]
B_CL=[c for c in CLASSES if c.startswith("ב ")]
DEU=[c for c in CLASSES if c[0] in "דהו"]

# extra capacity to absorb the physical deficit (per the sheet's own notes)
POOL={"מאמי":(4,CLASSES),"רובי":(4,CLASSES),"טלי":(3,B_CL),"ליאור":(2,CLASSES),
      "מרים":(4,DEU),"חסן":(4,DEU),"צופיה":(4,[c for c in CLASSES if c[0]=="ג"])}
DAYS_OFF.setdefault("מאמי",[]); DAYS_OFF.setdefault("רובי",["ראשון","שני","רביעי","חמישי","שישי"])
EVENTS.setdefault("מאמי",[]); EVENTS.setdefault("רובי",[])
for t in POOL:
    DAYS_OFF.setdefault(t,[]); EVENTS.setdefault(t,[]); QUOTA.setdefault(t,{})

def blocked(t):
    b=set()
    for dn in DAYS_OFF.get(t,[]):
        for h in range(1,9): b.add((DIDX[dn],h))
    for s in UNAVAIL.get(t,[])+EVENTS.get(t,[]): b.add(s)
    return b
BLOCK={t:blocked(t) for t in set(list(QUOTA)+list(POOL))}
def tln_block(c):
    b=set()
    for sub in TLN_PAIR[c]:
        for dn in TLN_OFF[sub]:
            for h in range(1,9): b.add((DIDX[dn],h))
        for s in TLN_UNAVAIL[sub]: b.add(s)
    return b
TB={c:tln_block(c) for c in CLASSES}

fixed={(c,s):FRIDAY_TEACHER[c] for c in CLASSES for s in FRI}
rem={t:dict(v) for t,v in QUOTA.items()}
for (c,s),t in fixed.items(): rem[t][c]-=1

allowed=collections.defaultdict(set)          # class -> teachers
for t,q in rem.items():
    for c,n in q.items():
        if n>0 or (t,c) in [(t,c)]: allowed[c].add(t)
for t,(cap,cls) in POOL.items():
    for c in cls: allowed[c].add(t)

m=cp_model.CpModel(); x={}
for c in CLASSES:
    for t in allowed[c]:
        blk=TB[c] if t=='תל"ן' else BLOCK[t]
        for s in NONFRI:
            if s in blk: continue
            x[(c,s,t)]=m.NewBoolVar(f"x{c}{s}{t}")

empty={}
for c in CLASSES:
    for s in NONFRI:
        e=m.NewBoolVar(f"e{c}{s}"); empty[(c,s)]=e
        m.Add(sum(x[(c,s,t)] for t in allowed[c] if (c,s,t) in x)+e==1)

pen=[]
for c in CLASSES:
    for t in allowed[c]:
        tgt=rem.get(t,{}).get(c,0)
        v=[x[(c,s,t)] for s in NONFRI if (c,s,t) in x]
        if not v:
            if tgt>0: pen.append(100*tgt)
            continue
        tot=sum(v)
        if tgt>0:
            sh=m.NewIntVar(0,tgt,f"sh{t}{c}"); ov=m.NewIntVar(0,10,f"ov{t}{c}")
            m.Add(tot+sh-ov==tgt); pen += [100*sh, 100*ov]
        else:                                  # pool usage
            u=m.NewIntVar(0,32,f"u{t}{c}"); m.Add(u==tot); pen.append(30*u)
        if tgt <= 8:            # small loads: spread out, but never below what fits
            nd=sum(1 for d in range(5)
                   if any((c,(d,h),t) in x for h in range(1,DAY_HOURS[d]+1)))
            cap=max(2,-(-tgt//max(nd,1)))
            for d in range(5):
                dv=[x[(c,(d,h),t)] for h in range(1,DAY_HOURS[d]+1) if (c,(d,h),t) in x]
                if dv: m.Add(sum(dv)<=cap)

for t,(cap,cls) in POOL.items():
    tot=sum(x[(c,s,t)] for c in cls for s in NONFRI if (c,s,t) in x)
    base=sum(rem.get(t,{}).get(c,0) for c in cls)
    m.Add(tot<=base+cap)

subs=collections.defaultdict(list)
for c in CLASSES:
    for sub in TLN_PAIR[c]: subs[sub].append(c)
for s in NONFRI:
    for t in set(list(rem)+list(POOL)):
        if t=='תל"ן': continue
        v=[x[(c,s,t)] for c in CLASSES if (c,s,t) in x]
        fx=sum(1 for c in CLASSES if fixed.get((c,s))==t)
        if v: m.Add(sum(v)<=1-fx)
    for sub,cs in subs.items():
        v=[x[(c,s,'תל"ן')] for c in cs if (c,s,'תל"ן') in x]
        if v: m.Add(sum(v)<=1)

for c in CLASSES:                              # rule 8: פאני never back-to-back
    for d in range(5):
        for h in range(1,DAY_HOURS[d]):
            a,b=(c,(d,h),"פאני"),(c,(d,h+1),"פאני")
            if a in x and b in x: m.Add(x[a]+x[b]<=1)

# HARD: תל"ן exactly 2h per class; אסיף/תמיר exactly 1h per ו class
for c in CLASSES:
    v=[x[(c,s,'תל"ן')] for s in NONFRI if (c,s,'תל"ן') in x]
    if v: m.Add(sum(v)==2)
for t in ("אסיף","תמיר"):
    for c in CLASSES:
        v=[x[(c,s,t)] for s in NONFRI if (c,s,t) in x]
        if v: m.Add(sum(v)==(1 if c.startswith("ו ") else 0))

for c in CLASSES:                              # תל"ן pairing
    ps=[]
    for d in range(5):
        for h in range(1,DAY_HOURS[d]):
            a,b=(c,(d,h),'תל"ן'),(c,(d,h+1),'תל"ן')
            if a in x and b in x:
                p=m.NewBoolVar(f"p{c}{d}{h}"); m.Add(x[a]+x[b]==2).OnlyEnforceIf(p); ps.append(p)
    if TLN_CONSEC[c] and ps: m.Add(sum(ps)==1)

for c in ("ה דני","ה תניה"):                   # אינס: 2 ברצף מדעים ביום ג
    ps=[]
    for h in range(1,6):
        a,b=(c,(2,h),"אינס"),(c,(2,h+1),"אינס")
        if a in x and b in x:
            p=m.NewBoolVar(f"q{c}{h}"); m.Add(x[a]+x[b]==2).OnlyEnforceIf(p); ps.append(p)
    if ps: m.Add(sum(ps)==1)

m.Minimize(10000*sum(empty.values())+sum(pen))
sol=cp_model.CpSolver(); sol.parameters.max_time_in_seconds=300; sol.parameters.num_workers=8
st=sol.Solve(m); print("status:",sol.StatusName(st))
if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    print("obj:",sol.ObjectiveValue(),"empty:",sum(sol.Value(v) for v in empty.values()))
    out={}
    for c in CLASSES:
        out[c]={}
        for s in SLOTS:
            k=f"{s[0]},{s[1]}"
            if s[0]==5: out[c][k]=fixed[(c,s)]
            else:
                w=[t for t in allowed[c] if (c,s,t) in x and sol.Value(x[(c,s,t)])]
                out[c][k]=w[0] if w else ""
    io.open("solution.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    # deviation report
    lines=[]
    for c in CLASSES:
        for t in sorted(allowed[c]):
            got=sum(1 for s in SLOTS if out[c][f"{s[0]},{s[1]}"]==t)
            tgt=QUOTA.get(t,{}).get(c,0)
            if got!=tgt: lines.append(f"{c} | {t} | בסדין {tgt} | בפועל {got} | {got-tgt:+d}")
    io.open("deviations.txt","w",encoding="utf-8").write("\n".join(lines) or "אין סטיות")
    print("deviations:",len(lines))
