מנוע מערכת השעות - בית חינוך ע"ש א.ד גורדון
=============================================

*** הדרך המומלצת (פותר מאוחד): ***
  python solveALL.py     - פותר יסודי+חטיבה במודל אחד
  python outGAPS.py      - בונה את קובץ האקסל (23 גיליונות)

הפותר המאוחד רואה שרשראות השפעה בין שני בתי הספר:
הזזת מורה ביסודי משפיעה על החטיבה ולהפך - הכל מאוזן גלובלית.
אין יותר צורך ב-fillgaps (מילוי חורים קורה בתוך המודל),
ואין סכנת דה-סנכרון בין הפותרים.

כלים:
  chain_report.py  - השוואת שני פתרונות והצגת שרשראות שינויים:
      cp sol_J.json prev_sol_J.json ; cp sol_hat.json prev_sol_hat.json
      (שנה משהו, הרץ solveALL) ואז: python chain_report.py
  make_unified.py  - בונה מחדש את solveALL.py משני הפותרים המקוריים
      (אחרי כל שינוי ב-solveEI.py או solveH.py: python make_unified.py)

קבצי מודל:
  data.py / data2.py - יסודי: כיתות, מכסות, ימי עבודה, מגמות, ספורט
  hdata.py           - חטיבה: תוכניות לימוד, פולים, ימי חופש
  solveEI.py/solveH.py - הפותרים המקוריים (מקור ל-make_unified)

דרך ישנה (שני שלבים, לגיבוי בלבד):
  python solveEI.py && python fillgaps.py && python solveH.py && python outGAPS.py

דרישות: pip install ortools openpyxl

צופה אינטרנטי:
  python make_viewer.py   - מייצר viewer.html מהפתרון הנוכחי
  את הקובץ מפרסמים כ-Artifact (או פותחים ישירות בדפדפן)
  הקישור הקבוע: https://claude.ai/code/artifact/7d591778-510b-4f26-b0b7-4a486b20bc94

=== ריצה מהירה ===
  python go.py        - ריצה מלאה (90 שניות)
  python go.py 240    - ריצה איטית ואיכותית יותר
הפותר מתחיל מהפתרון הקודם (warm start) ולכן מהיר.
אם יוצא INFEASIBLE - שום קובץ לא נדרס, האילוצים סותרים.

=== ארכיטקטורה חדשה (אוגוסט 2026) ===
  python go.py           - הצינור המלא: engine -> מילוי -> בדיקות -> אקסל -> צופה
  engine.py              - הפותר המאוחד (קובץ אחד, עורכים ישירות)
  rules.py               - חוקי המדיניות! כל חוק עם שם, תיאור ומתג active.
                           לביטול חוק: active=False. הלשונית בלוח מתעדכנת לבד.
  checks.py              - בדיקות אוטומטיות (רצות בכל ריצה, נכשלות בקול)
  git                    - כל שינוי יציב נשמר: git log / git checkout

לשנה הבאה / בנייה מחדש: לעדכן את data.py+data2.py+hdata.py (מורים, מכסות,
ימי חופש, תוכניות לימודים), לעבור על rules.py ולכבות חוקים שפגו, ולהריץ go.
make_unified.py, solveEI.py, solveH.py - ארכיון (המקור שממנו נבנה engine).
