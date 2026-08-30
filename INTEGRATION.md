# חיבור אפליקציית school-gordon ללוח המערכות

## שתי דרכים לקבל את הנתונים

### א. ייבוא קובץ (לא דורש שום חיבור לגיט) ⭐

בלוח גורדון יש כפתור **📤 ייצוא קובץ**. הוא מייצר את הקובץ בדפדפן עצמו,
מתוך אותם נתונים שמוצגים על המסך:

| מה שמורידים | למה זה טוב |
|---|---|
| `gordon-timetable-<תאריך>.json` | המבנה המלא: `lessons` + `app_map` + `full_names` |
| `gordon-timetable-<תאריך>.csv` | טבלה שטוחה (UTF-8 עם BOM) שאקסל וכל מערכת קוראים |
| העתקת ה-JSON ללוח | כשההורדה חסומה - מדביקים ישירות בשדה ייבוא |

הקובץ מסונן לפי ההרשאה של מי שמוריד: מנהל מקבל את כל 576 השיעורים,
רכז/ת בית את הבית שלו/ה, ומורה את הכיתה שהוא/היא מחנך/ת ואת השיעורים
שלו/ה עצמו/ה. שדה `generated` בקובץ = מועד בניית המערכת.

**מה שהאפליקציה צריכה לעשות:** לקרוא את `lessons` (ראו למטה) - זה הכול.
אין הבדל בין קובץ שהורד ידנית לבין `timetable.json` שנמשך מהרשת.

### ב. משיכה מהרשת (אם וכשזה עובד)

```
https://raw.githubusercontent.com/asifbenish-tech/gordon-timetable/master/timetable.json
https://raw.githubusercontent.com/asifbenish-tech/gordon-timetable/master/timetable.csv
```

הכתובת מחזירה `access-control-allow-origin: *`, כלומר `fetch` מהדפדפן מותר.
הקבצים מתעדכנים אוטומטית אחרי כל ריצת פותר.

## ⚠️ כלל הזהב: לזהות לפי `app_map`, לא לפי שמות

שמות הכיתות והמורים בפותר שונים לפעמים מהשמות באפליקציה
(למשל: בפותר `ח גלית` ↔ באפליקציה `גלית ב`; בפותר `חסן` ↔ באפליקציה `חסאן`).
לכן הקובץ כולל מיפוי מפורש למזהים של האפליקציה עצמה:

```json
"app_map": {
  "classes":  { "ח גלית": { "app_id": "c_1783243596863", "app_name": "גלית ב", "grade": "ח" }, ... },
  "teachers": { "חסן":    { "app_id": "t17834...", "full_name": "חסאן סראחן" }, ... }
}
```

**האפליקציה צריכה לעבוד כך:** לכל כיתה בקובץ ← לקחת את `app_map.classes[שם].app_id`
← וזה בדיוק ה-id של הכיתה ב-Firestore שלה (`classes[].id`). אותו דבר למורים.
אין לנסות להשוות שמות טקסטואלית.

## 📋 `index` — תפריט "איזו מערכת למשוך?"

לפני הייבוא, האפליקציה מציגה למשתמש רשימת בחירה. הרשימה מוכנה בשדה `index`
(60 פריטים): הכול · 3 בתים · 18 כיתות · 38 מורים.

```json
{ "id": "class:ד אינס", "type": "class", "label": "כיתה ד אינס",
  "level": "elementary", "class": "ד אינס",
  "app_id": "c_1783243540346", "count": 32 }
```

```js
const tt = await (await fetch(URL)).json();
showPicker(tt.index);                         // המשתמש בוחר פריט אחד

function lessonsFor(sel) {                    // מסננים את lessons לפי הבחירה
  if (sel.type === "all")     return tt.lessons;
  if (sel.type === "house")   return tt.lessons.filter(L => sel.classes.includes(L.class));
  if (sel.type === "class")   return tt.lessons.filter(L => L.class   === sel.class);
  if (sel.type === "teacher") return tt.lessons.filter(L => L.teacher === sel.teacher);
}
```

`count` = כמה שיעורים ייובאו — נוח להצגה ("ייובאו 32 שיעורים, להמשיך?").

## ⭐ הדרך הפשוטה: `lessons` — רשימה שטוחה ואחידה

**זה מה שכדאי לאפליקציה לקרוא.** מערך אחד, 576 שורות, **אותו מבנה בדיוק ליסודי ולחטיבה**:

