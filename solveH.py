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
for t in ["לייה","שרית","יערה","צופיה","אסיף","אלי"]:
    for h in SED["ישיבת ניהול שלישי"]: ebusy[t].add((2,h))

ebusy["אלי"].discard((CM["שלישי"],5))
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
        if subj=="חינוך":
            pairs[c].append((subj,HHOME[c]))
            if c=="ז אלי": pairs[c].append((subj,"שיר"))


        elif subj=="שירה בציבור":
            _sing = HHOME[c]
            if HHOME[c]=="אלי": _sing="שיר"          # אלי בחופש בשישי
            if c=="ט אסיף":     _sing="חסר מורה"      # שישי בכיתת אסיף: ללא מורה עד גיוס
            pairs[c].append((subj,_sing))
        elif subj=="מגמות": pairs[c].append((subj,"מגמות"))
        elif subj=="חינוך גופני": pairs[c].append((subj,"שרית + חסן"))
        else:
            for t in POOLS[subj].get(g,[]): pairs[c].append((subj,t))
# MISSING_FRI: ט אסיף בשישי - אסיף בחופש ואין מורה. השעות מסומנות "חסר מורה".
_MC="ט אסיף"
for _c9 in HCLASSES:
    for _sj in sorted({sj for (sj,_t) in pairs[_c9] if _t not in ("מגמות","שרית + חסן")}):
        if (_sj,"חסר מורה") not in pairs[_c9]: pairs[_c9].append((_sj,"חסר מורה"))

x={}
for c in HCLASSES:
    for (subj,t) in pairs[c]:
        b=set() if t in ("מגמות","שרית + חסן") else tblk(t)
        for s in HSLOTS:
            if s in b: continue
            x[(c,s,subj,t)]=m.NewBoolVar(f"x{c}{s}{subj}{t}")

vend={}
vgap={}
free={}
for c in HCLASSES:
    for s in HSLOTS:
        f=m.NewBoolVar(f"f{c}{s}"); free[(c,s)]=f
        m.Add(sum(x[(c,s,sj,t)] for (sj,t) in pairs[c] if (c,s,sj,t) in x)+f==1)
    g=GRADE[c]
    for subj,per in NEED.items():
        if per[g]==0: continue
        v=[x[(c,s,subj,t)] for s in HSLOTS for (sj,t) in pairs[c] if sj==subj and (c,s,subj,t) in x]
        _ovr={("ט אסיף","חינוך"):4,("ט אסיף","מתמטיקה"):3}
        m.Add(sum(v)==_ovr.get((c,subj),per[g]))

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
# אופיר: שעה אחת בכל כיתת ז, יום שלישי בלבד
for c in HCLASSES:
    for s2 in HSLOTS:
        _k=(c,s2,"העשרה טכנולוגית","אופיר")
        if _k in x and s2[0]!=2: m.Add(x[_k]==0)

# מורה חיצוני מתמטיקה: עד 3 ימי עבודה, לא ביום שישי
ext_days=[]
for _d in range(6):
    _b=m.NewBoolVar(f"extm_{_d}"); ext_days.append(_b)
    for c in HCLASSES:
        for _h in range(1,HDAY[_d]+1):
            _k=(c,(_d,_h),"מתמטיקה","מורה חיצוני")
            if _k in x: m.Add(x[_k]<=_b)
m.Add(sum(ext_days)<=3)
m.Add(ext_days[5]==0)          # לא בשישי

# ארז: רביעי + חמישי, בכל יום 2 שעות בכל כיתת ז (לא חייב רצוף)
for _c in [c for c in HCLASSES if GRADE[c]=="ז"]:
    for _d in (3,4):
        _v=[x[(_c,(_d,h),"אנגלית","ארז")] for h in range(1,HDAY[_d]+1) if (_c,(_d,h),"אנגלית","ארז") in x]
        if _v: m.Add(sum(_v)==2)

# שיר: מחליפה את אלי עם כיתתו בשישי (מגיעה רק ביום זה)
shir_fri=[x[("ז אלי",(5,h),sj,"שיר")] for h in range(1,5)
          for (sj,t) in pairs["ז אלי"] if t=="שיר" and ("ז אלי",(5,h),sj,"שיר") in x]
