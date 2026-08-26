# -*- coding: utf-8 -*-
# ============================================================
#  solveALL.py - פותר מאוחד: יסודי + חטיבה במודל CP-SAT אחד
#  נוצר אוטומטית ע"י make_unified.py משני הפותרים המקוריים.
#  היתרון: הפותר רואה שרשראות השפעה בין שני בתי הספר -
#  הזזת מורה ביסודי משפיעה מיידית על החטיבה ולהפך.
# ============================================================

# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from data2 import *

NONFRI=[s for s in SLOTS if s[0]!=5]; FRI=[s for s in SLOTS if s[0]==5]
DEU=[c for c in CLASSES if c[0] in "דהו"]; B_CL=[c for c in CLASSES if c.startswith("ב ")]
G_CL=[c for c in CLASSES if c[0]=="ג"]
POOL={"טלי":(3,B_CL),"ליאור":(6,CLASSES),"מרים":(8,CLASSES),"צופיה":(8,[c for c in CLASSES if c[0] in "אבג"]),"שחר":(2,[c for c in CLASSES if c[0] in "אבג"])}
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
ALEF=["א אנה","א פנינה"]
def tb(c):
    b=set()
    subs_c = ["חגית","הילית","יפעת"] if c in ALEF else list(TLN_PAIR[c])
    for sub in subs_c:
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

# צופיה: יום חופש קשיח בחמישי (בהתאם לבקשתה) + שני מתחיל ב-10:00 (משעה 3)
for d in (4,):
    for h in range(1,DAY_HOURS[d]+1):
        for c in CLASSES:
            if (c,(d,h),"צופיה") in x: m.Add(x[(c,(d,h),"צופיה")]==0)
for h in (1,2):
    for c in CLASSES:
        if (c,(1,h),"צופיה") in x: m.Add(x[(c,(1,h),"צופיה")]==0)

# חסן ופאני מורי ספורט: מכסה לכל כיתה קשיחה (שעה נוספת = שיעור ספורט שלישי)
for t in ("חסן","פאני"):
    for c in CLASSES:
        v=[x[(c,s,t)] for s in NONFRI if (c,s,t) in x]
        if v: m.Add(sum(v)==rem.get(t,{}).get(c,0))

# מגבלות ימי עבודה לפי הקובץ: ליאור 3, שחר 3, טלי 2
for _t,_maxd in (("ליאור",3),("שחר",3),("טלי",2)):
    _dv=[]
    for d in range(5):
        b=m.NewBoolVar(f"wd_{_t}_{d}"); _dv.append(b)
        for c in CLASSES:
            for h in range(1,DAY_HOURS[d]+1):
                if (c,(d,h),_t) in x: m.Add(x[(c,(d,h),_t)]<=b)
    m.Add(sum(_dv)<=_maxd)

# שחר: לא בשעה האחרונה של כל יום (מועדונית)
for d in range(5):
    for c in CLASSES:
        k=(c,(d,DAY_HOURS[d]),"שחר")
        if k in x: m.Add(x[k]==0)

# שחר: לא לבוא ליום עם שעה אחת בלבד (0 או 2+)
for d in range(5):
    dh=[x[(c,(d,h),"שחר")] for c in CLASSES for h in range(1,DAY_HOURS[d]+1) if (c,(d,h),"שחר") in x]
    if not dh: continue
    tot=m.NewIntVar(0,len(dh),f"shachar_tot{d}")
    m.Add(tot==sum(dh))
    u=m.NewBoolVar(f"shachar_used{d}")
    m.Add(tot>=2).OnlyEnforceIf(u)
    m.Add(tot==0).OnlyEnforceIf(u.Not())

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
OFF2={"גלית":["שני"],"אלי":["שישי"],"נעמי":["חמישי"],"תמיר":["שלישי"]}
for t in ALLC:
    v=m.NewBoolVar(f"g_{t}"); gm[t]=v
    off=DAYS_OFF2.get(t) or OFF2.get(t,[])
    if "שני" in off:   m.Add(v==0)
    if "שלישי" in off: m.Add(v==1)
m.Add(sum(gm.values())==9)
m.Add(gm["אלי"]==0)      # אלי בקבוצת שלישי - פנוי בשני 3-4 לכיסוי ח
m.Add(gm["נעמי"]==1)     # נעמי בקבוצת שני - פנויה בשלישי 5-6
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

# ---- תיקונים לפי המשוב ----
# דני: 11 בכיתתו + 9 אצל תניה = 20 בדיוק
for c,n in (("ה דני",11),("ה תניה",9)):
    v=[x[(c,s,"דני")] for s in NONFRI if (c,s,"דני") in x]
    fx=sum(1 for (cc,ss),tt in fixed.items() if tt=="דני" and cc==c)
    if v: m.Add(sum(v)==n-fx)
# דניאל: לפחות 17 בכיתה שלו, ולא בכיתות ו
v=[x[("ג דניאל",s,"דניאל")] for s in NONFRI if ("ג דניאל",s,"דניאל") in x]
fx=sum(1 for (cc,ss),tt in fixed.items() if tt=="דניאל" and cc=="ג דניאל")
if v: m.Add(sum(v)>=17-fx)
for c in ("ו שרית","ו אורנה"):
    v=[x[(c,s,"דניאל")] for s in NONFRI if (c,s,"דניאל") in x]
    if v: m.Add(sum(v)<=2)
