// מסמך וורד: מערכות שעות לכל המורים + מערכות הכיתות אצל המחנכים
const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, HeadingLevel, PageBreak,
  PageOrientation, BorderStyle,
} = require("docx");

const D = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const DAYS = D.days; // ראשון..שישי
const FONT = "Arial";

function run(text, opts = {}) {
  return new TextRun({ text, font: FONT, rightToLeft: true, size: opts.size || 18, bold: !!opts.bold, italics: !!opts.italics, color: opts.color });
}
function para(children, opts = {}) {
  return new Paragraph({ children, bidirectional: true, alignment: opts.align || AlignmentType.CENTER, spacing: opts.spacing });
}
function textPara(text, opts = {}) {
  return para([run(text, opts)], opts);
}

const HOUR_W = 700, DAY_W = 1550;               // DXA — סה"כ 700+6*1550=10000
const COLS = [HOUR_W, ...DAYS.map(() => DAY_W)];
const TBL_W = COLS.reduce((a, b) => a + b, 0);

function cell(paras, opts = {}) {
  return new TableCell({
    children: paras.length ? paras : [textPara("")],
    width: { size: opts.w || DAY_W, type: WidthType.DXA },
    shading: opts.fill ? { type: ShadingType.CLEAR, fill: opts.fill, color: "auto" } : undefined,
    verticalAlign: "center",
  });
}
function headerRow() {
  return new TableRow({
    tableHeader: true,
    children: [cell([textPara("שעה", { bold: true })], { w: HOUR_W, fill: "2F5597" }),
      ...DAYS.map(dn => cell([para([new TextRun({ text: dn, font: FONT, rightToLeft: true, size: 18, bold: true, color: "FFFFFF" })])], { fill: "2F5597" }))],
  });
}
function table(rows) {
  return new Table({
    rows, columnWidths: COLS, width: { size: TBL_W, type: WidthType.DXA },
    visuallyRightToLeft: true,
  });
}

// ---------- טבלת מורה ----------
function teacherTable(t) {
  const ev = D.teachers[t] || [];
  const per = {}, sedOnly = {};
  for (const [side, d, h, label] of ev) {
    const key = d + "," + h;
    const txt = side === "סדירות" ? "◦ " + label : label + (side !== "יסודי" && side !== "חטיבה" ? " (" + side + ")" : "");
    sedOnly[key] = (sedOnly[key] === undefined ? true : sedOnly[key]) && side === "סדירות";
    per[key] = per[key] ? per[key] + " · " + txt : txt;
  }
  const rows = [headerRow()];
  for (let h = 1; h <= 7; h++) {
    const cells = [cell([textPara(String(h), { bold: true })], { w: HOUR_W, fill: "DCE6F1" })];
    for (let d = 0; d < 6; d++) {
      const key = d + "," + h;
      const v = per[key] || "";
      cells.push(cell(v ? [textPara(v, { italics: !!sedOnly[key] })] : [], { fill: sedOnly[key] ? "EFECE4" : undefined }));
    }
    rows.push(new TableRow({ children: cells }));
  }
  return table(rows);
}

// ---------- טבלת כיתה ----------
function classTable(kind, c) {
  const info = (kind === "elem" ? D.elem : D.jun)[c];
  const hours = kind === "elem" ? D.day_hours_elem : D.day_hours_jun;
  const H = Math.max(...hours);
  const rows = [headerRow()];
  for (let h = 1; h <= H; h++) {
    const cells = [cell([textPara(String(h), { bold: true })], { w: HOUR_W, fill: "DCE6F1" })];
    for (let d = 0; d < 6; d++) {
      if (h > hours[d]) { cells.push(cell([], { fill: "F2F2F2" })); continue; }
      const cc = info.cells[d + "," + h] || { t: "" };
      const paras = [];
      const hole = cc.k === "hole";
      if (cc.t) paras.push(textPara(cc.t, { bold: hole, color: hole ? "990000" : undefined }));
      if (cc.s) paras.push(textPara(cc.s, { size: 14, color: hole ? "990000" : "666666" }));
      if (cc.co) paras.push(textPara(cc.co, { size: 14, color: "0E6E66" }));
      if (cc.away) paras.push(textPara("(" + cc.away + ")", { size: 13, italics: true, color: "8A6D3B" }));
      let fill;
      if (hole) fill = "FBD9D3";
      else if (cc.k === "home") fill = "E3EEF7";
      else if (cc.k === "tln") fill = "E4F0DF";
      else if (cc.k === "mag") fill = "E7E6F4";
      else if (cc.k === "pe") fill = "FBEFD8";
      else if (cc.k === "fill") fill = "D7EEF2";
      else if (cc.k === "off") fill = "F2F2F2";
      cells.push(cell(paras, { fill }));
    }
    rows.push(new TableRow({ children: cells }));
  }
  return table(rows);
}

