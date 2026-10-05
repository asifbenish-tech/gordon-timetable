// משתמשי לוח גורדון - צד השרת (Google Apps Script, רץ בחשבון של אסיף)
// עמוד הניהול הוא לשונית "👥 משתמשים" בלוח (viewer.html), שמופיעה רק לאסיף.
// הלוח קורא מכאן את הרשימה בכל טעינה (JSONP), כך שהוספה/הסרה נכנסות לתוקף מיד.
//
// פרטיות: אין כאן ואין בגיליון תעודות זהות. הדפדפן מגבב את הת"ז (PBKDF2, כמו
// בכניסה ללוח) ושולח רק את הגיבוב. הגיליון שומר רק *הבדלים* מול הרשימה שבנויה
// בלוח (access_map.json): מי נוסף, מי שונה, מי הוסר.
// הרשאת כתיבה: מפתח ניהול אקראי שנוצר ב-setup ונשלח למייל של אסיף בלבד.

var PAGE_URL = "https://asifbenish-tech.github.io/gordon-timetable/viewer.html";
// הגיבוב של ת"ז אסיף - כבר מופיע בלוח הציבורי (access_map.json), ולכן אינו סוד.
// אי אפשר להסיר את הבעלים או להוריד את הרשאתו, כדי שלא יינעל מחוץ לעמוד.
var OWNER_HASH = "41f9510f74c6f9b8cbce9d8e4e8935e07529928654e13e3261cd25397b4c2794";
// custom = הרשאה מותאמת: אילו כיתות (cls), מערכות מורים (t), לוח סדירויות (sed)
var ROLES = {admin: 1, coordinator: 1, classes: 1, teacher: 1, custom: 1};
var TVIEW = {none: 1, own: 1, classes: 1, all: 1};
var HOUSES = {A: 1, B: 1, C: 1};
var HEAD = ["hash", "name", "role", "house", "tv", "p", "status", "updatedAt", "cls", "t", "sed"];

function ensure_() {
  var p = PropertiesService.getScriptProperties();
  if (!p.getProperty("SHEET_ID")) {
    var ss = SpreadsheetApp.create("לוח גורדון - משתמשים");
    var u = ss.getSheets()[0].setName("users");
    u.getRange("A:H").setNumberFormat("@");
    u.appendRow(HEAD);
    ss.insertSheet("log").appendRow(["time", "action", "name", "details"]);
    p.setProperty("SHEET_ID", ss.getId());
  }
  if (!p.getProperty("ADMIN_KEY")) p.setProperty("ADMIN_KEY", Utilities.getUuid().replace(/-/g, ""));
  // גיליון מגרסה קודמת: משלים כותרות לעמודות החדשות
  var u2 = sheet_("users"), h0 = u2.getDataRange().getValues()[0];
  if (h0.length < HEAD.length || String(h0[HEAD.length - 1]) !== HEAD[HEAD.length - 1]) {
    u2.getRange(1, 1, 1, HEAD.length).setValues([HEAD]);
    u2.getRange("A:K").setNumberFormat("@");
  }
  return p;
}

// להרצה ידנית פעם אחת: מאשר הרשאות ושולח לאסיף את קישור הניהול.
function setup() {
  var p = ensure_();
  var link = PAGE_URL + "?ukey=" + p.getProperty("ADMIN_KEY");
  MailApp.sendEmail(owner_(), "לוח גורדון - קישור לניהול המשתמשים",
    "פתחו את הקישור הזה פעם אחת בכל מחשב/טלפון שממנו תרצו לנהל משתמשים:\n" + link +
    "\n\nאחרי הכניסה עם תעודת הזהות שלכם תופיע לשונית \"👥 משתמשים\".\n" +
    "לא להעביר את הקישור הלאה - מי שמחזיק בו ובת\"ז שלכם יכול לשנות הרשאות.\n\n" +
    "הגיליון (גיבוי ויומן שינויים): " + SpreadsheetApp.openById(p.getProperty("SHEET_ID")).getUrl());
  Logger.log("Admin link: " + link);
}

// הלוח קורא דרך GET עם callback (JSONP), כמו דף השיעורים.
function doGet(e) {
  var r = e.parameter || {}, cb = r.callback, out;
  try { ensure_(); out = r.action ? act_(r) : list_(isAdmin_(r.key)); }
  catch (err) { out = {ok: false, error: "שגיאה בשרת: " + err.message}; }
  if (cb && /^[A-Za-z_$][\w$]*$/.test(cb))
    return ContentService.createTextOutput(cb + "(" + JSON.stringify(out) + ");").setMimeType(ContentService.MimeType.JAVASCRIPT);
  return ContentService.createTextOutput(JSON.stringify(out)).setMimeType(ContentService.MimeType.JSON);
}

