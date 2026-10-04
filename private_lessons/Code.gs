// שיעורים פרטיים עם אסיף - צד השרת (Google Apps Script, רץ בחשבון של אסיף)
// העמוד: lessons.html באתר הלוח. השיבוצים נשמרים בגיליון שנוצר ב-setup,
// כל שיבוץ נכנס ליומן הראשי ושולח מייל. אין כאן סודות: מפתח הניהול נוצר
// ב-setup ונשמר במאפייני הסקריפט.

var PAGE_URL = "https://asifbenish-tech.github.io/gordon-timetable/lessons.html";
var TZ = "Asia/Jerusalem";
var FIRST = "2026-10-04", LAST = "2027-06-27";
var START = "10:00", END = "10:45";
var LOCATION = "בית חינוך א.ד גורדון";
// חופשות משרד החינוך תשפ"ז שנופלות ביום ראשון. ימים נוספים - מתוך מצב הניהול בעמוד.
var HOLIDAYS = {"2026-12-06": "חופשת חנוכה", "2027-04-18": "חופשת פסח", "2027-04-25": "חופשת פסח"};

// יוצר את הגיליון ואת מפתח הניהול אם חסרים. רץ אוטומטית בכל בקשה.
function ensure_() {
  var p = PropertiesService.getScriptProperties();
  if (!p.getProperty("SHEET_ID")) {
    var ss = SpreadsheetApp.create("שיעורים פרטיים - שיבוצים");
    var b = ss.getSheets()[0].setName("bookings");
    b.getRange("A:A").setNumberFormat("@");
    b.appendRow(["date", "name", "topic", "createdAt", "token", "eventId", "status"]);
    var c = ss.insertSheet("closed");
    c.getRange("A:A").setNumberFormat("@");
    c.appendRow(["date", "reason"]);
    p.setProperty("SHEET_ID", ss.getId());
  }
  if (!p.getProperty("ADMIN_KEY")) p.setProperty("ADMIN_KEY", Utilities.getUuid().replace(/-/g, ""));
  return p;
}

// להרצה ידנית: מאשר הרשאות ושולח לאסיף את קישור הניהול.
function setup() {
  var p = ensure_();
  var link = PAGE_URL + "?admin=" + p.getProperty("ADMIN_KEY");
  MailApp.sendEmail(owner_(), "שיעורים פרטיים - קישור הניהול שלך",
    "הגיליון: " + SpreadsheetApp.openById(p.getProperty("SHEET_ID")).getUrl() +
    "\n\nקישור הניהול (רק לך - רואים בו שמות ונושאים, מבטלים שיבוצים ומסמנים ימי חופש):\n" + link +
    "\n\nלמורים שולחים את הקישור בלי החלק ?admin=...:\n" + PAGE_URL);
  Logger.log("Admin link: " + link);
}

// העמוד קורא דרך GET עם callback (JSONP), כך שאין תלות בהגדרות CORS של הדפדפן.
function doGet(e) {
  var r = e.parameter || {}, cb = r.callback;
  var out;
  try { ensure_(); out = r.action ? act_(r) : list_(isAdmin_(r.key)); }
  catch (err) { out = {ok: false, error: "שגיאה בשרת: " + err.message}; }
  if (cb && /^[A-Za-z_$][\w$]*$/.test(cb))
    return ContentService.createTextOutput(cb + "(" + JSON.stringify(out) + ");").setMimeType(ContentService.MimeType.JAVASCRIPT);
  return json_(out);
}

function doPost(e) {
  var r;
  try { r = JSON.parse(e.postData.contents); } catch (err) { return json_({ok: false, error: "בקשה לא תקינה."}); }
  ensure_();
  return json_(act_(r));
}

function act_(r) {
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return {ok: false, error: "המערכת עמוסה. נסו שוב בעוד רגע."};
  try {
    if (r.action === "book") return book_(r);
    if (r.action === "cancel") return cancel_(r);
    if (r.action === "close" || r.action === "open") return setClosed_(r);
    return {ok: false, error: "פעולה לא מוכרת."};
  } finally { lock.releaseLock(); }
}

function list_(admin) {
  var out = {bookings: {}, closed: {}, holidays: HOLIDAYS, admin: admin};
  rows_("bookings").forEach(function (x) {
    if (x.row.status !== "booked") return;
    out.bookings[x.row.date] = admin ? {name: x.row.name, topic: x.row.topic} : {};
  });
  rows_("closed").forEach(function (x) { out.closed[x.row.date] = x.row.reason || "חופש"; });
  return out;
}