# צופיה: 2 שעות אנגלית בכל כיתת ג, וסה"כ עד 18
for c,n in (("ג לייה",2),("ג דליה",2),("ג דניאל",3)):
    v=[x[(c,s,"צופיה")] for s in NONFRI if (c,s,"צופיה") in x]
    if v: m.Add(sum(v)==n)
v=[x[(c,s,"צופיה")] for c in CLASSES for s in NONFRI if (c,s,"צופיה") in x]
m.Add(sum(v)<=23-4-6)                   # מכסה 23 פחות שישי ופחות 6 מקבילות
# צופיה: יום חופש חמישי
# שעות מקבילות של צופיה (מצטרפת, לא מחליפה) - גם הן לא בחמישי
co={}
for tag,cls,hr,n in (("anna","א אנה","אנה",4),("pnina","א פנינה","פנינה",1)):
    vs=[]
    for sl in NONFRI:
        b=m.NewBoolVar(f"co{tag}{sl}")
        if sl[0]==4:                              # חמישי חסום לצופיה
            m.Add(b==0); vs.append(b); co[(tag,sl)]=b; continue
        k=(cls,sl,hr)
        if k in x: m.Add(x[k]==1).OnlyEnforceIf(b)
        else:      m.Add(b==0)
        for c2 in CLASSES:                       # אינה יכולה ללמד במקום אחר באותה שעה
            kk=(c2,sl,"צופיה")
            if kk in x: m.Add(x[kk]+b<=1)
        vs.append(b); co[(tag,sl)]=b
    m.Add(sum(vs)==n)
for sl in NONFRI:                                # ולא בשתי מקבילות בו-זמנית
    m.Add(co[("anna",sl)]+co[("pnina",sl)]<=1)

# טלי: יומיים עבודה בלבד
tdays=[]
for d in range(5):
    b=m.NewBoolVar(f"tali{d}"); tdays.append(b)
    for c in CLASSES:
        for h in range(1,DAY_HOURS[d]+1):
            if (c,(d,h),"טלי") in x: m.Add(x[(c,(d,h),"טלי")]<=b)
m.Add(sum(tdays)<=2)
# אורנה: כמה שיותר בכיתה שלה
orna=[x[("ו אורנה",s,"אורנה")] for s in NONFRI if ("ו אורנה",s,"אורנה") in x]

# נעילת שעות אסיף/תמיר ביסודי לימים ראשון/שני בלבד (יציבות מול מודל החטיבה)
for c in CLASSES:
    for s2 in NONFRI:
        if s2[0]==1 and (c,s2,"אסיף") in x: m.Add(x[(c,s2,"אסיף")]==0)   # שני = חופש
        if s2[0] not in (0,1) and (c,s2,"תמיר") in x: m.Add(x[(c,s2,"תמיר")]==0)

# מרים: אפס יסודי בשלישי (שמורה לחטיבה), מקס 2 ביום בשאר הימים
for d in range(5):
    dv=[x[(c,(d,h),"מרים")] for c in CLASSES for h in range(1,DAY_HOURS[d]+1) if (c,(d,h),"מרים") in x]
    if dv: m.Add(sum(dv)<=(0 if d==2 else 2))

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

alef_sub={}
for c in ALEF:
    for s2 in NONFRI:
        for sub in ("הילית","יפעת"):
            alef_sub[(sub,c,s2)]=m.NewBoolVar(f"as_{sub}_{c}_{s2}")
for c in ALEF:
    for s2 in NONFRI:
        k=(c,s2,'תל"ן')
        tot=sum(alef_sub[(sub,c,s2)] for sub in ("הילית","יפעת"))
        if k in x: m.Add(tot==x[k])          # בכל שעת תל"ן בדיוק אחת מהן
        else: m.Add(tot==0)
    for sub in ("הילית","יפעת"):             # כל אחת בשעה אחת בדיוק
        m.Add(sum(alef_sub[(sub,c,s2)] for s2 in NONFRI)==1)

subs=collections.defaultdict(list)
for c in CLASSES:
    _p = ["חגית"] if c in ALEF else list(TLN_PAIR[c])
    for sub in _p: subs[sub].append(c)
# הילית ויפעת בשכבת א: שעה אחת כל אחת - מטופל בנפרד למטה
HL_CLASSES=[c for c in CLASSES if "הילית" in TLN_PAIR[c] and c not in ALEF]
YF_CLASSES=[c for c in CLASSES if "יפעת" in TLN_PAIR[c] and c not in ALEF]
for s in NONFRI:
    for t in set(list(rem)+list(POOL)):
        if t=='תל"ן': continue
        v=[x[(c,s,t)] for c in CLASSES if (c,s,t) in x]
        fx=sum(1 for c in CLASSES if fixed.get((c,s))==t)
        if v: m.Add(sum(v)<=1-fx)
    for sub,cs in subs.items():
        v=[x[(c,s,'תל"ן')] for c in cs if (c,s,'תל"ן') in x]
        if v: m.Add(sum(v)<=1)
    # הילית: כיתות רגילות + לכל היותר אחת מכיתות א באותה שעה
    for sub,base in (("הילית",HL_CLASSES),("יפעת",YF_CLASSES)):
        vv=[x[(c,s,'תל"ן')] for c in base if (c,s,'תל"ן') in x]
        aa=[alef_sub[(sub,c,s)] for c in ALEF if (sub,c,s) in alef_sub]
        if vv or aa: m.Add(sum(vv)+sum(aa)<=1)

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
    if c in ALEF and ps: m.Add(sum(ps)==1)   # חגית שעתיים רצוף בכיתה א
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
        if v:
            if c.startswith("ו "): m.Add(sum(v)==1)
            else: m.Add(sum(v)==0)
