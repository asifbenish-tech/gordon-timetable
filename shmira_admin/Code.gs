// לוח שמירות גורדון - צד השרת (Google Apps Script, רץ בחשבון של אסיף)
// הדף: shmira.html בלוח גורדון. כל מי שנכנס עם ת"ז רואה את הלוח; עריכה רק לאסיף ולחסן.
//
// קריאה: GET (JSONP) מחזיר את הלוח השמור ומספר גרסה.
// כתיבה: POST עם הלוח המלא + מפתח העריכה. המפתח נוצר ב-setup ונשלח למייל של אסיף בלבד;
//        אסיף מעביר את הקישור לחסן. בלי המפתח אי אפשר לשנות דבר.
// אין כאן תעודות זהות - רק שמות, מקומות ושעות.

var PAGE_URL = "https://asifbenish-tech.github.io/gordon-timetable/shmira.html";
var EDITORS = {"חסן": 1, "אסיף": 1};

function ensure_() {
  var p = PropertiesService.getScriptProperties();
  if (!p.getProperty("SHEET_ID")) {
    var ss = SpreadsheetApp.create("לוח גורדון - שמירות");
    var b = ss.getSheets()[0].setName("board");
    b.getRange("A1:B1").setNumberFormat("@").setValues([["0", ""]]);
    ss.insertSheet("history").appendRow(["time", "name", "rev", "board"]);
    p.setProperty("SHEET_ID", ss.getId());
  }
  if (!p.getProperty("EDIT_KEY")) p.setProperty("EDIT_KEY", Utilities.getUuid().replace(/-/g, ""));
  return p;
}

// להרצה ידנית פעם אחת: מאשר הרשאות ושולח לאסיף את קישור העריכה.
function setup() {
  var p = ensure_();
  var link = PAGE_URL + "?skey=" + p.getProperty("EDIT_KEY");
  MailApp.sendEmail(Session.getEffectiveUser().getEmail(), "לוח שמירות גורדון - קישור עריכה",
    "קישור העריכה של לוח השמירות (לאסיף ולחסן בלבד):\n" + link +
    "\n\nפותחים אותו פעם אחת בכל מחשב/טלפון שממנו עורכים, ונכנסים עם תעודת הזהות." +
    "\nאחרי זה מופיע הכפתור \"עריכת הלוח\". לא להעביר את הקישור למי שלא אמור לערוך.\n\n" +
    "הגיליון (גיבוי והיסטוריית שינויים): " + SpreadsheetApp.openById(p.getProperty("SHEET_ID")).getUrl());
  Logger.log("Edit link: " + link);
}

function doGet(e) {
  var r = e.parameter || {}, cb = r.callback, out;
  try { ensure_(); out = read_(); }
  catch (err) { out = {ok: false, error: "שגיאה בשרת: " + err.message}; }
  if (cb && /^[A-Za-z_$][\w$]*$/.test(cb))
    return ContentService.createTextOutput(cb + "(" + JSON.stringify(out) + ");").setMimeType(ContentService.MimeType.JAVASCRIPT);
  return ContentService.createTextOutput(JSON.stringify(out)).setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  var out;
  try { ensure_(); out = write_(JSON.parse(e.postData.contents)); }
  catch (err) { out = {ok: false, error: "שגיאה בשרת: " + err.message}; }
  return ContentService.createTextOutput(JSON.stringify(out)).setMimeType(ContentService.MimeType.JSON);
}

function read_() {
  var v = sheet_("board").getRange("A1:B1").getValues()[0], board = null;
  try { board = v[1] ? JSON.parse(String(v[1])) : null; } catch (err) {}
  return {ok: true, rev: Number(v[0]) || 0, board: board};
}

function write_(r) {
  var key = PropertiesService.getScriptProperties().getProperty("EDIT_KEY");
  if (!key || !r || String(r.key || "") !== key) return {ok: false, error: "אין הרשאת עריכה במכשיר הזה (קישור העריכה חסר או הוחלף)."};
  var name = clean_(r.name);
  if (!EDITORS[name]) return {ok: false, error: "רק אסיף וחסן רשאים לערוך את הלוח."};
  var board = tidy_(r.board);
  if (!board) return {ok: false, error: "מבנה הלוח לא תקין."};
  var json = JSON.stringify(board);
  if (json.length > 45000) return {ok: false, error: "הלוח גדול מדי."};
  var lock = LockService.getScriptLock();
  if (!lock.tryLock(10000)) return {ok: false, error: "המערכת עמוסה. נסו שוב בעוד רגע."};
  try {
    var rng = sheet_("board").getRange("A1:B1"), rev = Number(rng.getValues()[0][0]) || 0;
    if (Number(r.rev) !== rev) return {ok: false, error: "הלוח עודכן בינתיים ממכשיר אחר. רעננו את הדף וערכו שוב."};
    rev++;
    rng.setValues([[String(rev), json]]);
    sheet_("history").appendRow([new Date().toISOString(), name, rev, json]);
    return {ok: true, rev: rev};
  } finally { lock.releaseLock(); }
}

// מנקה ומאמת את מבנה הלוח (גרסה 2): אזורים, הפסקות, ושיבוץ "הפסקה|אזור|יום" -> שמות.
// עד 30 אזורים, 20 הפסקות, 8 שמות בתא. שיבוץ שמפנה להפסקה/אזור שלא קיימים נזרק.
function tidy_(b) {
  var ID = /^[a-z0-9]{1,20}$/;
  if (!b || !Array.isArray(b.zones) || !Array.isArray(b.breaks) || !b.a || typeof b.a !== "object") return null;
  if (b.zones.length > 30 || b.breaks.length > 20) return null;
  var out = {v: 2, title: clean_(b.title), zones: [], breaks: [], a: {}}, zs = {}, bs = {};
  for (var i = 0; i < b.zones.length; i++) {
    var z = b.zones[i];
    if (!z || !ID.test(String(z.id)) || zs[z.id]) return null;
    zs[z.id] = 1;
    out.zones.push({id: String(z.id), name: clean_(z.name) || "אזור", need: Math.max(0, Math.min(4, Math.round(Number(z.need)) || 0))});
  }
  for (var j = 0; j < b.breaks.length; j++) {
    var k = b.breaks[j];
    if (!k || !ID.test(String(k.id)) || bs[k.id] || !Array.isArray(k.days) || k.days.length !== 6 || !Array.isArray(k.zones)) return null;
    var nk = {id: String(k.id), name: clean_(k.name), time: clean_(k.time),
      after: Math.max(0, Math.min(12, Math.round(Number(k.after)) || 0)),
      days: k.days.map(function (d) { return d ? 1 : 0; }),
      zones: k.zones.map(String).filter(function (x, n, arr) { return zs[x] && arr.indexOf(x) === n; })};
    bs[nk.id] = nk;
    out.breaks.push(nk);
  }
  Object.keys(b.a).forEach(function (key) {
    var p = key.split("|"), kk = bs[p[0]];
    if (p.length !== 3 || !kk || kk.zones.indexOf(p[1]) < 0 || !/^[0-5]$/.test(p[2]) || !kk.days[Number(p[2])]) return;
    var c = (Array.isArray(b.a[key]) ? b.a[key] : []).map(clean_).filter(String).slice(0, 8);
    if (c.length) out.a[key] = c;
  });
  return out;
}

function clean_(s) { return String(s || "").replace(/[<>"`\\|]/g, "").replace(/\s+/g, " ").trim().slice(0, 40); }
function sheet_(name) {
  return SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("SHEET_ID")).getSheetByName(name);
}