function act_(r) {
  if (!isAdmin_(r.key)) return {ok: false, error: "אין הרשאה (מפתח הניהול חסר או שגוי)."};
  var h = String(r.hash || "");
  if (!/^[0-9a-f]{64}$/.test(h)) return {ok: false, error: "גיבוב לא תקין."};
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return {ok: false, error: "המערכת עמוסה. נסו שוב בעוד רגע."};
  try {
    if (r.action === "save") return save_(r, h);
    if (r.action === "remove") return remove_(r, h);
    return {ok: false, error: "פעולה לא מוכרת."};
  } finally { lock.releaseLock(); }
}

function save_(r, h) {
  var name = clean_(r.name), role = String(r.role || ""), house = String(r.house || "");
  if (!name) return {ok: false, error: "חסר שם."};
  if (!ROLES[role]) return {ok: false, error: "הרשאה לא מוכרת."};
  if (role === "coordinator" && !HOUSES[house]) return {ok: false, error: "לרכז/ת בית צריך לבחור בית."};
  if (h === OWNER_HASH && role !== "admin") return {ok: false, error: "אי אפשר להוריד את ההרשאה של בעל/ת העמוד."};
  var old = String(r.old || "");   // החלפת ת"ז: הגיבוב הקודם מוסר באותה פעולה
  if (old && (!/^[0-9a-f]{64}$/.test(old) || old === OWNER_HASH)) return {ok: false, error: "אי אפשר להחליף את תעודת הזהות הזו."};
  var tv = role === "classes" && r.tv === "1" ? "1" : "";
  var pk = role === "admin" || r.p === "1" ? "1" : "";
  var cls = "", t = "", sed = "";
  if (role === "custom") {
    cls = String(r.cls || "") === "*" ? "*" : String(r.cls || "").split(",").map(clean_).filter(String).slice(0, 40).join(",");
    t = TVIEW[r.t] ? String(r.t) : "none";
    sed = r.sed === "1" ? "1" : "";
    if (!cls && t === "none" && !sed) return {ok: false, error: "לא נבחר שום דבר לצפייה."};
  }
  var now = new Date().toISOString();
  put_(h, [h, name, role, role === "coordinator" ? house : "", tv, pk, "active", now, cls, t, sed]);
  if (old && old !== h) put_(old, [old, name, "", "", "", "", "removed", now, "", "", ""]);
  log_(old && old !== h ? "save+newid" : "save", name, role + (house && role === "coordinator" ? " " + house : "") + (tv ? " +מורים" : "") +
    (role === "custom" ? " כיתות:" + (cls || "-") + " מורים:" + t + (sed ? " +סדירויות" : "") : "") + (pk && role !== "admin" ? " +החלפות" : ""));
  return {ok: true};
}

function remove_(r, h) {
  if (h === OWNER_HASH) return {ok: false, error: "אי אפשר להסיר את בעל/ת העמוד."};
  var name = clean_(r.name) || "?";
  put_(h, [h, name, "", "", "", "", "removed", new Date().toISOString(), "", "", ""]);
  log_("remove", name, "");
  return {ok: true};
}

function list_(admin) {
  var users = {}, removed = {};
  rows_().forEach(function (x) {
    var w = x.row;
    if (w.status === "removed") { removed[w.hash] = w.name; return; }
    var e = {n: w.name, r: w.role};
    if (w.house) e.h = w.house;
    if (w.tv === "1") e.tv = 1;
    if (w.p === "1") e.p = 1;
    if (w.role === "custom") {
      e.cls = w.cls === "*" ? "*" : (w.cls ? w.cls.split(",") : []);
      e.t = w.t || "none";
      if (w.sed === "1") e.sed = 1;
    }
    users[w.hash] = e;
  });
  return {ok: true, users: users, removed: removed, admin: admin};
}

function put_(h, vals) {
  var sh = sheet_("users"), hit = rows_().filter(function (x) { return x.row.hash === h; })[0];
  if (hit) sh.getRange(hit.n, 1, 1, vals.length).setValues([vals]);
  else sh.appendRow(vals);
}

function rows_() {
  var v = sheet_("users").getDataRange().getValues(), head = v[0], out = [];
  for (var i = 1; i < v.length; i++) {
    var row = {};
    head.forEach(function (k, j) { row[k] = v[i][j] == null ? "" : String(v[i][j]); });
    if (/^[0-9a-f]{64}$/.test(row.hash)) out.push({n: i + 1, row: row});
  }
  return out;
}

function clean_(s) { return String(s || "").replace(/[<>"'&`\\]/g, "").replace(/\s+/g, " ").trim().slice(0, 60); }
function log_(a, n, d) { sheet_("log").appendRow([new Date().toISOString(), a, n, d]); }
function sheet_(name) {
  return SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("SHEET_ID")).getSheetByName(name);
}
function isAdmin_(k) { var a = PropertiesService.getScriptProperties().getProperty("ADMIN_KEY"); return !!(a && k && String(k) === a); }
function owner_() { return Session.getEffectiveUser().getEmail(); }
