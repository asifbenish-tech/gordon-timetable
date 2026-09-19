# -*- coding: utf-8 -*-
"""capacity.py - חשבון קיבולת בלי לפתור: משבצות פנויות לכל מורה/כיתה מול השעות הנדרשות.
   גירעון כאן אומר שהפותר ייפול בוודאות; מרווח 0-1 אומר שכל שינוי קטן עלול להפיל אותו.
   הרצה: python capacity.py   (מריץ את בניית המודל של engine.py ויוצא לפני הפתרון)"""
import os, subprocess, sys
env = dict(os.environ, CAPONLY="1")
r = subprocess.run([sys.executable, "engine.py"], env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
out = r.stdout
i = out.find("קיבולת")
print(out[i:] if i >= 0 else out[-2000:])
