# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from data2 import *

NONFRI=[s for s in SLOTS if s[0]!=5]; FRI=[s for s in SLOTS if s[0]==5]
DEU=[c for c in CLASSES if c[0] in "דהו"]; B_CL=[c for c in CLASSES if c.startswith("ב ")]
G_CL=[c for c in CLASSES if c[0]=="ג"]
POOL={"טלי":(3,B_CL),"ליאור":(4,CLASSES),"מרים":(5,DEU),"צופיה":(4,G_CL),"שחר":(2,[c for c in CLASSES if c[0] in "אבג"])}
TLN_OFF2={"הילית":["חמישי","שישי"],"חגית":["חמישי"],"יפעת":["חמישי","שישי"],"יעל":[]}
TLN_UN2={"הילית":[(2,h) for h in range(4,9)],"חגית":[],"יפעת":[],"יעל":[]}

def blk(t):
    b=set()
    for dn in DAYS_OFF2.get(t,[]):
        for h in range(1,9): b.add((DIDX[dn],h))
    for s in UNAVAIL2.get(t,[])+EVENTS2.get(t,[]): b.add(s)
    for (d,h),tt in MAGAMA.items():
        if t in tt: b.add((d,h))
    return b
BLOCK={t:blk(t) for t in set(list(QUOTA)+list(POOL))}
def tb(c):
    b=set()
    for sub in TLN_PAIR[c]:
        for dn in TLN_OFF2[sub]:
            for h in range(1,9): b.add((DIDX[dn],h))
        for s in TLN_UN2[sub]: b.add(s)
        for (d,h),tt in MAGAMA.items():
            if sub in tt: b.add((d,h))
    return b
TB={c:tb(c) for c in CLASSES}

fixed={(c,s):FRIDAY_TEACHER[c] for c in CLASSES for s in FRI}
rem={t:dict(v) for t,v in QUOTA.items()}
for (c,s),t in fixed.items(): rem[t][c]-=1

m=cp_model.CpModel()
# ---- חטיבה: ספורט שכבתי, 3 שעות רצופות בראשון ובחמישי/רביעי -> חוסם את שרית וחסן ----
pe={}
for tag,d,maxst in (("sun",0,3),("wed",3,4)):
    st=[m.NewBoolVar(f"pe{tag}{h}") for h in range(1,maxst+1)]
    m.Add(sum(st)==1)
    for h in range(1,DAY_HOURS[d]+1):
        v=m.NewBoolVar(f"peh{tag}{h}")
        src=[st[k-1] for k in range(max(1,h-2),h+1) if k<=maxst]
        if src: m.AddMaxEquality(v,src)
        else: m.Add(v==0)
        pe[(d,h)]=v

allowed=collections.defaultdict(set)
for t,q in rem.items():
    for c in q: allowed[c].add(t)
for t,(cap,cls) in POOL.items():
    for c in cls: allowed[c].add(t)

x={}
for c in CLASSES:
    for t in allowed[c]:
        b=TB[c] if t=='תל"ן' else BLOCK[t]
        for s in NONFRI:
            if s in b: continue
            x[(c,s,t)]=m.NewBoolVar(f"x{c}{s}{t}")
# שרית/חסן חסומים בשעות הספורט של החטיבה
for c in CLASSES:
    for t in ("שרית","חסן"):
        for (d,h),v in pe.items():
            if (c,(d,h),t) in x: m.Add(x[(c,(d,h),t)]+v<=1)

# צופיה: יום חופש ברביעי או בחמישי (לבחירת הפותר) + שני מתחיל ב-10:00 (משעה 3)
zwed=m.NewBoolVar("zofia_wed")
for d,flag in ((3,zwed),(4,zwed.Not())):
    for h in range(1,DAY_HOURS[d]+1):
        for c in CLASSES:
            if ("צופיה" in [t for t in allowed[c]]) and (c,(d,h),"צופיה") in x:
                m.Add(x[(c,(d,h),"צופיה")]+flag<=1)
for h in (1,2):
    for c in CLASSES:
        if (c,(1,h),"צופיה") in x: m.Add(x[(c,(1,h),"צופיה")]==0)

# חסן ופאני מורי ספורט: מכסה לכל כיתה קשיחה (שעה נוספת = שיעור ספורט שלישי)
for t in ("חסן","פאני"):
    for c in CLASSES:
        v=[x[(c,s,t)] for s in NONFRI if (c,s,t) in x]
        if v: m.Add(sum(v)==rem.get(t,{}).get(c,0))

