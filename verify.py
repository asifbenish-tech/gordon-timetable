# -*- coding: utf-8 -*-
import json, io, collections
from data import *
S=json.load(io.open("solution.json",encoding="utf-8"))
DIDX={n:i for i,n in enumerate(DAY_NAMES)}
NIHUL=["לייה","שרית","יערה","צופיה","אסיף"]
EVENTS["יערה"]=[(0,3)]; EVENTS["לייה"]=[(0,4)]
EVENTS["שרית"]=[(0,1)]; EVENTS["צופיה"]=[(0,2),(0,5)]
EVENTS["אסיף"]=[(3,2),(3,6),(4,2)]
MATH_WED={"אינס":1,"דליה":2,"פנינה":3,"אנה":3,"צופיה":3,
          "יערה":4,"אביטל":4,"טלי":4,"תניה":5,"שרית":6}

HEB_SUN={"אנה":2,"צופיה":2,"פנינה":2,"יערה":3,"אביטל":3,"טלי":3,"לייה":4,
         "דליה":4,"דניאל":4,"מירי":5,"דני":5,"אורנה":1,"שרית":1}

def blk(t):
    b=set()
    for dn in DAYS_OFF.get(t,[]):
        for h in range(1,9): b.add((DIDX[dn],h))
    for s in UNAVAIL.get(t,[])+EVENTS.get(t,[]): b.add(s)
    return b
err=[]
# 1 every slot filled
for c in CLASSES:
    for s in SLOTS:
        if not S[c][f"{s[0]},{s[1]}"]: err.append(f"ריק: {c} {DAY_NAMES[s[0]]} ש{s[1]}")
    if len(S[c])!=32: err.append(f"{c}: {len(S[c])} משבצות במקום 32")
# 2 no double booking
for s in SLOTS:
    k=f"{s[0]},{s[1]}"; seen=collections.defaultdict(list)
    for c in CLASSES: seen[S[c][k]].append(c)
    for t,cs in seen.items():
        if t=='תל"ן': continue
        if len(cs)>1: err.append(f"התנגשות: {t} ב-{DAY_NAMES[s[0]]} ש{s[1]} ב{cs}")
# 2b תל"ן sub-teachers
for s in SLOTS:
    k=f"{s[0]},{s[1]}"; use=collections.defaultdict(list)
    for c in CLASSES:
        if S[c][k]=='תל"ן':
            for sub in TLN_PAIR[c]: use[sub].append(c)
    for sub,cs in use.items():
        if len(cs)>1: err.append(f'התנגשות תל"ן: {sub} ב-{DAY_NAMES[s[0]]} ש{s[1]} ב{cs}')
# 3 availability
for c in CLASSES:
    for s in SLOTS:
        t=S[c][f"{s[0]},{s[1]}"]
        if t=='תל"ן':
            for sub in TLN_PAIR[c]:
                bad=set()
                for dn in TLN_OFF[sub]:
                    for h in range(1,9): bad.add((DIDX[dn],h))
                bad|=set(TLN_UNAVAIL[sub])
                if s in bad or s[0]==5: err.append(f'תל"ן {sub} לא זמין: {c} {DAY_NAMES[s[0]]} ש{s[1]}')
        elif s in blk(t): err.append(f"אילוץ מופר: {t} לא זמין {DAY_NAMES[s[0]]} ש{s[1]} ({c})")
# 4 Friday = homeroom only
for c in CLASSES:
    for h in range(1,5):
        t=S[c][f"5,{h}"]
        if t!=FRIDAY_TEACHER[c]: err.append(f"שישי לא מחנך: {c} ש{h} = {t}")
# 5 חינוך גופני (פאני+חסן): שתי שעות הספורט בימים שונים
for c in CLASSES:
    days=[d for d in range(6) for h in range(1,DAY_HOURS[d]+1)
          if S[c][f"{d},{h}"] in ("פאני","חסן")]
    if len(days)!=2: err.append(f"ספורט ב{c}: {len(days)} שעות במקום 2")
    if len(days)!=len(set(days)):
        err.append(f"ספורט פעמיים באותו יום: {c} ({[DAY_NAMES[d] for d in days]})")
# 6 אסיף/תמיר exactly 1h in each ו class, and nowhere else
for t in ("אסיף","תמיר"):
    for c in CLASSES:
        n=sum(1 for s in SLOTS if S[c][f"{s[0]},{s[1]}"]==t)
        want=1 if c.startswith("ו ") else 0
        if n!=want: err.append(f"{t} ב{c}: {n} (צריך {want})")