# חווה חקלאית: מחנכות ג' עם הכיתה בשני ש1-2 (רך)
farm=[]
for c in FARM_CLASSES:
    for s in FARM_SLOTS:
        k=(c,s,HOMEROOM[c])
        if k in x: farm.append(x[k])
keepg=[gm[t] for t in CIR_MON]+[gm[t].Not() for t in CIR_TUE]
OBJ_E=(-300*sum(orna)+10000*sum(empty.values())+sum(pen)+200*(len(farm)-sum(farm))+400*(len(keepg)-sum(keepg)))

# ---- נעילת סדירויות לפי sed_J.json (החלטות מאושרות) ----
_SEDF=json.load(io.open("sed_J.json",encoding="utf-8"))
for _t in ALLC:
    if _t in _SEDF["קבוצת שני"]:   m.Add(gm[_t]==1)
    elif _t in _SEDF["קבוצת שלישי"]: m.Add(gm[_t]==0)
for _tag,_key in (("m","מעגלי שיח שני"),("u","מעגלי שיח שלישי")):
    _hrs=set(_SEDF[_key])
    for _h in range(1,7):
        if (_tag,_h) in blkh: m.Add(blkh[(_tag,_h)]==(1 if _h in _hrs else 0))

# ---- חסימת מורי חטיבה בצד היסודי לפי ימי החופש והסדירויות שלהם ----
from hdata import HOFF as _HOFF, HEV as _HEV
_MENT=["אלי","גלית","תמיר","נעמי","צבי","רובי"]
for _t in _MENT:
    for _k in [k for k in x if k[2]==_t]:
        _d,_h=_k[1]
        if DAY_NAMES[_d] in _HOFF.get(_t,[]) or (_d,_h) in _HEV.get(_t,[]):
            m.Add(x[_k]==0)


# ================= צד החטיבה (בתוך אותו מודל) =================
# -*- coding: utf-8 -*-
import io, json, collections
from ortools.sat.python import cp_model
from hdata import *
from data2 import CLASSES as ECL, SLOTS as ESL

E=None
HSED=json.load(io.open("sed_J.json",encoding="utf-8"))
hebusy=collections.defaultdict(set)                       # מורה -> משבצות תפוסות ביסודי
pass  # הקישור ליסודי נעשה במודל המאוחד
HCM={"שני":1,"שלישי":2}
for day in ("שני","שלישי"):
    for t in HSED["קבוצת "+day]:
        for h in HSED["מעגלי שיח "+day]: hebusy[t].add((HCM[day],h))
for t in ["לייה","שרית","יערה","צופיה","אסיף"]:
    for h in HSED["ישיבת ניהול שלישי"]: hebusy[t].add((2,h))

def htblk(t):
    b=set(hebusy.get(t,()))
    for dn in HOFF.get(t,[]):
        for h in range(1,8): b.add((DIDX[dn],h))
    for s in HEV.get(t,[]): b.add(s)
    return b

# מודל משותף (מוגדר בצד היסודי)
# ---- חינוך גופני שכבתי: ראשון ש1-3 ורביעי ש4-6, שעה לכל שכבה ----
hpe={}
for d,hrs in PE_BLOCKS.items():
    for g in "זחט":
        for h in hrs: hpe[(g,d,h)]=m.NewBoolVar(f"hpe{g}{d}{h}")
    for g in "זחט": m.Add(sum(hpe[(g,d,h)] for h in hrs)==1)
    for h in hrs:   m.Add(sum(hpe[(g,d,h)] for g in "זחט")==1)

pairs=collections.defaultdict(list)                       # class -> [(subject,teacher)]
for c in HCLASSES:
    g=GRADE[c]
    for subj,per in NEED.items():
        if per[g]==0: continue
        if subj=="חינוך":
            pairs[c].append((subj,HHOME[c]))
            if c=="ז אלי": pairs[c].append((subj,"שיר"))

        elif subj=="שירה בציבור":
            _sing = "שיר" if HHOME[c]=="אלי" else HHOME[c]   # אלי בחופש בשישי - שיר מחליפה
            pairs[c].append((subj,_sing))
        elif subj=="מגמות": pairs[c].append((subj,"מגמות"))
        elif subj=="חינוך גופני": pairs[c].append((subj,"שרית + חסן"))
        else:
            for t in POOLS[subj].get(g,[]): pairs[c].append((subj,t))
