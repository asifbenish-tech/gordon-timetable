# -*- coding: utf-8 -*-
"""חבילת שינויי חטיבה: יום מגמות מסתיים ב-5, ספרות/היסטוריה, תנ"ך בלי מורה,
   אלי למתמטיקה בכיתות ו, אלי+נעמי יוצאים משאר היסודי."""
import io, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ============ hdata.py ============
p = "hdata.py"; s = io.open(p, encoding="utf-8").read()

# רב מלל מתפצל בז+ח לספרות (נעמי) והיסטוריה (אלי); ט נשאר רב מלל
a = '"רב מלל":{"ז":4,"ח":4,"ט":5},'
assert a in s, "need רב מלל"
s = s.replace(a, '"רב מלל":{"ז":0,"ח":0,"ט":5},\n "ספרות":{"ז":2,"ח":2,"ט":0},\n "היסטוריה":{"ז":2,"ח":2,"ט":0},')

a = '"רב מלל":{"ז":["נעמי","תמיר","אלי","שיר"],"ח":["נעמי","תמיר","אלי","מאמי"],"ט":["נעמי","תמיר","אלי"]},'
assert a in s, "pool רב מלל"
s = s.replace(a, '"רב מלל":{"ט":["נעמי","תמיר"]},\n "ספרות":{"ז":["נעמי","שיר"],"ח":["נעמי"]},\n "היסטוריה":{"ז":["אלי","שיר"],"ח":["אלי"]},')

# תנ"ך ז: בלי מורה כרגע
a = '\'תנ"ך\':{"ז":["תמיר","אלי","נעמי"],"ח":["לייה"],"ט":["תמיר","אלי","נעמי"]},'
assert a in s, "pool תנך"
s = s.replace(a, '\'תנ"ך\':{"ז":[],"ח":["לייה"],"ט":["תמיר","אלי","נעמי"]},   # ז: אין מורה כרגע')

# אלי פנוי בשלישי ש5 (מלמד חינוך בכיתתו)
a = '"אלי":[(2,3),(2,4),(2,5),(2,6),(4,3),(4,4),(3,6)],'
assert a in s, "HEV אלי"
s = s.replace(a, '"אלי":[(2,3),(2,4),(2,6),(4,3),(4,4),(3,6)],')

io.open(p, "w", encoding="utf-8").write(s)
print("hdata ok")

# ============ solveH.py ============
p = "solveH.py"; s = io.open(p, encoding="utf-8").read()

# 1) אלי משוחרר בשלישי ש5 בצד החטיבה
a = "def tblk(t):"
assert a in s, "tblk"
s = s.replace(a, 'ebusy["אלי"].discard((CM["שלישי"],5))   # מלמד חינוך ש5, מעגל מ-ש6\n' + a)

# 2) יום המגמות: ש5 חינוך, ואז הביתה. שלישי לז+ח, חמישי לט
a = '''for c in HCLASSES:
    for h in range(1,7): m.Add(free[(c,(2,h))]==0)     # שלישי מלא עד 6'''
assert a in s, "tuesday"
s = s.replace(a, '''for c in HCLASSES:
    _lt=5 if GRADE[c] in "זח" else 6                   # ז+ח: היום מסתיים אחרי חינוך ש5
    for h in range(1,_lt+1): m.Add(free[(c,(2,h))]==0)
    if GRADE[c] in "זח": m.Add(free[(c,(2,6))]==1)''')

A = '# שירה בציבור: יום שישי שעה 2, כל החטיבה יחד באולם חדר האוכל'
assert A in s, "anchor A"
s = s.replace(A, '''# יום המגמות: שיעור חינוך בש5 עם המחנך (בח - מחליף), ואז הביתה
for _cz in ("ז נעמי","ז אלי","ח גלית"):
    _v5=[x[k] for k in x if k[0]==_cz and k[1]==(2,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)
for _c9p in T9:
    _v5=[x[k] for k in x if k[0]==_c9p and k[1]==(4,5) and k[2]=="חינוך"]
    if _v5: m.Add(sum(_v5)==1)
    for _hb in (6,7): m.Add(free[(_c9p,(4,_hb))]==1)   # ט: הביתה אחרי ש5

''' + A)

# 3) חינוך ח: מחליף (נעמי/אלי) כשגלית במעגל
a = '''        if subj=="חינוך":
            pairs[c].append((subj,HHOME[c]))
            if c=="ז אלי": pairs[c].append((subj,"שיר"))'''
assert a in s, "hinuch pairs"
s = s.replace(a, a + '''
            if c=="ח גלית":
                pairs[c].append((subj,"נעמי")); pairs[c].append((subj,"אלי"))''')

# 4) תנ"ך ז: חסר מורה מותר שם
a = '''for _k in [k for k in x if k[3]=="חסר מורה" and k[1][0]!=5 and not (k[1][0]==2 and k[1][1] in (5,6))]:
    m.Add(x[_k]==0)'''
assert a in s, "miss rule"
s = s.replace(a, '''for _k in [k for k in x if k[3]=="חסר מורה" and k[1][0]!=5 and not (k[1][0]==2 and k[1][1] in (5,6))
            and not (k[2]=='תנ"ך' and k[0] in ("ז נעמי","ז אלי"))]:
    m.Add(x[_k]==0)''')

io.open(p, "w", encoding="utf-8").write(s)
print("solveH ok")

# ============ make_unified.py: היסודי ============
p = "make_unified.py"; s = io.open(p, encoding="utf-8").read()

# אלי: רק מתמטיקה בכיתות ו (2+2); נעמי יוצאת מהיסודי
a = "'POOL={\"אלי\":(6,CLASSES),\"נעמי\":(4,CLASSES),\"טלי\":(3,B_CL),'"
assert a in s, "epool"
s = s.replace(a, "'POOL={\"אלי\":(4,[\"ו אורנה\",\"ו שרית\"]),\"טלי\":(3,B_CL),'")

a = '_MENT=["אלי","גלית","תמיר","נעמי","צבי","רובי"]'
assert a in s, "ment"
s = s.replace(a, '''# אלי: בדיוק שעתיים מתמטיקה בכל אחת מכיתות ו
for _c6 in ("ו אורנה","ו שרית"):
    _v6=[x[k] for k in x if k[2]=="אלי" and k[0]==_c6]
    if _v6: m.Add(sum(_v6)==2)
_MENT=["אלי","גלית","תמיר","נעמי","צבי","רובי"]''')

io.open(p, "w", encoding="utf-8").write(s)
print("make_unified ok")
