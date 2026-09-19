# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from data import *
NIHUL=["לייה","שרית","יערה","צופיה","אסיף"]          # + אלי (לא מלמד יסודי)
EVENTS["יערה"]=[(0,3)]; EVENTS["לייה"]=[(0,4)]
EVENTS["שרית"]=[(0,1)]; EVENTS["צופיה"]=[(0,2),(0,5)]
EVENTS["אסיף"]=[(3,2),(3,6),(4,2)]

DIDX={n:i for i,n in enumerate(DAY_NAMES)}
NONFRI=[s for s in SLOTS if s[0]!=5]; FRI=[s for s in SLOTS if s[0]==5]
DEU=[c for c in CLASSES if c[0] in "דהו"]
B_CL=[c for c in CLASSES if c.startswith("ב ")]
G_CL=[c for c in CLASSES if c[0]=="ג"]

# מאמי / רובי deliberately NOT used
POOL={"טלי":(3,B_CL),"ליאור":(2,CLASSES),"מרים":(6,DEU),"חסן":(0,DEU),"צופיה":(4,G_CL)}
for t in POOL: DAYS_OFF.setdefault(t,[]); EVENTS.setdefault(t,[]); QUOTA.setdefault(t,{})

def blocked(t):
    b=set()
    for dn in DAYS_OFF.get(t,[]):
        for h in range(1,9): b.add((DIDX[dn],h))
    for s in UNAVAIL.get(t,[])+EVENTS.get(t,[]): b.add(s)
    return b
BLOCK={t:blocked(t) for t in set(list(QUOTA)+list(POOL))}
def tlnb(c):
    b=set()
    for sub in TLN_PAIR[c]:
        for dn in TLN_OFF[sub]:
            for h in range(1,9): b.add((DIDX[dn],h))
        for s in TLN_UNAVAIL[sub]: b.add(s)
    return b
TB={c:tlnb(c) for c in CLASSES}

fixed={(c,s):FRIDAY_TEACHER[c] for c in CLASSES for s in FRI}
rem={t:dict(v) for t,v in QUOTA.items()}
for (c,s),t in fixed.items(): rem[t][c]-=1

allowed=collections.defaultdict(set)
for t,q in rem.items():
    for c in q: allowed[c].add(t)
for t,(cap,cls) in POOL.items():
    for c in cls: allowed[c].add(t)

m=cp_model.CpModel(); x={}
for c in CLASSES:
    for t in allowed[c]:
        blk=TB[c] if t=='תל"ן' else BLOCK[t]
        for s in NONFRI:
            if s in blk: continue
            x[(c,s,t)]=m.NewBoolVar(f"x{c}{s}{t}")

# ---- מעגלי שיח: group membership + movable 2-hour block ----
gmon={}                                  # 1 = teacher sits in the Monday circle
for t in CIRCLE_TEACHERS:
    off=DAYS_OFF.get(t, CIRCLE_OFF.get(t,[]))
    v=m.NewBoolVar(f"g{t}"); gmon[t]=v
    if "שני"   in off: m.Add(v==0)
    if "שלישי" in off: m.Add(v==1)
    f=CIRCLE_FORCE.get(t)
    if f=="ג": m.Add(v==0)
    if f=="ב": m.Add(v==1)
m.Add(sum(gmon.values())==9)             # two equal groups of 9
JH=["אסיף","אלי","נעמי","גלית","תמיר"]   # keep both groups mixed יסודי/חטיבה
m.Add(sum(gmon[t] for t in JH)>=2); m.Add(sum(gmon[t] for t in JH)<=3)

blk_h={}
for tag,day in (("m",1),("u",2)):
    st=[m.NewBoolVar(f"{tag}s{h}") for h in range(1,6)]
    m.Add(sum(st)==1)
    for h in (2,4): m.Add(st[h-1]==0)      # blocks start only at 1, 3 or 5
    for h in range(1,7):
        v=m.NewBoolVar(f"{tag}h{h}")
        src=[st[h-1]] if h==1 else ([st[h-2]] if h==6 else [st[h-2],st[h-1]])
        m.AddMaxEquality(v,src); blk_h[(tag,h)]=v
for t in CIRCLE_TEACHERS:
    if t not in allowed_any if False else False: pass
for c in CLASSES:
    for t in allowed[c]:
        if t not in gmon: continue
        for h in range(1,7):
            if (c,(1,h),t) in x:                     # Monday circle
                m.Add(x[(c,(1,h),t)]+gmon[t]+blk_h[("m",h)]<=2)
            if (c,(2,h),t) in x:                     # Tuesday circle
                m.Add(x[(c,(2,h),t)]+(1-gmon[t])+blk_h[("u",h)]<=2)

# ---- ישיבת ניהול הובלה ושילוח: יום ג, שעות 3-4 (10:00) או 5-6 (11:30) ----
late=m.NewBoolVar("nihul_late")
nb={h:(m.NewConstant(0)) for h in (1,2)}
nb[3]=nb[4]=late.Not(); nb[5]=nb[6]=late
for c in CLASSES:
    for t in allowed[c]:
        if t not in NIHUL: continue
        for h in range(1,7):
            if (c,(2,h),t) in x: m.Add(x[(c,(2,h),t)]+nb[h]<=1)
