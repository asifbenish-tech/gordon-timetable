# -*- coding: utf-8 -*-
"""pull_app.py - מושך את כל נתוני האפליקציה (school-gordon.web.app) מ-Firestore
   ושומר אותם ב-app_data/ (קובץ JSON לכל מסמך, מפוענח).
   קריאה בלבד - לא משנה שום דבר בפותר ולא כותב ל-Firestore.
   שימוש: python pull_app.py"""
import json, io, os, sys, urllib.request
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

URL = ("https://firestore.googleapis.com/v1/projects/school-gordon/"
       "databases/(default)/documents/schools/main/data?pageSize=300")

def decode(v):
    if "stringValue" in v: return v["stringValue"]
    if "integerValue" in v: return int(v["integerValue"])
    if "doubleValue" in v: return v["doubleValue"]
    if "booleanValue" in v: return v["booleanValue"]
    if "nullValue" in v: return None
    if "timestampValue" in v: return v["timestampValue"]
    if "mapValue" in v: return {k: decode(x) for k, x in v["mapValue"].get("fields", {}).items()}
    if "arrayValue" in v: return [decode(x) for x in v["arrayValue"].get("values", [])]
    return v

raw = json.load(urllib.request.urlopen(URL, timeout=30))
if "error" in raw:
    sys.exit("שגיאת Firestore: " + raw["error"].get("message", "?"))
os.makedirs("app_data", exist_ok=True)
for doc in raw.get("documents", []):
    name = doc["name"].split("/")[-1]
    fields = {k: decode(v) for k, v in doc.get("fields", {}).items()}
    val = fields.get("value")
    if isinstance(val, str):
        try: val = json.loads(val)
        except Exception: pass
    io.open(f"app_data/{name}.json", "w", encoding="utf-8").write(
        json.dumps({"updatedAt": fields.get("updatedAt"), "value": val}, ensure_ascii=False, indent=1))
print("נמשכו", len(raw.get("documents", [])), "מסמכים אל app_data/")
