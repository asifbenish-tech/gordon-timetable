# -*- coding: utf-8 -*-
"""cons_sync.py - גשר בין מסך "אילוצי מורים" (Artifact עם מסד נתונים) לקבצי המקור.

   python cons_sync.py export > seed.json
       מייצא את האילוצים הנוכחיים (data2/hdata) כרשומות למסד של המסך - זה
       מה שנטען למסך (seed) ומה שנשמר בכל רשומה כ-"base" להשוואה.
   python cons_sync.py diff <dump.json> [<שם הצעה>]
       מקבל dump של אוסף teachers מהמסך (רשימת רשומות), משווה לקבצי המקור
       ומדפיס overrides. עם שם הצעה: כותב proposals/<שם>/proposal.json
       שאפשר להריץ ב-propose.py. הנתונים בקבצי המקור משתנים רק אחרי אישור.
   מזהה רשומה: "t_" + hex(utf8(שם)) - כי מזהי מסמכים חייבים להיות ASCII."""
import io, json, os, sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from data import QUOTA as EQ, DAY_NAMES
from data2 import TCONS, MAXDAYS, DAYS_OFF2, UNAVAIL2, EVENTS2, MAGAMA, QUOTA_FILE
from hdata import CAP as HCAP, HOFF, HEV

SKIP = {'תל"ן', "מגמות", "חסר מורה", "שרית + חסן", "מדעים חיצוני", "אבי קרן צבי"}

def tid(name): return "t_" + name.encode("utf-8").hex()
def tname(i): return bytes.fromhex(i[2:]).decode("utf-8")

def current():
    rows = {}
    for t in sorted(set(EQ) | set(HCAP) | set(TCONS) | set(DAYS_OFF2) | set(HOFF) | set(QUOTA_FILE)):
        if t in SKIP: continue
        in_e = t in EQ or t in DAYS_OFF2; in_j = t in HCAP or t in HOFF
        ev = {}
        for (d, h) in EVENTS2.get(t, []): ev[f"{d},{h}"] = "סדירות"
        for (d, h) in HEV.get(t, []): ev.setdefault(f"{d},{h}", "ישיבה/הדרכה")
        for (d, h), ts in MAGAMA.items():
            if t in ts: ev[f"{d},{h}"] = "מגמות"
        tc = {k: ({str(a): b for a, b in v.items()} if isinstance(v, dict) else v) for k, v in TCONS.get(t, {}).items()}
        rows[t] = {"name": t, "side": "both" if (in_e and in_j) else ("jun" if in_j else "elem"),
                   "quota": QUOTA_FILE.get(t), "off_elem": list(DAYS_OFF2.get(t) or []), "off_jun": list(HOFF.get(t) or []),
                   "events": ev, "unavail": [f"{d},{h}" for (d, h) in UNAVAIL2.get(t, [])],
                   "tcons": tc, "maxdays": MAXDAYS.get(t)}
    return rows

def clean_tc(tc):
    out = {}
    for k, v in (tc or {}).items():
        if v in ("", None, False, [], {}): continue
        if k == "day_until": v = {str(a): int(b) for a, b in v.items() if b}
        if k == "no_slots": v = [[int(a), int(b)] for a, b in v]
        if k in ("max_hour", "max_days", "min_per_day", "max_gap"): v = int(v)
        out[k] = v
    return out

def diff(rows_db):
    cur = current(); ov = {"data2": {}, "hdata": {}}; notes = []
    def norm(x): return json.dumps(x, ensure_ascii=False, sort_keys=True)
    for r in rows_db:
        t = r.get("name") or tname(r["id"]); b = cur.get(t)
        if not b: notes.append(f"{t}: לא בקבצי המקור - מדלג"); continue
        if b["side"] != "jun" and norm(r.get("off_elem", [])) != norm(b["off_elem"]): ov["data2"].setdefault("DAYS_OFF2", {})[t] = r["off_elem"]
        if b["side"] != "elem" and norm(r.get("off_jun", [])) != norm(b["off_jun"]): ov["hdata"].setdefault("HOFF", {})[t] = r["off_jun"]
        tc = clean_tc(r.get("tcons"))
        if norm(tc) != norm(clean_tc(b["tcons"])): ov["data2"].setdefault("TCONS", {})[t] = tc or None
        if b["side"] != "jun" and (r.get("maxdays") or None) != (b["maxdays"] or None): ov["data2"].setdefault("MAXDAYS", {})[t] = r.get("maxdays") or None
        if r.get("note"): notes.append(f"{t}: הערה - {r['note']}")
    ov = {k: v for k, v in ov.items() if v}
    return ov, notes

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "export":
        rows = current()
        print(json.dumps([{"id": tid(t), **v, "base": {k: v[k] for k in ("off_elem", "off_jun", "tcons", "maxdays")}} for t, v in rows.items()], ensure_ascii=False, indent=1))
    elif cmd == "diff":
        dump = json.load(io.open(sys.argv[2], encoding="utf-8"))
        rows = dump if isinstance(dump, list) else list(dump.values())
        ov, notes = diff(rows)
        n = sum(len(v) for sec in ov.values() for v in sec.values())
        print(f"שינויים מול קבצי המקור: {n}")
        for k, sec in ov.items():
            for tab, per in sec.items():
                for t, v in per.items(): print(f"  {tab}[{t}] = {json.dumps(v, ensure_ascii=False)}")
        for x in notes: print("  " + x)
        if len(sys.argv) > 3:
            name = sys.argv[3]; d = os.path.join("proposals", name); os.makedirs(d, exist_ok=True)
            cfg = {"_doc": "נוצר מ-cons_sync.py מתוך מסך אילוצי המורים", "title": "הצעה: עדכון אילוצי מורים", "banner": "הצעה - לא מפורסם",
                   "base": "published", "env": {"STAB": "80"}, "overrides": ov}
            json.dump(cfg, io.open(os.path.join(d, "proposal.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            print(f"נכתב proposals/{name}/proposal.json - להריץ: python propose.py {name}")
    else: print(__doc__)