# ---- סדירויות שבועיות: מעגלי שיח (חלוקה מקורית, נעולה) + ישיבת ניהול ----
CIR_MON=["דני","אינס","דניאל","תמיר","אלי","נעמי","תניה","דליה","אנה"]
CIR_TUE=["אסיף","פנינה","יערה","אורנה","גלית","שרית","לייה","מירי","אביטל"]
NIHUL=["לייה","שרית","יערה","צופיה","אסיף"]
blkh={}
for tag,d in (("m",1),("u",2)):
    st=[m.NewBoolVar(f"{tag}st{k}") for k in (1,3,5)]      # בלוקים אמיתיים בלבד
    m.Add(sum(st)==1)
    for h in range(1,DAY_HOURS[d]+1):
        v=m.NewBoolVar(f"{tag}h{h}")
        src=[st[i] for i,k in enumerate((1,3,5)) if k<=h<=k+1]
        if src: m.AddMaxEquality(v,src)
        else: m.Add(v==0)
        blkh[(tag,h)]=v
nst=[m.NewBoolVar(f"n{k}") for k in (3,5)]                  # ישיבת ניהול: 3-4 או 5-6
m.Add(sum(nst)==1); m.Add(nst[0]==1)   # לפי הסדין: ישיבת ניהול ג 3-4
nb={}
for h in range(1,DAY_HOURS[2]+1):
    v=m.NewBoolVar(f"nb{h}")
    src=[nst[i] for i,k in enumerate((3,5)) if k<=h<=k+1]
    if src: m.AddMaxEquality(v,src)
    else: m.Add(v==0)
    nb[h]=v
ALLC=CIR_MON+CIR_TUE
gm={}
OFF2={"גלית":["שני","חמישי"],"אלי":["שישי"],"נעמי":["חמישי"],"תמיר":[]}
for t in ALLC:
    v=m.NewBoolVar(f"g_{t}"); gm[t]=v
    off=DAYS_OFF2.get(t) or OFF2.get(t,[])
    if "שני" in off:   m.Add(v==0)
    if "שלישי" in off: m.Add(v==1)
m.Add(sum(gm.values())==9)
JH=["אסיף","אלי","נעמי","גלית","תמיר"]
m.Add(sum(gm[t] for t in JH)>=2); m.Add(sum(gm[t] for t in JH)<=3)
for t in ALLC:                                   # מי שבמגמות ג' לא יכול בקבוצת שלישי באותן שעות
    for (d,h),tt in MAGAMA.items():
        if d==2 and t in tt: m.Add(blkh[("u",h)]+gm[t].Not()<=1)
for c in CLASSES:
    for t in allowed[c]:
        if t in gm:
            for h in range(1,DAY_HOURS[1]+1):
                if (c,(1,h),t) in x: m.Add(x[(c,(1,h),t)]+blkh[("m",h)]+gm[t]<=2)
            for h in range(1,DAY_HOURS[2]+1):
                if (c,(2,h),t) in x: m.Add(x[(c,(2,h),t)]+blkh[("u",h)]+gm[t].Not()<=2)
        for h in range(1,DAY_HOURS[2]+1):
            if t in NIHUL and (c,(2,h),t) in x: m.Add(x[(c,(2,h),t)]+nb[h]<=1)
for h in range(1,DAY_HOURS[2]+1):                            # אין חפיפה בין השתיים
    m.Add(blkh[("u",h)]+nb[h]<=1)
