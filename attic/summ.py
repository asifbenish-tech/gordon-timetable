import pymupdf, io, collections
d = pymupdf.open(r"C:/Users/asifb/Downloads/מערכות מורים.pdf")
out=io.open("summaries.txt","w",encoding="utf-8")
for pi in range(d.page_count):
    pg=d[pi]; words=pg.get_text("words")
    txt=pg.get_text().split("\n"); name=""
    for i,l in enumerate(txt):
        if "מכסה פרונטלית" in l and i>0: name=txt[i-1].strip()
    # summary words = those containing marker chars, gather their y-lines
    ys=set()
    for w in words:
        if any(k in w[4] for k in ("אירועים","קבועים","זמין","חופש:","ימי")) or w[4] in ("שעות:",):
            ys.add(round(w[1],0))
    lines=collections.defaultdict(list)
    for w in words:
        key=round(w[1],0)
        for y in ys:
            if abs(key-y)<4: lines[y].append(w); break
    out.write(f"\n### p{pi+1} :: {name}\n")
    for y in sorted(lines):
        ws=sorted(lines[y], key=lambda w:-w[0])
        out.write("   " + " ".join(w[4] for w in ws) + "\n")
out.close()
print("done")
