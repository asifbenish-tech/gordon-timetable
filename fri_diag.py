# -*- coding: utf-8 -*-
import io
from hdata import *
o=['יום שישי לכיתות ז - מי יכול ללמד מה (ארז כבר לא בשישי... הוא מעולם לא היה):','']
FRI=[t for t in CAP if 'שישי' not in HOFF.get(t,[])]
o.append('זמינים בשישי: '+', '.join(sorted(FRI)))
o.append('')
for c in [c for c in HCLASSES if GRADE[c]=='ז']:
    g='ז'; opts={}
    for subj,per in NEED.items():
        if per[g]==0 or subj in ('מגמות','חינוך גופני','שירה בציבור'): continue
        pool=[HHOME[c]] if subj=='חינוך' else POOLS[subj].get(g,[])
        if c=='ז אלי' and subj=='חינוך': pool=pool+['שיר']
        if c=='ז אלי' and subj=='רב מלל': pool=pool  # שיר כבר בפול
        av=[t for t in pool if t in FRI]
        if av: opts[subj]=av
    o.append(f'{c}:')
    for subj,av in opts.items(): o.append(f'   {subj}: '+', '.join(av))
o.append('')
o.append('שישי ז: צריך למלא ש1 (לפני שירה בש2), ואפשר ש3-4 או שחרור.')
o.append('מתמטיקה ירדה ל-4 שכולן אצל הדר (לא בשישי) -> צבי כבר לא במשחק בשישי!')
io.open('fd.txt','w',encoding='utf-8').write(chr(10).join(o))
