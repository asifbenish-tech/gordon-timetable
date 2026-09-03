# -*- coding: utf-8 -*-
"""מייצר viewer.html - צופה מערכות אינטראקטיבי מנתוני הפתרון."""
import io, json
from data2 import CLASSES, SLOTS, DAY_NAMES, DAY_HOURS, HOMEROOM, QUOTA, APP_ALIAS, LESSON_LABEL
from hdata import HCLASSES, HSLOTS, HDAY, HHOME, NEED, GRADE

try: _FULLN={k:v for k,v in json.load(io.open("names_map.json",encoding="utf-8")).items() if v}
except Exception: _FULLN={}
try: _ACCESS=json.load(io.open("access_map.json",encoding="utf-8"))
except Exception: _ACCESS={}
S   = json.load(io.open("sol_J.json",  encoding="utf-8"))
H   = json.load(io.open("sol_hat.json",encoding="utf-8"))
TLN = json.load(io.open("tln_map.json",encoding="utf-8"))
FIL = json.load(io.open("fills.json",  encoding="utf-8"))
SED = json.load(io.open("sed_J.json",  encoding="utf-8"))
try: DUTY = json.load(io.open("duty.json",encoding="utf-8"))
except Exception: DUTY = {}
try: CO = json.load(io.open("co_zofia3.json",encoding="utf-8"))
except Exception: CO = {}

MAGROLES={
 "2,1":[("חסן","ליווי מגמה ימית"),("רובי","אומנויות"),("שרית","בישול וספורט אתגרי"),("אסיף","חדשנות וטכנולוגיה")],
 "2,2":[("חסן","ליווי מגמה ימית"),("רובי","אומנויות"),("שרית","בישול וספורט אתגרי"),("אסיף","חדשנות וטכנולוגיה")],
 "2,3":[("חסן","ליווי מגמה ימית"),("חגית","אומנויות"),("יעל","בישול וספורט אתגרי"),("אופיר","חדשנות וטכנולוגיה")],
 "2,4":[("חסן","ליווי מגמה ימית"),("חגית","אומנויות"),("יעל","בישול וספורט אתגרי"),("אופיר","חדשנות וטכנולוגיה")],
 "4,1":[("אסיף","יזמות"),("מאמי","אומנות בתנועה"),("חסן","ספורט"),("תמיר","ימאות")],
 "4,2":[("אסיף","יזמות"),("מאמי","אומנות בתנועה"),("חסן","ספורט"),("תמיר","ימאות")],
 "4,3":[("אלי","יזמות"),("מאמי","אומנות בתנועה"),("יעל","תזונה"),("תמיר","ליווי כדורעף")],
 "4,4":[("אלי","יזמות"),("מאמי","אומנות בתנועה"),("יעל","תזונה"),("תמיר","ליווי כדורעף")]}
EXT={"2,1":"כדורעף חופים (מדריך חיצוני)","2,2":"כדורעף חופים (מדריך חיצוני)",
     "2,3":"ימאות","2,4":"ימאות",
     "4,3":"כדורעף חופים (מדריך חיצוני)","4,4":"כדורעף חופים (מדריך חיצוני)"}
MAGT={k:" · ".join(f"{t} {r}" for t,r in v)+(" · "+EXT[k] if k in EXT else "") for k,v in MAGROLES.items()}
CM={"שני":1,"שלישי":2}
NIHUL=["לייה","שרית","יערה","צופיה","אסיף"]

def away_map(hr):
    out={}
    for day in ("שני","שלישי"):
        if hr in SED.get("קבוצת "+day,[]):
            for h in SED["מעגלי שיח "+day]: out[f"{CM[day]},{h}"]="מפגשה (מעגלי שיח)"
    if hr in NIHUL:
        for h in SED["ישיבת ניהול שלישי"]: out[f"2,{h}"]="ישיבת מרכזי בית חינוך"
    return out

def _home_busy(hr, c, d, h):
    """האם מחנך/ת הכיתה תפוס/ה במקום אחר באותה שעה? מחזיר את הסיבה, או None.
       בלי הבדיקה הזו תא של חוסר הציג את המחנך/ת ככיסוי גם כשהיא מלמדת
       כיתה אחרת באותו רגע - כלומר שיבץ אותה בשתי כיתות בו-זמנית."""
    for c2 in CLASSES:
        if c2 != c and S[c2].get(f"{d},{h}") == hr: return c2
    for c2 in HCLASSES:
        v = H[c2].get(f"{d},{h}") or ""
        if hr in v.split(" – ")[-1].split(" + "): return c2   # 'שרית + חסן' = שניהם תפוסים
    a = away_map(hr).get(f"{d},{h}")
    return a or None