shir_all=[x[("ז אלי",(5,h),sj,"שיר")] for h in (1,3,4)
          for (sj,t) in pairs["ז אלי"] if t=="שיר" and ("ז אלי",(5,h),sj,"שיר") in x]
if shir_all: m.Add(sum(shir_all)>=2)   # שיר עם הכיתה בשישי, לפחות שעתיים

# גלית: שני שיעורים משותפים עם ארז בכיתות ז (נספר במכסה שלה)
gj={}
for c in [c for c in HCLASSES if GRADE[c]=="ז"]:
    for h in range(1,HDAY[3]+1):
        if (3,h) in HEV.get("גלית",[]): continue
        _ke=(c,(3,h),"אנגלית","ארז")
        if _ke in x:
            b=m.NewBoolVar(f"gj{c}{h}")
            m.Add(b<=x[_ke])                       # רק כשארז מלמד שם
            gj[(c,h)]=b
for _zc in [c for c in HCLASSES if GRADE[c]=="ז"]:
    _zv=[b for (c2,h2),b in gj.items() if c2==_zc]
    if _zv: m.Add(sum(_zv)==1)                    # שעה אחת בכל כיתת ז
m.Add(sum(gj.values())==2)
for h in range(1,HDAY[3]+1):                        # לא כשגלית מלמדת בעצמה
    _gv=[x[k] for k in x if k[3]=="גלית" and k[1]==(3,h)]
    _gh=[b for (c2,h2),b in gj.items() if h2==h]
    if _gv and _gh: m.Add(sum(_gv)+sum(_gh)<=1)
_gx=[x[k] for k in x if k[3]=="גלית"]
m.Add(sum(_gx)+sum(gj.values())<=CAP["גלית"])       # נספר במכסה

# אלי: נוכחות מוגברת בכיתה שלו - תנ"ך ורב מלל בז אלי
eli_own=[x[("ז אלי",s2,sj,"אלי")] for s2 in HSLOTS
         for (sj,t) in pairs["ז אלי"] if t=="אלי" and sj in ('תנ"ך',"רב מלל","חינוך")
         and ("ז אלי",s2,sj,"אלי") in x]
_all_eli=[x[(c,s2,sj,"אלי")] for c in HCLASSES for s2 in HSLOTS
          for (sj,t) in pairs[c] if t=="אלי" and (c,s2,sj,"אלי") in x]
if _all_eli: m.Add(sum(_all_eli)>=8)   # ירד מ-12: שכבת ט סגורה בפניו
_ch=[x[("ז אלי",s2,"חינוך","אלי")] for s2 in HSLOTS if ("ז אלי",s2,"חינוך","אלי") in x]

_tn=[x[("ז אלי",s2,'תנ"ך',"אלי")] for s2 in HSLOTS if ("ז אלי",s2,'תנ"ך',"אלי") in x]
if _tn: m.Add(sum(_tn)==2)          # תנ"ך של כיתתו - אלי
_rm=[x[("ז אלי",s2,"רב מלל","אלי")] for s2 in HSLOTS if ("ז אלי",s2,"רב מלל","אלי") in x]
if _rm: m.Add(sum(_rm)==3)

# ---- שיעורים משותפים לשתי כיתות ט (ספרות של נעמי, ושיעור של תמיר בשישי) ----
T9=[c for c in HCLASSES if GRADE[c]=="ט"]
litS={}; tjS={}
# ספרות נעמי: שעה נפרדת בכל כיתת ט (לא מאוחד) - האכיפה הכמותית ב-rules_rm
# שיעור כפול: תמיר מלמד את שתי כיתות ט יחד בשעה אחת בשישי (2 מהמכסה)
for s2 in [(5,h) for h in (1,3,4)]:
    subs={sj for (sj,t) in pairs[T9[0]] if t=="תמיר"} & {sj for (sj,t) in pairs[T9[1]] if t=="תמיר"}
    for sj in sorted(subs):
        kk=[(c,s2,sj,"תמיר") for c in T9]
        if all(k in x for k in kk):
            b=m.NewBoolVar(f"tj{s2}{sj}")
            for k in kk: m.Add(x[k]==1).OnlyEnforceIf(b)
            tjS[(s2,sj)]=b