hx={}
for c in HCLASSES:
    for (subj,t) in pairs[c]:
        b=set() if t in ("מגמות","שרית + חסן") else htblk(t)
        for s in HSLOTS:
            if s in b: continue
            hx[(c,s,subj,t)]=m.NewBoolVar(f"hx{c}{s}{subj}{t}")

vend={}
vgap={}
hfree={}
for c in HCLASSES:
    for s in HSLOTS:
        f=m.NewBoolVar(f"f{c}{s}"); hfree[(c,s)]=f
        m.Add(sum(hx[(c,s,sj,t)] for (sj,t) in pairs[c] if (c,s,sj,t) in hx)+f==1)
    g=GRADE[c]
    for subj,per in NEED.items():
        if per[g]==0: continue
        v=[hx[(c,s,subj,t)] for s in HSLOTS for (sj,t) in pairs[c] if sj==subj and (c,s,subj,t) in hx]
        m.Add(sum(v)==per[g])

# מגמות: בלוקים קבועים
for c in HCLASSES:
    g=GRADE[c]; blk=MAG_H["ט" if g=="ט" else "ז+ח"]
    for s in HSLOTS:
        k=(c,s,"מגמות","מגמות")
        if k in hx: m.Add(hx[k]==(1 if (s[0]==blk["day"] and s[1] in blk["hours"]) else 0))
# חינוך גופני: לפי הבלוקים השכבתיים
for c in HCLASSES:
    g=GRADE[c]
    for s in HSLOTS:
        k=(c,s,"חינוך גופני","שרית + חסן")
        if k not in hx: continue
        if s in [(d,h) for d,hrs in PE_BLOCKS.items() for h in hrs]:
            m.Add(hx[k]==hpe[(g,s[0],s[1])])
        else: m.Add(hx[k]==0)
# אופיר: שעה אחת בכל כיתת ז, יום שלישי בלבד
for c in HCLASSES:
    for s2 in HSLOTS:
        _k=(c,s2,"העשרה טכנולוגית","אופיר")
        if _k in hx and s2[0]!=2: m.Add(hx[_k]==0)

# מורה חיצוני מתמטיקה: עד 3 ימי עבודה, לא ביום שישי
ext_days=[]
for _d in range(6):
    _b=m.NewBoolVar(f"extm_{_d}"); ext_days.append(_b)
    for c in HCLASSES:
        for _h in range(1,HDAY[_d]+1):
            _k=(c,(_d,_h),"מתמטיקה","מורה חיצוני")
            if _k in hx: m.Add(hx[_k]<=_b)
m.Add(sum(ext_days)<=3)
m.Add(ext_days[5]==0)          # לא בשישי

# ארז: רביעי + חמישי, בכל יום 2 שעות בכל כיתת ז (לא חייב רצוף)
for _c in [c for c in HCLASSES if GRADE[c]=="ז"]:
    for _d in (3,4):
        _v=[hx[(_c,(_d,h),"אנגלית","ארז")] for h in range(1,HDAY[_d]+1) if (_c,(_d,h),"אנגלית","ארז") in hx]
        if _v: m.Add(sum(_v)==2)

# שיר: מחליפה את אלי עם כיתתו בשישי (מגיעה רק ביום זה)
shir_fri=[hx[("ז אלי",(5,h),sj,"שיר")] for h in range(1,5)
          for (sj,t) in pairs["ז אלי"] if t=="שיר" and ("ז אלי",(5,h),sj,"שיר") in hx]
shir_all=[hx[("ז אלי",(5,h),sj,"שיר")] for h in (1,3,4)
          for (sj,t) in pairs["ז אלי"] if t=="שיר" and ("ז אלי",(5,h),sj,"שיר") in hx]
for h in (1,3,4):
    _v=[hx[("ז אלי",(5,h),sj,"שיר")] for (sj,t) in pairs["ז אלי"]
        if t=="שיר" and ("ז אלי",(5,h),sj,"שיר") in hx]
    if _v: m.Add(sum(_v)==1)

# אלי: נוכחות מוגברת בכיתה שלו - תנ"ך ורב מלל בז אלי
eli_own=[hx[("ז אלי",s2,sj,"אלי")] for s2 in HSLOTS
         for (sj,t) in pairs["ז אלי"] if t=="אלי" and sj in ('תנ"ך',"רב מלל","חינוך")
         and ("ז אלי",s2,sj,"אלי") in hx]
_all_eli=[hx[(c,s2,sj,"אלי")] for c in HCLASSES for s2 in HSLOTS
          for (sj,t) in pairs[c] if t=="אלי" and (c,s2,sj,"אלי") in hx]
if _all_eli: m.Add(sum(_all_eli)>=12)
_ch=[hx[("ז אלי",s2,"חינוך","אלי")] for s2 in HSLOTS if ("ז אלי",s2,"חינוך","אלי") in hx]

_tn=[hx[("ז אלי",s2,'תנ"ך',"אלי")] for s2 in HSLOTS if ("ז אלי",s2,'תנ"ך',"אלי") in hx]
if _tn: m.Add(sum(_tn)==2)          # תנ"ך של כיתתו - אלי
_rm=[hx[("ז אלי",s2,"רב מלל","אלי")] for s2 in HSLOTS if ("ז אלי",s2,"רב מלל","אלי") in hx]
if _rm: m.Add(sum(_rm)==3)

