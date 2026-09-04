# -*- coding: utf-8 -*-
import io, json, collections
from data2 import *
from hdata import HCLASSES, HSLOTS
def tof(v): return v.split(' – ')[1] if ' – ' in v else None
def build():
    S=json.load(io.open('sol_J.json',encoding='utf-8'))
    H=json.load(io.open('sol_hat.json',encoding='utf-8'))
    T=json.load(io.open('tln_map.json',encoding='utf-8'))
    CO=json.load(io.open('co_zofia3.json',encoding='utf-8'))
    try: ZH=json.load(io.open('zvi_hila.json',encoding='utf-8'))   # צבי מצטרף להילה
    except Exception: ZH={}
    MAG={(2,1):['חסן','רובי','שרית','אסיף'],(2,2):['חסן','רובי','שרית','אסיף'],
         (2,3):['חסן','חגית','יעל','אופיר'],(2,4):['חסן','חגית','יעל','אופיר'],
         (4,1):['חסן','מאמי','אסיף'],(4,2):['חסן','מאמי','אסיף'],
         (4,3):['אלי','יעל','מאמי'],(4,4):['אלי','יעל','מאמי']}
    E=collections.Counter(); Hh=collections.Counter(); TL=collections.Counter()
    MG=collections.Counter(); PEc=collections.Counter()
    for c in CLASSES:
        for s in SLOTS:
            t=S[c][f'{s[0]},{s[1]}']
            if t and t!='תל"ן': E[t]+=1
    seenPE=set()
    for c in HCLASSES:
        for s in HSLOTS:
            t=tof(H[c][f'{s[0]},{s[1]}'])
            if t=='שרית + חסן':
                if s not in seenPE: seenPE.add(s); PEc['שרית']+=1; PEc['חסן']+=1
            elif t and t not in ('מגמות','שירה בציבור'): Hh[t]+=1
    for k,v in T.items():
        for sub in v.split(' + '): TL[sub]+=1
    for k,l in MAG.items():
        for t in l: MG[t]+=1
    # המכסות מגיעות מ-data2 (מקור אחד). קודם הייתה כאן טבלה נפרדת שהתיישנה:
    # מרים 23 במקום 25, צופיה 23 במקום 18, וגם "ליאור" שכבר לא קיים אחרי
    # שהשם תוקן ל"לי-אור" - כלומר גיליון האקסל הציג מספרים לא נכונים.
    from data2 import QUOTA_FILE as Q
    rows=[]
    for t,q in Q.items():
        zo=len(CO) if t=='צופיה' else 0
        zh=sum(1 for v in ZH.values() if v==t)      # הצטרפות לשיעור של מורה אחר/ת
        tot=E[t]+Hh[t]+PEc[t]+TL[t]+MG[t]+zo+zh
        rows.append([t,E[t],Hh[t]+PEc[t],TL[t],MG[t],zo,tot,q,q-tot])
    rows.sort(key=lambda r:(r[8], -r[7]))
    return rows