m.Add(sum(tjS.values())==0)   # בוטל: תמיר בשישי רק עם כיתתו

# מורה אחד בכל רגע (כולל מול היסודי)
for s in HSLOTS:
    for t in set(CAP):        # ספורט שכבתי = שתי כיתות יחד, מנוהל ע"י pe
        v=[x[(c,s,sj,t)] for c in HCLASSES for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in x]
        if not v: continue
        allow=[]
        if t=="נעמי" and s in litS: allow.append(litS[s])
        if t=="תמיר":
            allow += [b for (ss,sj2),b in tjS.items() if ss==s]
            if s==(5,2): allow.append(1)          # שירה בציבור כפולה
        m.Add(sum(v)<=1+sum(allow)) if allow else m.Add(sum(v)<=1)
# תקרות מורים
for t,cap in CAP.items():
    v=[x[(c,s,sj,t)] for c in HCLASSES for s in HSLOTS for (sj,tt) in pairs[c] if tt==t and (c,s,sj,t) in x]
    if v: m.Add(sum(v)<=cap)   # CAP הוא תקציב החטיבה בלבד
# מתמטיקה ז: הדר 8 שעות (4+4 לפי הסדין), צבי משלים 2
hadar=[x[(c,s,"מתמטיקה","הדר")] for c in HCLASSES for s in HSLOTS if (c,s,"מתמטיקה","הדר") in x]
# הדר: בדיוק יומיים, בכל יום 2 שעות בכל כיתת ז (2+2)
# הדר מפוצלת: שעה בכל כיתת ז בשלישי 5-6, והיתרה ביומיים (2-3 ימי עבודה)
for _c in [c for c in HCLASSES if GRADE[c]=="ז"]:
    _tot=[x[(_c,s,"מתמטיקה","הדר")] for s in HSLOTS if (_c,s,"מתמטיקה","הדר") in x]
    if _tot: m.Add(sum(_tot)==4)
hd_act={d:m.NewBoolVar(f"hd_day{d}") for d in range(5)}
for d in range(5):
    _v=[x[(_c2,(d,h),"מתמטיקה","הדר")] for _c2 in HCLASSES if GRADE[_c2]=="ז"
        for h in range(1,HDAY[d]+1) if (_c2,(d,h),"מתמטיקה","הדר") in x]
    if _v:
        for _vv in _v: m.Add(_vv<=hd_act[d])
        m.Add(sum(_v)>=2*hd_act[d])               # יום פעיל = לפחות שעתיים
    else: m.Add(hd_act[d]==0)
m.Add(sum(hd_act.values())<=3)

# מניעת חלונות במערכת של תמיר: השעות שלו רצופות בכל יום
for _t in ("תמיר",):
    for _d in range(6):
        _busy={}
        for _h in range(1,HDAY[_d]+1):
            _v=[x[(c,(_d,_h),sj,_t)] for c in HCLASSES for (sj,tt) in pairs[c]
                if tt==_t and (c,(_d,_h),sj,_t) in x]
            if not _v: continue
            _b=m.NewBoolVar(f"nogap_t{_t}{_d}{_h}"); m.AddMaxEquality(_b,_v); _busy[_h]=_b
        _hs=sorted(_busy)
        for _i in range(len(_hs)):
            for _j in range(_i+2,len(_hs)):
                for _k in range(_i+1,_j):          # עסוק ב-i וב-j => עסוק גם באמצע
                    m.Add(_busy[_hs[_i]]+_busy[_hs[_j]]-_busy[_hs[_k]]<=1)

# "חסר מורה": רק בט אסיף, רק בשישי, בדיוק 4 שעות
# ט אסיף בשישי: אסיף בחופש -> בדיוק 4 שעות חסרות
# בט אסיף חסר מורה נרשם כחינוך בלבד (miss_hinuch)
for _k in [k for k in x if k[0]==_MC and k[3]=="חסר מורה" and k[2]!="חינוך" and k[1][0]!=5]:
    m.Add(x[_k]==0)