# ---- שיעורים משותפים לשתי כיתות ט (ספרות של נעמי, ושיעור של תמיר בשישי) ----
T9=[c for c in HCLASSES if GRADE[c]=="ט"]
litS={}; tjS={}
for s2 in HSLOTS:
    ks=[(c,s2,"רב מלל","נעמי") for c in T9]
    if all(k in hx for k in ks):
        b=m.NewBoolVar(f"lit{s2}")
        for k in ks: m.Add(hx[k]==1).OnlyEnforceIf(b)
        for k in ks: m.Add(hx[k]==0).OnlyEnforceIf(b.Not())
        litS[s2]=b
    else:
        for k in ks:
            if k in hx: m.Add(hx[k]==0)
m.Add(sum(litS.values())==1)
# (בוטל) תמיר אינו מלמד את כל שכבת ט יחד בשישי - כל כיתה עם המחנך שלה

# מורה אחד בכל רגע (כולל מול היסודי)
for s in HSLOTS:
    for t in set(CAP):        # ספורט שכבתי = שתי כיתות יחד, מנוהל ע"י hpe
        v=[hx[(c,s,sj,t)] for c in HCLASSES for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in hx]
        if not v: continue
        allow=[]
        if t=="נעמי" and s in litS: allow.append(litS[s])
        if t=="תמיר": allow += [b for (ss,sj2),b in tjS.items() if ss==s]
        m.Add(sum(v)<=1+sum(allow)) if allow else m.Add(sum(v)<=1)
# תקרות מורים
for t,cap in CAP.items():
    v=[hx[(c,s,sj,t)] for c in HCLASSES for s in HSLOTS for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in hx]
    if v: m.Add(sum(v)<=cap)   # CAP הוא תקציב החטיבה בלבד
# מתמטיקה ז: הדר 8 שעות (4+4 לפי הסדין), צבי משלים 2
hadar=[hx[(c,s,"מתמטיקה","הדר")] for c in HCLASSES for s in HSLOTS if (c,s,"מתמטיקה","הדר") in hx]
# הדר: בדיוק יומיים, בכל יום 2 שעות בכל כיתת ז (2+2)
hd_act={d:m.NewBoolVar(f"hd_day{d}") for d in range(5)}
m.Add(sum(hd_act.values())==2)
for _c in [c for c in HCLASSES if GRADE[c]=="ז"]:
    for d in range(5):
        _v=[hx[(_c,(d,h),"מתמטיקה","הדר")] for h in range(1,HDAY[d]+1) if (_c,(d,h),"מתמטיקה","הדר") in hx]
        if _v: m.Add(sum(_v)==2*hd_act[d])
        else:  m.Add(hd_act[d]==0)
    _tot=[hx[(_c,s,"מתמטיקה","הדר")] for s in HSLOTS if (_c,s,"מתמטיקה","הדר") in hx]
    if _tot: m.Add(sum(_tot)==4)

# מניעת חלונות במערכת של תמיר: השעות שלו רצופות בכל יום
for _t in ("תמיר",):
    for _d in range(6):
        _busy={}
        for _h in range(1,HDAY[_d]+1):
            _v=[hx[(c,(_d,_h),sj,_t)] for c in HCLASSES for (sj,tt) in pairs[c]
                if tt==_t and (c,(_d,_h),sj,_t) in hx]
            if not _v: continue
            _b=m.NewBoolVar(f"nogap_t{_t}{_d}{_h}"); m.AddMaxEquality(_b,_v); _busy[_h]=_b
        _hs=sorted(_busy)
        for _i in range(len(_hs)):
            for _j in range(_i+2,len(_hs)):
                for _k in range(_i+1,_j):          # עסוק ב-i וב-j => עסוק גם באמצע
                    m.Add(_busy[_hs[_i]]+_busy[_hs[_j]]-_busy[_hs[_k]]<=1)

# שירה בציבור: יום שישי שעה 2, כל החטיבה יחד באולם חדר האוכל
for c in HCLASSES:
    for s2 in HSLOTS:
        k=(c,s2,"שירה בציבור","שיר" if HHOME[c]=="אלי" else HHOME[c])
        if k in hx: m.Add(hx[k]==(1 if s2==(5,2) else 0))

# יום שישי: עדיף מחנך הכיתה, אחרת המחנך המקביל
GH2={"ז":["נעמי","אלי"],"ח":["גלית"],"ט":["תמיר","אסיף"]}
fri=[]
for c in HCLASSES:
    for h in range(1,5):
        fri += [hx[(c,(5,h),sj,t)] for (sj,t) in pairs[c]
                if t in GH2[GRADE[c]] and (c,(5,h),sj,t) in hx]

