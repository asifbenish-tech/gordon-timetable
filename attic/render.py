# -*- coding: utf-8 -*-
import json, io, collections
from data import *
S=json.load(io.open("solution.json",encoding="utf-8"))
with io.open("schedules.txt","w",encoding="utf-8") as f:
    for c in CLASSES:
        f.write(f"\n=== כיתה {c} ===\n")
        f.write("שעה | " + " | ".join(f"{DAY_NAMES[d]:<8}" for d in range(6)) + "\n")
        for h in range(1,7):
            row=[]
            for d in range(6):
                row.append(f"{S[c].get(f'{d},{h}','—'):<8}" if h<=DAY_HOURS[d] else f"{'':<8}")
            f.write(f" {h}   | " + " | ".join(row) + "\n")
        cnt=collections.Counter(S[c][f"{s[0]},{s[1]}"] for s in SLOTS)
        f.write("סה\"כ: " + ", ".join(f"{t} {n}" for t,n in cnt.most_common()) + f"  [{sum(cnt.values())} ש']\n")