elem={}
for c in CLASSES:
    cells={}
    for (d,h) in SLOTS:
        k=f"{d},{h}"; t=S[c][k]; cell={"t":t}
        if t=='תל"ן' and f"{c}|{k}" in TLN: cell["t"]='תל"ן · '+TLN[f"{c}|{k}"]; cell["k"]="tln"
        elif t=='תל"ן': cell["k"]="tln"
        elif not t:
            _bz=_home_busy(HOMEROOM[c],c,d,h)
            if _bz: cell["t"]="חסר מורה"; cell["s"]=f"{HOMEROOM[c]} ב{_bz}"; cell["k"]="hole"
            else:   cell["t"]=HOMEROOM[c]; cell["s"]="מחנך/ת הכיתה - זמני"; cell["k"]="hole"
        elif f"{c}|{k}" in FIL: cell["k"]="fill"
        if t==HOMEROOM[c]: cell["k"]="home"
        if t and (c,(d,h)) in LESSON_LABEL: cell["s"]=LESSON_LABEL[(c,(d,h))]
        _tk=f"{c}|{k}"
        if t and t!='תל"ן' and _tk in TLN and TLN[_tk].startswith("חצי"):
            _tu=TLN[_tk].split('חצי תל"ן ')[1].split(" · ")[0]
            cell["co"]='½ הכיתה בתל"ן · '+_tu
            cell["k"]="half"
        cells[k]=cell
    _ED={"ה דני":3,"ה תניה":0,"ו אורנה":2,"ו שרית":1}
    if c in _ED:
        _kk=f"{_ED[c]},4"
        if _kk in cells:
            cells[_kk]["co"]="סידור חדר אוכל 🍽"
    for k,v in away_map(HOMEROOM[c]).items():
        if k in cells and cells[k].get("k")!="hole": cells[k]["away"]=v
    if c=="א אנה":
        for key in CO:
            d,h=key.split("|")[1].split(","); kk=f"{d},{h}"
            if key.startswith("anna") and kk in cells: cells[kk]["co"]="+ צופיה"
    if c=="א פנינה":
        for key in CO:
            d,h=key.split("|")[1].split(","); kk=f"{d},{h}"
            if key.startswith("pnina") and kk in cells: cells[kk]["co"]="+ צופיה"
    _plan=[]
    _actual={}
    for (d,h) in SLOTS:
        t=S[c][f"{d},{h}"]
        if t and t!='תל"ן': _actual[t]=_actual.get(t,0)+1
    _planned={t:q[c] for t,q in QUOTA.items() if c in q}
    # שם כשובר-שוויון: בלי זה הסדר משתנה בין ריצות ויוצר הבדל מדומה בקובץ
    for t in sorted(set(_planned)|set(_actual), key=lambda z:(-(_planned.get(z,0)), z)):
        _plan.append({"n":t,"want":_planned.get(t,0),"got":_actual.get(t,0)})
    _full=sum(1 for (d,h) in SLOTS if S[c][f"{d},{h}"]=='תל"ן')
    _halfs=sum(1 for (d,h) in SLOTS if TLN.get(f"{c}|{d},{h}","").startswith("חצי"))
    _plan.append({"n":'תל"ן (לכל תלמיד/ה)',"want":2,"got":_full+_halfs//2})
    elem[c]={"home":HOMEROOM[c],"cells":cells,"hours":DAY_HOURS,"plan":_plan}

try: GJ=json.load(io.open("galit_erez.json",encoding="utf-8"))
except Exception: GJ={}
jun={}
for c in HCLASSES:
    cells={}
    for (d,h) in HSLOTS:
        k=f"{d},{h}"; v=H[c][k]; cell={}
        if not v: cell={"t":"","k":"off"}
        else:
            subj,t=(v.split(" – ")+[""])[:2]
            if subj=="מגמות": cell={"t":"מגמות","s":MAGT.get(k,""),"k":"mag"}
            elif subj=="שירה בציבור": cell={"t":"שירה בציבור","s":"כל החטיבה","k":"mag"}
            elif subj=="שעת גיבוש": cell={"t":"שעת גיבוש","s":"שתי כיתות ט יחד","k":"mag"}
            elif t=="שרית + חסן": cell={"t":subj,"s":"שרית + חסן (שכבתי)","k":"pe"}
            elif t=="חסר מורה": cell={"t":subj,"s":"חסר מורה","k":"hole"}
            elif t=="צבי" and d==5:
                cell={"t":"צבי","s":"ממלא מקום"}      # שישי בט אסיף - בלי מקצוע
            else:
                cell={"t":subj,"s":t}
                if t==HHOME[c]: cell["k"]="home"
        if f"{c}|{k}" in GJ: cell["co"]="+ גלית"
        cells[k]=cell
    if c=="ז אלי" and "2,5" in cells and cells["2,5"].get("s")=="אלי":
        cells["2,5"]["co"]="זמני – עד תחילת המפגשות"
    dd=DUTY.get(c)
    if dd:
        for _d2,_dn2 in enumerate(DAY_NAMES):
            if _dn2==dd and f"{_d2},5" in cells:
                cells[f"{_d2},5"]["co"]="סידור חדר אוכל 🍽"
    _plan=[]
    _cnt={}; _mis={}
    for (d,h) in HSLOTS:
        v=H[c][f"{d},{h}"]
        if not v: continue
        sj=v.split(" – ")[0]; t=(v.split(" – ")+[""])[1]
        _cnt[sj]=_cnt.get(sj,0)+1
        if t=="חסר מורה": _mis[sj]=_mis.get(sj,0)+1
    g=GRADE[c]
    for sj,per in NEED.items():
        if per[g]==0: continue
        _plan.append({"n":sj,"want":per[g],"got":_cnt.get(sj,0),"miss":_mis.get(sj,0)})
    jun[c]={"home":HHOME[c],"cells":cells,"hours":HDAY,"duty":dd,"plan":_plan}

teachers={}
def add_t(t,side,d,h,label):
    teachers.setdefault(t,[]).append([side,d,h,label])
# כשכיתה מתפצלת או מלמדים בה שניים - כל מורה רואה במערכת שלו עם מי
def _half_tln(c,d,h):        # מורת התל"ן שלוקחת חצי כיתה בתא הזה, אם יש
    v=TLN.get(f"{c}|{d},{h}","")
    return v.split('חצי תל"ן ')[1].split(" · ")[0] if v.startswith("חצי") else None
for c in CLASSES:
    for (d,h) in SLOTS:
        t=S[c][f"{d},{h}"]
        if t and t!='תל"ן':
            _u=_half_tln(c,d,h)
            _lb=LESSON_LABEL.get((c,(d,h)))
            add_t(t,"יסודי",d,h,f"{c} · חצי כיתה עם {_u}" if _u else (f"{c} · {_lb}" if _lb else c))
for k,v in TLN.items():
    c,sl=k.split("|"); d,h=map(int,sl.split(","))
    if v.startswith("חצי"):
        _u=v.split('חצי תל"ן ')[1].split(" · ")[0]
        _with=S[c].get(f"{d},{h}") or HOMEROOM[c]
        add_t(_u,"תל\"ן",d,h,f"{c} · חצי כיתה עם {_with}")
    else:
        _pair=v.split(" + ")
        for sub in _pair:
            _oth=[z for z in _pair if z!=sub]
            add_t(sub,"תל\"ן",d,h,f"{c} · עם {' · '.join(_oth)}" if _oth else c)
for c in HCLASSES:
    for (d,h) in HSLOTS:
        v=H[c][f"{d},{h}"]
        if not v: continue
        subj,t=(v.split(" – ")+[""])[:2]
        if t and t not in ("מגמות","שירה בציבור","חסר מורה","שכבת ט יחד"):
            if t=="שרית + חסן":
                add_t("שרית","חטיבה",d,h,f"{c} · {subj}"); add_t("חסן","חטיבה",d,h,f"{c} · {subj}")
            else: add_t(t,"חטיבה",d,h,f"{c} · {subj}")

add_t("תניה","יסודי",0,3,"שיעור הדרכה")   # שעת הוראה לכל דבר (לא בכיתה)
# צופיה מצטרפת לשיעור (לא מחליפה) - שתי המורות רואות זו את זו במערכת
for _ck,_cls,_home in (("anna","א אנה","אנה"),("pnina","א פנינה","פנינה")):
    for _key in CO:
        if not _key.startswith(_ck): continue
        _d4,_h4=map(int,_key.split("|")[1].split(","))
        add_t("צופיה","יסודי",_d4,_h4,f"{_cls} · עם {_home}")
        for _ev in teachers.get(_home,[]):      # להוסיף לתווית הקיימת, לא לשכפל שעה
            if _ev[1]==_d4 and _ev[2]==_h4 and _ev[3]==_cls: _ev[3]=f"{_cls} · עם צופיה"
# ---------- מגמות: שעות המורים המובילים ----------
for k2 in GJ:
    c2,sl=k2.split("|"); d2,h2=map(int,sl.split(","))
    add_t("גלית","חטיבה",d2,h2,c2+" · אנגלית (עם ארז)")
# ---------- מחויבויות שאינן הוראה: מעגלים, ניהול, הדרכות, ישיבות ----------
_CM2={"שני":1,"שלישי":2}
for _day in ("שני","שלישי"):
    for _t in SED.get("קבוצת "+_day,[]):
        for _h in SED["מעגלי שיח "+_day]:
            add_t(_t,"סדירות",_CM2[_day],_h,"מפגשה (מעגלי שיח)")
for _t in ("לייה","שרית","יערה","צופיה","אסיף","אלי"):
    for _h in SED.get("ישיבת ניהול שלישי",[3,4]):
        add_t(_t,"סדירות",2,_h,"ישיבת מרכזי בית חינוך")
_COMMIT=[
 ("גלית",0,5,"הדרכת אנגלית (סיגל)"),("סימה",0,5,"הדרכת אנגלית (סיגל)"),
 ("שרית",0,1,"הדרכת עברית (קטיה)"),("אורנה",0,1,"הדרכת עברית (קטיה)"),
 ("אנה",0,2,"הדרכת שפה (קטיה)"),("פנינה",0,2,"הדרכת שפה (קטיה)"),("צופיה",0,2,"הדרכת שפה (קטיה)"),
 ("אביטל",0,3,"הדרכת שפה (קטיה)"),("יערה",0,3,"הדרכת שפה (קטיה)"),
 ("לייה",0,4,"הדרכת שפה (קטיה)"),("דליה",0,4,"הדרכת שפה (קטיה)"),("דניאל",0,4,"הדרכת שפה (קטיה)"),
 ("מירי",0,5,"הדרכת שפה (קטיה)"),("דני",0,5,"הדרכת שפה (קטיה)"),
 ("אסיף",3,2,"הדרכת שפה חט\"ב (זוהר)"),("נעמי",3,2,"הדרכת שפה חט\"ב (זוהר)"),
 ("הדר",1,2,"הדרכת מתמטיקה (ויקי)"),("ארז",0,5,"הדרכת אנגלית (סיגל)"),
 ("מורה חיצוני",1,5,"הדרכת מתמטיקה (ויקי)"),
 ("אלי",3,6,"ישיבת צוות חטיבה"),("נעמי",3,6,"ישיבת צוות חטיבה"),
 ("גלית",3,6,"ישיבת צוות חטיבה"),("תמיר",3,6,"ישיבת צוות חטיבה"),("אסיף",3,6,"ישיבת צוות חטיבה"),
 ("תניה",0,1,"מתחילה ב-10:00"),("תניה",0,2,"מתחילה ב-10:00"),
 ("תניה",3,1,"מתחילה ב-10:00"),("תניה",3,2,"מתחילה ב-10:00"),
 ("תמיר",1,3,"פגישות הנהלה"),("תמיר",1,4,"פגישות הנהלה"),
]
for _t,_d,_h,_lbl in _COMMIT:
    add_t(_t,"סדירות",_d,_h,_lbl)
for k,lst in MAGROLES.items():
    d,h=map(int,k.split(","))
    for t,role in lst:
        _oth=[f"{z} ({r})" for z,r in lst if z!=t]
        add_t(t,"מגמות",d,h,"מגמת "+role+(" · במקביל: "+" · ".join(_oth) if _oth else ""))
# אסיפת צוות: ראשון 6-7, כל המורים
for _t in list(teachers):
    add_t(_t,"סדירות",0,6,"אסיפת צוות"); add_t(_t,"סדירות",0,7,"אסיפת צוות")

# ---------- לוח סדירויות: מתי כל מחויבות ומי משתתף ----------
_cmt={}
_KINDS=("הדרכ","מפגשה","ישיב","אסיפ")
for _t,_evs in teachers.items():
    for _side,_d,_h,_lbl in _evs:
        if _side=="סדירות" and any(_k in _lbl for _k in _KINDS):
            _cmt.setdefault((_d,_h,_lbl),[]).append(_t)
_ALLN=sum(1 for t in teachers)
commit=[]
for (_d,_h,_lbl),_ps in sorted(_cmt.items()):
    _ps=sorted(set(_ps))
    commit.append({"d":_d,"h":_h,"n":_lbl,"p":("כל המורים" if len(_ps)>=20 else " · ".join(_ps))})

# ---------- ניצול שעות מול מכסה ----------
# מכסות לתצוגת "ניצול שעות". אצל מורות התל"ן המכסה = שעות התל"ן + שעות המגמה
# שהן מלמדות (יעל 12+4, חגית 8+2) - אחרת הן נראות חורגות בלי שהן באמת חורגות.
QUOTA_FILE={"יעל":16,"חגית":10,"דליה":24,"תמיר":24,"סימה":24,"לייה":23,"פנינה":23,"מירי":23,
 "אסיף":20,"גלית":20,"נעמי":20,"תניה":18,"אורנה":18,"הילית":16,"פאני":16,"יפעת":16,
 "ארז":8,"הדר":8,"לי-אור":10,"אינס":24,"שחר":10,"אנה":25,"אביטל":25,"מרים":25,"שיר":4,
 "דניאל":26,"צופיה":18,"רובי":6,"חסן":26,"דני":20,"טלי":10,"שרית":28,"יערה":25,
 "מאמי":10,"אופיר":2,"אלי":20,"מורה חיצוני":15}
util=[]
for t,q in sorted(QUOTA_FILE.items(), key=lambda kv:-kv[1]):
    ev=teachers.get(t,[])
    ye=sum(1 for e in ev if e[0]=="יסודי"); ch=sum(1 for e in ev if e[0]=="חטיבה")
    tl=sum(1 for e in ev if e[0]=='תל"ן'); mg=sum(1 for e in ev if e[0]=="מגמות")
    tot=ye+ch+tl+mg
    util.append({"t":t,"ye":ye,"ch":ch,"tl":tl,"mg":mg,"tot":tot,"q":q,"left":q-tot})

# ---------- חוסרים + פתרונות ----------
gapl=[]
# ---- מי פנוי לכל חוסר: חישוב מועמדים אמיתי ----
from data2 import DAYS_OFF2, UNAVAIL2, EVENTS2, MAGAMA
try: from data2 import HATIVA2
except Exception: HATIVA2={}
from hdata import HOFF as _HOFF, HEV as _HEV
_CM={"שני":1,"שלישי":2}
# מורי היסודי שנבדקים כמועמדים לחוסר. המכסה נלקחת מ-QUOTA_FILE - מקור אחד,
# אחרת עדכון מכסה מזיז את התצוגה ולא את רשימת המועמדים (מרים 23 מול 25).
_QF={t:QUOTA_FILE[t] for t in (
 "מרים","צופיה","טלי","לי-אור","שחר","דניאל","דני","אינס","מירי","אנה","פנינה",
 "אביטל","יערה","לייה","דליה","תניה","אורנה","סימה","פאני","חסן","שרית")}
_load={}
for _c in CLASSES:
    for (_d,_h) in SLOTS:
        _t=S[_c][f"{_d},{_h}"]
        if _t and _t!='תל"ן': _load[_t]=_load.get(_t,0)+1
def _free_for(d,h):
    out=[]
    for t,q in _QF.items():
        if _load.get(t,0)>=q: continue
        off=list(DAYS_OFF2.get(t) or [])
        if t=="צופיה": off.append("חמישי")
        if t=="טלי" and DAY_NAMES[d] not in ("שני","שלישי"): continue
        if t=="שחר" and DAY_NAMES[d] not in ("שני","שלישי","רביעי"): continue
        if DAY_NAMES[d] in off: continue
        if (d,h) in (UNAVAIL2.get(t,[])+EVENTS2.get(t,[])+_HEV.get(t,[])): continue
        if t in MAGAMA.get((d,h),[]): continue
        if any(S[cc][f"{d},{h}"]==t for cc in CLASSES): continue
        if h<=HDAY[d] and any((H[cc][f"{d},{h}"] or "").endswith("– "+t) for cc in HCLASSES): continue
        bad=False
        for day in ("שני","שלישי"):
            if t in SED.get("קבוצת "+day,[]) and _CM[day]==d and h in SED["מעגלי שיח "+day]: bad=True
        if t in ["לייה","שרית","יערה","צופיה","אסיף","אלי"] and d==2 and h in SED["ישיבת ניהול שלישי"]: bad=True
        if t in ("שרית","חסן") and ((d==0 and h in (1,2,3)) or (d==3 and h in (1,2,3))): bad=True
        if not bad: out.append({"t":t,"left":q-_load.get(t,0)})
    out.sort(key=lambda z:-z["left"])
    return out[:6]
def _free_ext(d,h,exclude=()):
    """פנויים בזמן אך במכסה מלאה - אופציית הגדלת משרה"""
    out=[]
    for t,q in _QF.items():
        if t in exclude or _load.get(t,0)<q: continue
        off=list(DAYS_OFF2.get(t) or [])
        if t=="צופיה": off.append("חמישי")
        if t=="טלי" and DAY_NAMES[d] not in ("שני","שלישי"): continue
        if t=="שחר" and DAY_NAMES[d] not in ("שני","שלישי","רביעי"): continue
        if DAY_NAMES[d] in off: continue
        if (d,h) in (UNAVAIL2.get(t,[])+EVENTS2.get(t,[])+_HEV.get(t,[])): continue
        if t in MAGAMA.get((d,h),[]): continue
        if any(S[cc][f"{d},{h}"]==t for cc in CLASSES): continue
        if h<=HDAY[d] and any((H[cc][f"{d},{h}"] or "").endswith("– "+t) for cc in HCLASSES): continue
        bad=False
        for day in ("שני","שלישי"):
            if t in SED.get("קבוצת "+day,[]) and _CM[day]==d and h in SED["מעגלי שיח "+day]: bad=True
        if t in ["לייה","שרית","יערה","צופיה","אסיף","אלי"] and d==2 and h in SED["ישיבת ניהול שלישי"]: bad=True
        if t in ("שרית","חסן") and ((d==0 and h in (1,2,3)) or (d==3 and h in (4,5,6))): bad=True
        if not bad: out.append({"t":t,"left":0,"ext":1})
    return out[:5]
def _why(c,d,h):
    hr=HOMEROOM.get(c)
    if not hr: return ""
    if DAY_NAMES[d] in (DAYS_OFF2.get(hr) or []): return f"{hr} (מחנך/ת) בחופש ביום {DAY_NAMES[d]}"
    for day in ("שני","שלישי"):
        if hr in SED.get("קבוצת "+day,[]) and _CM[day]==d and h in SED["מעגלי שיח "+day]:
            return f"{hr} (מחנך/ת) במפגשה (מעגל שיח)"
    if hr in ["לייה","שרית","יערה","צופיה","אסיף","אלי"] and d==2 and h in SED["ישיבת ניהול שלישי"]:
        return f"{hr} (מחנך/ת) בישיבת מרכזי בית חינוך"
    if hr in MAGAMA.get((d,h),[]): return f"{hr} (מחנך/ת) מוביל/ה מגמה"
    return f"{hr} (מחנך/ת) מלמד/ת כיתה אחרת"
for c in CLASSES:
    for (d,h) in SLOTS:
        if not S[c][f"{d},{h}"]:
            _c1=_free_for(d,h)
            gapl.append({"c":c,"d":DAY_NAMES[d],"h":h,"lvl":"elem",
                         "why":_why(c,d,h),"cand":_c1+_free_ext(d,h,[z["t"] for z in _c1])})
for c in HCLASSES:
    for (d,h) in HSLOTS:
        v=H[c][f"{d},{h}"]
        if v and "חסר מורה" in v:
            gapl.append({"c":c,"d":DAY_NAMES[d],"h":h,"lvl":"jun",
                         "subj":v.split(" – ")[0],
                         "why":("אסיף (מחנך) בחופש בשישי" if c=="ט אסיף" and d==5
                                else "אין מורה זמין למקצוע בשעה זו"),
                         "cand":_free_for(d,h)+_free_ext(d,h)})
SOLUTIONS=[
 {"t":"להחזיר מורה חטיבה אחד ליסודי","d":"אלי או גלית לבדם כיסו 9 שעות כשהורשו. הכי אפקטיבי — מורה אחד סוגר את רוב החוסרים.","i":"גבוהה"},
 {"t":"לשחרר את שחר ממגבלת השעה האחרונה","d":"היא לא משובצת בשעה אחרונה של אף יום. ביטול המגבלה סוגר מיידית את החוסרים בשעה 6 בשלישי.","i":"גבוהה"},
 {"t":"להזיז את יום החופש של דליה","d":"ג׳ דליה חסרה מורה בכמה שעות בחמישי — דליה בחופש והמורים הפנויים תפוסים. יום חופש אחר פותר את כולם.","i":"בינונית"},
 {"t":"להוריד לשרית מגמה בשלישי","d":"שרית נותנת 10 שעות שבועיות לחטיבה ולמגמות, ולכן ו׳ שרית נשארת חשופה. שחרור משעתיים מגמה מחזיר אותה לכיתה.","i":"בינונית"},
 {"t":"להעלות את לי-אור ל-10 שעות בפועל","d":"אישרת להעלות אותה מ-8 ל-10. יש לה מקום פנוי במכסה.","i":"נמוכה"},
 {"t":"להוציא את גלית ממעגל השיח בשלישי","d":"ח׳ גלית מסיימת שלישי בשעה 4 בלבד. בשעות 5-6 גלית עצמה במעגל שיח ושאר מורי ח׳ בחופש.","i":"נקודתית"},
]
# ---------- אילוצי מערכת ----------
import rules as _R
SYS_CORE=[
 ("מבנה השבוע","יסודי: א5 ב6 ג6 ד6 ה5 ו4. חטיבה: א5 ב7 ג6(ז+ח עד 5) ד6 ה7(ט עד 5) ו4."),
 ("יום המגמות","ז+ח בשלישי, ט בחמישי: מגמות ש1-4, שיעור חינוך עם המחנך בש5, ובזה מסתיים היום."),
 ("שישי ביסודי","המחנך/ת בלבד עם הכיתה (א אנה: צופיה)."),
 ("שירה בציבור","כל החטיבה בשישי ש2, אצל המחנך ונספרת לו."),
 ("מפגשה (מעגלי שיח) - שני 3-4","תדהר+עדי עם: אנה, אינס, אסיף, דליה, דני, דניאל, מירי, נעמי, תמיר."),
 ("מפגשה (מעגלי שיח) - שלישי 5-6","תדהר+גלית עם: אביטל, אורנה, אלי, גלית, יערה, לייה, פנינה, שרית, תניה."),
 ("ישיבת מרכזי בית חינוך","שלישי 3-4: לייה, שרית, יערה, צופיה, אסיף, אלי."),
 ("אסיפת צוות","ראשון 6-7: כל המורים."),
 ("חינוך גופני שכבתי","חטיבה: ראשון 1-3 ורביעי 4-6, שרית+חסן, שעה לכל שכבה."),
 ("חווה חקלאית","כיתות ג בשני 1-2 עם המחנכות."),
 ("סידור חדר אוכל - חטיבה","כל כיתת חטיבה פעם בשבוע בש5 עם המחנך, כל כיתה ביום אחר."),
 ("סידור חדר אוכל - ה+ו","משמרת ראשונה, שעה 4 עם המחנך/ת: ה דני-רביעי, ה תניה-ראשון, ו אורנה-שלישי, ו שרית-שני. בנוסף, כל שבוע כיתה אחרת נכנסת בחמישי (רוטציה חודשית)."),
 ("שוויון מקבילות","כיתות באותה שכבה לומדות אותו מספר שעות בכל יום."),
 ("חלונות","אין חלונות באמצע יום - שחרור רק בסוף היום."),
 ("תל\"ן","שעתיים בכל כיתה; יעל, חגית, יפעת והילית מלמדות תל\"ן ומעט מגמה בלבד."),
 ("תנ\"ך בכיתות ז","במערכת ללא מורה כרגע - עד גיוס."),
 ("שישי בט אסיף","ש1 שעת גיבוש שכבתית (שתי כיתות ט יחד); בשאר השעות המורה צבי נכנס."),
 ("חוסרים ביסודי","במשבצות ללא מורה מחנך/ת הכיתה נכנס/ת בינתיים - שיבוץ זמני עד לסגירת החוסר."),
]
SYS_RULES=[("["+r["id"]+"] "+r["name"]+("" if r["active"] else " — כבוי"),r["desc"]) for r in _R.RULES]
SYS_RULES+= [("— כללי היסוד של המנוע —","הכללים הבאים מובנים במנוע (engine.py). שינוי שלהם דורש עריכת קוד:")]+SYS_CORE
SYS_RULES.insert(0,("איך משנים חוק?","כל חוק מדיניות מופיע עם מזהה בסוגריים. כדי לכבות, לשנות או למחוק - אמרו לקלוד את המזהה (למשל: \"תכבה את thursday_67\") והשינוי ייכנס בריצה הבאה. החוקים שמורים בקובץ rules.py."))
# ---------- אילוצי מורים ----------
from data2 import DAYS_OFF2 as _DO
from hdata import HOFF as _HO
_TEACH_SUBJ={
 "נעמי":"מחנכת ז נעמי · שפה ז+ח · ספרות ז+ח","אלי":"מנהל החטיבה · מחנך ז אלי (8 שעות) · תנ\"ך והיסטוריה ז · היסטוריה+גיאוגרפיה ח · מגמת יזמות",
 "גלית":"מחנכת ח · אנגלית ח+ט · שיעורים עם ארז בז","תמיר":"מחנך ט תמיר · תנ\"ך ט · היסטוריה ט · אזרחות ט · 4 שעות בכיתות ו · ליווי מגמות חמישי",
 "אסיף":"מחנך ט אסיף · שפה ט · מדעים ז · חינוך פיננסי ט · מגמת יזמות","מרים":"ערבית ז+ח+ט · סטאז עברית ביסודי (13 שעות, דגש א-ג)",
 "הדר":"מתמטיקה ז (8 שעות, 2-3 ימים)","ארז":"אנגלית ז (רביעי+חמישי, 2+2)","מורה חיצוני":"מתמטיקה ח+ט (עד 3 ימים, לא שישי)",
 "שיר":"שישי בלבד - עם ז אלי (ספרות/היסטוריה/חינוך)","אופיר":"מגמת חדשנות · שעות בכיתות ו בשלישי","מאמי":"מגמת אומנות בתנועה · רב מלל ח בחמישי 5-6",
 "חסן":"ספורט יסודי · מגמות (ליווי ימית, ספורט ט)","שרית":"מחנכת ו שרית · ספורט חטיבה · מגמת בישול","פאני":"ספורט יסודי (פעמיים בשבוע לכיתה, בימים שונים)",
 "צופיה":"אנגלית ג · מקבילות עם אנה ופנינה · שישי בא אנה","לייה":"מחנכת ג לייה · תנ\"ך ח (כפול רצוף)","טלי":"יסודי (שני+שלישי בלבד)",
 "לי-אור":"יסודי (עד 3 ימים)","שחר":"יסודי (שני-רביעי, לא בשעה אחרונה)","דניאל":"מחנך ג דניאל","דני":"מחנך ה דני (20 שעות)",
 "אנה":"מחנכת א אנה","פנינה":"מחנכת א פנינה","אביטל":"מחנכת ב אביטל","יערה":"מחנכת ב יערה","דליה":"מחנכת ג דליה",
 "מירי":"מחנכת ד מירי","אינס":"מחנכת ד אינס","תניה":"מחנכת ה תניה (ראשון+רביעי מ-10:00)","אורנה":"מחנכת ו אורנה","סימה":"יסודי",
 "יעל":"תל\"ן בישול (ד-ו) · מגמה","חגית":"תל\"ן אומנות (א+ד) · מגמה","הילית":"תל\"ן פיסול","יפעת":"תל\"ן חינוך סביבתי","רובי":"מגמת אומנויות (שלישי בלבד)"}
# ---- מיפוי לאפליקציה (school-gordon): כיתות ומורים -> המזהים באתר ----
def _build_app_map():
    try:
        AC = json.load(io.open("app_data/v10_2026-2027_classes.json", encoding="utf-8"))["value"]
        AT = json.load(io.open("app_data/v10_2026-2027_teachers.json", encoding="utf-8"))["value"]
    except Exception:
        return {"classes": {}, "teachers": {}}
    alias = {v: k for k, v in APP_ALIAS.items()}   # שם בפותר -> שם באפליקציה
    cmap = {}
    for c in list(HOMEROOM) + list(HHOME.keys()):
        grade, home = c.split(" ", 1)
        first = alias.get(home, home).split()[0]
        for ac in AC:
            if ac.get("grade") == grade and (ac.get("name") or "").split()[0] == first:
                cmap[c] = {"app_id": ac["id"], "app_name": ac.get("name"), "grade": grade}
                break
    tmap = {}
    # ממוין: איטרציה על set משנה סדר בין ריצות ויוצרת הבדל מדומה בקובץ
    for t in sorted(set(list(HOMEROOM.values()) + list(HHOME.values())) | set(teachers)):
        first = alias.get(t, t)
        for at in AT:
            if (at.get("name") or "").strip().split()[0:1] == [first]:
                tmap[t] = {"app_id": at["id"],
                           "full_name": " ".join(((at.get("name") or "") + " " + (at.get("lastName") or "")).split())}
                break
    return {"classes": cmap, "teachers": tmap}
APP_MAP = _build_app_map()

def _now():   # שעון ישראל, כדי שחותמת העדכון תהיה מובנת
    import datetime
    try:
        from zoneinfo import ZoneInfo
        return datetime.datetime.now(ZoneInfo("Asia/Jerusalem"))
    except Exception:
        return datetime.datetime.utcnow()+datetime.timedelta(hours=3)

TR=[]
for t,subj in _TEACH_SUBJ.items():
    off=_DO.get(t) or _HO.get(t) or []
    ev=teachers.get(t,[])
    TR.append({"t":t,"off":", ".join(off) if off else "—","subj":subj,"n":len(ev)})
_HOUSES={"A":{"name":"בית א","kind":"elem","classes":[c for c in CLASSES if c[0] in "אבג"]},
         "B":{"name":"בית ב","kind":"elem","classes":[c for c in CLASSES if c[0] in "דהו"]},
         "C":{"name":"בית ג","kind":"jun","classes":list(HCLASSES)}}
_HT={}
for _hk,_hv in _HOUSES.items():
    _cset=set(_hv["classes"]); _ts=set()
    for _t2,_evs in teachers.items():
        for _side,_d3,_h3,_lbl in _evs:
            _cls=_lbl.split(" · ")[0] if _side=="חטיבה" else _lbl
            if _side in ("יסודי","חטיבה",'תל"ן') and _cls in _cset: _ts.add(_t2); break
    _HT[_hk]=sorted(_ts)
data={"rules":SYS_RULES,"trules":TR,"util":util,"gaps":gapl,"sol":SOLUTIONS,"elem":elem,"jun":jun,"teachers":{k:sorted(v,key=lambda z:(z[1],z[2])) for k,v in sorted(teachers.items())},"commit":commit,
      "days":DAY_NAMES,"legend_sed":{k:v for k,v in SED.items() if "קבוצת" not in k},
      "full_names":_FULLN,"access":_ACCESS,"houses":_HOUSES,"house_teachers":_HT,"app_map":APP_MAP,
      "built":_now().strftime("%d.%m.%Y %H:%M")}

html = io.open("viewer_template.html", encoding="utf-8").read()
html = html.replace("/*__DATA__*/", "const DATA="+json.dumps(data,ensure_ascii=False)+";")
io.open("viewer.html","w",encoding="utf-8").write(html)
# index.html - הפניה עם חותמת גרסה שנקבעת בזמן הריצה (Date.now).
# קודם החותמת הוטבעה כאן בזמן הבנייה, ולכן דפדפן ששמר את index.html
# במטמון המשיך להפנות לגרסה הישנה - וזו בדיוק הסיבה שמורה יכול היה
# לראות מערכת לא מעודכנת. עכשיו התוכן של index.html קבוע (אפשר
# לשמור אותו במטמון בלי נזק) והכתובת של הלוח ייחודית בכל כניסה.
_v = _now().strftime("%Y%m%d%H%M")
io.open("index.html", "w", encoding="utf-8").write(
 '<!doctype html>\n<html lang="he" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
 '<title>\u05dc\u05d5\u05d7 \u05d2\u05d5\u05e8\u05d3\u05d5\u05df</title>\n'
 '<script>location.replace("viewer.html?v=" + Date.now());</script>\n'
 '<noscript><meta http-equiv="refresh" content="0; url=viewer.html?v=' + _v + '"></noscript>\n'
 '</head>\n<body>\n<p style="font-family:sans-serif;text-align:center;margin-top:3rem">\n'
 '\u05de\u05e2\u05d1\u05d9\u05e8 \u05dc\u05dc\u05d5\u05d7 \u05d4\u05de\u05e2\u05e8\u05db\u05d5\u05ea\u2026 '
 '<a href="viewer.html?v=' + _v + '">\u05dc\u05d7\u05e6\u05d5 \u05db\u05d0\u05df \u05d0\u05dd '
 '\u05dc\u05d0 \u05d4\u05d5\u05e2\u05d1\u05e8\u05ea\u05dd</a>\n</p>\n'
 '</body>\n</html>\n')
print("viewer.html נוצר,", len(html)//1024, "KB | index.html v="+_v)
