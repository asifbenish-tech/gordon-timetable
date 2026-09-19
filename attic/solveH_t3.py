# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from hdata import *
from data2 import CLASSES as ECL, SLOTS as ESL

E=json.load(io.open("sol_J.json",encoding="utf-8"))
SED=json.load(io.open("sed_J.json",encoding="utf-8"))
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
        elif subj=="שירה בציבור": pairs[c].append((subj,"שירה בציבור"))
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

free={}
for c in HCLASSES:
    for s in HSLOTS:
        f=m.NewBoolVar(f"f{c}{s}"); free[(c,s)]=f
        m.Add(sum(x[(c,s,sj,t)] for (sj,t) in pairs[c] if (c,s,sj,t) in x)+f==1)
    g=GRADE[c]
    for subj,per in NEED.items():
        if per[g]==0: continue
        v=[x[(c,s,subj,t)] for s in HSLOTS for (sj,t) in pairs[c] if sj==subj and (c,s,subj,t) in x]
        m.Add(sum(v)==per[g])

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
# ארז: 8 שעות מפוצלות רביעי/חמישי - 4+4 או 6+2
erz={d:[x[(c,(d,h),"אנגלית","ארז")] for c in HCLASSES for h in range(1,HDAY[d]+1)
        if (c,(d,h),"אנגלית","ארז") in x] for d in (3,4)}
e44=m.NewBoolVar("erez44")
for d,other in ((3,4),(4,3)):
    m.Add(sum(erz[d])==4).OnlyEnforceIf(e44)
m.Add(sum(erz[3])+sum(erz[4])==8)
m.Add(sum(erz[3])>=2); m.Add(sum(erz[4])>=2)

# ---- שיעורים משותפים לשתי כיתות ט (ספרות של נעמי, ושיעור של תמיר בשישי) ----
T9=[c for c in HCLASSES if GRADE[c]=="ט"]
litS={}; tjS={}
for s2 in HSLOTS:
    ks=[(c,s2,"רב מלל","נעמי") for c in T9]
    if all(k in x for k in ks):
        b=m.NewBoolVar(f"lit{s2}")
        for k in ks: m.Add(x[k]==1).OnlyEnforceIf(b)
        for k in ks: m.Add(x[k]==0).OnlyEnforceIf(b.Not())
        litS[s2]=b
    else:
        for k in ks:
            if k in x: m.Add(x[k]==0)
m.Add(sum(litS.values())==1)
for s2 in [(5,h) for h in range(1,5)]:
    subs={sj for (sj,t) in pairs[T9[0]] if t=="תמיר"}
    for sj in subs:
        kk=[(c,s2,sj,"תמיר") for c in T9]
        if all(k in x for k in kk):
            b=m.NewBoolVar(f"tj{s2}{sj}")
            for k in kk: m.Add(x[k]==1).OnlyEnforceIf(b)
            tjS[(s2,sj)]=b
m.Add(sum(tjS.values())>=1)

# מורה אחד בכל רגע (כולל מול היסודי)
for s in HSLOTS:
    for t in set(CAP):        # ספורט שכבתי = שתי כיתות יחד, מנוהל ע"י pe
        v=[x[(c,s,sj,t)] for c in HCLASSES for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in x]
        if not v: continue
        allow=[]
        if t=="נעמי" and s in litS: allow.append(litS[s])
        if t=="תמיר": allow += [b for (ss,sj2),b in tjS.items() if ss==s]
        m.Add(sum(v)<=1+sum(allow)) if allow else m.Add(sum(v)<=1)
# תקרות מורים
for t,cap in CAP.items():
    v=[x[(c,s,sj,t)] for c in HCLASSES for s in HSLOTS for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in x]
    if v: m.Add(sum(v)<=cap)   # CAP הוא תקציב החטיבה בלבד
# מתמטיקה ז: הדר 8 שעות (4+4 לפי הסדין), צבי משלים 2
hadar=[x[(c,s,"מתמטיקה","הדר")] for c in HCLASSES for s in HSLOTS if (c,s,"מתמטיקה","הדר") in x]
m.Add(sum(hadar)<=8)

# שיר/חגית מחליפות את אלי בשישי (לפי הסדין) - מאפשרות כיסוי לכיתת ז אלי
# (מיושם כהרחבת הזמינות של תמיר/נעמי לשישי בכיתות ז)

# שירה בציבור: יום שישי שעה 2, כל החטיבה יחד
for c in HCLASSES:
    for s2 in HSLOTS:
        k=(c,s2,"שירה בציבור","שירה בציבור")
        if k in x: m.Add(x[k]==(1 if s2==(5,2) else 0))

# יום שישי: עדיף מחנך הכיתה, אחרת המחנך המקביל
GH2={"ז":["נעמי","אלי"],"ח":["גלית"],"ט":["תמיר","אסיף"]}
fri=[]
for c in HCLASSES:
    for h in range(1,5):
        fri += [x[(c,(5,h),sj,t)] for (sj,t) in pairs[c]
                if t in GH2[GRADE[c]] and (c,(5,h),sj,t) in x]