# אנגלית=גלית ושפה=נעמי/אסיף - חסר מורה אסור בהן (no_miss_eng)
for _k in [k for k in x if k[3]=="חסר מורה" and k[2] in ("אנגלית","שפה")]:
    m.Add(x[_k]==0)
_miss_fri=[x[k] for k in x if k[3]=="חסר מורה" and k[0]==_MC and k[1][0]==5]
if _miss_fri: m.Add(sum(_miss_fri)==4)   # כל שישי בכיתת אסיף ללא מורה   # תמיר מכסה 2 (שירה + כפול)
for _k in [k for k in x if k[3]=="חסר מורה" and k[1][0]==5 and k[0]!=_MC]:
    m.Add(x[_k]==0)                      # בשאר הכיתות אין חוסר בשישי
# שלישי: כל הכיתות עד שעה 6 - מותר "חסר מורה" בקנס
for _k in [k for k in x if k[3]=="חסר מורה" and k[1][0]!=5 and not (k[1][0]==2 and k[1][1] in (5,6))
]:
    m.Add(x[_k]==0)                               # חסר מורה: שלישי 5-6 (בקנס) או שישי ט אסיף
MISSING=[x[k] for k in x if k[3]=="חסר מורה" and k[1][0]!=5]
for c in HCLASSES:
    _lt=5 if GRADE[c] in "זח" else 6
    for h in range(1,_lt+1): m.Add(free[(c,(2,h))]==0)
    if GRADE[c] in "זח": m.Add(free[(c,(2,6))]==1)     # סוף יום המגמות

# תמיר: חינוך כיתתו כולו שלו; אזרחות אסיף==2; לייה לא בשעות 6-7
_v=[x[("ט תמיר",s2,"חינוך","תמיר")] for s2 in HSLOTS if ("ט תמיר",s2,"חינוך","תמיר") in x]
if _v: m.Add(sum(_v)==2)
_v=[x[("ט אסיף",s2,"אזרחות","תמיר")] for s2 in HSLOTS if ("ט אסיף",s2,"אזרחות","תמיר") in x]
if _v: m.Add(sum(_v)==2)
_v=[x[("ט אסיף",s2,"היסטוריה","תמיר")] for s2 in HSLOTS if ("ט אסיף",s2,"היסטוריה","תמיר") in x]
if _v: m.Add(sum(_v)==2)
_v=[x[("ט תמיר",s2,"היסטוריה","תמיר")] for s2 in HSLOTS if ("ט תמיר",s2,"היסטוריה","תמיר") in x]
if _v: m.Add(sum(_v)==2)
_v=[x[("ט תמיר",s2,"אזרחות","תמיר")] for s2 in HSLOTS if ("ט תמיר",s2,"אזרחות","תמיר") in x]
if _v: m.Add(sum(_v)==2)
_v=[x[("ט תמיר",s2,'תנ"ך',"תמיר")] for s2 in HSLOTS if ("ט תמיר",s2,'תנ"ך',"תמיר") in x]
if _v: m.Add(sum(_v)==2)
for _kl in [k for k in x if k[3]=="לייה" and k[1][1]>=6]:
    m.Add(x[_kl]==0)

# ח גלית: שני בדיוק 5 שעות; תנ"ך לייה רק בשעות 1-4
m.Add(free[("ח גלית",(1,5))]==0)
pass
pass
pass