# a teacher in both meetings cannot have them overlap
for t in NIHUL:
    if t not in gmon: continue
    for h in range(1,7):
        m.Add(nb[h]+blk_h[("u",h)]+(1-gmon[t])<=2)

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
        if not v: continue
        tot=sum(v)
        if tgt>0:
            sh=m.NewIntVar(0,tgt,f"sh{t}{c}"); ov=m.NewIntVar(0,10,f"ov{t}{c}")
            m.Add(tot+sh-ov==tgt); pen += [100*sh,100*ov]
        else:
            u=m.NewIntVar(0,32,f"u{t}{c}"); m.Add(u==tot); pen.append(30*u)
        if tgt<=8:
            nd=sum(1 for d in range(5) if any((c,(d,h),t) in x for h in range(1,DAY_HOURS[d]+1)))
            cap=max(2,-(-tgt//max(nd,1)))
            for d in range(5):
                dv=[x[(c,(d,h),t)] for h in range(1,DAY_HOURS[d]+1) if (c,(d,h),t) in x]
                if dv: m.Add(sum(dv)<=cap)

for t,(cap,cls) in POOL.items():
    tot=sum(x[(c,s,t)] for c in cls for s in NONFRI if (c,s,t) in x)
    m.Add(tot<=sum(rem.get(t,{}).get(c,0) for c in cls)+cap)

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

# חינוך גופני (פאני + חסן): לכל היותר שיעור ספורט אחד ליום בכל כיתה
for c in CLASSES:
    for d in range(5):
        dv=[x[(c,(d,h),t)] for t in ("פאני","חסן")
            for h in range(1,DAY_HOURS[d]+1) if (c,(d,h),t) in x]
        if dv: m.Add(sum(dv)<=1)
for c in CLASSES:
    v=[x[(c,s,'תל"ן')] for s in NONFRI if (c,s,'תל"ן') in x]
    if v: m.Add(sum(v)==2)
for t in ("אסיף","תמיר"):
    for c in CLASSES:
        v=[x[(c,s,t)] for s in NONFRI if (c,s,t) in x]
        if v: m.Add(sum(v)==(1 if c.startswith("ו ") else 0))
for c in CLASSES:
    ps=[]
    for d in range(5):
        for h in range(1,DAY_HOURS[d]):
            a,b=(c,(d,h),'תל"ן'),(c,(d,h+1),'תל"ן')
            if a in x and b in x:
                p=m.NewBoolVar(f"p{c}{d}{h}"); m.Add(x[a]+x[b]==2).OnlyEnforceIf(p); ps.append(p)
    if TLN_CONSEC[c] and ps: m.Add(sum(ps)==1)
for c in ("ה דני","ה תניה"):
    ps=[]
    for h in range(1,6):
        a,b=(c,(2,h),"אינס"),(c,(2,h+1),"אינס")
        if a in x and b in x:
            p=m.NewBoolVar(f"q{c}{h}"); m.Add(x[a]+x[b]==2).OnlyEnforceIf(p); ps.append(p)
    if ps: m.Add(sum(ps)==1)

m.Minimize(10000*sum(empty.values())+sum(pen))
sol=cp_model.CpSolver(); sol.parameters.max_time_in_seconds=420; sol.parameters.num_workers=8
st=sol.Solve(m); print("status:",sol.StatusName(st))
if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    print("obj:",sol.ObjectiveValue(),"empty:",sum(sol.Value(v) for v in empty.values()))
    mb=[h for h in range(1,7) if sol.Value(blk_h[("m",h)])]
    ub=[h for h in range(1,7) if sol.Value(blk_h[("u",h)])]
    grp={"שני":sorted(t for t in CIRCLE_TEACHERS if sol.Value(gmon[t])),
         "שלישי":sorted(t for t in CIRCLE_TEACHERS if not sol.Value(gmon[t]))}
    out={}
    for c in CLASSES:
        out[c]={f"{s[0]},{s[1]}": (fixed[(c,s)] if s[0]==5 else
                next((t for t in allowed[c] if (c,s,t) in x and sol.Value(x[(c,s,t)])),"")) for s in SLOTS}
    io.open("solution_d.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    io.open("circles_d.json","w",encoding="utf-8").write(json.dumps(
        {"ישיבת ניהול יום ג":("שעות 5-6 (11:30)" if sol.Value(late) else "שעות 3-4 (10:00)"),"שני":{"שעות":mb,"מחנכים":grp["שני"]},"שלישי":{"שעות":ub,"מחנכים":grp["שלישי"]}},ensure_ascii=False,indent=1))
    lines=[]
    for c in CLASSES:
        cnt=collections.Counter(out[c].values())
        for t in sorted(set(list(cnt)+[k for k,v in QUOTA.items() if c in v])):
            got,tgt=cnt.get(t,0),QUOTA.get(t,{}).get(c,0)
            if got!=tgt: lines.append(f"{c} | {t} | בסדין {tgt} | בפועל {got} | {got-tgt:+d}")
    io.open("deviations_d.txt","w",encoding="utf-8").write("\n".join(lines) or "אין סטיות")
    print("deviations:",len(lines))
