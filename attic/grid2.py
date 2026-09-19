import pymupdf, io, json
d = pymupdf.open(r"C:/Users/asifb/Downloads/מערכות מורים.pdf")
DAYS=["א","ב","ג","ד","ה","ו"]
res=[]
for pi in range(d.page_count):
    pg=d[pi]; words=pg.get_text("words")
    # header y = y of the 'יום' words
    yom=[w for w in words if w[4]=="יום" and any(abs(w2[1]-w[1])<3 and w2[4] in DAYS for w2 in words)]
    hy=min(w[1] for w in yom)
    centers={}
    for w in words:
        if w[4] in DAYS and abs(w[1]-hy)<4:
            centers[w[4]]=(w[0]+w[2])/2
    cx=sorted(centers.items(), key=lambda kv:-kv[1])  # RTL: א first
    order=[k for k,_ in cx]; xs=[v for _,v in cx]
    bounds=[]
    for i in range(len(xs)):
        lo = (xs[i]+xs[i+1])/2 if i+1<len(xs) else -1e9
        hi = (xs[i]+xs[i-1])/2 if i>0 else 1e9
        bounds.append((order[i],lo,hi))
    rightmost=max(xs)
    # hour markers: single digits right of rightmost day col, below header
    hrs=[]
    for w in words:
        if w[4] in "12345678" and len(w[4])==1 and w[1]>hy+2 and (w[0]+w[2])/2 > rightmost+8:
            hrs.append((int(w[4]), w[1], w[3]))
    hrs.sort(key=lambda t:t[1])
    seen={}; hlist=[]
    for h,y0,y1 in hrs:
        if h not in seen: seen[h]=1; hlist.append((h,y0))
    hlist.sort(key=lambda t:t[1])
    bands=[]
    for i,(h,y0) in enumerate(hlist):
        y_end = hlist[i+1][1]-1 if i+1<len(hlist) else y0+60
        bands.append((h,y0-3,y_end))
    grid={h:{dd:[] for dd in DAYS} for h,_,_ in bands}
    for w in words:
        c=(w[0]+w[2])/2
        for h,y0,y1 in bands:
            if y0<=w[1]<y1:
                for dd,lo,hi in bounds:
                    if lo<=c<hi:
                        grid[h][dd].append(w[4])
                break
    # teacher name: text below the table (largest y block, before 'מכסה')
    txt=pg.get_text().split("\n")
    name=""
    for i,l in enumerate(txt):
        if "מכסה פרונטלית" in l and i>0: name=txt[i-1].strip()
    res.append({"page":pi+1,"name":name,
        "grid":{str(h):{dd:" ".join(grid[h][dd]) for dd in DAYS if grid[h][dd]} for h,_,_ in bands}})
io.open("grids.json","w",encoding="utf-8").write(json.dumps(res,ensure_ascii=False,indent=1))
print("ok", len(res))
