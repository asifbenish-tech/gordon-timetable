# -*- coding: utf-8 -*-
import json, io, collections, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from data2 import *
from hdata import HCLASSES, GRADE, HHOME, HDAY, HSLOTS, NEED
E=json.load(io.open("sol_J.json",encoding="utf-8"))
H=json.load(io.open("sol_hat.json",encoding="utf-8"))
D=json.load(io.open("sed_J.json",encoding="utf-8"))
wb=openpyxl.Workbook(); wb.remove(wb.active)
th=Side(style="thin",color="B0B0B0"); BO=Border(left=th,right=th,top=th,bottom=th)
HDRF=PatternFill("solid",fgColor="2F5597"); HF=Font(bold=True,color="FFFFFF")
HDRG=PatternFill("solid",fgColor="7030A0")
HR=PatternFill("solid",fgColor="DCE6F1"); FR=PatternFill("solid",fgColor="FFF2CC")
TL=PatternFill("solid",fgColor="E2EFDA"); AW=PatternFill("solid",fgColor="FCE4D6")
MG=PatternFill("solid",fgColor="D9E1F2"); CO=json.load(io.open("co_zofia3.json",encoding="utf-8"))
FILLS=json.load(io.open("fills.json",encoding="utf-8"))
FILLMAP={}
for _k,_t in FILLS.items():
    _c,_sl=_k.split("|"); _d,_h=_sl.split(",")
    FILLMAP[(_c,(int(_d),int(_h)))]=_t
FILLFILL=PatternFill("solid",fgColor="00B0F0")
try: TLNMAP=json.load(io.open("tln_map.json",encoding="utf-8"))
except Exception: TLNMAP={}
from data2 import MAG_ROLES, MAG_EXT, NIHUL
from hdata import FRIDAY_H1, FRIDAY_COVER, PE_BLOCKS as _PEB   # מגמות - מקור אחד ב-data2 (לא לכתוב כאן שמות)
MAGT={k:" / ".join(t for t,_r in v) for k,v in MAG_ROLES.items()}
COMAP={}
for _k in CO:
    _tag,_sl=_k.split("|"); _d,_h=_sl.split(",")
    COMAP[("א אנה" if _tag=="anna" else "א פנינה",(int(_d),int(_h)))]="צופיה"
COFILL=PatternFill("solid",fgColor="D5A6BD")
CEN=Alignment(horizontal="center",vertical="center",wrap_text=True)
CM={"שני":1,"שלישי":2}

def _home_busy(hr, c, d, h, away):
    """המחנך/ת תפוס/ה במקום אחר באותה שעה? (אותו כלל כמו בלוח - make_viewer._home_busy).
       אם כן - התא הוא "חסר מורה" ולא "מחנך/ת (זמני)", אחרת היא משובצת בשני מקומות."""
    if (d, h) in away: return away[(d, h)]
    if DAY_NAMES[d] in (DAYS_OFF2.get(hr) or []): return f"{hr} בחופש"
    for c2 in CLASSES:
        if c2 != c and E[c2].get(f"{d},{h}") == hr: return f"{hr} מלמד/ת ב{c2}"
    for c2 in HCLASSES:
        v = H[c2].get(f"{d},{h}") or ""
        if hr in v.split(" – ")[-1].split(" + "): return f"{hr} מלמד/ת ב{c2}"
    if hr in MAGAMA.get((d, h), []): return f"{hr} במגמות"
    return None