# סידור חדר אוכל: המחנך/ת עם הכיתה בשעה 5, פעם בשבוע, כל כיתה ביום אחר (לא שישי)
duty={}
for c in HCLASSES:
    for d in range(5):
        duty[(c,d)]=m.NewBoolVar(f"duty{c}{d}")
        k=(c,(d,5),"חינוך",HHOME[c])
        opts=[hx[(c,(d,5),sj,t)] for (sj,t) in pairs[c] if t==HHOME[c] and (c,(d,5),sj,t) in hx]
        if opts: m.Add(sum(opts)>=1).OnlyEnforceIf(duty[(c,d)])
        else:    m.Add(duty[(c,d)]==0)
    m.Add(sum(duty[(c,d)] for d in range(5))==1)
for d in range(5):
    m.Add(sum(duty[(c,d)] for c in HCLASSES)<=1)

# אסיף מלמד בשישי עם הכיתה שלו (לפחות שעתיים)
asif_fri=[hx[("ט אסיף",(5,h),sj,"אסיף")] for h in (1,3,4)
          for (sj,t) in pairs["ט אסיף"] if t=="אסיף" and ("ט אסיף",(5,h),sj,"אסיף") in hx]
if asif_fri: m.Add(sum(asif_fri)>=2)

# אסיף: לא מלמד שפה בשעה האחרונה של היום (שעה 6 בסדר)
for c in HCLASSES:
    for d in range(6):
        k=(c,(d,HDAY[d]),"שפה","אסיף")
        if k in hx: m.Add(hx[k]==0)

# מקצועות ליבה: לפחות שיעור כפול אחד בשבוע (שתי שעות רצופות)
CORE=["מתמטיקה","אנגלית","שפה","מדעים"]
for c in HCLASSES:
    for subj in CORE:
        if NEED[subj][GRADE[c]]<2: continue
        ps=[]
        for d in range(6):
            for h in range(1,HDAY[d]):
                a=[hx[(c,(d,h),subj,t)] for (sj,t) in pairs[c] if sj==subj and (c,(d,h),subj,t) in hx]
                b=[hx[(c,(d,h+1),subj,t)] for (sj,t) in pairs[c] if sj==subj and (c,(d,h+1),subj,t) in hx]
                if a and b:
                    pv=m.NewBoolVar(f"dbl{c}{subj}{d}{h}")
                    m.Add(sum(a)==1).OnlyEnforceIf(pv); m.Add(sum(b)==1).OnlyEnforceIf(pv)
                    ps.append(pv)
        if ps: m.Add(sum(ps)>=1)

# החטיבה מסיימת לא לפני שעה 5 (למעט שישי שהוא בן 4 שעות)
vend={}
for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            if d==2 and GRADE[c]=="ט": m.Add(hfree[(c,(d,h))]==0)   # ט: שלישי עד 6 חובה
            else:
                _w = 2500 if d==2 else 1               # שלישי כמעט-חובה לשאר
                b=m.NewBoolVar(f"ve{c}{d}{h}"); m.Add(hfree[(c,(d,h))]<=b); vend[(c,d,h,_w)]=b

# אין חלונות באמצע היום - חלון רק בסוף
for c in HCLASSES:
    for d in range(6):
        for h in range(1,HDAY[d]):
            m.AddImplication(hfree[(c,(d,h))], hfree[(c,(d,h+1))])

# פיזור: לא יותר מ-2 שעות של אותו מקצוע ביום (חוץ ממגמות/ספורט)
for c in HCLASSES:
    for subj in NEED:
        if subj in ("מגמות","חינוך גופני"): continue
        for d in range(6):
            v=[hx[(c,(d,h),subj,t)] for h in range(1,HDAY[d]+1) for (sj,t) in pairs[c] if sj==subj and (c,(d,h),subj,t) in hx]
            if v: m.Add(sum(v)<=2)
# עדיף לסיים מוקדם: קנס על שעות מאוחרות
late=[]
for c in HCLASSES:
    for (d,h) in HSLOTS:
        if h>=6: late.append(hfree[(c,(d,h))].Not())
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
            v=[hx[(c,s,subj,t)] for s in HSLOTS if (c,s,subj,t) in hx]
            if v:
                m.AddMaxEquality(u,v); us.append(u)
        if us:
            n=m.NewIntVar(0,len(us),f"n{c}{subj}"); m.Add(n==sum(us)); split.append(n)

# עדיף שהמחנך/ת ילמד/תלמד רב מלל בכיתה שלו/ה
own=[hx[(c,s,"רב מלל",HHOME[c])] for c in HCLASSES for s in HSLOTS
     if (c,s,"רב מלל",HHOME[c]) in hx]
# עדיף מחנך מאותה שכבה (המקביל) על פני מורה משכבה אחרת
GH={"ז":["נעמי","אלי"],"ח":["גלית"],"ט":["תמיר","אסיף"]}
same=[]
for c in HCLASSES:
    for (sj,t) in pairs[c]:
        if sj in ("מגמות","חינוך גופני","חינוך"): continue
        if t in GH[GRADE[c]]:
            same += [hx[(c,s,sj,t)] for s in HSLOTS if (c,s,sj,t) in hx]
OBJ_H=(sum(400*_k[3]*_v for _k,_v in vend.items())+5*sum(late) - 80*sum(eli_own) - 150*sum(fri) - 50*sum(hadar) - 200*sum(own) - 120*sum(same) + 60*sum(split))
# חייב למלא בדיוק את מספר השעות -> hfree נקבע ע"י האילוצים


