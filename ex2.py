import pymupdf, sys, io
p, out = sys.argv[1], sys.argv[2]
d = pymupdf.open(p)
with io.open(out, "w", encoding="utf-8") as f:
    f.write(f"PAGES {d.page_count}\n")
    for i in range(d.page_count):
        f.write(f"\n=== PAGE {i+1} ===\n")
        f.write(d[i].get_text())