// ---------- הרכבת המסמך ----------
const SPEC = process.argv[4] ? JSON.parse(fs.readFileSync(process.argv[4], "utf8")) : null;
const FN = t => (D.full_names && D.full_names[t]) || t;
const kids = [];
function heading(text, size, opts = {}) {
  kids.push(new Paragraph({
    children: [new TextRun({ text, font: FONT, rightToLeft: true, size, bold: true })],
    bidirectional: true, alignment: opts.center ? AlignmentType.CENTER : AlignmentType.RIGHT,
    spacing: { before: opts.before || 60, after: opts.after || 100 },
  }));
}
function pageBreak() { kids.push(new Paragraph({ children: [new PageBreak()] })); }

if (SPEC) {
  // קובץ בית: קודם מערכות הכיתות, אחר כך מערכות המורים
  heading(SPEC.title, 40, { center: true, after: 120 });
  kids.push(textPara(SPEC.subtitle || "", { size: 16, align: AlignmentType.CENTER, spacing: { after: 240 } }));
  heading("מערכות הכיתות", 32, { center: true, after: 200 });
  SPEC.classes.forEach(([kind, c], i) => {
    if (i > 0) pageBreak();
    heading("כיתה " + c + "   (מחנך/ת: " + (kind === "elem" ? D.elem : D.jun)[c].home + ")", 28);
    kids.push(classTable(kind, c));
  });
  pageBreak();
  heading("מערכות המורים", 32, { center: true, after: 200 });
  SPEC.teachers.forEach((t, i) => {
    if (i > 0) pageBreak();
    const homes = D.home_of[t] || [];
    const homeNote = homes.length ? " — מחנך/ת " + homes.map(x => x[1]).join(", ") : "";
    heading(FN(t) + homeNote, 28);
    kids.push(teacherTable(t));
  });
} else {
kids.push(new Paragraph({
  children: [new TextRun({ text: 'מערכות שעות מורים – בית חינוך ע"ש א.ד גורדון', font: FONT, rightToLeft: true, size: 40, bold: true })],
  bidirectional: true, alignment: AlignmentType.CENTER, spacing: { after: 120 },
}));
kids.push(textPara("כל מערכות המורים; אצל מחנכי הכיתות מצורפת גם מערכת הכיתה. ◦ = סדירות (לא שעת הוראה). משבצת אדומה = חוסר, מחנך/ת הכיתה נכנס/ת זמנית.", { size: 16, align: AlignmentType.CENTER, spacing: { after: 240 } }));

const names = Object.keys(D.teachers).sort((a, b) => a.localeCompare(b, "he"));
names.forEach((t, i) => {
  const homes = D.home_of[t] || [];
  const homeNote = homes.length ? " — מחנך/ת " + homes.map(x => x[1]).join(", ") : "";
  if (i > 0) kids.push(new Paragraph({ children: [new PageBreak()] }));
  kids.push(new Paragraph({
    children: [new TextRun({ text: FN(t) + homeNote, font: FONT, rightToLeft: true, size: 30, bold: true })],
    bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 60, after: 100 },
  }));
  kids.push(teacherTable(t));
  for (const [kind, c] of homes) {
    kids.push(new Paragraph({
      children: [new TextRun({ text: "מערכת כיתה " + c, font: FONT, rightToLeft: true, size: 24, bold: true })],
      bidirectional: true, alignment: AlignmentType.RIGHT, spacing: { before: 220, after: 100 },
    }));
    kids.push(classTable(kind, c));
  }
});
}

const doc = new Document({
  sections: [{
    properties: {
      page: {
        size: { width: 11906, height: 16838 },   // A4 עומד
        margin: { top: 700, bottom: 700, left: 900, right: 900 },
      },
    },
    children: kids,
  }],
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(process.argv[3], buf);
  console.log("written", process.argv[3], buf.length, "bytes");
});