def grid(ws,title,home,cells,dayhours,hdr,away,cls=None,hcls=None):
    ws.sheet_view.rightToLeft=True
    ws["A1"]=title; ws["A1"].font=Font(bold=True,size=14); ws.merge_cells("A1:G1"); ws["A1"].alignment=CEN
    for i,v in enumerate(["שעה"]+DAY_NAMES):
        c=ws.cell(row=2,column=1+i,value=v); c.fill=hdr; c.font=HF; c.alignment=CEN; c.border=BO
    for h in range(1,max(dayhours)+1):
        rc=ws.cell(row=2+h,column=1,value=h); rc.fill=hdr; rc.font=HF; rc.alignment=CEN; rc.border=BO
        for d in range(6):
            cell=ws.cell(row=2+h,column=2+d); cell.alignment=CEN; cell.border=BO
            if h>dayhours[d]: cell.fill=PatternFill("solid",fgColor="F2F2F2"); continue
            v=cells.get((d,h),"")
            if not v:
                _busy=_home_busy(home,cls,d,h,away) if cls is not None else None
                if cls is not None and not _busy:         # חוסר ביסודי: מחנך/ת הכיתה פנוי/ה ונכנס/ת בינתיים
                    cell.value=f"{home} (זמני)"
                    cell.comment=openpyxl.comments.Comment("מחנך/ת הכיתה נכנס/ת בינתיים - שיבוץ זמני עד סגירת החוסר","מערכת")
                elif cls is not None and "מפגשה" in _busy:   # מפגשה פעם בשלושה שבועות: בשאר השבועות המחנך/ת נכנס/ת
                    cell.value=f"{home} (זמני)"
                    cell.comment=openpyxl.comments.Comment(f"בשבוע של מפגשה (פעם בשלושה שבועות) - חסר מורה. בשאר השבועות {home} נכנס/ת","מערכת")
                elif cls is not None:                     # המחנך/ת תפוס/ה - אין מי שייכנס
                    cell.value="חסר מורה"
                    cell.comment=openpyxl.comments.Comment(f"אין מורה: {_busy}","מערכת")
                else:
                    cell.value="חסר מורה"
                cell.fill=PatternFill("solid",fgColor="FF9999"); cell.font=Font(bold=True,color="990000")
                cell.border=BO; continue
            if d==5 and hcls:                              # שישי ט: אותה תצוגה כמו בלוח (hdata)
                _sj,_t=(v.split(" – ")+[""])[:2]
                if _sj=="ליווי" and hcls in FRIDAY_H1:
                    _sh=FRIDAY_H1[hcls].get("show"); v=f"{_sh} – {_t}" if _sh else _t
                elif hcls in FRIDAY_COVER and _t==FRIDAY_COVER[hcls]["teacher"] and _sj!="שירה בציבור":
                    _sh=FRIDAY_COVER[hcls].get("show"); v=f"{_sh} – {_t}" if _sh else _t
            cell.value=v
            if cls is not None and (cls,(d,h)) in FILLMAP:
                cell.fill=FILLFILL; cell.font=Font(bold=True,color="FFFFFF")
                cell.comment=openpyxl.comments.Comment(
                    "מורה שהוכנס לכיסוי חלון – "+FILLMAP[(cls,(d,h))],"מערכת")
                cell.border=BO; continue
            if cls is not None and (cls,(d,h)) in COMAP:
                cell.value=v+"  + צופיה"
                cell.fill=COFILL
                cell.comment=openpyxl.comments.Comment(
                    "צופיה מצטרפת לשיעור (שתי מורות בכיתה) – היא אינה מחליפה את "+home,"מערכת")
                cell.border=BO; continue
            _tk=f"{cls}|{d},{h}" if cls else None
            if v=='תל"ן' and _tk in TLNMAP: cell.value='תל"ן – '+TLNMAP[_tk]   # שמות המורות גם כשהמחנכת בחוץ
            if (d,h) in away:
                cell.fill=AW; cell.comment=openpyxl.comments.Comment(f"{home} בחוץ: {away[(d,h)]}","מערכת")
            elif "מגמות" in v:
                cell.fill=MG
                if (d,h) in MAGT: cell.value="מגמות – "+MAGT[(d,h)]
            elif d==5: cell.fill=FR
            elif v==home or v.endswith("– "+home): cell.fill=HR
            elif v=='תל"ן':
                cell.fill=TL
            else:
                _tk2=f"{cls}|{d},{h}" if cls else None
                if _tk2 and _tk2 in TLNMAP and TLNMAP[_tk2].startswith("חצי"):
                    _u2=TLNMAP[_tk2].split('חצי תל"ן ')[1].split(" · ")[0]
                    cell.value=v+'  (½ כיתה בתל"ן – '+_u2+")"
                    cell.fill=TL
    ws.column_dimensions["A"].width=8
    for d in range(6): ws.column_dimensions[get_column_letter(2+d)].width=22