```json
{ "level": "elementary",          // או "junior"
  "class": "ד אינס",
  "class_app_id": "c_1783243540346",   // ← המזהה שלכם ב-Firestore
  "day": 0, "day_name": "ראשון", "hour": 5,
  "subject": "שיעור (½ כיתה) + תל\"ן (½ כיתה)",
  "teacher": "אינס",
  "teacher_app_id": "t1784696803096_19",
  "kind": "half",                 // regular / home / tln / half / mag / pe / fill / hole
  "note": "½ הכיתה בתל\"ן · חגית",
  "temporary": false }            // true = חוסר שהמחנך/ת מכסה זמנית
```

```js
const tt = await (await fetch(URL)).json();
for (const L of tt.lessons) {
  if (!L.class_app_id) continue;            // כיתה לא מוכרת - לדלג
  save(L.class_app_id, L.day, L.hour, { subject: L.subject, teacherId: L.teacher_app_id, note: L.note });
}
```

**למה זה חשוב:** במבנה ה-`cells` הישן, ביסודי `t` הוא **שם המורה** ובחטיבה `t` הוא **המקצוע** — ולכן ייבוא שעובד לחטיבה נשבר ביסודי. ב-`lessons` השדות תמיד `subject` ו-`teacher` בנפרד, בשתי הרמות.

**מקצוע ביסודי:** בדרך כלל ריק — הפותר מנהל *מי מלמד*, לא *מה מלמדים* (המחנך/ת מלמד/ת את רוב המקצועות). מלא רק כשידוע: תל"ן, חצי כיתה, ספורט, היסטוריה וכד'. אם באפליקציה יש תוכנית לימודים, אפשר להשלים ממנה.

## מבנה המערכות (המפורט - `cells`)

- ימים: אינדקס 0=ראשון … 5=שישי (רשימת `days`)
- `elementary` (יסודי א-ו) ו-`junior` (חטיבה ז-ט): לכל כיתה
  `home` (מחנך/ת), `hours` (מס' שעות לכל יום), `cells`
- תא: מפתח `"יום,שעה"` (למשל `"2,5"` = שלישי שעה 5) ←
  - `t` — הטקסט הראשי: **ביסודי שם המורה, בחטיבה שם המקצוע**
  - `s` — שורת משנה: **בחטיבה שם המורה**, ביסודי מקצוע/הערה
  - `k` — סוג: `home` מחנך · `tln` תל"ן · `mag` מגמות/מרוכז · `pe` ספורט שכבתי ·
    `fill` מילוי חלון · `hole` חוסר (מחנך נכנס זמנית) · `off` אין לימודים
  - `co` — תוספת ("+ צופיה", "זמני", "סידור חדר אוכל")
  - `away` — המחנך/ת בחוץ (מפגשה / ישיבת מרכזי בית חינוך)

כלומר: מורה של תא בחטיבה = `cell.s`; מורה של תא ביסודי = `cell.t`.
מקצוע בחטיבה = `cell.t`; ביסודי לרוב אין מקצוע מפורש (מחנך מלמד את רוב המקצועות).

## מורים

`teachers` — לכל מורה (שם פרטי כמפתח) רשימת אירועים:
`[side, day, hour, label]` כאשר `side` אחד מ:
`יסודי` / `חטיבה` (label = כיתה או "כיתה · מקצוע") / `תל"ן` / `מגמות` /
`סדירות` (מפגשה, ישיבת מרכזי בית חינוך, אסיפת צוות, הדרכות - לא שעת הוראה).
שם מלא: `full_names[שם]` או `app_map.teachers[שם].full_name`.

## דוגמת קוד (JavaScript)

```js
const tt = await (await fetch(URL)).json();
for (const [cls, info] of Object.entries({...tt.elementary, ...tt.junior})) {
  const appId = tt.app_map.classes[cls]?.app_id;   // המזהה אצלכם ב-Firestore
  if (!appId) continue;                            // כיתה לא מוכרת - לדווח, לא לנחש
  for (const [key, cell] of Object.entries(info.cells)) {
    const [day, hour] = key.split(",").map(Number);
    const isJunior = cls in tt.junior;
    const subject = isJunior ? cell.t : (cell.s || "");
    const teacher = isJunior ? (cell.s || "") : cell.t;
    const teacherAppId = tt.app_map.teachers[teacher]?.app_id || null;
    // ... לשמור אצלכם לפי appId + day + hour
  }
}
```

## מה שאין לו התאמה

`app_map` לא יכיל: מורים שאינם קיימים באפליקציה (למשל "מורה חיצוני", "אופיר")
וערכים שאינם מורה ("תל\"ן", "מגמות", "שעת גיבוש"). האפליקציה צריכה לדלג/לסמן
אותם ולא להפיל את הייבוא.
