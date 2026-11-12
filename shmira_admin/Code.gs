// לוח שמירות גורדון - צד השרת (Google Apps Script, רץ בחשבון של אסיף)
// הדף: shmira.html בלוח גורדון. כל מי שנכנס עם ת"ז רואה את הלוח; עריכה רק לאסיף ולחסן.
//
// קריאה: GET (JSONP) מחזיר את הלוח השמור ומספר גרסה.
// כתיבה: POST עם הלוח המלא + מפתח העריכה. המפתח נוצר ב-setup ונשלח למייל של אסיף בלבד;
//        אסיף מעביר את הקישור לחסן. בלי המפתח אי אפשר לשנות דבר.
// אין כאן תעודות זהות - רק שמות, מקומות ושעות.

var PAGE_URL = "https://asifbenish-tech.github.io/gordon-timetable/shmira.html";
var EDITORS = {"אסיף": 1, "חסן": 1};

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

// מנקה ומאמת: עד 20 הפסקות, 30 מקומות בהפסקה, 6 ימים, 8 שמות בתא.
function tidy_(b) {
  if (!b || !Array.isArray(b.breaks) || b.breaks.length > 20) return null;
  var out = {title: clean_(b.title), breaks: []};
  for (var i = 0; i < b.breaks.length; i++) {
    var k = b.breaks[i];
    if (!k || !Array.isArray(k.spots) || k.spots.length > 30) return null;
    var nk = {time: clean_(k.time), spots: []};
    for (var j = 0; j < k.spots.length; j++) {
      var s = k.spots[j];
      if (!s || !Array.isArray(s.a) || s.a.length !== 6) return null;
      nk.spots.push({name: clean_(s.name), a: s.a.map(function (c) {
        return (Array.isArray(c) ? c : []).map(clean_).filter(String).slice(0, 8);
      })});
    }
    out.breaks.push(nk);
  }
  return out;
}

function clean_(s) { return String(s || "").replace(/[<>"`\\]/g, "").replace(/\s+/g, " ").trim().slice(0, 40); }
function sheet_(name) {
  return SpreadsheetApp.openById(PropertiesService.getScriptProperties().getProperty("SHEET_ID")).getSheetByName(name);
}
