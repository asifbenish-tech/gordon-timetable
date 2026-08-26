# -*- coding: utf-8 -*-
"""מרכיב את solveALL.py: פותר מאוחד יסודי+חטיבה במודל CP-SAT אחד."""
import io, re

srcE = io.open("solveEI.py", encoding="utf-8").read()
srcH = io.open("solveH.py",  encoding="utf-8").read()

# ---- פיצול build/emit ----
iE = srcE.index("sol=cp_model.CpSolver()")
buildE, emitE = srcE[:iE], srcE[iE:]
iH = srcH.index("sol=cp_model.CpSolver()")
buildH, emitH = srcH[:iH], srcH[iH:]

# ---- E: הרחבת ה-POOL במורי חטיבה -> מילוי חורים נטיבי ----
buildE = buildE.replace(
 'POOL={"טלי":(3,B_CL),',
 'POOL={"אלי":(4,["ו אורנה","ו שרית"]),"אופיר":(3,["ו אורנה","ו שרית"]),"טלי":(3,B_CL),')

# ---- E: המרת המטרה למשתנה ----
buildE = buildE.replace("m.Minimize(", "OBJ_E=(", 1)

# ---- E: נעילת החלטות הסדירויות לערכי sed_J (עקביות מול צד החטיבה) ----
buildE += '''
# ---- נעילת סדירויות לפי sed_J.json (החלטות מאושרות) ----
_SEDF=json.load(io.open("sed_J.json",encoding="utf-8"))
for _t in ALLC:
    if False: pass
    elif _t in _SEDF["קבוצת שני"]:   m.Add(gm[_t]==1)
    elif _t in _SEDF["קבוצת שלישי"]: m.Add(gm[_t]==0)
# שלישי: רק שני שילובים אפשריים (מגמות תופסות 1-4). נעילה למצב המקורי.
for _h in range(1,7):
    if ("u",_h) in blkh: m.Add(blkh[("u",_h)]==(1 if _h in (5,6) else 0))
m.Add(nst[0]==1)
_hm={5,6}
for _h in range(1,7):
    if ("m",_h) in blkh: m.Add(blkh[("m",_h)]==(1 if _h in _hm else 0))

# ---- חסימת מורי חטיבה בצד היסודי לפי ימי החופש והסדירויות שלהם ----
from hdata import HOFF as _HOFF, HEV as _HEV
# אופיר: עד 3 שעות בכיתות ו, רק ביום שלישי
for _ko in [k for k in x if k[2]=="אופיר" and k[1][0]!=2]:
    m.Add(x[_ko]==0)
# אלי: בדיוק שעתיים מתמטיקה בכל אחת מכיתות ו
for _c6 in ("ו אורנה","ו שרית"):
    _v6=[x[k] for k in x if k[2]=="אלי" and k[0]==_c6]
    if _v6: m.Add(sum(_v6)==2)
_MENT=["אלי","גלית","תמיר","נעמי","צבי","רובי"]
for _t in _MENT:
    for _k in [k for k in x if k[2]==_t]:
        _d,_h=_k[1]
        if DAY_NAMES[_d] in _HOFF.get(_t,[]) or (_d,_h) in _HEV.get(_t,[]):
            m.Add(x[_k]==0)
'''

# ---- H: ביטול חסימה מקובץ; שמירת חסימות הסדירויות ----
buildH = buildH.replace('E=json.load(io.open("sol_J.json",encoding="utf-8"))', 'E=None')
buildH = buildH.replace('''for c in ECL:
    for (d,h) in ESL:
        t=E[c][f"{d},{h}"]
        if t and t!='תל"ן': ebusy[t].add((d,h))''', 'pass  # הקישור ליסודי נעשה במודל המאוחד')

# ---- H: מניעת התנגשות שמות עם E ----
for old,new in (("x","hx"),("free","hfree"),("pe","hpe"),("SED","HSED"),
                ("CM","HCM"),("ebusy","hebusy"),("tblk","htblk")):
    buildH = re.sub(rf"\b{old}\b", new, buildH)
    emitH  = re.sub(rf"\b{old}\b", new, emitH)