for h in (1,2): m.Add(blkh[("m",h)]==0)                      # שני 1-2 = חווה חקלאית
for t in set(CIR_TUE)|set(NIHUL):                            # מגמות חוסמות את המפגשים
    for (d,h),tt in MAGAMA.items():
        if d==2 and t in tt:
            if t in CIR_TUE: m.Add(blkh[("u",h)]==0)
            if t in NIHUL:   m.Add(nb[h]==0)

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
        if tgt>0:
            sh=m.NewIntVar(0,tgt,f"s{t}{c}"); ov=m.NewIntVar(0,10,f"o{t}{c}")
            m.Add(sum(v)+sh-ov==tgt); pen += [100*sh,100*ov]
        else:
            u=m.NewIntVar(0,32,f"u{t}{c}"); m.Add(u==sum(v)); pen.append(30*u)
        if tgt<=8:
            nd=sum(1 for d in range(5) if any((c,(d,h),t) in x for h in range(1,DAY_HOURS[d]+1)))
            cap=max(2,-(-tgt//max(nd,1)))
            for d in range(5):
                dv=[x[(c,(d,h),t)] for h in range(1,DAY_HOURS[d]+1) if (c,(d,h),t) in x]
                if dv: m.Add(sum(dv)<=cap)
for t,(cap,cls) in POOL.items():
    m.Add(sum(x[(c,s,t)] for c in cls for s in NONFRI if (c,s,t) in x)
          <= sum(rem.get(t,{}).get(c,0) for c in cls)+cap)
for t,q in MAXQ2.items():
    v=[x[(c,s,t)] for c in CLASSES for s in NONFRI if (c,s,t) in x]
    fx=sum(1 for (c,s),tt in fixed.items() if tt==t)
    if v: m.Add(sum(v)<=q-HATIVA2.get(t,0)-fx)

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

# ספורט יסודי (פאני+חסן): שיעור אחד ליום לכל היותר
for c in CLASSES:
    for d in range(5):
        dv=[x[(c,(d,h),t)] for t in ("פאני","חסן") for h in range(1,DAY_HOURS[d]+1) if (c,(d,h),t) in x]
        if dv: m.Add(sum(dv)<=1)
# תל"ן
for c in CLASSES:
    v=[x[(c,s,'תל"ן')] for s in NONFRI if (c,s,'תל"ן') in x]
    if v: m.Add(sum(v)==2)
    ps=[]
    for d in range(5):
        for h in range(1,DAY_HOURS[d]):
            a,b2=(c,(d,h),'תל"ן'),(c,(d,h+1),'תל"ן')
            if a in x and b2 in x:
                p=m.NewBoolVar(f"p{c}{d}{h}"); m.Add(x[a]+x[b2]==2).OnlyEnforceIf(p); ps.append(p)
    if TLN_CONSEC[c] and ps: m.Add(sum(ps)==1)
# אינס: 2 מדעים ברצף - כל יום חוץ משלישי (יום החופש החדש שלה)
for c in ("ה דני","ה תניה"):
    ps=[]
    for d in (0,1,3,4):
        for h in range(1,DAY_HOURS[d]):
            a,b2=(c,(d,h),"אינס"),(c,(d,h+1),"אינס")
            if a in x and b2 in x:
                p=m.NewBoolVar(f"q{c}{d}{h}"); m.Add(x[a]+x[b2]==2).OnlyEnforceIf(p); ps.append(p)
    if ps: m.Add(sum(ps)==1)
# אסיף/תמיר: שעה בכל כיתת ו
for t in ("אסיף","תמיר"):
    for c in CLASSES:
        v=[x[(c,s,t)] for s in NONFRI if (c,s,t) in x]
        if v: m.Add(sum(v)==(1 if c.startswith("ו ") else 0))
# חווה חקלאית: מחנכות ג' עם הכיתה בשני ש1-2 (רך)
farm=[]
for c in FARM_CLASSES:
    for s in FARM_SLOTS:
        k=(c,s,HOMEROOM[c])
        if k in x: farm.append(x[k])
keepg=[gm[t] for t in CIR_MON]+[gm[t].Not() for t in CIR_TUE]
m.Minimize(10000*sum(empty.values())+sum(pen)+200*(len(farm)-sum(farm))+400*(len(keepg)-sum(keepg)))
sol=cp_model.CpSolver(); sol.parameters.max_time_in_seconds=420; sol.parameters.num_workers=8
st=sol.Solve(m); print("status:",sol.StatusName(st))
if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    print("obj:",sol.ObjectiveValue(),"empty:",sum(sol.Value(v) for v in empty.values()))
    print("farm ok:",sum(sol.Value(v) for v in farm),"/",len(farm))
    peh={d:[h for h in range(1,DAY_HOURS[d]+1) if sol.Value(pe[(d,h)])] for d in (0,3)}
    print("ספורט חטיבה: ראשון",peh[0],"| רביעי",peh[3]);print("יום חופש צופיה:", "רביעי" if sol.Value(zwed) else "חמישי")
    mb=[h for h in range(1,7) if sol.Value(blkh[("m",h)])]
    ub=[h for h in range(1,7) if sol.Value(blkh[("u",h)])]
    nbh=[h for h in range(1,7) if sol.Value(nb[h])]
    io.open("sed_fin.json","w",encoding="utf-8").write(json.dumps(
      {"מעגלי שיח שני":mb,"מעגלי שיח שלישי":ub,"ישיבת ניהול שלישי":nbh,
       "קבוצת שני":sorted(t for t in ALLC if sol.Value(gm[t])),"קבוצת שלישי":sorted(t for t in ALLC if not sol.Value(gm[t]))},ensure_ascii=False,indent=1))
    out={c:{f"{s[0]},{s[1]}":(fixed[(c,s)] if s[0]==5 else
        next((t for t in allowed[c] if (c,s,t) in x and sol.Value(x[(c,s,t)])),"")) for s in SLOTS} for c in CLASSES}
    io.open("sol_elem_fin.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    io.open("pe_blocks.json","w",encoding="utf-8").write(json.dumps(peh,ensure_ascii=False))
    dev=[]
    for c in CLASSES:
        cnt=collections.Counter(out[c].values())
        for t in sorted(set(list(cnt)+[k for k,v in QUOTA.items() if c in v])):
            g,tg=cnt.get(t,0),QUOTA.get(t,{}).get(c,0)
            if g!=tg: dev.append(f"{c} | {t} | בסדין {tg} | בפועל {g} | {g-tg:+d}")
    io.open("dev_elem_fin.txt","w",encoding="utf-8").write("\n".join(dev))
    print("deviations:",len(dev))