# יום המגמות: חינוך בש5, ואז הביתה
for _cz in ("ז נעמי","ז אלי"):
    _v5=[x[k] for k in x if k[0]==_cz and k[1]==(2,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)
_v5m=[x[k] for k in x if k[0]=="ח גלית" and k[1]==(2,5) and k[2]=="מתמטיקה" and k[3]=="מורה חיצוני"]
if _v5m: m.Add(sum(_v5m)==1)   # ח: מתמטיקה עם המורה החיצוני אחרי המגמות
for _c9p in T9:
    _v5=[x[k] for k in x if k[0]==_c9p and k[1]==(4,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)
    for _hb in (6,7): m.Add(free[(_c9p,(4,_hb))]==1)
# ספרות והיסטוריה: נעמי ואלי בעצמם לפחות שעה בכל כיתה (שיר משלימה בשישי)
for _cz2 in ("ז נעמי","ז אלי","ח גלית"):
    _vv=[x[(_cz2,s2,"ספרות","נעמי")] for s2 in HSLOTS if (_cz2,s2,"ספרות","נעמי") in x]
    if _vv: m.Add(sum(_vv)>=1)
    _vv=[x[(_cz2,s2,"היסטוריה","אלי")] for s2 in HSLOTS if (_cz2,s2,"היסטוריה","אלי") in x]
    if _vv: m.Add(sum(_vv)>=1)

# תמיר: לא בשעות 6-7 של חמישי; אלי שם עם כיתתו
for _kt6 in [k for k in x if k[3]=="תמיר" and k[1] in ((4,6),(4,7)) and k[0]!="ז נעמי"]:
    m.Add(x[_kt6]==0)   # חמישי 6-7: לא בז אלי (אלי שם) ולא בט (הלכו הביתה)
_va67=[x[k] for k in x if k[0]=="ז אלי" and k[1] in ((4,6),(4,7)) and k[3]=="אלי"]
if _va67: m.Add(sum(_va67)>=1)   # אלי עם כיתתו לפחות שעה בחמישי 6-7

# תמיר בשישי: רק עם הכיתה שלו
for _kt in [k for k in x if k[3]=="תמיר" and k[1][0]==5 and k[0]!="ט תמיר"]:
    m.Add(x[_kt]==0)

# שירה בציבור: יום שישי שעה 2, כל החטיבה יחד באולם חדר האוכל
for c in HCLASSES:
    for s2 in HSLOTS:
        _sg = "שיר" if HHOME[c]=="אלי" else ("חסר מורה" if c=="ט אסיף" else HHOME[c])
        k=(c,s2,"שירה בציבור",_sg)
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
_DUTY_FIX={"ז נעמי":2,"ז אלי":1,"ח גלית":4,"ט תמיר":0,"ט אסיף":3}
for _dc,_dd in _DUTY_FIX.items():
    m.Add(duty[(_dc,_dd)]==1)

# אסיף מלמד בשישי עם הכיתה שלו (לפחות שעתיים)
asif_fri=[x[("ט אסיף",(5,h),sj,"אסיף")] for h in (1,3,4)
          for (sj,t) in pairs["ט אסיף"] if t=="אסיף" and ("ט אסיף",(5,h),sj,"אסיף") in x]
if asif_fri: m.Add(sum(asif_fri)>=2)

# אסיף: לא מלמד שפה בשעה האחרונה של היום (שעה 6 בסדר)
for c in HCLASSES:
    for d in range(6):
        k=(c,(d,HDAY[d]),"שפה","אסיף")
        if k in x: m.Add(x[k]==0)

# ==== חלוקת רב מלל ותנ"ך בכיתות ט (rules_rm) ====
# אסיף: שעת החינוך השנייה שלו בשעה שישית
_a5t=("ט אסיף",(2,5),"חינוך","אסיף")
if _a5t in x: m.Add(x[_a5t]==1)   # שלישי ש5: חינוך עם אסיף; אם חסר - בסוף היום
# רב מלל ט בוטל - הוחלף בהיסטוריה/ספרות
_v=[x[("ט תמיר",s2,'תנ"ך',"תמיר")] for s2 in HSLOTS if ("ט תמיר",s2,'תנ"ך',"תמיר") in x]
if _v: m.Add(sum(_v)==2)

# ח גלית: שעת החינוך הנוספת = שעה שביעית עם גלית (galit_h7)
_g6=("ח גלית",(1,6),"חינוך","גלית")
if _g6 in x: m.Add(x[_g6]==1)   # חינוך עם גלית בסוף יום שני (ש6)

# ח גלית: מינימום 5 שעות לימוד בכל יום א-ה (hg_min)
# אלי לא מלמד בשכבת ט כלל (no_eli_9); תנ"ך ט אסיף = תמיר
for _k in [k for k in x if k[0] in T9 and k[3]=="אלי"]:
    m.Add(x[_k]==0)
_v9=[x[k] for k in x if k[0]=="ט אסיף" and k[2]=='תנ"ך' and k[3]=="תמיר"]
if _v9: m.Add(sum(_v9)==2)
# מאמי: מלמדת רק חמישי 5-6, עד שעתיים (mami_thu)
for _k in [k for k in x if k[3]=="מאמי" and k[1] not in ((4,5),(4,6))]:
    m.Add(x[_k]==0)
_mv2=[x[k] for k in x if k[3]=="מאמי"]
if _mv2: m.Add(sum(_mv2)<=2)

# תנ"ך של לייה בח גלית: שיעור כפול רצוף (leah_double)
_ld=[]
for _d in range(6):
    for _h in range(1,HDAY[_d]):
        _a=("ח גלית",(_d,_h),'תנ"ך',"לייה"); _b2=("ח גלית",(_d,_h+1),'תנ"ך',"לייה")
        if _a in x and _b2 in x:
            _pv=m.NewBoolVar(f"ld{_d}{_h}")
            m.Add(x[_a]+x[_b2]==2).OnlyEnforceIf(_pv)
            _ld.append(_pv)
if _ld: m.Add(sum(_ld)==1)

# ראשון ש5 וחמישי ש5 חייבים שיעור (h5_pin)
m.Add(hfree[("ח גלית",(0,5))]==0)
m.Add(hfree[("ח גלית",(4,5))]==0)
for _d in range(5):
    _occ=[m.NewBoolVar(f"hgm{_d}{_h}") for _h in range(1,HDAY[_d]+1)]
    for _h,_b in zip(range(1,HDAY[_d]+1),_occ):
        m.Add(hfree[("ח גלית",(_d,_h))]+_b==1)
    m.Add(sum(_occ)>=min(4,HDAY[_d]))   # מינימום 4 (30 שעות שבועיות לא מאפשרות 5 בכל יום)

# ח גלית: שישי מלא - כל 4 השעות עם מורה (galit_fri_full)
for _h in range(1,5):
    m.Add(free[("ח גלית",(5,_h))]==0)

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
vend={}
for c in HCLASSES:
    for d in range(5):
        last = 6 if d==2 else min(5,HDAY[d])
        for h in range(1,last+1):
            if d==2 and GRADE[c]=="ט": m.Add(free[(c,(d,h))]==0)   # ט: שלישי מלא עד 6
            else:
                _w = 2500 if d==2 else 1               # שלישי כמעט-חובה לשאר
                b=m.NewBoolVar(f"ve{c}{d}{h}"); m.Add(free[(c,(d,h))]<=b); vend[(c,d,h,_w)]=b

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
m.Minimize(9500*sum(MISSING)+sum(400*_k[3]*_v for _k,_v in vend.items())+5*sum(late) - 80*sum(eli_own) - 150*sum(fri) - 50*sum(hadar) - 200*sum(own) - 120*sum(same) + 60*sum(split))
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
    _gjo={f"{c}|{3},{h}":"גלית" for (c,h),b in gj.items() if sol.Value(b)}
    io.open("galit_erez.json","w",encoding="utf-8").write(json.dumps(_gjo,ensure_ascii=False))
    _tjo=[{"day":ss[0],"hour":ss[1],"subj":sj} for (ss,sj),b in tjS.items() if sol.Value(b)]
    io.open("tj.json","w",encoding="utf-8").write(json.dumps(_tjo,ensure_ascii=False))
    io.open("viol_report.txt","w",encoding="utf-8").write(chr(10).join(
        [f"מסיים מוקדם: {c} {DAY_NAMES[d]} ש{h}" for (c,d,h,_w2),v in sorted(vend.items()) if sol.Value(v)]) or "אין חריגות")
    print("filled:",sum(1 for c in HCLASSES for s in HSLOTS if out[c][f'{s[0]},{s[1]}']),
          "/",sum(sum(v[GRADE[c]] for v in NEED.values()) for c in HCLASSES))
