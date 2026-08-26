# -*- coding: utf-8 -*-
"""ניתוח עמוק: לכל חוסר - מי חסום ולמה, ואילו שרשראות החלפה קיימות."""
import io,json,collections,sys
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
from data2 import *
from hdata import HCLASSES,HSLOTS,HDAY,HOFF,HEV,GRADE,NEED,POOLS,CAP,HHOME
S=json.load(io.open('sol_J.json',encoding='utf-8'))
H=json.load(io.open('sol_hat.json',encoding='utf-8'))
SED=json.load(io.open('sed_J.json',encoding='utf-8'))
def tof(v): return v.split(' – ')[1] if ' – ' in v else None
def sof(v): return v.split(' – ')[0] if ' – ' in v else None
CM={'שני':1,'שלישי':2}
QF={'מרים':23,'צופיה':18,'טלי':10,'ליאור':10,'שחר':10,'דניאל':26,'דני':24,'אינס':24,
 'מירי':23,'אנה':25,'פנינה':23,'אביטל':25,'יערה':25,'לייה':23,'דליה':24,'תניה':18,
 'אורנה':18,'סימה':24,'פאני':16,'חסן':26,'שרית':28,'נעמי':20,'אלי':18,'תמיר':24,'אסיף':16,
 'גלית':20,'מורה חיצוני':15,'הדר':8,'ארז':8,'אופיר':4}
el=collections.Counter(); hl=collections.Counter()
for c in CLASSES:
    for s2 in SLOTS:
        t=S[c][f'{s2[0]},{s2[1]}']
        if t and t!='תל"ן': el[t]+=1
for c in HCLASSES:
    for s2 in HSLOTS:
        t=tof(H[c][f'{s2[0]},{s2[1]}'])
        if t and t!='חסר מורה': hl[t]+=1
def left(t): return QF.get(t,0)-el.get(t,0)-hl.get(t,0)
def where(t,d,h):
    for c in CLASSES:
        if S[c][f'{d},{h}']==t: return ('יסודי',c,None)
    if h<=HDAY[d]:
        for c in HCLASSES:
            v=H[c][f'{d},{h}']
            if v and tof(v)==t: return ('חטיבה',c,sof(v))
    return None
def blocked(t,d,h):
    off=list(DAYS_OFF2.get(t) or [])+list(HOFF.get(t) or [])
    if t=='צופיה': off.append('חמישי')
    if DAY_NAMES[d] in off: return 'יום חופש'
    if t=='טלי' and DAY_NAMES[d] not in ('שני','שלישי'): return 'ימי עבודה'
    if t=='שחר' and (DAY_NAMES[d] not in ('שני','שלישי','רביעי') or h==DAY_HOURS[d]): return 'מגבלת שחר'
    if (d,h) in (UNAVAIL2.get(t,[])+EVENTS2.get(t,[])+HEV.get(t,[])): return 'סדירות'
    if t in MAGAMA.get((d,h),[]): return 'מגמות'
    for day in ('שני','שלישי'):
        if t in SED.get('קבוצת '+day,[]) and CM[day]==d and h in SED['מעגלי שיח '+day]: return 'מעגל שיח'
    if t in ['לייה','שרית','יערה','צופיה','אסיף','אלי'] and d==2 and h in SED['ישיבת ניהול שלישי']: return 'ישיבת ניהול'
    if t in ('שרית','חסן') and ((d==0 and h in(1,2,3)) or (d==3 and h in(1,2,3))): return 'ספורט חטיבה'
    w=where(t,d,h)
    if w: return f'מלמד {w[1]}'
    return None
# ---- רשימת החוסרים ----
gaps=[('יסודי',c,d,h,None) for c in CLASSES for (d,h) in SLOTS if not S[c][f'{d},{h}']]
for c in HCLASSES:
    for (d,h) in HSLOTS:
        v=H[c][f'{d},{h}']
        if v and 'חסר מורה' in v: gaps.append(('חטיבה',c,d,h,sof(v)))
out=['מורים עם יתרת שעות: '+', '.join(f'{t}(+{left(t)})' for t in sorted(QF,key=lambda z:-left(z)) if left(t)>0),'']
for lvl,gc,d,h,subj in gaps:
    out.append(f'════ {gc} {DAY_NAMES[d]} ש{h}'+(f' ({subj})' if subj else '')+' ════')
    # מי המורים הרלוונטיים לכיתה הזו
    if lvl=='חטיבה':
        g=GRADE[gc]
        cand=set()
        for sj,pools in POOLS.items():
            if NEED.get(sj,{}).get(g,0)>0:
                for t in pools.get(g,[]): cand.add(t)
        cand |= {HHOME[gc]}
    else:
        cand=set(QF)-{'מורה חיצוני','הדר','ארז','אופיר','גלית'}
    lines=0
    for t in sorted(cand):
        if t=='חסר מורה' or t not in QF: continue
        b=blocked(t,d,h)
        if b is None and left(t)>0:
            out.append(f'   ✔ {t} פנוי! (+{left(t)})'); lines+=1
        elif b and b.startswith('מלמד') and left(t)==0:
            pass
        elif b and b.startswith('מלמד'):
            c2=b.split(' ',1)[1]
            subs=[y for y in QF if y!=t and left(y)>0 and blocked(y,d,h) is None]
            if subs:
                out.append(f'   ⛓ {t} {b} -> יכולים להחליפו שם: '+', '.join(f'{y}(+{left(y)})' for y in subs[:4])); lines+=1
    if not lines:
        why=collections.Counter()
        for t in sorted(cand):
            if t in QF:
                b=blocked(t,d,h) or ('מכסה מלאה' if left(t)<=0 else '?')
                why[b]+=1
        out.append('   אין אף מהלך: '+', '.join(f'{k}×{v}' for k,v in why.most_common(6)))
    out.append('')
io.open('deep_out.txt','w',encoding='utf-8').write('\n'.join(out))
print("done")
