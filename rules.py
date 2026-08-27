# -*- coding: utf-8 -*-
"""rules.py — חוקי מדיניות מוצהרים. כל חוק: שם, תיאור, מתג הפעלה, ופונקציה.
   לביטול חוק: active=False. לשונית 'אילוצים' בלוח נבנית אוטומטית מכאן.
   ctx = globals() של המנוע: m, x (יסודי), hx/hfree (חטיבה), HSLOTS, T9, duty..."""


def r_tamir_subjects(c):
    """תמיר: חינוך/היסטוריה/אזרחות/תנ"ך בכיתות ט — שעתיים כל אחד, אצלו בלבד."""
    m, hx, HSLOTS = c["m"], c["hx"], c["HSLOTS"]
    for cls, subj, n in (("ט תמיר", "חינוך", 3), ("ט אסיף", "אזרחות", 2), ("ט אסיף", "היסטוריה", 2),
                         ("ט תמיר", "היסטוריה", 2), ("ט תמיר", "אזרחות", 2), ("ט תמיר", 'תנ"ך', 2)):
        v = [hx[(cls, s2, subj, "תמיר")] for s2 in HSLOTS if (cls, s2, subj, "תמיר") in hx]
        if v: m.Add(sum(v) == n)


def r_leah_not_late(c):
    """תנ"ך של לייה — לא בשעות 6-7 (לא בסוף היום)."""
    m, hx = c["m"], c["hx"]
    for k in [k for k in hx if k[3] == "לייה" and k[1][1] >= 6]:
        m.Add(hx[k] == 0)


def r_het_monday5(c):
    """ח גלית: יום שני — שעה 5 מאוישת (יום של 5+ שעות)."""
    m, hfree = c["m"], c["hfree"]
    m.Add(hfree[("ח גלית", (1, 5))] == 0)


def r_track_day(c):
    """יום המגמות: אחרי 4 שעות מגמה — ש5 שיעור חינוך עם המחנך (בח: מתמטיקה עם
       המורה החיצוני, כי גלית במעגל שיח); בט גם ש6-7 ריקות והולכים הביתה."""
    m, hx, hfree, T9 = c["m"], c["hx"], c["hfree"], c["T9"]
    for cz in ("ז נעמי", "ז אלי"):
        v5 = [hx[k] for k in hx if k[0] == cz and k[1] == (2, 5) and k[2] == "חינוך"]
        if v5: m.Add(sum(v5) == 1)
    v5m = [hx[k] for k in hx if k[0] == "ח גלית" and k[1] == (2, 5)
           and k[2] == "מתמטיקה" and k[3] == "מורה חיצוני"]
    if v5m: m.Add(sum(v5m) == 1)
    for c9 in T9:
        v5 = [hx[k] for k in hx if k[0] == c9 and k[1] == (4, 5) and k[2] == "חינוך"]
        if v5: m.Add(sum(v5) == 1)
        for hb in (6, 7): m.Add(hfree[(c9, (4, hb))] == 1)


def r_sifrut_historia(c):
    """ספרות (נעמי) והיסטוריה (אלי): לפחות שעה אישית בכל כיתת ז ובח (שיר משלימה בשישי)."""
    m, hx, HSLOTS = c["m"], c["hx"], c["HSLOTS"]
    for cz in ("ז נעמי", "ז אלי", "ח גלית"):
        for subj, t in (("ספרות", "נעמי"), ("היסטוריה", "אלי")):
            v = [hx[(cz, s2, subj, t)] for s2 in HSLOTS if (cz, s2, subj, t) in hx]
            if v: m.Add(sum(v) >= 1)


def r_thursday_67(c):
    """חמישי 6-7: תמיר לא מלמד (חוץ מז נעמי); אלי עם כיתתו לפחות שעה אחת."""
    m, hx = c["m"], c["hx"]
    for k in [k for k in hx if k[3] == "תמיר" and k[1] in ((4, 6), (4, 7)) and k[0] != "ז נעמי"]:
        m.Add(hx[k] == 0)
    va = [hx[k] for k in hx if k[0] == "ז אלי" and k[1] in ((4, 6), (4, 7)) and k[3] == "אלי"]
    if va: m.Add(sum(va) >= 1)


def r_duty_days(c):
    """סידור חדר אוכל חטיבה: נעמי-שלישי, אלי-שני, ח-חמישי, תמיר-ראשון, אסיף-רביעי."""
    m, duty = c["m"], c["duty"]
    for dc, dd in {"ז נעמי": 2, "ז אלי": 1, "ח גלית": 4, "ט תמיר": 0, "ט אסיף": 3}.items():
        m.Add(duty[(dc, dd)] == 1)


