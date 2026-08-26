import fitz, sys
p = sys.argv[1]
d = fitz.open(p)
print("PAGES", d.page_count)
for i in range(min(d.page_count, 3)):
    print(f"=== PAGE {i+1} ===")
    print(d[i].get_text())