for c in CLASSES:                                     # ---- יסודי ----
    ws=wb.create_sheet(c[:31]); hr=HOMEROOM[c]; away={}
    for day in ("שני","שלישי"):
        if hr in D["קבוצת "+day]:
            for h in D["מעגלי שיח "+day]: away[(CM[day],h)]="מפגשה (מעגלי שיח)"
    if hr in NIHUL:
        for h in D["ישיבת ניהול שלישי"]: away[(2,h)]="ישיבת מרכזי בית חינוך"
    grid(ws,f"יסודי – כיתה {c}   (מחנך/ת: {hr})",hr,
         {(d,h):E[c][f"{d},{h}"] for (d,h) in SLOTS},DAY_HOURS,HDRF,away,cls=c)
    coh=[(d,h) for (cc,(d,h)) in COMAP if cc==c]
    if coh:
        ws.cell(row=9,column=1,value="צופיה מצטרפת (לא מחליפה): "+
                " · ".join(f"{DAY_NAMES[d]} ש{h}" for d,h in sorted(coh))).font=Font(bold=True,color="7B3F61")
    r=10; ws.cell(row=r,column=1,value="סיכום:").font=Font(bold=True)
    for i,(t,n) in enumerate(collections.Counter(E[c][f"{s[0]},{s[1]}"] for s in SLOTS).most_common()):
        ws.cell(row=r+1+i,column=1,value=t); ws.cell(row=r+1+i,column=2,value=n)

DUTY=json.load(io.open("duty.json",encoding="utf-8"))
DUTYFILL=PatternFill("solid",fgColor="FFD966")
for c in HCLASSES:                                    # ---- חטיבה ----
    ws=wb.create_sheet(c[:31]); hr=HHOME[c]; away={}
    for day in ("שני","שלישי"):
        if hr in D.get("קבוצת "+day,[]):
            for h in D["מעגלי שיח "+day]: away[(CM[day],h)]="מפגשה (מעגלי שיח)"
    if c=="ז אלי": away.pop((2,5),None)               # אלי נכנס לכיתתו בש5 (זמני)
    grid(ws,f"חטיבה – כיתה {c}   (מחנך/ת: {hr})",hr,
         {(d,h):H[c][f"{d},{h}"] for (d,h) in HSLOTS},HDAY,HDRG,away,hcls=c)
    if c=="ז אלי" and "אלי" in H[c]["2,5"]:
        _c25=ws.cell(row=2+5,column=2+2)
        _c25.comment=openpyxl.comments.Comment("אלי נכנס לכיתתו זמנית עד תחילת המפגשות (מתנגש במפגשה)","מערכת")
    dd=DAY_NAMES.index(DUTY[c])
    cell=ws.cell(row=2+5,column=2+dd); cell.fill=DUTYFILL
    cell.comment=openpyxl.comments.Comment(f"סידור חדר אוכל – {hr} עם הכיתה","מערכת")
    _last=2+max(HDAY)   # שורת השעה האחרונה (7 או 8) - ההערות מתחתיה, לא על שעה 7
    ws.cell(row=_last+2,column=1,value=f"סידור חדר אוכל: יום {DUTY[c]}, שעה 5 (עם {hr})").font=Font(bold=True,color="BF8F00")
    r=_last+4; ws.cell(row=r,column=1,value="שעות לפי מקצוע:").font=Font(bold=True)
    cnt=collections.Counter(v.split(" – ")[0] for v in H[c].values() if v)
    for i,(sj,n) in enumerate(cnt.most_common()):
        ws.cell(row=r+1+i,column=1,value=sj); ws.cell(row=r+1+i,column=2,value=n)
        _nd=NEED.get(sj,{}).get(GRADE[c])
        ws.cell(row=r+1+i,column=3,value="✔" if _nd is None or n==_nd else f"נדרש {_nd}")

