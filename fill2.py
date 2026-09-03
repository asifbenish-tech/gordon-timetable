# -*- coding: utf-8 -*-
import io,json,collections
from data2 import *
from hdata import HCLASSES,HSLOTS,HDAY,HOFF,HEV,PE_BLOCKS   # PE_BLOCKS: מקור אחד (pe_blocks.json)
S=json.load(io.open('sol_J.json',encoding='utf-8'))
H=json.load(io.open('sol_hat.json',encoding='utf-8'))
SED=json.load(io.open('sed_J.json',encoding='utf-8'))
F=json.load(io.open('fills.json',encoding='utf-8'))
def tof(v): return v.split(' – ')[1].split(' + ') if ' – ' in v else []   # 'שרית + חסן' = שניהם עסוקים
CM={'שני':1,'שלישי':2}
CAPS={'מרים':13,'צופיה':13,'טלי':10,'לי-אור':10,'שחר':12,'דניאל':23,'דני':20,'אינס':23,
      'מירי':23,'אנה':24,'פנינה':23,'אביטל':23,'יערה':21,'לייה':21,'דליה':24,'תניה':18,
      'אורנה':18,'סימה':24,'פאני':16,'חסן':16,'שרית':16}
CAPS.pop('צבי',None)
# תקרה בטוחה: המילוי לא יעלה לעולם על המכסה האמיתית של המורה.
# בלי זה הערכים כאן יכולים לסטות מ-MAXQ2 (למשל שחר, שהיה 12 מול מכסה 10).
CAPS={t:min(v,MAXQ2.get(t,v)) for t,v in CAPS.items()}
def load():
    L=collections.Counter()
    for c in CLASSES:
        for s in SLOTS:
            t=S[c][f'{s[0]},{s[1]}']
            if t and t!='תל"ן': L[t]+=1
    return L
def ok(t,c,d,h):
    L=load()
    if L.get(t,0)>=CAPS.get(t,0): return False
    off=list(DAYS_OFF2.get(t) or [])
    if t=='צופיה': off.append('חמישי')
    # מגבלת ימי עבודה - חייבת להתאים למנוע, אחרת המילוי מוסיף יום שלישי/רביעי
    md=MAXDAYS.get(t)
    if md:
        days={dd for cc in CLASSES for (dd,hh) in SLOTS if S[cc][f'{dd},{hh}']==t}
        if d not in days and len(days)>=md: return False
    if t=='טלי' and DAY_NAMES[d] not in ('שני','שלישי'): return False
    if t=='שחר' and DAY_NAMES[d] not in ('שני','שלישי','רביעי'): return False
    if t=='שחר' and h==DAY_HOURS[d]: return False
    if DAY_NAMES[d] in off: return False
    if (d,h) in (UNAVAIL2.get(t,[])+EVENTS2.get(t,[])+HEV.get(t,[])): return False
    if t in MAGAMA.get((d,h),[]): return False
    if any(S[cc][f'{d},{h}']==t for cc in CLASSES): return False
    if h<=HDAY[d] and any(t in tof(H[cc][f'{d},{h}']) for cc in HCLASSES): return False
    for day in ('שני','שלישי'):
        if t in SED.get('קבוצת '+day,[]) and CM[day]==d and h in SED['מעגלי שיח '+day]: return False
    if t in ['לייה','שרית','יערה','צופיה','אסיף','אלי'] and d==2 and h in SED['ישיבת ניהול שלישי']: return False
    if t in ('שרית','חסן') and h in PE_BLOCKS.get(d,[]): return False   # ספורט חטיבה - היה עותק ישן (1-3) והכניס את חסן לשני מקומות
    return True
gaps=[(c,d,h) for c in CLASSES for (d,h) in SLOTS if not S[c][f'{d},{h}']]
# סדר: המשבצות עם הכי מעט מועמדים קודם
done=[]
for _ in range(len(gaps)):
    best=None
    for (c,d,h) in gaps:
        if S[c][f'{d},{h}']: continue
        cand=[t for t in CAPS if ok(t,c,d,h)]
        if not cand: continue
        if best is None or len(cand)<best[3]: best=(c,d,h,len(cand),cand)
    if not best: break
    c,d,h,_,cand=best
    cand.sort(key=lambda t:-(CAPS[t]-load().get(t,0)))
    t=cand[0]
    assert not S[c][f'{d},{h}']
    S[c][f'{d},{h}']=t; F[f'{c}|{d},{h}']=t
    done.append(f'{c} {DAY_NAMES[d]} ש{h}: {t}')
json.dump(S,io.open('sol_J.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
json.dump(F,io.open('fills.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
rem=[(c,DAY_NAMES[d],h) for c in CLASSES for (d,h) in SLOTS if not S[c][f'{d},{h}']]
out=['שובצו '+str(len(done))+':']+['   '+d for d in done]+['','נשארו '+str(len(rem))+':']+['   '+f'{c} {d} ש{h}' for c,d,h in rem]
io.open('fill2.txt','w',encoding='utf-8').write(chr(10).join(out))
print('filled',len(done),'remaining',len(rem))
