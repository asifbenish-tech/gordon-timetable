מערכת השעות - בית חינוך ע"ש א.ד גורדון
=======================================
כללי העבודה המחייבים (אישור, היקף השפעה, פרסום) - ב-CLAUDE.md.

=== ריצה רגילה ===
  python go.py [שניות]     הצינור המלא: engine -> fill2 -> checks -> outGAPS ->
                           make_viewer -> outAPI -> outPDF -> smoke_viewer (דפדפן)
                           ברירת מחדל 90 שניות לפותר. INFEASIBLE = שום קובץ לא נדרס,
                           מודפס דוח קיבולת ורץ אבחון אוטומטי (diagnose.py).
  python approve.py        אחרי אישור המנהל בלבד: מדפיס את היקף השינוי (תאים,
                           כיתות, מורים, היה <- נהיה) ומעדכן את ה-baseline.
                           DRY=1 - רק מדפיס. אחר כך דחיפה ל-master = פרסום.

=== הצעות (בצד, בלי לגעת במפורסם) ===
  python propose.py <שם> [שניות]
      proposals/<שם>/proposal.json  - כותרת, בסיס (המפורסם או הצעה אחרת - ההגדרות
                                      יורשות), env, rules_off, הקפאות, נעילות (pins),
                                      עקיפות נתונים (overrides), אילוצים נוספים (extra.py)
      proposals/<שם>/out/           - viewer.html עם סימוני "היה <- נהיה", impact.txt
                                      (היקף ההשפעה), אקסל עם גיליון "שינויים", sol_*.json
      proposals/example             - דוגמה קטנה. hila_science, elem_ines_pani - ההצעות
                                      שהוצגו ב-19.09 (משוחזרות בדיוק דרך freeze_*).
  בקשות נעילה מהלוח: הנהלה לוחצת על תא -> "בקשת שינוי" -> כפתור 🔒 בכותרת מייצא
  JSON שנכנס ל-"pins" ב-proposal.json.

=== כלי אבחון ===
  python capacity.py       חשבון משבצות מול שעות (מורים וכיתות) - בלי פותר.
  python diagnose.py [שנ'] על INFEASIBLE: מכבה כלל אחד בכל פעם (במקביל) ואומר מי אשם.
  כפתורי ניסוי למנוע (משתני סביבה; להצעות בלבד, לא לפרסום):
    TL=שניות  STAB=0/80  RULES_OFF=id1,id2  FREEZEJ/FREEZEH=1|<קובץ>  PINS=<json>
    OVERRIDES=<json>  EXTRA=<py>  CAPONLY=1  NODIAG=1  SMOKE=0

=== קבצי המקור (מקום אחד לכל דבר - ראו CLAUDE.md) ===
  data.py / data2.py   יסודי: כיתות, מכסות (QUOTA/MAXQ2), ימי חופש, אירועים, מגמות,
                       TCONS (אילוצי מורים אישיים: עד איזו שעה, ימים, חלונות),
                       DAYCAP_EXC, INES_SCI_PAIR, APP_ALIAS, QUOTA_FILE
  hdata.py             חטיבה: NEED/OVR (תוכנית לימודים), POOLS, CAP, HOFF/HEV, HDAY,
                       MAG_H (יום המגמות), FIXED_H (נעילות קבועות), FRIDAY_H1/FRIDAY_COVER
                       (שישי ט), JOINT (שיעורים משותפים)
  rules.py             חוקי מדיניות עם מזהה, תיאור ומתג; לשונית "אילוצים" בלוח נבנית מכאן
  engine.py            הפותר המאוחד (OR-Tools CP-SAT): יסודי + חטיבה במודל אחד, יציבות
                       מול baseline_*.json
  fill2.py / checks.py מילוי חוסרים / בדיקות (נכשלות בקול)
  make_viewer.py       הלוח (viewer_template.html -> viewer.html); הזדהות: gen_access.py
  outGAPS / outAPI / outPDF   אקסל, timetable.json לאפליקציה (INTEGRATION.md), PDF
  overrides.py, smoke_viewer.py, staff_private.py (גיליון צוות מקומי, לא בגיט)

=== ארכיון ===
  attic/    ניסויים וסקריפטים ישנים (הפותרים המקוריים solveEI/solveH/solveALL, ניסויי
            אבלציה, דיאגנוסטיקות חד-פעמיות). לא רצים, לא מתוחזקים - שמורים להיסטוריה.

דרישות: pip install ortools openpyxl playwright   (כרום ל-smoke_viewer: playwright install chromium)
