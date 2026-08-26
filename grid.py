import pymupdf, io, json, re
d = pymupdf.open(r"C:/Users/asifb/Downloads/מערכות מורים.pdf")
out=[]
for pi in range(d.page_count):
    pg = d[pi]
    words = pg.get_text("words")  # x0,y0,x1,y1,word,block,line,wordno
    # find header day cells
    days={}
    for w in words:
        if w[4] in ("א","ב","ג","ד","ה","ו"):
            # look for preceding "יום" on same line at similar y
            for w2 in words:
                if w2[4]=="יום" and abs(w2[1]-w[1])<3 and 0<=w[0]-w2[1]*0 and abs(w2[0]-w[0])<40:
                    days.setdefault(w[4],(min(w[0],w2[0]),max(w[2],w2[2]),w[1]))
    out.append({"page":pi+1,"days":{k:(round(v[0],1),round(v[1],1),round(v[2],1)) for k,v in days.items()}})
io.open("grid_dbg.json","w",encoding="utf-8").write(json.dumps(out[:3],ensure_ascii=False,indent=1))
