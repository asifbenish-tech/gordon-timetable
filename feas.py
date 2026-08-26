# -*- coding: utf-8 -*-
import io
from data import *
DIDX={n:i for i,n in enumerate(DAY_NAMES)}
def blocked(t):
    b=set()
    for dn in DAYS_OFF.get(t,[]):
        for h in range(1,9): b.add((DIDX[dn],h))
    for s in UNAVAIL.get(t,[])+EVENTS.get(t,[]): b.add(s)
    return b
rows=[]
for t,q in QUOTA.items():
    if t=='תל"ן': continue
    need=sum(q.values()); blk=blocked(t)
    a=sum(1 for (d,h) in SLOTS if (d,h) not in blk and not (d==5 and FRIDAY_TEACHER.get(next((c for c in q),""))!=t))
    a=0
    for (d,h) in SLOTS:
        if (d,h) in blk: continue
        if d==5 and t not in FRIDAY_TEACHER.values(): continue
        a+=1
    rows.append((t,need,a,a-need))
rows.sort(key=lambda r:r[3])
with io.open("feas.txt","w",encoding="utf-8") as f:
    f.write("מורה | נדרש | פנוי | מרווח\n")
    for t,n,a,s in rows: f.write(f"{t} | {n} | {a} | {s}{'  <== חוסר' if s<0 else ('  (אפס גמישות)' if s==0 else '')}\n")
    for sub in ("הילית","חגית","יפעת","יעל"):
        need=sum(2 for c in CLASSES if sub in TLN_PAIR[c]); b=set()
        for dn in TLN_OFF[sub]:
            for h in range(1,9): b.add((DIDX[dn],h))
        for s in TLN_UNAVAIL[sub]: b.add(s)
        a=sum(1 for (d,h) in SLOTS if (d,h) not in b and d!=5)
        f.write(f'{sub} (תל"ן) | {need} | {a} | {a-need}\n')
