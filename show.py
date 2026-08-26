import json, io
r=json.load(io.open("grids.json",encoding="utf-8"))
DAYS=["א","ב","ג","ד","ה","ו"]
with io.open("grids.txt","w",encoding="utf-8") as f:
    for p in r:
        f.write(f"\n### p{p['page']} :: {p['name']}\n")
        for h in map(str,range(1,9)):
            g=p["grid"].get(h,{})
            if not g: continue
            cells=[f"{dd}:{g[dd]}" for dd in DAYS if g.get(dd)]
            if cells: f.write(f"  h{h}  " + "   ||  ".join(cells) + "\n")