def r_asif_tue5(c):
    """אסיף: שיעור החינוך שאחרי המגמות בשלישי ש5 — שלו; חסר בסוף היום."""
    m, hx = c["m"], c["hx"]
    k = ("ט אסיף", (2, 5), "חינוך", "אסיף")
    if k in hx: m.Add(hx[k] == 1)


def r_galit_spread(c):
    """גלית בכיתתה גם בתחילת השבוע: לפחות שיעור אחד בראשון ואחד ברביעי."""
    m, hx, HDAY = c["m"], c["hx"], c["HDAY"]
    for d in (0, 3):
        v = [hx[k] for k in hx if k[0] == "ח גלית" and k[1][0] == d and k[3] == "גלית"]
        if v: m.Add(sum(v) >= 1)


def r_hadracha_sunday(c):
    """הדרכות ראשון: גלית+סימה בהדרכת אנגלית ש5; שרית+אורנה בהדרכת עברית ש1."""
    m, x, hx = c["m"], c["x"], c["hx"]
    for k in [k for k in hx if k[3] == "גלית" and k[1] == (0, 5)]:
        m.Add(hx[k] == 0)
    for t, sl in (("סימה", (0, 5)), ("אורנה", (0, 1)), ("שרית", (0, 1))):
        for k in [k for k in x if k[2] == t and k[1] == sl]:
            m.Add(x[k] == 0)


RULES = [
    {"id": "hadracha_sunday", "name": "הדרכות יום ראשון", "active": True, "fn": r_hadracha_sunday,
     "desc": "גלית וסימה פנויות בראשון ש5 (הדרכת אנגלית עם סיגל); שרית ואורנה פנויות בראשון ש1 (הדרכת עברית עם קטיה)."},
    {"id": "galit_spread", "name": "גלית עם כיתתה בראשון וברביעי", "active": True, "fn": r_galit_spread,
     "desc": "לפחות שיעור אחד של גלית בח בראשון ולפחות אחד ברביעי — לא הכל בסוף השבוע."},
    {"id": "tamir_subjects", "name": "המקצועות של תמיר בט", "active": True, "fn": r_tamir_subjects,
     "desc": 'חינוך, היסטוריה, אזרחות ותנ"ך בכיתות ט — שעתיים כל אחד + חינוך 3, תמיר בלבד (24 שעות).'},
    {"id": "leah_not_late", "name": "תנ\"ך לייה לא בסוף היום", "active": True, "fn": r_leah_not_late,
     "desc": "שיעורי התנ\"ך של לייה בח רק בשעות 1-5."},
    {"id": "het_monday5", "name": "ח גלית — שני 5+ שעות", "active": True, "fn": r_het_monday5,
     "desc": "יום שני של ח לא מסתיים אחרי 4 שעות."},
    {"id": "track_day", "name": "יום המגמות", "active": True, "fn": r_track_day,
     "desc": "מגמות ש1-4, שיעור חינוך עם המחנך בש5 (בח: מתמטיקה — גלית במעגל), ואז הביתה."},
    {"id": "sifrut_historia", "name": "ספרות והיסטוריה", "active": True, "fn": r_sifrut_historia,
     "desc": "נעמי (ספרות) ואלי (היסטוריה) — שעתיים בכל כיתת ז ובח; שיר משלימה בשישי בז אלי."},
    {"id": "thursday_67", "name": "חמישי 6-7", "active": True, "fn": r_thursday_67,
     "desc": "תמיר לא בשעות 6-7 של חמישי; אלי שם עם כיתתו."},
    {"id": "duty_days", "name": "תורנות חדר אוכל חטיבה", "active": True, "fn": r_duty_days,
     "desc": "ז נעמי-שלישי · ז אלי-שני · ח-חמישי · ט תמיר-ראשון · ט אסיף-רביעי (בש5 עם המחנך)."},
    {"id": "asif_tue5", "name": "אסיף בשלישי ש5", "active": True, "fn": r_asif_tue5,
     "desc": "החינוך שאחרי המגמות בכיתתו — איתו; אם יש חסר הוא בסוף היום."},
]


def apply(ctx):
    n = 0
    for r in RULES:
        if r["active"]:
            r["fn"](ctx); n += 1
    print(f"rules: הוחלו {n}/{len(RULES)} חוקים")


def export():
    """ללשונית האילוצים בלוח."""
    return [(r["name"] + ("" if r["active"] else " (כבוי)"), r["desc"]) for r in RULES]
