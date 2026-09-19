# -*- coding: utf-8 -*-
"""חיפוש רב-שלבי: מזיזים שיעורים בתוך הכיתה כדי לנדוד עם החור לשעה שבה מישהו פנוי."""
import io,json,collections,sys
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
from data2 import *
from hdata import HCLASSES,HSLOTS,HDAY,HOFF,HEV,GRADE,NEED,POOLS,HHOME
S=json.load(io.open('sol_J.json',encoding='utf-8'))
H=json.load(io.open('sol_hat.json',encoding='utf-8'))
SED=json.load(io.open('sed_J.json',encoding='utf-8'))
def tof(v): return v.split(' – ')[1] if ' – ' in v else None
def sof(v): return v.split(' – ')[0] if ' – ' in v else None
CM={'שני':1,'שלישי':2}
QF={'מרים':23,'צופיה':18,'טלי':10,'ליאור':10,'שחר':10,'דניאל':26,'דני':24,'אינס':24,
 'מירי':23,'אנה':25,'פנינה':23,'אביטל':25,'יערה':25,'לייה':23,'דליה':24,'תניה':18,
 'אורנה':18,'סימה':24,'פאני':16,'חסן':26,'שרית':28,'נעמי':20,'אלי':18,'תמיר':24,'אסיף':16,'גלית':20}
SUBJ_ONLY={'מורה חיצוני':'מתמטיקה','הדר':'מתמטיקה','ארז':'אנגלית','אופיר':'העשרה טכנולוגית','שיר':None}
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
def busy(t,d,h):
    if h<=DAY_HOURS[d] and any(S[c][f'{d},{h}']==t for c in CLASSES): return True
    if h<=HDAY[d] and any((H[c][f'{d},{h}'] or '').endswith('– '+t) for c in HCLASSES): return True
    return False
def blocked(t,d,h):
    off=list(DAYS_OFF2.get(t) or [])+list(HOFF.get(t) or [])
    if t=='צופיה': off.append('חמישי')
    if DAY_NAMES[d] in off: return 'חופש'
    if t=='טלי' and DAY_NAMES[d] not in ('שני','שלישי'): return 'ימים'
    if t=='שחר' and (DAY_NAMES[d] not in ('שני','שלישי','רביעי') or h==DAY_HOURS[d]): return 'שחר'
    if (d,h) in (UNAVAIL2.get(t,[])+EVENTS2.get(t,[])+HEV.get(t,[])): return 'סדירות'
    if t in MAGAMA.get((d,h),[]): return 'מגמות'
    for day in ('שני','שלישי'):
        if t in SED.get('קבוצת '+day,[]) and CM[day]==d and h in SED['מעגלי שיח '+day]: return 'מעגל'
    if t in ['לייה','שרית','יערה','צופיה','אסיף','אלי'] and d==2 and h in SED['ישיבת ניהול שלישי']: return 'ניהול'
    if t in ('שרית','חסן') and ((d==0 and h in(1,2,3)) or (d==3 and h in(1,2,3))): return 'ספורט'
    if busy(t,d,h): return 'מלמד'
    return None
def can_fill(lvl,gc,subj,d,h):
    """מי יכול למלא ישירות: פנוי + מכסה + מתאים למקצוע"""
    res=[]
    if lvl=='חטיבה':
        g=GRADE[gc]
        pool=POOLS.get(subj,{}).get(g,[]) if subj not in ('חינוך',) else [HHOME[gc]]
        if subj=='חינוך': pool=[HHOME[gc]]
        for t in pool:
            if t=='חסר מורה': continue
            if t=='אלי' and gc in ('ט תמיר','ט אסיף'): continue   # אלי לא בשכבת ט
            if SUBJ_ONLY.get(t) and SUBJ_ONLY[t]!=subj: continue
            if t=='מורה חיצוני' and d==5: continue
            if left(t)>0 and blocked(t,d,h) is None: res.append(t)
    else:
        for t in QF:
            if left(t)>0 and blocked(t,d,h) is None: res.append(t)
    return res
def lessons_of(lvl,gc):
    out=[]
    if lvl=='יסודי':
        for (d,h) in SLOTS:
            t=S[gc][f'{d},{h}']
            if t and t!='תל"ן': out.append((d,h,None,t))
    else:
        for (d,h) in HSLOTS:
            v=H[gc][f'{d},{h}']
            if v and 'חסר מורה' not in v and sof(v) not in ('מגמות','שירה בציבור','חינוך גופני'):
                out.append((d,h,sof(v),tof(v)))
    return out
gaps=[('יסודי',c,d,h,None) for c in CLASSES for (d,h) in SLOTS if not S[c][f'{d},{h}']]
for c in HCLASSES:
    for (d,h) in HSLOTS:
        v=H[c][f'{d},{h}']
        if v and 'חסר מורה' in v: gaps.append(('חטיבה',c,d,h,sof(v)))
out=[]
for lvl,gc,d0,h0,subj0 in gaps:
    out.append(f'════ {gc} {DAY_NAMES[d0]} ש{h0}'+(f' ({subj0})' if subj0 else '')+' ════')
    direct=can_fill(lvl,gc,subj0,d0,h0)
    if direct: out.append('   שלב 1 - ישיר: '+', '.join(f'{t}(+{left(t)})' for t in direct))
    # רב-שלבי: BFS על מיקום החור בתוך הכיתה (עד עומק 3)
    seen={(d0,h0)}
    frontier=[((d0,h0),[])]
    found=[]
    for depth in (1,2,3):
        nxt=[]
        for (dh,path) in frontier:
            for (d2,h2,sj2,t2) in lessons_of(lvl,gc):
                if (d2,h2) in seen: continue
                # אפשר להזיז את השיעור הזה אל החור?
                if blocked(t2,dh[0],dh[1]) is not None: continue
                if lvl=='חטיבה' and SUBJ_ONLY.get(t2) and t2=='מורה חיצוני' and dh[0]==5: continue
                np=path+[f'{sj2 or ""}{"·" if sj2 else ""}{t2} עובר מ{DAY_NAMES[d2]} ש{h2} לחור']
                # החור זז ל(d2,h2). מי ממלא שם?
                fillers=can_fill(lvl,gc,sj2,d2,h2) if lvl=='חטיבה' else can_fill(lvl,gc,None,d2,h2)
                fillers=[f for f in fillers if f!=t2]
                if fillers:
                    found.append((np,fillers,(d2,h2)))
                if len(found)>=3: break
                nxt.append(((d2,h2),np)); seen.add((d2,h2))
            if len(found)>=3: break
        frontier=nxt
        if found: break
    if found:
        for path,fillers,endpos in found[:3]:
            out.append('   ⛓ שרשרת: '+' -> '.join(path))
            out.append('      ואז נכנס: '+', '.join(f'{t}(+{left(t)})' for t in fillers[:4]))
    elif not direct:
        out.append('   אין מהלך עד עומק 3')
    out.append('')
io.open('deep2_out.txt','w',encoding='utf-8').write('\n'.join(out))
print("done")
