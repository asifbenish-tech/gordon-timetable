# -*- coding: utf-8 -*-
import pymupdf, io, collections, re
d=pymupdf.open(r"C:/Users/asifb/Downloads/מערכות מורים.pdf")
out=io.open("recheck.txt","w",encoding="utf-8")
for pi in range(d.page_count):
    pg=d[pi]; words=pg.get_text("words")
    txt=pg.get_text().split("\n"); name=""
    for i,l in enumerate(txt):
        if "מכסה פרונטלית" in l and i>0: name=txt[i-1].strip()
    lines=collections.defaultdict(list)
    for w in words: lines[round(w[1],0)].append(w)
    keys=sorted(lines); merged=[]
    for k in keys:
        if merged and k-merged[-1][0]<4: merged[-1][1].extend(lines[k])
        else: merged.append([k,list(lines[k])])
    off=nz=""
    for k,ws in merged:
        s=" ".join(w[4] for w in sorted(ws,key=lambda w:-w[0]))
        if "ימי חופש" in s and ":" in s and "אירוע" not in s: off=s
        if "שעות לא זמין" in s: nz=s
    out.write(f"p{pi+1} | {name}\n    חופש: {off.strip()}\n    לא זמין: {nz.strip()}\n")
out.close()
