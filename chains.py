# -*- coding: utf-8 -*-
"""לכל חור: מחפש שרשרת דו-שלבית - מורה Y פנוי מחליף את X בכיתה B, ו-X עובר לחור."""
import io,json,collections,sys
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
from data2 import *
from hdata import HCLASSES,HSLOTS,HDAY,HOFF,HEV
S=json.load(io.open('sol_J.json',encoding='utf-8'))
H=json.load(io.open('sol_hat.json',encoding='utf-8'))
SED=json.load(io.open('sed_J.json',encoding='utf-8'))
def tof(v): return v.split(' – ')[1] if ' – ' in v else None
CM={'שני':1,'שלישי':2}
QF={'מרים':23,'צופיה':18,'טלי':10,'ליאור':10,'שחר':10,'דניאל':26,'דני':24,'אינס':24,
 'מירי':23,'אנה':25,'פנינה':23,'אביטל':25,'יערה':25,'לייה':23,'דליה':24,'תניה':18,
 'אורנה':18,'סימה':24,'פאני':16,'חסן':26,'שרית':28,'נעמי':20,'אלי':20,'תמיר':24}
el=collections.Counter(); hl=collections.Counter()
for c in CLASSES:
    for s2 in SLOTS:
        t=S[c][f'{s2[0]},{s2[1]}']
        if t and t!='תל"ן': el[t]+=1
for c in HCLASSES:
    for s2 in HSLOTS:
        t=tof(H[c][f'{s2[0]},{s2[1]}'])
        if t: hl[t]+=1
def free_at(t,d,h):
    off=list(DAYS_OFF2.get(t) or [])+list(HOFF.get(t) or [])
    if t=='צופיה': off.append('חמישי')
    if t=='טלי' and DAY_NAMES[d] not in ('שני','שלישי'): return False
    if t=='שחר' and DAY_NAMES[d] not in ('שני','שלישי','רביעי'): return False
    if t=='שחר' and h==DAY_HOURS[d]: return False
    if DAY_NAMES[d] in off: return False
    if (d,h) in (UNAVAIL2.get(t,[])+EVENTS2.get(t,[])+HEV.get(t,[])): return False
    if t in MAGAMA.get((d,h),[]): return False
    if any(S[cc][f'{d},{h}']==t for cc in CLASSES): return False
    if h<=HDAY[d] and any(tof(H[cc][f'{d},{h}'])==t for cc in HCLASSES): return False
    for day in ('שני','שלישי'):
        if t in SED.get('קבוצת '+day,[]) and CM[day]==d and h in SED['מעגלי שיח '+day]: return False
    if t in ['לייה','שרית','יערה','צופיה','אסיף','אלי'] and d==2 and h in SED['ישיבת ניהול שלישי']: return False
    if t in ('שרית','חסן') and ((d==0 and h in(1,2,3)) or (d==3 and h in(1,2,3))): return False
    return True
BAN={'יעל','חגית','יפעת','הילית','מאמי','שיר','הדר','ארז','רובי','צבי','מורה חיצוני','אסיף','תמיר'}
gaps=[(c,d,h) for c in CLASSES for (d,h) in SLOTS if not S[c][f'{d},{h}']]
out=[]
for gc,d,h in gaps:
    out.append(f'=== {gc} {DAY_NAMES[d]} ש{h} ===')
    found=0
    for bc in CLASSES:
        X=S[bc][f'{d},{h}']
        if not X or X=='תל"ן' or X in BAN: continue
        for Y,q in QF.items():
            if Y==X or Y in BAN: continue
            if q-el.get(Y,0)-hl.get(Y,0)<=0: continue
            if not free_at(Y,d,h): continue
            out.append(f'   {X} עובר מ{bc} אל {gc}; {Y} (נותרו {q-el.get(Y,0)-hl.get(Y,0)}) נכנס ל{bc}')
            found+=1
            if found>=4: break
        if found>=4: break
    if not found: out.append('   אין שרשרת דו-שלבית')
io.open('chains_out.txt','w',encoding='utf-8').write('\n'.join(out))
print("done", len(gaps))