# ================= קישור צולב: מורה אחד בכל רגע =================
_ET=set(k[2] for k in x); _HT=set(k[3] for k in hx)
CROSS=sorted(_ET & _HT)
_nlink=0
for _t in CROSS:
    for _d in range(6):
        for _h in range(1,8):
            _ev=[x[k] for k in x  if k[2]==_t and k[1]==(_d,_h)]
            _hv=[hx[k] for k in hx if k[3]==_t and k[1]==(_d,_h)]
            if _ev and _hv:
                m.Add(sum(_ev)+sum(_hv)<=1); _nlink+=1
print(f"קישור צולב: {len(CROSS)} מורים משותפים, {_nlink} אילוצי בו-זמניות")

# ---- תקרה כוללת אמיתית (יסודי+חטיבה) למורים המשותפים ----
_MAG={"אסיף":4,"אלי":2,"חסן":6,"שרית":2,"רובי":2,"מאמי":4,"יעל":4,"חגית":2,"אופיר":2}
_QUOTA={"אלי":20,"גלית":20,"תמיר":24,"נעמי":20,"צבי":12,"רובי":6,
        "מרים":23,"לייה":23,"אסיף":20,"שרית":28,"חסן":26}
_TOTCAP={t:q-_MAG.get(t,0) for t,q in _QUOTA.items()}   # מכסה פחות שעות המגמה
for _t,_capv in _TOTCAP.items():
    _ev=[x[k] for k in x  if k[2]==_t]
    _hv=[hx[k] for k in hx if k[3]==_t]
    if _ev or _hv: m.Add(sum(_ev)+sum(_hv)<=_capv)

# ---- NOGAP_CROSS: בלי חלונות למורים נבחרים, על פני שני בתי הספר ----
for _t in ("תמיר",):
    for _d in range(6):
        _busy={}
        for _h in range(1,8):
            _v =[x[k]  for k in x  if k[2]==_t and k[1]==(_d,_h)]
            _v+=[hx[k] for k in hx if k[3]==_t and k[1]==(_d,_h)]
            if not _v: continue
            _b=m.NewBoolVar(f"ng_{_t}_{_d}_{_h}"); m.AddMaxEquality(_b,_v); _busy[_h]=_b
        _hs=sorted(_busy)
        for _i in range(len(_hs)):
            for _j in range(_i+2,len(_hs)):
                for _kk in range(_i+1,_j):
                    m.Add(_busy[_hs[_i]]+_busy[_hs[_j]]-_busy[_hs[_kk]]<=1)

# ---- PARALLEL_EQ: כיתות מקבילות מסיימות באותה שעה בכל יום ----
import collections as _cl
_bygrade=_cl.defaultdict(list)
for _c in HCLASSES: _bygrade[GRADE[_c]].append(_c)
_neq=0
for _g,_cs in _bygrade.items():
    if len(_cs)<2: continue
    for _d in range(6):
        _tot=[]
        for _c in _cs:
            _v=[hx[k] for k in hx if k[0]==_c and k[1][0]==_d]
            _iv=m.NewIntVar(0,HDAY[_d],f"pq_{_c}_{_d}")
            m.Add(_iv==sum(_v)); _tot.append(_iv)
        for _i in range(1,len(_tot)):
            m.Add(_tot[0]==_tot[_i]); _neq+=1
print(f"שוויון מקבילות: {_neq} אילוצים")

# ---- WARM START: רמז מהפתרון הקודם -> פתרון מהיר בהרבה ----
_H={}
try:
    _pE=json.load(io.open("sol_J.json",encoding="utf-8"))
    for k,v in x.items():
        _c,(_d,_h),_t = k
        _H[v.Index()]=(v, 1 if _pE.get(_c,{}).get(f"{_d},{_h}")==_t else 0)
    _pH=json.load(io.open("sol_hat.json",encoding="utf-8"))
    for k,v in hx.items():
        _c,(_d,_h),_sj,_t = k
        _H[v.Index()]=(v, 1 if _pH.get(_c,{}).get(f"{_d},{_h}")==f"{_sj} – {_t}" else 0)
    pass  # warm start מבוטל זמנית
    print(f"warm start: {len(_H)} רמזים")
except Exception as _e:
    print("ללא warm start:",_e)

# ================= מטרה משולבת + פתרון =================
m.Minimize(OBJ_E + OBJ_H)
sol=cp_model.CpSolver()
import os as _os
sol.parameters.max_time_in_seconds=float(_os.environ.get("TL","150"))
sol.parameters.num_search_workers=8
sol.parameters.relative_gap_limit=0.02
sol.parameters.num_workers=8
sol.parameters.random_seed=7

_v=m.Validate()
io.open('valerr.txt','w',encoding='utf-8').write(_v[:3000] if _v else 'MODEL OK')
st=sol.Solve(m)
print("status:", sol.StatusName(st))

