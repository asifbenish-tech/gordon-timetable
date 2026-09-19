# -*- coding: utf-8 -*-
"""סורק שרשראות עד עומק 6: הזזת שיעור בתוך כיתה + החלפת מורה בין כיתות באותה שעה."""
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
 'אורנה':18,'סימה':24,'פאני':16,'חסן':26,'שרית':28,'רובי':6}
el=collections.Counter()
for c in CLASSES:
    for s2 in SLOTS:
        t=S[c][f'{s2[0]},{s2[1]}']
        if t and t!='תל"ן': el[t]+=1
hl=collections.Counter()
for c in HCLASSES:
    for s2 in HSLOTS:
        t=tof(H[c][f'{s2[0]},{s2[1]}'] or '')
        if t and t!='חסר מורה': hl[t]+=1
def left(t): return QF.get(t,0)-el.get(t,0)-hl.get(t,0)
def blocked(t,d,h,ignore=None):
    off=list(DAYS_OFF2.get(t) or [])+list(HOFF.get(t) or [])
    if t=='צופיה': off.append('חמישי')
    if DAY_NAMES[d] in off: return 'חופש'
    if t=='רובי' and DAY_NAMES[d]!='שלישי': return 'רק שלישי'
    if t=='טלי' and DAY_NAMES[d] not in ('שני','שלישי'): return 'ימים'
    if t=='שחר' and (DAY_NAMES[d] not in ('שני','שלישי','רביעי') or h==DAY_HOURS[d]): return 'שחר'
    if (d,h) in (UNAVAIL2.get(t,[])+EVENTS2.get(t,[])+HEV.get(t,[])): return 'סדירות'
    if t in MAGAMA.get((d,h),[]): return 'מגמות'
    for day in ('שני','שלישי'):
        if t in SED.get('קבוצת '+day,[]) and CM[day]==d and h in SED['מעגלי שיח '+day]: return 'מעגל'
    if t in ['לייה','שרית','יערה','צופיה','אסיף','אלי'] and d==2 and h in SED['ישיבת ניהול שלישי']: return 'ניהול'
    if t in ('שרית','חסן') and ((d==0 and h in(1,2,3)) or (d==3 and h in(4,5,6))): return 'ספורט חטיבה'
    for cc in CLASSES:
        if (cc,d,h)!=(ignore or ('',None,None)) and S[cc][f'{d},{h}']==t: return 'מלמד '+cc
    if h<=HDAY[d]:
        for cc in HCLASSES:
            if tof(H[cc][f'{d},{h}'] or '')==t: return 'חטיבה '+cc
    return None
def fillers(c,d,h,ignore=None):
    return [t for t in QF if left(t)>0 and blocked(t,d,h,ignore) is None]
gaps=[(c,d,h) for c in CLASSES for (d,h) in SLOTS if not S[c][f'{d},{h}']]
out=[]
for gc,gd,gh in gaps:
    out.append(f'════ {gc} {DAY_NAMES[gd]} ש{gh} ════')
    start=(gc,gd,gh)
    seen={start}
    frontier=[(start,[])]
    found=[]
    for depth in range(1,7):
        nxt=[]
        for (hc,hd,hh),path in frontier:
            # מהלך א: הזזת שיעור אחר של אותה כיתה אל החור
            for (d2,h2) in SLOTS:
                if (hc,d2,h2) in seen: continue
                t2=S[hc][f'{d2},{h2}']
                if not t2 or t2=='תל"ן': continue
                if blocked(t2,hd,hh,ignore=(hc,d2,h2)) is not None: continue
                np=path+[f'{t2}: {hc} {DAY_NAMES[d2]}ש{h2} ← עובר לחור']
                fs=[f for f in fillers(hc,d2,h2) if f!=t2]
                if fs: found.append((np,('מילוי',hc,d2,h2,fs)))
                nxt.append(((hc,d2,h2),np)); seen.add((hc,d2,h2))
            # מהלך ב: מורה מכיתה אחרת באותה שעה עובר לחור
            for cc in CLASSES:
                if (cc,hd,hh) in seen or cc==hc: continue
                t2=S[cc][f'{hd},{hh}']
                if not t2 or t2=='תל"ן': continue
                np=path+[f'{t2}: עובר מ{cc} אל {hc} באותה שעה ({DAY_NAMES[hd]}ש{hh})']
                fs=[f for f in fillers(cc,hd,hh) if f!=t2]
                if fs: found.append((np,('מילוי',cc,hd,hh,fs)))
                nxt.append(((cc,hd,hh),np)); seen.add((cc,hd,hh))
            if len(found)>=4: break
        if found: break
        frontier=nxt[:400]
    if found:
        for np,(_,fc,fd,fh,fs) in found[:4]:
            out.append(f'  ⛓ עומק {len(np)+1}:')
            for step in np: out.append(f'     {step}')
            out.append(f'     ואז נכנס ל{fc} {DAY_NAMES[fd]}ש{fh}: '+', '.join(f'{f}(+{left(f)})' for f in fs[:4]))
    else:
        out.append('  אין שרשרת עד עומק 6')
    out.append('')
io.open('chains6.txt','w',encoding='utf-8').write('\n'.join(out))
print('done')