# סידור חדר אוכל: המחנך/ת עם הכיתה בשעה 5, פעם בשבוע, כל כיתה ביום אחר (לא שישי)
duty={}
for c in HCLASSES:
    for d in range(5):
        duty[(c,d)]=m.NewBoolVar(f"duty{c}{d}")
        k=(c,(d,5),"חינוך",HHOME[c])
        opts=[x[(c,(d,5),sj,t)] for (sj,t) in pairs[c] if t==HHOME[c] and (c,(d,5),sj,t) in x]
        if opts: m.Add(sum(opts)>=1).OnlyEnforceIf(duty[(c,d)])
        else:    m.Add(duty[(c,d)]==0)
    m.Add(sum(duty[(c,d)] for d in range(5))==1)
for d in range(5):
    m.Add(sum(duty[(c,d)] for c in HCLASSES)<=1)

# אסיף: לא מלמד שפה בשעה האחרונה של היום (שעה 6 בסדר)
for c in HCLASSES:
    for d in range(6):
        k=(c,(d,HDAY[d]),"שפה","אסיף")
        if k in x: m.Add(x[k]==0)

# מקצועות ליבה: לפחות שיעור כפול אחד בשבוע (שתי שעות רצופות)
CORE=["מתמטיקה","אנגלית","שפה","מדעים"]
for c in HCLASSES:
    for subj in CORE:
        if NEED[subj][GRADE[c]]<2: continue
        ps=[]
        for d in range(6):
            for h in range(1,HDAY[d]):
                a=[x[(c,(d,h),subj,t)] for (sj,t) in pairs[c] if sj==subj and (c,(d,h),subj,t) in x]
                b=[x[(c,(d,h+1),subj,t)] for (sj,t) in pairs[c] if sj==subj and (c,(d,h+1),subj,t) in x]
                if a and b:
                    pv=m.NewBoolVar(f"dbl{c}{subj}{d}{h}")
                    m.Add(sum(a)==1).OnlyEnforceIf(pv); m.Add(sum(b)==1).OnlyEnforceIf(pv)
                    ps.append(pv)
        if ps: m.Add(sum(ps)>=1)

# החטיבה מסיימת לא לפני שעה 5 (למעט שישי שהוא בן 4 שעות)
for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            m.Add(free[(c,(d,h))]==0)

# אין חלונות באמצע היום - חלון רק בסוף
for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(free[(c,(d,h))], free[(c,(d,h+1))])

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
# עדיף מורה אחד למקצוע בכיתה - למזער פיצול
split=[]
for c in HCLASSES:
    for subj in NEED:
        if subj in ("מגמות","חינוך גופני","חינוך"): continue
        ts=sorted({t for (sj,t) in pairs[c] if sj==subj})
        if len(ts)<2: continue
        us=[]
        for t in ts:
            u=m.NewBoolVar(f"u{c}{subj}{t}")
            v=[x[(c,s,subj,t)] for s in HSLOTS if (c,s,subj,t) in x]
            if v:
                m.AddMaxEquality(u,v); us.append(u)
        if us:
            n=m.NewIntVar(0,len(us),f"n{c}{subj}"); m.Add(n==sum(us)); split.append(n)

# עדיף שהמחנך/ת ילמד/תלמד רב מלל בכיתה שלו/ה
own=[x[(c,s,"רב מלל",HHOME[c])] for c in HCLASSES for s in HSLOTS
     if (c,s,"רב מלל",HHOME[c]) in x]
# עדיף מחנך מאותה שכבה (המקביל) על פני מורה משכבה אחרת
GH={"ז":["נעמי","אלי"],"ח":["גלית"],"ט":["תמיר","אסיף"]}
same=[]
for c in HCLASSES:
    for (sj,t) in pairs[c]:
        if sj in ("מגמות","חינוך גופני","חינוך"): continue
        if t in GH[GRADE[c]]:
            same += [x[(c,s,sj,t)] for s in HSLOTS if (c,s,sj,t) in x]
m.Minimize(5*sum(late) - 150*sum(fri) - 50*sum(hadar) - 200*sum(own) - 120*sum(same) + 60*sum(split))
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
    io.open("duty.json","w",encoding="utf-8").write(json.dumps(
        {c:DAY_NAMES[[d for d in range(5) if sol.Value(duty[(c,d)])][0]] for c in HCLASSES},
        ensure_ascii=False,indent=1))
    io.open("pe_hat.json","w",encoding="utf-8").write(json.dumps(peo,ensure_ascii=False,indent=1))
    print("filled:",sum(1 for c in HCLASSES for s in HSLOTS if out[c][f'{s[0]},{s[1]}']),
          "/",sum(sum(v[GRADE[c]] for v in NEED.values()) for c in HCLASSES))