ws=wb.create_sheet("סדירויות"); ws.sheet_view.rightToLeft=True   # ---- ריכוז ----
ws["A1"]="סדירויות ובלוקים קבועים"; ws["A1"].font=Font(bold=True,size=14)
def _mag_line(day):   # מי מלווה כל מגמה - מ-MAG_ROLES (לא טקסט ידני)
    hrs=sorted(h for (d,h) in MAG_ROLES if d==day); parts=[]; prev=None
    for h in hrs:
        who=", ".join(t for t,_r in MAG_ROLES[(day,h)])
        if parts and who==prev: parts[-1]=(parts[-1][0],h,who)
        else: parts.append((h,h,who))
        prev=who
    return " | ".join(f"ש{a}-{b}: {w}" if a!=b else f"ש{a}: {w}" for a,b,w in parts)
_zof=[DAY_NAMES.index(x) for x in DAYS_OFF2.get("צופיה",[])]
rows=[("מפגשה (מעגלי שיח) – קבוצה א'","שני",D["מעגלי שיח שני"],", ".join(D["קבוצת שני"])),
      ("מפגשה (מעגלי שיח) – קבוצה ב'","שלישי",D["מעגלי שיח שלישי"],", ".join(D["קבוצת שלישי"])),
      ("ישיבת מרכזי בית חינוך","שלישי",D["ישיבת ניהול שלישי"],", ".join(NIHUL)),
      ("אסיפת צוות","ראשון",[6,7],"כל המורים"),
      ("מגמות ז + ח","שלישי",[1,2,3,4],_mag_line(2)),
      ("מגמות ט","חמישי",[1,2,3,4],_mag_line(4))]+[
      ("ספורט שכבתי חטיבה",DAY_NAMES[_d],_hs,"שרית (בנות) + חסן (בנים) – שעה לכל שכבה") for _d,_hs in sorted(_PEB.items())]+[
      ("חווה חקלאית שכבת ג'","שני",[1,2],"לייה, דליה ודניאל עם הכיתות שלהן (רצוי, לא חובה)")]
r=3
for name,day,hrs,who in rows:
    ws.cell(row=r,column=1,value=name).font=Font(bold=True)
    ws.cell(row=r,column=2,value=f"{day}, שעות {hrs[0]}-{hrs[-1]}")
    ws.cell(row=r,column=3,value=who); r+=1
ws.cell(row=r+1,column=1,value="צופיה: יום חופש "+", ".join(DAYS_OFF2.get("צופיה",[]))+" | שני ורביעי מתחילה משעה 3").font=Font(bold=True)
ws.column_dimensions["A"].width=30; ws.column_dimensions["B"].width=24; ws.column_dimensions["C"].width=95
# (גיליון "הבעיה בשכבת ו" הישן הוסר: טקסט ידני שהתיישן. גיליון "חוסרים" נכתב ב-make_viewer מאותם
# חוסרים שהלוח מציג, עם הסיבה והמועמדים)
wsm=wb.create_sheet("מגמות חטיבה"); wsm.sheet_view.rightToLeft=True
wsm["A1"]="מגמות חטיבה – טבלת המורים לפי הטופס המקורי"; wsm["A1"].font=Font(bold=True,size=14)
# הטבלה נבנית מ-MAG_ROLES: בכל שעה - מי מלמד/ת או מלווה איזו מגמה, ומדריך חיצוני אם יש
_r0=3
for _day,_title in ((2,"יום שלישי – מגמות לשכבות ז+ח"),(4,"יום חמישי – מגמות לשכבת ט")):
    wsm.cell(row=_r0,column=1,value=_title).font=Font(bold=True,size=12)
    _hrs=sorted(h for (d,h) in MAG_ROLES if d==_day)
    _w=max(len(MAG_ROLES[(_day,h)]) for h in _hrs)
    for ci,v in enumerate(["שעה"]+[f"מורה {i+1}" for i in range(_w)]+["מדריך חיצוני"]):
        cc=wsm.cell(row=_r0+1,column=1+ci,value=v); cc.fill=HDRG; cc.font=HF
    for ri,h in enumerate(_hrs):
        wsm.cell(row=_r0+2+ri,column=1,value=h)
        for ci,(t,role) in enumerate(MAG_ROLES[(_day,h)]):
            wsm.cell(row=_r0+2+ri,column=2+ci,value=f"{t} – {role}")
        wsm.cell(row=_r0+2+ri,column=2+_w,value=MAG_EXT.get((_day,h),""))
    _r0+=len(_hrs)+4
