# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from hdata import *
from data2 import CLASSES as ECL, SLOTS as ESL

E=json.load(io.open("sol_F.json",encoding="utf-8"))
SED=json.load(io.open("sed_F.json",encoding="utf-8"))
ebusy=collections.defaultdict(set)                       # מורה -> משבצות תפוסות ביסודי
for c in ECL:
    for (d,h) in ESL:
        t=E[c][f"{d},{h}"]
        if t and t!='תל"ן': ebusy[t].add((d,h))
CM={"שני":1,"שלישי":2}
for day in ("שני","שלישי"):
    for t in SED["קבוצת "+day]:
        for h in SED["מעגלי שיח "+day]: ebusy[t].add((CM[day],h))
for t in ["לייה","שרית","יערה","צופיה","אסיף"]:
    for h in SED["ישיבת ניהול שלישי"]: ebusy[t].add((2,h))

def tblk(t):
    b=set(ebusy.get(t,()))
    for dn in HOFF.get(t,[]):
        for h in range(1,8): b.add((DIDX[dn],h))
    for s in HEV.get(t,[]): b.add(s)
    return b

m=cp_model.CpModel()
# ---- חינוך גופני שכבתי: ראשון ש1-3 ורביעי ש4-6, שעה לכל שכבה ----
pe={}
for d,hrs in PE_BLOCKS.items():
    for g in "זחט":
        for h in hrs: pe[(g,d,h)]=m.NewBoolVar(f"pe{g}{d}{h}")
    for g in "זחט": m.Add(sum(pe[(g,d,h)] for h in hrs)==1)
    for h in hrs:   m.Add(sum(pe[(g,d,h)] for g in "זחט")==1)

pairs=collections.defaultdict(list)                       # class -> [(subject,teacher)]
for c in HCLASSES:
    g=GRADE[c]
    for subj,per in NEED.items():
        if per[g]==0: continue
        if subj=="חינוך": pairs[c].append((subj,HHOME[c]))
        elif subj=="מגמות": pairs[c].append((subj,"מגמות"))
        elif subj=="חינוך גופני": pairs[c].append((subj,"שרית + חסן"))
        else:
            for t in POOLS[subj].get(g,[]): pairs[c].append((subj,t))
x={}
for c in HCLASSES:
    for (subj,t) in pairs[c]:
        b=set() if t in ("מגמות","שרית + חסן") else tblk(t)
        for s in HSLOTS:
            if s in b: continue
            x[(c,s,subj,t)]=m.NewBoolVar(f"x{c}{s}{subj}{t}")

miss={}
free={}
for c in HCLASSES:
    for s in HSLOTS:
        f=m.NewBoolVar(f"f{c}{s}"); free[(c,s)]=f
        m.Add(sum(x[(c,s,sj,t)] for (sj,t) in pairs[c] if (c,s,sj,t) in x)+f==1)
    g=GRADE[c]
    for subj,per in NEED.items():
        if per[g]==0: continue
        v=[x[(c,s,subj,t)] for s in HSLOTS for (sj,t) in pairs[c] if sj==subj and (c,s,subj,t) in x]
        sh=m.NewIntVar(0,per[g],f"sh{c}{subj}"); miss[(c,subj)]=sh
        m.Add(sum(v)+sh==per[g])

# מגמות: בלוקים קבועים
for c in HCLASSES:
    g=GRADE[c]; blk=MAG_H["ט" if g=="ט" else "ז+ח"]
    for s in HSLOTS:
        k=(c,s,"מגמות","מגמות")
        if k in x: m.Add(x[k]==(1 if (s[0]==blk["day"] and s[1] in blk["hours"]) else 0))
# חינוך גופני: לפי הבלוקים השכבתיים
for c in HCLASSES:
    g=GRADE[c]
    for s in HSLOTS:
        k=(c,s,"חינוך גופני","שרית + חסן")
        if k not in x: continue
        if s in [(d,h) for d,hrs in PE_BLOCKS.items() for h in hrs]:
            m.Add(x[k]==pe[(g,s[0],s[1])])
        else: m.Add(x[k]==0)
# מורה אחד בכל רגע (כולל מול היסודי)
for s in HSLOTS:
    for t in set(CAP):        # ספורט שכבתי = שתי כיתות יחד, מנוהל ע"י pe
        v=[x[(c,s,sj,t)] for c in HCLASSES for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in x]
        if v: m.Add(sum(v)<=1)
# תקרות מורים
for t,cap in CAP.items():
    v=[x[(c,s,sj,t)] for c in HCLASSES for s in HSLOTS for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in x]
    if v: m.Add(sum(v)<=cap)   # CAP הוא תקציב החטיבה בלבד
# פיזור: לא יותר מ-2 שעות של אותו מקצוע ביום (חוץ ממגמות/ספורט)
for c in HCLASSES:
    for subj in NEED:
        if subj in ("מגמות","חינוך גופני"): continue
        for d in range(6):
            v=[x[(c,(d,h),subj,t)] for h in range(1,HDAY[d]+1) for (sj,t) in pairs[c] if sj==subj and (c,(d,h),subj,t) in x]
            if v: m.Add(sum(v)<=2)
# עדיף לסיים מוקדם: קנס על שעות מאוחרות
late=[]
for c in HCLASSES:
    for (d,h) in HSLOTS:
        if h>=6: late.append(free[(c,(d,h))].Not())
m.Minimize(1000*sum(miss.values()) + 5*sum(late))
# חייב למלא בדיוק את מספר השעות -> free נקבע ע"י האילוצים
sol=cp_model.CpSolver(); sol.parameters.max_time_in_seconds=600; sol.parameters.num_workers=8
st=sol.Solve(m); print("status:",sol.StatusName(st))
if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    out={}
    for c in HCLASSES:
        out[c]={}
        for s in HSLOTS:
            got=[(sj,t) for (sj,t) in pairs[c] if (c,s,sj,t) in x and sol.Value(x[(c,s,sj,t)])]
            out[c][f"{s[0]},{s[1]}"]= (f"{got[0][0]} – {got[0][1]}" if got else "")
    io.open("sol_hat.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    peo={f"{DAY_NAMES[d]} ש{h}":g for (g,d,h) in pe if sol.Value(pe[(g,d,h)])}
    io.open("pe_hat.json","w",encoding="utf-8").write(json.dumps(peo,ensure_ascii=False,indent=1))
    for (c,subj),v in sorted(miss.items()):
        if sol.Value(v): print("חסר:",c,subj,sol.Value(v))
    print("filled:",sum(1 for c in HCLASSES for s in HSLOTS if out[c][f'{s[0]},{s[1]}']),
          "/",sum(sum(v[GRADE[c]] for v in NEED.values()) for c in HCLASSES))