if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    print("obj:",sol.ObjectiveValue(),"empty:",sum(sol.Value(v) for v in empty.values()))
    print("farm ok:",sum(sol.Value(v) for v in farm),"/",len(farm))
    peh={d:[h for h in range(1,DAY_HOURS[d]+1) if sol.Value(pe[(d,h)])] for d in (0,3)}
    print("ספורט חטיבה: ראשון",peh[0],"| רביעי",peh[3]);print("יום חופש צופיה: חמישי (קבוע)")
    mb=[h for h in range(1,7) if sol.Value(blkh[("m",h)])]
    ub=[h for h in range(1,7) if sol.Value(blkh[("u",h)])]
    nbh=[h for h in range(1,7) if sol.Value(nb[h])]
    io.open("sed_J.json","w",encoding="utf-8").write(json.dumps(
      {"מעגלי שיח שני":mb,"מעגלי שיח שלישי":ub,"ישיבת ניהול שלישי":nbh,
       "קבוצת שני":sorted(t for t in ALLC if sol.Value(gm[t])),"קבוצת שלישי":sorted(t for t in ALLC if not sol.Value(gm[t]))},ensure_ascii=False,indent=1))
    out={c:{f"{s[0]},{s[1]}":(fixed[(c,s)] if s[0]==5 else
        next((t for t in allowed[c] if (c,s,t) in x and sol.Value(x[(c,s,t)])),"")) for s in SLOTS} for c in CLASSES}
    tlnmap={}
    for c in CLASSES:
        for s2 in NONFRI:
            k=(c,s2,'תל"ן')
            if k in x and sol.Value(x[k]):
                if c in ALEF:
                    other=[sub for sub in ("הילית","יפעת") if sol.Value(alef_sub[(sub,c,s2)])]
                    tlnmap[f"{c}|{s2[0]},{s2[1]}"]="חגית + "+(other[0] if other else "?")
                else:
                    tlnmap[f"{c}|{s2[0]},{s2[1]}"]=" + ".join(TLN_PAIR[c])
    io.open("tln_map.json","w",encoding="utf-8").write(json.dumps(tlnmap,ensure_ascii=False,indent=1))
    io.open("co_zofia3.json","w",encoding="utf-8").write(json.dumps(
        {tag+"|"+f"{sl[0]},{sl[1]}":1 for (tag,sl),b in co.items() if sol.Value(b)},ensure_ascii=False))
    io.open("sol_J.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    io.open("pe_blocks.json","w",encoding="utf-8").write(json.dumps(peh,ensure_ascii=False))
    dev=[]
    for c in CLASSES:
        cnt=collections.Counter(out[c].values())
        for t in sorted(set(list(cnt)+[k for k,v in QUOTA.items() if c in v])):
            g,tg=cnt.get(t,0),QUOTA.get(t,{}).get(c,0)
            if g!=tg: dev.append(f"{c} | {t} | בסדין {tg} | בפועל {g} | {g-tg:+d}")
    io.open("dev_J.txt","w",encoding="utf-8").write("\n".join(dev))
    print("deviations:",len(dev))


# ================= פלט צד החטיבה =================
if st in (cp_model.OPTIMAL,cp_model.FEASIBLE):
    out={}
    for c in HCLASSES:
        out[c]={}
        for s in HSLOTS:
            got=[(sj,t) for (sj,t) in pairs[c] if (c,s,sj,t) in hx and sol.Value(hx[(c,s,sj,t)])]
            out[c][f"{s[0]},{s[1]}"]= (f"{got[0][0]} – {got[0][1]}" if got else "")
    io.open("sol_hat.json","w",encoding="utf-8").write(json.dumps(out,ensure_ascii=False,indent=1))
    peo={f"{DAY_NAMES[d]} ש{h}":g for (g,d,h) in hpe if sol.Value(hpe[(g,d,h)])}
    io.open("duty.json","w",encoding="utf-8").write(json.dumps(
        {c:DAY_NAMES[[d for d in range(5) if sol.Value(duty[(c,d)])][0]] for c in HCLASSES},
        ensure_ascii=False,indent=1))
    io.open("pe_hat.json","w",encoding="utf-8").write(json.dumps(peo,ensure_ascii=False,indent=1))
    io.open("viol_report.txt","w",encoding="utf-8").write(chr(10).join(
        [f"מסיים מוקדם: {c} {DAY_NAMES[d]} ש{h}" for (c,d,h,_w2),v in sorted(vend.items()) if sol.Value(v)]) or "אין חריגות")
    print("filled:",sum(1 for c in HCLASSES for s in HSLOTS if out[c][f'{s[0]},{s[1]}']),
          "/",sum(sum(v[GRADE[c]] for v in NEED.values()) for c in HCLASSES))


# ================= fills.json: תאי כיסוי (לצביעה באקסל) =================
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    _S=json.load(io.open("sol_J.json",encoding="utf-8"))
    _FILLSET={"אלי","גלית","תמיר","נעמי","צבי","רובי"}
    _fills={}
    for _c in CLASSES:
        for (_d,_h) in SLOTS:
            _t=_S[_c][f"{_d},{_h}"]
            if _t in _FILLSET:
                _fills[f"{_c}|{_d},{_h}"]=_t
    io.open("fills.json","w",encoding="utf-8").write(json.dumps(_fills,ensure_ascii=False,indent=1))
    print("fills:",len(_fills),"תאי כיסוי ממורי חטיבה")