for i in range(1,8): wsm.column_dimensions[get_column_letter(i)].width=26

# ---- מערכות מורים: הגיליון נכתב ב-make_viewer מתוך DATA.teachers (אותו מקור כמו הלוח:
# יסודי + חטיבה + תל"ן + מגמות + הצטרפויות + שישי ט + סדירויות, כולל שעה שמינית) ----
wst = wb.create_sheet("מערכות מורים"); wst.sheet_view.rightToLeft = True
wst["A1"] = "מערכות המורים נכתבות ב-make_viewer (רץ אחרי outGAPS בצינור)"

# ---- גיליון ניצול שעות ----
from util import build as _build
_rows=_build()
wsu=wb.create_sheet("ניצול שעות"); wsu.sheet_view.rightToLeft=True
wsu["A1"]="ניצול שעות מול מכסה פרונטלית"; wsu["A1"].font=Font(bold=True,size=14)
_hdr=["מורה","יסודי","חטיבה","תל\"ן","מגמות","מקבילות","סה\"כ","מכסה","נותר"]
for i,hh in enumerate(_hdr):
    cc=wsu.cell(row=3,column=1+i,value=hh); cc.fill=HDRF; cc.font=HF; cc.alignment=CEN; cc.border=BO
_over=PatternFill("solid",fgColor="FFC7CE"); _full=PatternFill("solid",fgColor="C6EFCE")
for ri,r in enumerate(_rows):
    for ci,v in enumerate(r):
        cc=wsu.cell(row=4+ri,column=1+ci,value=v); cc.alignment=CEN; cc.border=BO
        if ci==0: cc.alignment=Alignment(horizontal="right")
    if r[8]<0:
        for ci in range(9): wsu.cell(row=4+ri,column=1+ci).fill=_over
    elif r[8]==0:
        for ci in range(9): wsu.cell(row=4+ri,column=1+ci).fill=_full
_n=len(_rows)+4
wsu.cell(row=_n+1,column=1,value="סה\"כ").font=Font(bold=True)
wsu.cell(row=_n+1,column=7,value=sum(r[6] for r in _rows)).font=Font(bold=True)
wsu.cell(row=_n+1,column=8,value=sum(r[7] for r in _rows)).font=Font(bold=True)
wsu.cell(row=_n+1,column=9,value=sum(r[8] for r in _rows)).font=Font(bold=True)
wsu.cell(row=_n+3,column=1,value="אדום = חריגה מהמכסה | ירוק = מכסה מלאה").font=Font(italic=True)
wsu.cell(row=_n+4,column=1,value="יעל, חגית, הילית, יפעת = מורות תל\"ן בלבד - אין לשבצן מעבר לתל\"ן ומעט מגמה")
wsu.column_dimensions["A"].width=18
for i in range(2,10): wsu.column_dimensions[get_column_letter(i)].width=11

# נתיב מקומי. קודם היה כאן נתיב ווינדוס קשיח, ובלינוקס הוא נוצר כשם קובץ
# מילולי אחד ארוך ("C:\Users\...") בתיקיית הריפו במקום להישמר איפשהו.
wb.save("מערכות שעות.xlsx")
print("saved", len(wb.sheetnames), "sheets")
