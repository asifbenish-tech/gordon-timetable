import pymupdf, io, collections
d = pymupdf.open(r"C:/Users/asifb/Downloads/מערכות מורים.pdf")
out=io.open("summaries.txt","w",encoding="utf-8")
for pi in range(d.page_count):
    pg=d[pi]; words=pg.get_text("words")
    txt=pg.get_text().split("\n"); name=""
    for i,l in enumerate(txt):
        if "מכסה פרונטלית" in l and i>0: name=txt[i-1].strip()
    anchor=None
    for w in words:
        if "אירועים" in w[4] or "קבועים" in w[4]:
            anchor = w[1] if anchor is None else min(anchor,w[1])
    if anchor is None: anchor=1e9
    lines=collections.defaultdict(list)
    for w in words:
        if w[1] >= anchor-14: lines[round(w[1],0)].append(w)
    keys=sorted(lines); merged=[]
    for k in keys:
        if merged and k-merged[-1][0]<4: merged[-1][1].extend(lines[k])
        else: merged.append([k,list(lines[k])])
    out.write(f"\n### p{pi+1} :: {name}\n")
    for k,ws in merged:
        s=" ".join(w[4] for w in sorted(ws,key=lambda w:-w[0]))
        if s.strip(): out.write("   "+s+"\n")
out.close()
print("ok")