function book_(r) {
  var d = String(r.date || ""), name = String(r.name || "").trim().slice(0, 80), topic = String(r.topic || "").trim().slice(0, 1500);
  var bad = checkDate_(d);
  if (bad) return {ok: false, error: bad};
  if (!name || !topic) return {ok: false, error: "צריך למלא שם ונושא."};
  if (active_(d)) return {ok: false, error: "התאריך נתפס בינתיים.", taken: true};
  var t = times_(d);
  var ev = CalendarApp.getDefaultCalendar().createEvent("שיעור פרטי – " + name, t[0], t[1], {
    location: LOCATION, description: "נושא: " + topic + "\n\nנקבע דרך דף השיבוץ: " + PAGE_URL});
  var token = Utilities.getUuid().replace(/-/g, "");
  sheet_("bookings").appendRow([d, name, topic, new Date().toISOString(), token, ev.getId(), "booked"]);
  MailApp.sendEmail(owner_(), "שיבוץ חדש: שיעור פרטי " + nice_(d) + " – " + name,
    name + " השתבץ/ה לשיעור פרטי ביום ראשון " + nice_(d) + ", שעה 3 (" + START + "–" + END + ").\n\nנושא:\n" + topic +
    "\n\nהאירוע נוסף ליומן שלך.");
  return {ok: true, token: token};
}

function cancel_(r) {
  var d = String(r.date || ""), x = active_(d);
  if (!x) return {ok: true};
  if (!(isAdmin_(r.key) || (r.token && r.token === x.row.token))) return {ok: false, error: "אפשר לבטל רק שיבוץ שנעשה מהמכשיר הזה."};
  try { CalendarApp.getDefaultCalendar().getEventById(x.row.eventId).deleteEvent(); } catch (err) {}
  sheet_("bookings").getRange(x.n, 7).setValue("cancelled");
  MailApp.sendEmail(owner_(), "בוטל: שיעור פרטי " + nice_(d) + " – " + x.row.name,
    "השיעור הפרטי עם " + x.row.name + " ביום ראשון " + nice_(d) + " בוטל" + (isAdmin_(r.key) ? " (על ידך)." : " על ידי המורה.") +
    "\nהאירוע הוסר מהיומן והתאריך פנוי שוב.");
  return {ok: true};
}

function setClosed_(r) {
  if (!isAdmin_(r.key)) return {ok: false, error: "אין הרשאה."};
  var d = String(r.date || ""), sh = sheet_("closed");
  rows_("closed").filter(function (x) { return x.row.date === d; }).reverse().forEach(function (x) { sh.deleteRow(x.n); });
  if (r.action === "close") {
    if (active_(d)) return {ok: false, error: "יש שיבוץ בתאריך הזה. בטלו אותו קודם."};
    sh.appendRow([d, String(r.reason || "חופש").slice(0, 60)]);
  }
  return {ok: true};
}

function checkDate_(d) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(d) || d < FIRST || d > LAST) return "תאריך לא תקין.";
  var t = times_(d);
  if (Utilities.formatDate(t[0], TZ, "u") !== "7") return "אפשר להשתבץ רק לימי ראשון.";
  if (t[0].getTime() <= Date.now()) return "התאריך כבר עבר.";
  if (HOLIDAYS[d]) return HOLIDAYS[d] + " – אין שיעור ביום הזה.";
  var c = rows_("closed").filter(function (x) { return x.row.date === d; })[0];
  if (c) return (c.row.reason || "חופש") + " – אין שיעור ביום הזה.";
  return "";
}

function times_(d) {
  var off = Utilities.formatDate(new Date(d + "T12:00:00Z"), TZ, "XXX");
  return [new Date(d + "T" + START + ":00" + off), new Date(d + "T" + END + ":00" + off)];
}

function active_(d) {
  return rows_("bookings").filter(function (x) { return x.row.date === d && x.row.status === "booked"; })[0] || null;
}

function rows_(name) {
  var v = sheet_(name).getDataRange().getValues(), head = v[0], out = [];
  for (var i = 1; i < v.length; i++) {
    var row = {};
    head.forEach(function (h, j) {
      var c = v[i][j];
      row[h] = c instanceof Date ? Utilities.formatDate(c, TZ, "yyyy-MM-dd") : String(c);
    });
    out.push({n: i + 1, row: row});
  }
  return out;
}

function sheet_(name) {
  return SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("SHEET_ID")).getSheetByName(name);
}
function isAdmin_(k) { var a = PropertiesService.getScriptProperties().getProperty("ADMIN_KEY"); return !!(a && k && k === a); }
function owner_() { return Session.getEffectiveUser().getEmail(); }
function nice_(d) { var p = d.split("-"); return p[2] + "." + p[1] + "." + p[0]; }
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
