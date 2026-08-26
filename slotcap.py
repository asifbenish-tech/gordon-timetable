# -*- coding: utf-8 -*-
import io, collections
from data import *
DIDX={n:i for i,n in enumerate(DAY_NAMES)}
def blocked(t):
    b=set()
    for dn in DAYS_OFF.get(t,[]):
        for h in range(1,9): b.add((DIDX[dn],h))
    for s in UNAVAIL.get(t,[])+EVENTS.get(t,[]): b.add(s)
    return b
BL={t:blocked(t) for t in QUOTA if t!='תל"ן'}
def tlnb(c):
    b=set()
    for sub in TLN_PAIR[c]:
        for dn in TLN_OFF[sub]:
            for h in range(1,9): b.add((DIDX[dn],h))
        for s in TLN_UNAVAIL[sub]: b.add(s)
    return b
TB={c:tlnb(c) for c in CLASSES}
with io.open("slotcap.txt","w",encoding="utf-8") as f:
    for d in range(5):
        for h in range(1,DAY_HOURS[d]+1):
            sup=set()
            for t,q in QUOTA.items():
                if t=='תל"ן': continue
                if (d,h) not in BL[t] and any(v>0 for v in q.values()): sup.add(t)
            tln=sum(1 for c in CLASSES if (d,h) not in TB[c])
            mark="  <<< צוואר בקבוק" if len(sup)+min(tln,1)<13 else ""
            f.write(f"{DAY_NAMES[d]} ש{h}: מורים זמינים {len(sup)} / 13 כיתות{mark}\n")
            if len(sup)<15:
                f.write("      זמינים: "+", ".join(sorted(sup))+"\n")