# 7 no junior-high homeroom teachers in elementary except אסיף/תמיר
BAN={"נעמי","אלי","גלית","הדר","ארז","צבי"}
for c in CLASSES:
    for s in SLOTS:
        if S[c][f"{s[0]},{s[1]}"] in BAN: err.append(f"מורה חטיבה: {S[c][f'{s[0]},{s[1]}']} ב{c}")
# 8 תל"ן 2h + consecutive where required
for c in CLASSES:
    sl=[s for s in SLOTS if S[c][f"{s[0]},{s[1]}"]=='תל"ן']
    if len(sl)!=2: err.append(f'תל"ן ב{c}: {len(sl)} שעות במקום 2')
    elif TLN_CONSEC[c]:
        (d1,h1),(d2,h2)=sl
        if not(d1==d2 and abs(h1-h2)==1): err.append(f'תל"ן ב{c} לא ברצף: {sl}')
# 9 אינס 2 consecutive Tue in ה
for c in ("ה דני","ה תניה"):
    sl=[s for s in SLOTS if S[c][f"{s[0]},{s[1]}"]=="אינס" and s[0]==2]
    ok=any((2,h) in sl and (2,h+1) in sl for h in range(1,6))
    if not ok: err.append(f"אינס: אין שעתיים רצופות ביום ג ב{c}")

import json as _j
CIR=_j.load(io.open("circles_c.json",encoding="utf-8"))
DI={"שני":1,"שלישי":2}
NH=[3,4] if "3-4" in CIR["ישיבת ניהול יום ג"] else [5,6]
for t in NIHUL:
    for h in NH:
        for c in CLASSES:
            if S[c][f"2,{h}"]==t: err.append(f"ישיבת ניהול: {t} משובץ ב{c} ביום ג ש{h}")
for dn,info in CIR.items():
    if isinstance(info,str): continue
    for t in info["מחנכים"]:
        for h in info["שעות"]:
            for c in CLASSES:
                if S[c][f"{DI[dn]},{h}"]==t:
                    err.append(f"מעגלי שיח: {t} משובץ ב{c} ביום {dn} ש{h}")
    if dn.startswith("ישיב"): continue
    if len(info["מחנכים"])!=9: err.append(f"קבוצת {dn}: {len(info['מחנכים'])} מחנכים")
    if info["שעות"]!=[min(info["שעות"]),min(info["שעות"])+1]: err.append(f"קבוצת {dn}: שעות לא רצופות")
for t in ("מאמי","רובי"):
    n=sum(1 for c in CLASSES for s in SLOTS if S[c][f"{s[0]},{s[1]}"]==t)
    if n: err.append(f"{t} שובץ {n} שעות (ביקשת לא לשבץ)")

info=[]
for _t,_h in MATH_WED.items():
    for c in CLASSES:
        if S[c][f"3,{_h}"]==_t: info.append(f"{_t} מלמד {c} ברביעי ש{_h}")
io.open("math_overlap.txt","w",encoding="utf-8").write(chr(10).join(
    ["חופפים להדרכת מתמטיקה (אחת לחודש - דורש מחליף באותו יום):"]+info))
for _t,_h in HEB_SUN.items():
    for c in CLASSES:
        if S[c][f"0,{_h}"]==_t: err.append(f"הדרכת שפה: {_t} מלמד {c} בראשון ש{_h}")

MAXQ={"אנה":25,"אסיף":20,"דליה":24,"לייה":23,"פנינה":23,"שרית":28,"תניה":18,"יערה":25,
 "דני":24,"אורנה":18,"צופיה":23,"פאני":16,"תמיר":24,"מירי":23,"אינס":24,"אביטל":25,
 "דניאל":26,"מרים":23,"סימה":24,"חסן":26,"ליאור":8,"טלי":10,"שחר":12}
HAT={"לייה":2,"שרית":6,"חסן":10,"מרים":10,"אסיף":18,"תמיר":22}
for _t,_q in MAXQ.items():
    n=sum(1 for c in CLASSES for s in SLOTS if S[c][f"{s[0]},{s[1]}"]==_t)
    lim=_q-HAT.get(_t,0)
    if n>lim: err.append(f"חריגת מכסה: {_t} משובץ {n} ש' מול תקרה {lim}")
io.open("errors.txt","w",encoding="utf-8").write("\n".join(err) or "✔ כל הבדיקות עברו")
print(f"בדיקות: {len(err)} שגיאות")
