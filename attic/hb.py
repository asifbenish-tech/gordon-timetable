# -*- coding: utf-8 -*-
import io,os,sys,subprocess,re
sys.stdout.reconfigure(encoding="utf-8",errors="replace")
DEST=r"C:/Users/asifb/Desktop/מערכת שעות/_מנוע_מערכת"
HD0=io.open(DEST+"/hdata.py",encoding="utf-8").read()
def run2(n,sd,tl="90"):
    io.open("hdata.py","w",encoding="utf-8").write(sd)
    r0=subprocess.run([sys.executable,"make_unified.py"],capture_output=True)
    if r0.returncode: print(n+": GEN-ERR"); return
    os.environ["TL"]=tl
    r=subprocess.run([sys.executable,"solveALL.py"],capture_output=True,text=True,encoding="utf-8",errors="replace")
    o=(r.stdout or "")+(r.stderr or "")
    m=re.search(r"status:\s*(\w+)",o)
    print(n+": "+(m.group(1) if m else "ERR "+o[-160:].replace(chr(10),' ')))
# 0: hdata מקורי
run2("0 מקורי", HD0)
# a: פיצול ספרות/היסטוריה בלבד
ha=HD0.replace('"רב מלל":{"ז":4,"ח":4,"ט":5},','"רב מלל":{"ז":0,"ח":0,"ט":5},\n "ספרות":{"ז":2,"ח":2,"ט":0},\n "היסטוריה":{"ז":2,"ח":2,"ט":0},')
ha=ha.replace('"רב מלל":{"ז":["נעמי","תמיר","אלי","שיר"],"ח":["נעמי","תמיר","אלי","מאמי"],"ט":["נעמי","תמיר","אלי"]},',
              '"רב מלל":{"ט":["נעמי","תמיר"]},\n "ספרות":{"ז":["נעמי","שיר"],"ח":["נעמי"]},\n "היסטוריה":{"ז":["אלי","שיר"],"ח":["אלי"]},')
run2("a פיצול בלבד", ha)
# b: תנ"ך ז ריק בלבד
hb=HD0.replace('\'תנ"ך\':{"ז":["תמיר","אלי","נעמי"],"ח":["לייה"],"ט":["תמיר","אלי","נעמי"]},',
               '\'תנ"ך\':{"ז":[],"ח":["לייה"],"ט":["תמיר","אלי","נעמי"]},')
run2("b תנך-ז-ריק בלבד", hb)