buildH = buildH.replace("m=cp_model.CpModel()", "# מודל משותף (מוגדר בצד היסודי)")
buildH = buildH.replace("m.Minimize(", "OBJ_H=(", 1)

# ---- emit: הסרת יצירת solver כפולה ----
def strip_solver(txt):
    lines = txt.split("\n")
    out=[]
    for ln in lines:
        if ln.startswith("sol=cp_model.CpSolver") or ln.startswith("st=sol.Solve"):
            continue
        out.append(ln)
    return "\n".join(out)
emitE = strip_solver(emitE)
emitH = strip_solver(emitH)

# ---- הרכבה ----
final = '''# -*- coding: utf-8 -*-
# ============================================================
#  solveALL.py - פותר מאוחד: יסודי + חטיבה במודל CP-SAT אחד
#  נוצר אוטומטית ע"י make_unified.py משני הפותרים המקוריים.
#  היתרון: הפותר רואה שרשראות השפעה בין שני בתי הספר -
#  הזזת מורה ביסודי משפיעה מיידית על החטיבה ולהפך.
# ============================================================

''' + buildE + '''

# ================= צד החטיבה (בתוך אותו מודל) =================
''' + buildH + '''

# ================= קישור צולב: מורה אחד בכל רגע =================
_ET=set(k[2] for k in x); _HT=set(k[3] for k in hx)
CROSS=sorted(_ET & _HT)
_nlink=0
for _t in CROSS:
    for _d in range(6):
        for _h in range(1,8):
            _ev=[x[k] for k in x  if k[2]==_t and k[1]==(_d,_h)]
            _hv=[hx[k] for k in hx if k[3]==_t and k[1]==(_d,_h)]
            if _ev and _hv:
                m.Add(sum(_ev)+sum(_hv)<=1); _nlink+=1
print(f"קישור צולב: {len(CROSS)} מורים משותפים, {_nlink} אילוצי בו-זמניות")

# ---- תקרה כוללת אמיתית (יסודי+חטיבה) למורים המשותפים ----
_MAG={"אסיף":4,"אלי":2,"חסן":6,"שרית":2,"רובי":2,"מאמי":4,"יעל":4,"חגית":2,"אופיר":2}
_QUOTA={"אלי":20,"גלית":20,"תמיר":24,"נעמי":20,"צבי":12,"רובי":6,
        "מרים":23,"לייה":23,"אסיף":20,"שרית":28,"חסן":26}
_TOTCAP={t:q-_MAG.get(t,0) for t,q in _QUOTA.items()}   # מכסה פחות שעות המגמה
for _t,_capv in _TOTCAP.items():
    _ev=[x[k] for k in x  if k[2]==_t]
    _hv=[hx[k] for k in hx if k[3]==_t]
    if _ev or _hv: m.Add(sum(_ev)+sum(_hv)<=_capv)

# ---- NOGAP_CROSS: בלי חלונות למורים נבחרים, על פני שני בתי הספר ----
for _t in ("תמיר",):
    for _d in range(6):
        _busy={}
        for _h in range(1,8):
            from hdata import HEV as _NGHEV
            if (_d,_h) in _NGHEV.get(_t,[]) or (_t=="תמיר" and _d==4 and _h in (1,2,3,4)):
                _busy[_h]=1; continue              # פגישות/ליווי = תפוס (לא חלון)
            _v =[x[k]  for k in x  if k[2]==_t and k[1]==(_d,_h)]
            _v+=[hx[k] for k in hx if k[3]==_t and k[1]==(_d,_h)]
            if not _v: continue
            _b=m.NewBoolVar(f"ng_{_t}_{_d}_{_h}"); m.AddMaxEquality(_b,_v); _busy[_h]=_b
        _hs=sorted(_busy)
        for _i in range(len(_hs)):
            for _j in range(_i+2,len(_hs)):
                for _kk in range(_i+1,_j):
                    _e1=_busy[_hs[_i]];_e2=_busy[_hs[_j]];_e3=_busy[_hs[_kk]]
                    if isinstance(_e3,int): continue
                    _t1=_e1 if not isinstance(_e1,int) else None
                    _t2=_e2 if not isinstance(_e2,int) else None
                    if _t1 is None and _t2 is None: m.Add(_e3>=1)
                    elif _t1 is None: m.Add(_t2-_e3<=0)
                    elif _t2 is None: m.Add(_t1-_e3<=0)
                    else: m.Add(_t1+_t2-_e3<=1)

# ---- PARALLEL_EQ: כיתות מקבילות מסיימות באותה שעה בכל יום ----
import collections as _cl
_bygrade=_cl.defaultdict(list)
for _c in HCLASSES: _bygrade[GRADE[_c]].append(_c)
_neq=0
for _g,_cs in _bygrade.items():
    if len(_cs)<2: continue
    for _d in range(6):
        _tot=[]
        for _c in _cs:
            _v=[hx[k] for k in hx if k[0]==_c and k[1][0]==_d]
            _iv=m.NewIntVar(0,HDAY[_d],f"pq_{_c}_{_d}")
            m.Add(_iv==sum(_v)); _tot.append(_iv)
        for _i in range(1,len(_tot)):
            if _g=="ט" and _d==2: _neq+=1; continue   # שלישי: ט תמיר מסיים ב-5, ט אסיף ב-6
            m.Add(_tot[0]==_tot[_i]); _neq+=1
print(f"שוויון מקבילות: {_neq} אילוצים")

# ---- WARM START: רמז מהפתרון הקודם -> פתרון מהיר בהרבה ----
_H={}
try:
    _pE=json.load(io.open("sol_J.json",encoding="utf-8"))
    for k,v in x.items():
        _c,(_d,_h),_t = k
        _H[v.Index()]=(v, 1 if _pE.get(_c,{}).get(f"{_d},{_h}")==_t else 0)
    _pH=json.load(io.open("sol_hat.json",encoding="utf-8"))
    for k,v in hx.items():
        _c,(_d,_h),_sj,_t = k
        _H[v.Index()]=(v, 1 if _pH.get(_c,{}).get(f"{_d},{_h}")==f"{_sj} – {_t}" else 0)
    for _vv,_val in _H.values(): m.AddHint(_vv,_val)
    print(f"warm start: {len(_H)} רמזים")
except Exception as _e:
    print("ללא warm start:",_e)

# ================= מטרה משולבת + פתרון =================
m.Minimize(OBJ_E + OBJ_H)
sol=cp_model.CpSolver()
import os as _os
sol.parameters.max_time_in_seconds=float(_os.environ.get("TL","150"))
sol.parameters.num_workers=8
sol.parameters.random_seed=7
st=sol.Solve(m)
print("status:", sol.StatusName(st))

''' + emitE + '''

# ================= פלט צד החטיבה =================
''' + emitH + '''

# ================= fills.json: תאי כיסוי (לצביעה באקסל) =================
if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    _S=json.load(io.open("sol_J.json",encoding="utf-8"))
    _FILLSET={"אלי","גלית","תמיר","נעמי","צבי","רובי"}
    _fills={}
    for _c in CLASSES:
        for (_d,_h) in SLOTS:
            _t=_S[_c][f"{_d},{_h}"]
            if _t in _FILLSET:
                _fills[f"{_c}|{_d},{_h}"]=_t
    io.open("fills.json","w",encoding="utf-8").write(json.dumps(_fills,ensure_ascii=False,indent=1))
    print("fills:",len(_fills),"תאי כיסוי ממורי חטיבה")
'''
io.open("solveALL.py","w",encoding="utf-8").write(final)
print("solveALL.py נוצר,", len(final.split(chr(10))), "שורות")
