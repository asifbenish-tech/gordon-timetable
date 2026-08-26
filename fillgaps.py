# -*- coding: utf-8 -*-
import io,json,collections
from data2 import *
from hdata import HCLASSES, HSLOTS, HDAY, HOFF, HEV
S=json.load(io.open('sol_J.json',encoding='utf-8'))
H=json.load(io.open('sol_hat.json',encoding='utf-8'))
SED=json.load(io.open('sed_J.json',encoding='utf-8'))
CO=json.load(io.open('co_zofia3.json',encoding='utf-8'))
def tof(v): return v.split(' – ')[1] if ' – ' in v else None
CM={'שני':1,'שלישי':2}
cozof={(int(k.split('|')[1].split(',')[0]),int(k.split('|')[1].split(',')[1])) for k in CO}
MAG={(2,1):['חסן','רובי','שרית','אסיף'],(2,2):['חסן','רובי','שרית','אסיף'],
     (2,3):['חסן','חגית','יעל','אופיר'],(2,4):['חסן','חגית','יעל','אופיר'],
     (4,1):['חסן','מאמי','אסיף'],(4,2):['חסן','מאמי','אסיף'],
     (4,3):['אלי','יעל','מאמי'],(4,4):['אלי','יעל','מאמי']}
PE={(0,1),(0,2),(0,3),(3,1),(3,2),(3,3)}
BAN={'יעל','חגית','יפעת','הילית','מאמי','שיר','הדר'}
CAPS={'מרים':23,'תמיר':24,'צבי':12,'גלית':20,'צופיה':18,'טלי':10,'נעמי':20,'אלי':20,
      'הדר':8,'ליאור':10,'שחר':12,'ארז':8,'חסן':26,'שרית':28,'רובי':6}
def load():
    L=collections.Counter()
    for c in CLASSES:
        for s in SLOTS:
            t=S[c][f'{s[0]},{s[1]}']
            if t and t!='תל"ן': L[t]+=1
    seen=set()
    for c in HCLASSES:
        for s in HSLOTS:
            t=tof(H[c][f'{s[0]},{s[1]}'])
            if t=='שרית + חסן':
                if s not in seen: seen.add(s); L['שרית']+=1; L['חסן']+=1
            elif t and t not in ('מגמות','שירה בציבור'): L[t]+=1
    for k,l in MAG.items():
        for t in l: L[t]+=1
    L['צופיה']+=len(CO)
    return L
def free_at(t,d,h,L):
    if t in BAN: return False
    off=(DAYS_OFF2.get(t) or [])+(HOFF.get(t) or [])
    if t=='צופיה': off=off+['חמישי']
    if t=='טלי' and DAY_NAMES[d] not in ('שני','שלישי'): return False
    if t=='שחר' and DAY_NAMES[d] not in ('שני','שלישי','רביעי'): return False
    if t=='רובי' and DAY_NAMES[d]!='שלישי': return False
    if t=='צבי' and DAY_NAMES[d] not in ('ראשון','שני','רביעי'): return False
    if t=='מאמי' and DAY_NAMES[d]=='שלישי': return False
    if t=='שיר' and d!=5: return False
    if DAY_NAMES[d] in off: return False
    if (d,h) in (HEV.get(t,[])+UNAVAIL2.get(t,[])+EVENTS2.get(t,[])): return False
    if t in MAG.get((d,h),[]) or t in MAGAMA.get((d,h),[]): return False
    if any(S[cc][f'{d},{h}']==t for cc in CLASSES): return False
    if t=='צופיה' and (d,h) in cozof: return False
    if h<=HDAY[d] and any(tof(H[cc][f'{d},{h}'])==t for cc in HCLASSES): return False
    if t in ('שרית','חסן') and (d,h) in PE: return False
    for day in ('שני','שלישי'):
        if t in SED.get('קבוצת '+day,[]) and CM[day]==d and h in SED['מעגלי שיח '+day]: return False
    if t in ['לייה','שרית','יערה','צופיה','אסיף'] and d==2 and h in SED['ישיבת ניהול שלישי']: return False
    if L.get(t,0)>=CAPS.get(t,0): return False
    return True
gaps=[(c,d,h) for c in CLASSES for (d,h) in SLOTS if not S[c][f'{d},{h}']]
L=load(); plan=[]
# greedy: התחל מהחורים עם הכי מעט מועמדים
while gaps:
    opts={}
    for c,d,h in gaps:
        opts[(c,d,h)]=[t for t in CAPS if free_at(t,d,h,L)]
    tgt=min(opts,key=lambda k:len(opts[k]))
    cands=opts[tgt]
    if not cands:
        print("אין מועמד ל:",tgt[0],DAY_NAMES[tgt[1]],tgt[2]); gaps.remove(tgt); continue
    best=max(cands,key=lambda t:CAPS[t]-L.get(t,0))
    c,d,h=tgt
    S[c][f'{d},{h}']=best; L[best]+=1; plan.append((c,d,h,best)); gaps.remove(tgt)
io.open('sol_J.json','w',encoding='utf-8').write(json.dumps(S,ensure_ascii=False,indent=1))
io.open('fills.json','w',encoding='utf-8').write(json.dumps({f'{c}|{d},{h}':t for c,d,h,t in plan},ensure_ascii=False,indent=1))
out=[f'שובצו {len(plan)} חורים:']
for c,d,h,t in plan: out.append(f'   {c} {DAY_NAMES[d]} ש{h}: {t}')
tot=sum(1 for c in CLASSES for s in SLOTS if S[c][f'{s[0]},{s[1]}'])
out.append(f'יסודי: {tot}/416')
io.open('fillres.txt','w',encoding='utf-8').write(chr(10).join(out))
