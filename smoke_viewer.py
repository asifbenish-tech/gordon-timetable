# -*- coding: utf-8 -*-
"""smoke_viewer.py - בדיקת עשן של הלוח בדפדפן אמיתי (Chromium דרך Playwright).
   פותח את viewer.html, נכנס כהנהלה, מרנדר יסודי/חטיבה/מורים/כל המורים, ומוודא
   שאין שגיאות JS ושכל התצוגות ריקות מ"undefined". בלוח של הצעה מוודא גם שהסרט
   וסימוני היה ← נהיה מופיעים. שימוש: python smoke_viewer.py [viewer.html ...]
   יציאה 1 = כשל. go.py מריץ את זה בסוף הצינור (SMOKE=0 מדלג)."""
import asyncio, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
CHROME = next((p for p in ("/opt/pw-browsers/chromium-1194/chrome-linux/chrome",) if os.path.exists(p)), None)

JS = r"""() => {
  USER = {n: "אסיף", r: "admin", p: 1};
  document.querySelectorAll('#login,.login,[id*=auth]').forEach(e => e.remove());
  const out = {views: {}, bad: []};
  const check = (name) => {
    const cards = document.querySelectorAll('.card').length, tds = document.querySelectorAll('td').length;
    const undef = (document.body.innerText.match(/undefined|NaN|\[object/g) || []).length;
    out.views[name] = {cards, tds, undef, chg: document.querySelectorAll('td.chg').length};
    if (!cards || undef || (!tds && name !== "cons")) out.bad.push(name);
  };
  view = "elem"; pick = null; render(); check("elem");
  view = "jun"; pick = null; render(); check("jun");
  view = "teach"; pick = "*"; render(); check("teach_all");
  const t = Object.keys(DATA.teachers)[0]; view = "teach"; pick = t; render(); check("teach_one");
  // מצב עריכה: פתיחת פאנל תא, הוספת בקשת נעילה, ייצוא, ניקוי
  try {
    view = "elem"; pick = null; render();
    const td = document.querySelector("td.pick"); if (!td) out.bad.push("no-pick-cells");
    else {
      slotPanel(td.dataset.cls, td.dataset.key);
      const pb = document.querySelector("[data-pin]"); if (!pb) out.bad.push("no-pin-button"); else pb.click();
      out.pins = {pending: document.querySelectorAll("td.pend").length, btn: (document.getElementById("pinsbtn") || {}).textContent};
      if (!out.pins.pending) out.bad.push("pin-not-marked");
      pinsModal(); if (!document.querySelector("textarea")) out.bad.push("no-pins-export");
      const x = document.getElementById("pinsclear"); if (x) x.click();
      if (document.querySelectorAll("td.pend").length) out.bad.push("pins-not-cleared");
    }
  } catch (e) { out.bad.push("edit-mode: " + String(e).slice(0, 120)); }
  view = "cons"; pick = null; render(); check("cons");
  if (!document.querySelector('a[href*="artifact"]')) out.bad.push("cons-no-link");
  if (DATA.prop) {
    const pb = document.getElementById("propbanner");
    out.prop = {banner: pb && !pb.hidden ? pb.textContent : null,
                diffcells: Object.values(DATA.diff || {}).reduce((a, v) => a + Object.keys(v).length, 0)};
    if (!out.prop.banner) out.bad.push("banner");
    if (out.prop.diffcells && !Object.values(out.views).some(v => v.chg)) out.bad.push("diff-markers");
  }
  return out;
}"""

async def main(files):
    from playwright.async_api import async_playwright
    fail = 0
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
        for f in files:
            page = await b.new_page(); errs = []
            page.on("pageerror", lambda e: errs.append(str(e)))
            # שגיאות טעינת משאב (גופנים מגוגל וכד') אינן באג בלוח - רק שגיאות JS נספרות
            page.on("console", lambda m: errs.append(m.text) if m.type == "error" and not m.text.startswith("Failed to load resource") else None)
            try:
                await page.goto("file://" + os.path.abspath(f)); await page.wait_for_timeout(400)
                r = await page.evaluate(JS)
            except Exception as e: r = {"views": {}, "bad": [str(e).split("\n")[0][:200]]}
            ok = not r["bad"] and not errs
            v = " ".join(f"{k}:{x['cards']}כרטיסים/{x['tds']}תאים" + (f"/{x['chg']}שינויים" if x.get("chg") else "") for k, x in r["views"].items())
            print(("✔" if ok else "✗") + f" {os.path.basename(os.path.dirname(f)) or '.'}/{os.path.basename(f)}: {v}" + (f" | הצעה: {r['prop']}" if r.get("prop") else ""))
            if not ok: fail += 1; print("   בעיות:", r["bad"], errs[:3])
            await page.close()
        await b.close()
    return fail

if __name__ == "__main__":
    files = sys.argv[1:] or ["viewer.html"]
    sys.exit(1 if asyncio.run(main(files)) else 0)
